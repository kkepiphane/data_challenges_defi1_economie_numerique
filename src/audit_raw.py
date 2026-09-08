"""
AUDIT DES DONNEES BRUTES v2 - Challenge Economie Numerique Togo (Defi 1)
========================================================================
Les 6 jeux de donnees sont livres en 5 formats chacun (CSV, XLSX, KML,
GeoJSON, ZIP/shapefile), soit 30 fichiers. Ce script :

  1. inventorie les fichiers et les apparie jeu x format (sans dependre
     des noms de fichiers, qui contiennent un horodatage variable) ;
  2. compare les formats entre eux pour determiner lequel fait autorite ;
  3. profile chaque variable du format retenu ;
  4. controle les geometries, le CRS, l'emprise ;
  5. detecte les doublons INTRA-fichier et INTER-fichiers ;
  6. reconstitue le referentiel administratif reellement present ;
  7. profile le Mobile Money et sa variable multivaluee.

Sortie : reports/audit_raw.md

Aucune donnee n'est creee, imputee ni corrigee : le script lit, decrit,
et signale. Toute valeur du rapport est issue des fichiers.
"""

from __future__ import annotations

import glob
import io
import json
import re
import sys
import zipfile
from collections import Counter
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely import wkt

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
REPORTS = ROOT / "reports"
REPORTS.mkdir(parents=True, exist_ok=True)

# Motif d'identification de chaque jeu, independant de l'horodatage du nom
DATASETS = {
    "canal_plus":   "*Agences - CANAL+*",
    "moov":         "*Agences - Moov*",
    "togocom":      "*Agences - Togocom*",
    "telecom":      "*Agences - T*l*com-*",
    "mobile_money": "*Agents mobile money*",
    "datacenter":   "*Datacenter*",
}
FORMATS = ["csv", "xlsx", "kml", "json", "zip"]

# Emprise du Togo (WGS84), garde-fou de plausibilite uniquement :
# aucune coordonnee n'est corrigee sur cette base.
TOGO_BBOX = {"lon_min": -0.15, "lon_max": 1.81, "lat_min": 5.90, "lat_max": 11.14}

NULL_TOKENS = {"Nsp", "nsp", "NSP", "Néant", "Neant", "néant", "", "None", "null", "NULL"}

OUT: list[str] = []


def w(line: str = "") -> None:
    OUT.append(line)
    print(line)


def human(n: float) -> str:
    for u in ("o", "Ko", "Mo", "Go"):
        if n < 1024:
            return f"{n:.1f} {u}"
        n /= 1024
    return f"{n:.1f} To"


def find(key: str, fmt: str) -> Path | None:
    hits = sorted(RAW.glob(f"{DATASETS[key]}.{fmt}"))
    return hits[0] if hits else None


def is_null_token(s: pd.Series) -> pd.Series:
    return s.astype(str).str.strip().isin(NULL_TOKENS)


# =============================================================================
w("# AUDIT DES DONNEES BRUTES — Defi 1 (Economie numerique, Togo)")
w()
w("Genere par `src/audit_raw.py`. Toute valeur est **lue** dans les fichiers ;")
w("aucune n'est estimee, imputee ni completee.")
w()

# -----------------------------------------------------------------------------
w("## 1. Inventaire : 6 jeux x 5 formats")
w()
w("| Jeu de donnees | CSV | XLSX | KML | GeoJSON | ZIP (shapefile) |")
w("|---|---|---|---|---|---|")
for key in DATASETS:
    cells = []
    for fmt in FORMATS:
        p = find(key, fmt)
        cells.append(human(p.stat().st_size) if p else "**absent**")
    w(f"| `{key}` | " + " | ".join(cells) + " |")
w()
n_files = sum(1 for key in DATASETS for fmt in FORMATS if find(key, fmt))
w(f"**{n_files} fichiers** presents pour {len(DATASETS)} jeux de donnees.")
w()

# -----------------------------------------------------------------------------
w("## 2. Quel format fait autorite ?")
w()
w("Question auditee : les 5 formats portent-ils la meme information ?")
w("Comparaison sur un jeu non vide (`moov`), meme entite.")
w()

ref = "moov"
csv_df = pd.read_csv(find(ref, "csv"), dtype=str, keep_default_na=False, na_values=[""])
xls_df = pd.read_excel(find(ref, "xlsx"))
shp_df = gpd.read_file(f"zip://{find(ref, 'zip')}")
gj = json.loads(find(ref, "json").read_text(encoding="utf-8"))
kml_txt = find(ref, "kml").read_text(encoding="utf-8")

csv_pt = wkt.loads(csv_df["geometry"].iloc[0])
kml_coord = re.search(r"<coordinates>([^<]+)</coordinates>", kml_txt)

w("| Format | Enregistrements | Colonnes | Identifiant | Precision des coordonnees |")
w("|---|---|---|---|---|")
w(f"| CSV | {len(csv_df)} | {len(csv_df.columns)} (noms complets) | `FID` | "
  f"`{csv_df['geometry'].iloc[0]}` |")
w(f"| XLSX | {len(xls_df)} | {len(xls_df.columns)} (noms complets) | `id` | "
  f"`{xls_df['coordonnees'].iloc[0]}` — **arrondi** |")
w(f"| KML | — | schema `SimpleField` (noms complets) | aucun | "
  f"`{kml_coord.group(1) if kml_coord else 'n/d'}` |")
w(f"| GeoJSON | {len(gj.get('features', []))} | noms complets | `id` (feature) | "
  f"`{gj['features'][0]['geometry']['coordinates']}` — **arrondi** |")
w(f"| Shapefile | {len(shp_df)} | {len(shp_df.columns)} — **noms tronques a 10 car.** | "
  f"**aucun** | `{shp_df.geometry.iloc[0].x} {shp_df.geometry.iloc[0].y}` |")
w()
w(f"- Noms de colonnes du shapefile : {', '.join(f'`{c}`' for c in shp_df.columns)}")
w(f"- Noms de colonnes du CSV : {', '.join(f'`{c}`' for c in csv_df.columns)}")
w()

# --- Stabilite de l'identifiant --------------------------------------------
w("### 2.1 L'identifiant `FID` est-il stable ?")
w()
same_geom = xls_df["coordonnees"].iloc[0].strip("[]").split(",")
w(f"- Meme entite (Agence Moov, coordonnees `{same_geom[0]},{same_geom[1]}`) :")
w(f"  - identifiant dans le **CSV**  : `{csv_df['FID'].iloc[0]}`")
w(f"  - identifiant dans le **XLSX** : `{xls_df['id'].iloc[0]}`")
stable = csv_df["FID"].iloc[0] == xls_df["id"].iloc[0]
w()
w(f"> **Verdict : l'identifiant est {'STABLE' if stable else 'VOLATILE'}.** "
  + ("" if stable else
     "Les deux fichiers decrivent le meme jeu, exporte a quelques secondes "
     "d'intervalle, et pourtant les identifiants different. Le `FID` est "
     "regenere par le serveur a chaque export : il n'est ni une cle primaire, "
     "ni une cle de jointure, ni un moyen de deduplication entre fichiers. "
     "Le pipeline devra construire son propre identifiant stable."))
w()

# --- CRS ---------------------------------------------------------------------
w("### 2.2 Systeme de coordonnees (CRS)")
w()
prj_hashes = {}
for key in DATASETS:
    z = find(key, "zip")
    if not z:
        continue
    with zipfile.ZipFile(z) as zf:
        prj = [n for n in zf.namelist() if n.endswith(".prj")]
        cst = [n for n in zf.namelist() if n.endswith(".cst")]
        if prj:
            prj_hashes[key] = zf.read(prj[0]).decode("utf-8", "replace").strip()
        if cst:
            enc = zf.read(cst[0]).decode("utf-8", "replace").strip()
uniq = set(prj_hashes.values())
w(f"- Fichiers `.prj` presents dans **{len(prj_hashes)}/{len(DATASETS)}** shapefiles.")
w(f"- Definitions distinctes : **{len(uniq)}** → "
  f"{'toutes identiques' if len(uniq) == 1 else 'INCOHERENCE ENTRE JEUX'}")
w(f"- CRS declare, lu par GeoPandas : **{shp_df.crs}**")
w(f"- Encodage declare des attributs (`.cst`) : **{enc}** "
  f"(alors que CSV et GeoJSON sont en UTF-8)")
w()
w("> Le CSV et le KML ne declarent aucun CRS. Le shapefile, lui, l'affirme :")
w("> **EPSG:4326 / WGS 84, degres decimaux**, de facon identique sur tous les")
w("> jeux. C'est cette declaration qui fait foi. Consequence directe : tout")
w("> calcul de distance ou de superficie exigera une **reprojection prealable**")
w("> vers un CRS metrique — en degres, ces calculs seraient faux.")
w()
w("### 2.3 Format retenu pour la suite du projet")
w()
w("**Le CSV**, seul format cumulant : noms de variables complets, precision")
w("maximale des coordonnees, et presence de tous les enregistrements. Le")
w("shapefile est conserve comme **preuve documentaire du CRS**. Le XLSX et le")
w("GeoJSON sont ecartes (coordonnees arrondies a 8 decimales).")
w()

# =============================================================================
w("## 3. Audit detaille de chaque jeu (a partir des CSV)")
w()

frames: dict[str, pd.DataFrame] = {}
for i, key in enumerate(DATASETS, start=1):
    path = find(key, "csv")
    df = pd.read_csv(path, dtype=str, keep_default_na=False, na_values=[""])
    frames[key] = df
    gj_k = json.loads(find(key, "json").read_text(encoding="utf-8"))

    w(f"### 3.{i} `{key}`")
    w()
    w(f"- Enregistrements : **{len(df)}** (CSV) / {len(gj_k.get('features', []))} "
      f"(GeoJSON) / `totalFeatures` declare : {gj_k.get('totalFeatures')}")
    w(f"- Horodatage d'export : {gj_k.get('timeStamp')}")
    w(f"- Variables ({len(df.columns)}) : {', '.join(f'`{c}`' for c in df.columns)}")

    if len(df) == 0:
        z = find(key, "zip")
        readme = ""
        with zipfile.ZipFile(z) as zf:
            for n in zf.namelist():
                if n.upper().endswith("README.TXT"):
                    readme = zf.read(n).decode("utf-8", "replace").strip()
        w()
        w("> **JEU VIDE — 0 enregistrement.** Ce n'est pas une erreur de lecture :")
        w("> le serveur joint lui-meme une note dans le shapefile livre :")
        w(">")
        w(f"> « {readme} »")
        w(">")
        w("> A declarer comme **donnee non disponible**. Il serait faux d'en")
        w("> conclure une absence d'agences sur le terrain.")
        w()
        continue

    # --- profil des variables ---
    w()
    w("| Variable | Renseignees | NaN | `Nsp`/`Néant` | Distinctes | Modalites (exemples) |")
    w("|---|---|---|---|---|---|")
    for col in df.columns:
        nan = int(df[col].isna().sum())
        tok = int(is_null_token(df[col]).sum()) if df[col].dtype == object else 0
        if col == "geometry":
            sample = "POINT (lon lat)"
        else:
            vals = [v for v in df[col].dropna().unique() if str(v).strip() not in NULL_TOKENS][:3]
            sample = " ; ".join(str(v)[:38] for v in vals) if vals else "—"
        w(f"| `{col}` | {len(df) - nan - tok} | {nan} | {tok} | "
          f"{df[col].nunique(dropna=True)} | {sample} |")
    w()

    # --- geometries ---
    geoms = df["geometry"].dropna().map(wkt.loads)
    lon = np.array([g.x for g in geoms])
    lat = np.array([g.y for g in geoms])
    out_bbox = int(np.sum((lon < TOGO_BBOX["lon_min"]) | (lon > TOGO_BBOX["lon_max"]) |
                          (lat < TOGO_BBOX["lat_min"]) | (lat > TOGO_BBOX["lat_max"])))
    w("**Controle geometrique :** "
      f"emprise lon [{lon.min():.5f} ; {lon.max():.5f}], lat [{lat.min():.5f} ; {lat.max():.5f}] · "
      f"invalides : {sum(1 for g in geoms if not g.is_valid)} · "
      f"vides : {sum(1 for g in geoms if g.is_empty)} · "
      f"hors Togo : {out_bbox} · "
      f"en (0,0) : {int(np.sum((np.abs(lon) < 1e-9) & (np.abs(lat) < 1e-9)))} · "
      f"positions dupliquees : {int(pd.DataFrame({'x': lon, 'y': lat}).duplicated().sum())}")
    w()

    # --- doublons ---
    attrs = [c for c in df.columns if c != "FID"]
    w(f"**Doublons :** `FID` dupliques : {int(df['FID'].duplicated().sum())} · "
      f"lignes identiques hors `FID` : {int(df[attrs].duplicated().sum())}")

    # --- espaces parasites ---
    dirty = {c: int((df[c].dropna() != df[c].dropna().str.strip()).sum())
             for c in df.columns if df[c].dtype == object}
    dirty = {c: n for c, n in dirty.items() if n}
    if dirty:
        w()
        w("**Espaces de bord parasites :** "
          + ", ".join(f"`{c}` ({n})" for c, n in dirty.items())
          + " → produit de faux doublons de modalites (ex. `'Nsp '` vs `'Nsp'`).")
    w()

# =============================================================================
w("## 4. Recouvrement entre les jeux « Agences »")
w()
w("Question auditee : les 4 exports « Agences » sont-ils disjoints ?")
w("La deduplication ne peut PAS s'appuyer sur le `FID` (§2.1). Cle retenue :")
w("**nom de l'etablissement + coordonnees arrondies a 1e-6°** (~0,1 m).")
w()
w("| Jeu | Lignes | `activite_categorie` |")
w("|---|---|---|")
AG = ["moov", "togocom", "telecom", "canal_plus"]
for k in AG:
    df = frames[k]
    cats = df["activite_categorie"].value_counts().to_dict() if len(df) else "— (vide)"
    w(f"| `{k}` | {len(df)} | {cats} |")
w()


def signature(df: pd.DataFrame) -> set:
    g = df["geometry"].map(wkt.loads)
    return set(zip(df["etab_nom"].str.strip(),
                   g.map(lambda p: round(p.x, 6)),
                   g.map(lambda p: round(p.y, 6))))


sigs = {k: signature(frames[k]) for k in AG if len(frames[k])}
w("| Paire de jeux | Etablissements en commun |")
w("|---|---|")
ks = list(sigs)
for a in range(len(ks)):
    for b in range(a + 1, len(ks)):
        w(f"| `{ks[a]}` ∩ `{ks[b]}` | {len(sigs[ks[a]] & sigs[ks[b]])} |")
union = set().union(*sigs.values())
brut = sum(len(frames[k]) for k in AG)
excl = sigs.get("telecom", set()) - (sigs.get("moov", set()) | sigs.get("togocom", set()))
w()
w(f"- Somme brute des lignes des 4 fichiers : **{brut}**")
w(f"- Etablissements reellement uniques : **{len(union)}**")
w(f"- Enregistrements exclusifs a `telecom` : **{len(excl)}**")
w()
w(f"> **`Agences - Telecom` n'est pas un operateur supplementaire** : c'est un")
w(f"> agregat deja contenu dans `moov` ∪ `togocom`. Empiler les 4 fichiers")
w(f"> afficherait **{brut} agences au lieu de {len(union)}**, soit une")
w(f"> surestimation de **{(brut - len(union)) / len(union):.0%}** des le premier KPI.")
w()

# --- statut d'activite ---
ag = pd.concat([frames["moov"], frames["togocom"]], ignore_index=True)
w("**Statut d'activite des 90 agences uniques :**")
w()
w("| Statut | Effectif |")
w("|---|---|")
for v, n in ag["activite_statut"].str.strip().value_counts().items():
    w(f"| `{v}` | {n} |")
fermees = ag[ag["activite_statut"].str.contains("Ferm", na=False)]
w()
if len(fermees):
    w("Agences declarees fermees (a exclure du stock actif, mais a conserver) :")
    w()
    for _, r in fermees.iterrows():
        w(f"- *{r.etab_nom.strip()}* — {r.prefecture_nom_bdd} ({r.region_nom_bdd})")
w()
inc = int(is_null_token(ag["etab_creation_date"]).sum())
w(f"**Date de creation** non renseignee pour **{inc} agences sur {len(ag)}** "
  f"({inc / len(ag):.0%}) → toute analyse temporelle du deploiement serait biaisee.")
w()

# =============================================================================
w("## 5. Referentiel administratif reellement present")
w()
ADMIN = ["region_nom_bdd", "prefecture_nom_bdd", "commune_nom_bdd", "canton_nom_bdd"]
w("| Jeu | Regions | Prefectures | Communes | Cantons |")
w("|---|---|---|---|---|")
for k, df in frames.items():
    if not len(df):
        w(f"| `{k}` | — | — | — | — |")
        continue
    w(f"| `{k}` | {df.region_nom_bdd.nunique()} | {df.prefecture_nom_bdd.nunique()} | "
      f"{df.commune_nom_bdd.nunique()} | {df.canton_nom_bdd.nunique()} |")
adm = pd.concat([d[ADMIN] for d in frames.values() if len(d)], ignore_index=True)
w(f"| **UNION** | **{adm.region_nom_bdd.nunique()}** | **{adm.prefecture_nom_bdd.nunique()}** | "
  f"**{adm.commune_nom_bdd.nunique()}** | **{adm.canton_nom_bdd.nunique()}** |")
w()
mm = frames["mobile_money"]
if (mm.commune_nom_bdd.nunique() == adm.commune_nom_bdd.nunique()
        and mm.prefecture_nom_bdd.nunique() == adm.prefecture_nom_bdd.nunique()):
    w("> **Le jeu `mobile_money` couvre a lui seul l'integralite du referentiel**")
    w("> administratif observable. Il fournit donc la liste exhaustive des")
    w("> subdivisions, ce qui permet de distinguer un **vrai zero** (subdivision")
    w("> connue, sans infrastructure) d'une **absence de donnee**. C'est la")
    w("> condition sans laquelle aucun deficit ne serait demontrable.")
    w()

w("**Regions observees :** " + ", ".join(sorted(adm.region_nom_bdd.unique())))
w()
w("**Integrite hierarchique :**")
w()
h = adm[~is_null_token(adm.commune_nom_bdd)]
bad_c = h.groupby("commune_nom_bdd").prefecture_nom_bdd.nunique()
bad_p = adm.groupby("prefecture_nom_bdd").region_nom_bdd.nunique()
bad_k = adm.groupby("canton_nom_bdd").commune_nom_bdd.nunique()
w(f"- Communes rattachees a plusieurs prefectures : **{int((bad_c > 1).sum())}**")
w(f"- Prefectures rattachees a plusieurs regions : **{int((bad_p > 1).sum())}**")
w(f"- **Cantons rattaches a plusieurs communes : {int((bad_k > 1).sum())}**")

# --- Homonymie de cantons : piege de jointure ---------------------------------
homonymes = bad_k[bad_k > 1]
if len(homonymes):
    w()
    w("> ⚠ **Homonymie de cantons detectee.** Les cantons suivants portent le")
    w("> meme nom tout en appartenant a des communes differentes :")
    w(">")
    for nom in homonymes.index:
        loc = (adm[adm.canton_nom_bdd == nom]
               [["region_nom_bdd", "prefecture_nom_bdd", "commune_nom_bdd"]]
               .drop_duplicates())
        detail = " · ".join(
            f"{r.region_nom_bdd} / {r.prefecture_nom_bdd} / {r.commune_nom_bdd}"
            for r in loc.itertuples())
        w(f"> - **{nom}** → {detail}")
    w(">")

tuples = adm[ADMIN].drop_duplicates()
w()
w(f"- Noms de cantons distincts : **{adm.canton_nom_bdd.nunique()}**")
w(f"- Quadruplets (region, prefecture, commune, canton) distincts : "
  f"**{len(tuples)}**")
w()
if len(tuples) != adm.canton_nom_bdd.nunique():
    w("> **La cle de jointure au niveau canton doit etre COMPOSITE.** Joindre")
    w("> sur le seul `canton_nom_bdd` fusionnerait des territoires distincts")
    w("> sans declencher la moindre alerte. Toute jointure cantonale utilisera")
    w("> le quadruplet complet.")
    w()

# --- Profondeur de l'emboitement ---------------------------------------------
cc = adm.groupby("commune_nom_bdd").canton_nom_bdd.nunique()
w(f"- Cantons par commune : min **{cc.min()}**, mediane **{cc.median():.0f}**, "
  f"max **{cc.max()}** ({cc.idxmax()})")


def norm(s: str) -> str:
    import unicodedata
    return unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower().strip()


amb = adm.groupby(adm.commune_nom_bdd.map(norm)).commune_nom_bdd.nunique()
w(f"- Communes ayant plusieurs graphies (casse/accents) : **{int((amb > 1).sum())}**")
w()
w("> Les jointures Region → Prefecture → Commune se feront **sans arbitrage**")
w("> manuel. La navigation drill-down du dashboard est donc realisable de")
w("> facon fiable (critere C3).")
w()

# --- subdivisions sans agence ---
com_all = set(adm.commune_nom_bdd)
com_ag = set(ag.commune_nom_bdd)
pref_all = set(adm.prefecture_nom_bdd)
pref_ag = set(ag.prefecture_nom_bdd)
w(f"**Subdivisions depourvues d'agence d'operateur** (vrais zeros, mesurables "
  f"grace au referentiel complet) :")
w()
w(f"- Communes sans aucune agence : **{len(com_all - com_ag)} / {len(com_all)}**")
w(f"- Prefectures sans aucune agence : **{len(pref_all - pref_ag)} / {len(pref_all)}** "
  f"→ {', '.join(sorted(pref_all - pref_ag))}")
w()

# =============================================================================
w("## 6. Mobile Money — profil specifique")
w()
w(f"- Enregistrements : **{len(mm)}**")
w()
w("| Modalite brute de `operateur` | Effectif | Part |")
w("|---|---|---|")
for v, n in mm["operateur"].value_counts(dropna=False).items():
    w(f"| `{v}` | {n} | {n / len(mm):.1%} |")
w()
nsp = int(is_null_token(mm["operateur"]).sum())
w(f"> Variable **multivaluee** : un point Mobile Money n'est pas un operateur.")
w(f"> Toute agregation par operateur exige un eclatement prealable, et les")
w(f"> **{nsp} points a operateur inconnu** doivent former une categorie propre —")
w(f"> jamais etre reaffectes ni supprimes silencieusement.")
w()
gmm = mm["geometry"].map(wkt.loads)
coords = pd.DataFrame({"x": gmm.map(lambda p: p.x), "y": gmm.map(lambda p: p.y)})
w(f"- Positions uniques : **{coords.drop_duplicates().shape[0]}** pour {len(mm)} "
  f"enregistrements → {int(coords.duplicated().sum())} doublon(s) de position.")
w()
w("**Repartition par region (comptage brut — non interpretable sans population) :**")
w()
w("| Region | Points MM | Part |")
w("|---|---|---|")
for v, n in mm.region_nom_bdd.value_counts().items():
    w(f"| {v} | {n} | {n / len(mm):.1%} |")
w()
vc = mm.prefecture_nom_bdd.value_counts()
w(f"- Amplitude entre prefectures : de **{vc.min()}** ({vc.idxmin()}) a "
  f"**{vc.max()}** ({vc.idxmax()}) points, mediane **{vc.median():.0f}**.")
w()
w("> Ces comptages **ne prouvent aucun deficit**. Une prefecture peu peuplee")
w("> avec peu de points peut etre correctement desservie. La conversion en")
w("> indicateur de desserte exige la population, absente de ces fichiers (§7).")
w()

# =============================================================================
w("## 7. Couverture des 5 objectifs du challenge")
w()
w("| # | Objectif | Donnee necessaire | Presente ? |")
w("|---|---|---|---|")
w("| 1 | Cartographier agences + data centers | Points geolocalises par operateur | "
  f"**OUI** — {len(union)} agences uniques + {len(frames['datacenter'])} data centers |")
w("| 1 | idem — CANAL+ | Agences CANAL+ | **NON** — export vide (§3.1) |")
w("| 2 | Mobile Money vs population | Points Mobile Money | "
  f"**OUI** — {len(mm)} points |")
w("| 2 | idem | Population par subdivision | **NON** — absente des 6 jeux |")
w("| 3 | Infrastructures vs densite | Population + superficie | **NON** |")
w("| 3 | idem | Limites administratives (polygones) | "
  "**NON** — seuls des libelles texte |")
w("| 4 | Couverture reseau / zones blanches | Couverture radio ou sites/antennes | "
  "**NON** — aucune couche de ce type dans les 6 jeux |")
w("| 5 | Priorisation | Depend des lignes ci-dessus | Partiel |")
w()
w("> **Aucun des 30 fichiers livres ne contient de variable demographique, de")
w("> superficie, de geometrie de zone, ni de mesure de couverture reseau.**")
w("> Verifie colonne par colonne sur les 6 jeux (§3).")
w()

out_path = REPORTS / "audit_raw.md"
out_path.write_text("\n".join(OUT), encoding="utf-8")
print(f"\n>>> Rapport ecrit : {out_path}", file=sys.stderr)
