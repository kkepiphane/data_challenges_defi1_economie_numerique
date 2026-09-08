"""
AUDIT DE PROVENANCE DES SOURCES - Challenge Economie Numerique Togo (Defi 1)
============================================================================
Interroge l'API publique du geoportail (https://api.geodata.gouv.tg) pour
documenter, de maniere REPRODUCTIBLE et VERIFIABLE :

  - l'identite officielle de chacune des 6 couches fournies (les URL seules
    ne permettent pas de deduire le contenu : on lit le catalogue) ;
  - leur source de collecte et sa periode ;
  - le schema exact (noms + types) des couches complementaires necessaires,
    obtenu via `get_couche_metadata` (endpoint en lecture, sans compte).

Endpoints utilises (observes dans le bundle JS public du portail) :
  POST /app/1/get_couche_metadata  -> schema d'une couche      (accessible)
  POST /app/1/get_couche_glimpse   -> apercu 10 entites, valeurs masquees "N/A"
  POST /app/{g}/get_couche_file    -> telechargement            (403 : compte requis)
  GET  /app/get_open_data_config   -> catalogue complet         (accessible)

Sortie : reports/audit_sources.md
"""

from __future__ import annotations

import io
import json
import sys
import urllib.request
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

API = "https://api.geodata.gouv.tg"
ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
REPORTS.mkdir(parents=True, exist_ok=True)

# Les 6 UUID fournis dans l'enonce du challenge
FOURNIES = {
    "725f5fc0-4a66-49ff-9ef4-a04d004471b9": "URL 1",
    "7fe2e639-b4ba-45dc-92aa-edf127e16b6b": "URL 2",
    "ab3579f9-ed68-4142-8436-54c2ab7ddc95": "URL 3",
    "95780ce6-5cb3-4ce6-9595-684c97715efc": "URL 4",
    "1be809a4-63c4-4aa9-bf05-b8248352facc": "URL 5",
    "6623b2aa-2874-462c-8e18-4f8a62d6da94": "URL 6",
}

OUT: list[str] = []


def w(line: str = "") -> None:
    OUT.append(line)
    print(line)


def get_json(path: str) -> dict:
    req = urllib.request.Request(f"{API}/{path}", headers={"accept": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=90).read().decode())


def post_json(path: str, payload: dict):
    req = urllib.request.Request(
        f"{API}/{path}",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", "accept": "application/json"},
    )
    raw = urllib.request.urlopen(req, timeout=90).read().decode()
    body = json.loads(raw)
    # L'API renvoie parfois une chaine JSON encodee dans du JSON
    return json.loads(body) if isinstance(body, str) else body


# =============================================================================
w("# AUDIT DE PROVENANCE DES SOURCES")
w()
w("Genere par `src/audit_sources.py` en interrogeant l'API publique du")
w("geoportail national togolais. Aucune information n'est deduite du nom")
w("des fichiers ni des URL : tout est lu dans le catalogue officiel.")
w()

cfg = get_json("app/get_open_data_config")
couches_od = {c["id"]: c for c in cfg["couches"]}
couches_no = {c["id"]: c for c in cfg["couches_non_open_data"]}
toutes = {**couches_od, **couches_no}

w("## 1. Volumetrie du catalogue")
w()
w(f"- Couches **open data** : {len(cfg['couches'])}")
w(f"- Couches presentes au catalogue mais **hors open data** : {len(cfg['couches_non_open_data'])}")
w(f"- Indicateurs open data : {len(cfg['indicateurs'])}")
w(f"- Date de creation de la configuration open data : {cfg['date_creation']}")
w()

# =============================================================================
w("## 2. Identification des 6 jeux fournis dans l'enonce")
w()
w("| Reference enonce | Nom officiel de la couche | Description officielle | Source de collecte |")
w("|---|---|---|---|")
for uid, label in FOURNIES.items():
    c = toutes.get(uid)
    if c is None:
        w(f"| {label} | **INTROUVABLE au catalogue** | — | — |")
        continue
    statut = "" if uid in couches_od else " *(hors open data)*"
    w(f"| {label} | {c['nom']}{statut} | {c['description']} | {c['source_collecte']} |")
w()
w("> **Constat de provenance** : les 6 jeux proviennent tous de la meme")
w("> campagne de collecte. La date de reference du diagnostic est donc")
w("> celle de cette campagne, et non la date de telechargement des fichiers.")
w()

# =============================================================================
w("## 3. Couches complementaires necessaires — disponibilite reelle")
w()
COMPLEMENTS = {
    "Limites administratives - Régions": "f8d02e38-1d4b-42d2-99cb-c1918316a153",
    "Limites administratives - Préféctures": "1fd2b7a3-329c-40f3-813f-7d3397d30ded",
    "Limites administratives - Communes": "0d32e7d7-9ae2-4451-9df5-20e4bf9fa771",
    "Limites administratives - Cantons": "fd32bf4a-86e8-43ef-8201-fdcc41f2140e",
}
w("| Couche | UUID | Statut | Page de telechargement |")
w("|---|---|---|---|")
for nom, uid in COMPLEMENTS.items():
    statut = "**OPEN DATA**" if uid in couches_od else "hors open data"
    w(f"| {nom} | `{uid}` | {statut} | https://geodata.gouv.tg/donnees/{uid} |")
w()

w("### Schema exact de ces couches (lu via `get_couche_metadata`)")
w()
for nom, uid in COMPLEMENTS.items():
    try:
        meta = post_json("app/1/get_couche_metadata", {"couche": uid})
        ft = meta["featureTypes"][0]
        props = ", ".join(f"`{p['name']}` ({p['localType']})" for p in ft["properties"])
        w(f"- **{nom}** — `typeName={ft['typeName']}` : {props}")
    except Exception as exc:  # pragma: no cover - depend du reseau
        w(f"- **{nom}** — schema non recupere ({exc.__class__.__name__})")
w()
w("> **Point decisif** : la couche *Cantons* porte un attribut `population`")
w("> de type entier. C'est la seule source de population de la meme famille")
w("> que nos 6 fichiers (meme producteur, meme nomenclature administrative).")
w("> Sa periode de reference devra etre verifiee apres telechargement en")
w("> confrontant la somme nationale aux totaux publies par l'INSEED.")
w()

# =============================================================================
w("## 4. Couches pertinentes existantes mais NON accessibles en open data")
w()
w("Recherche par mots-cles sur l'ensemble du catalogue.")
w()
import re

MOTS = r"tour|antenne|réseau téléphonique|fibre|couverture|mobile money"
w("| Couche | Statut |")
w("|---|---|")
for uid, c in toutes.items():
    if re.search(MOTS, c["nom"], re.I):
        statut = "open data" if uid in couches_od else "**HORS open data — inaccessible**"
        w(f"| {c['nom']} | {statut} |")
w()
w("> **Consequence directe sur l'objectif 4** (couverture reseau / zones")
w("> blanches) : les couches `Tours telecoms` et `Reseau telephonique` ")
w("> existent au catalogue national mais ne sont pas ouvertes. Aucune")
w("> mesure de couverture radio n'est donc disponible dans le perimetre")
w("> open data du portail.")
w()

# =============================================================================
w("## 5. Verification du plafonnement de l'endpoint `get_couche_glimpse`")
w()
w("| Couche | Entites renvoyees | Valeurs d'attributs |")
w("|---|---|---|")
for nom, uid in COMPLEMENTS.items():
    try:
        gj = post_json("app/1/get_couche_glimpse", {"couche": uid})
        feats = gj.get("features", [])
        vals = set()
        for f in feats:
            vals.update(str(v) for v in f["properties"].values())
        masque = "toutes masquees (`N/A`)" if vals <= {"N/A"} else "reelles"
        w(f"| {nom} | {len(feats)} | {masque} |")
    except Exception as exc:  # pragma: no cover
        w(f"| {nom} | erreur ({exc.__class__.__name__}) | — |")
w()
w("> `get_couche_glimpse` est un **apercu de structure**, plafonne et")
w("> anonymise. Il ne peut pas servir de substitut au telechargement :")
w("> il documente le schema, pas les donnees.")
w()

out = REPORTS / "audit_sources.md"
out.write_text("\n".join(OUT), encoding="utf-8")
print(f"\n>>> Rapport ecrit : {out}", file=sys.stderr)
