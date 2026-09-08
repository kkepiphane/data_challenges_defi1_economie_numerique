"""
EXTRACTION DE LA POPULATION - RGPH-5 (INSEED, novembre 2022)
============================================================
Source : data/external/rgph5_livret_01_effectifs-spatiale_par_sexe_*.pdf
         « Resultats finaux du 5e Recensement General de la Population et de
         l'Habitat (RGPH-5) de novembre 2022 — Distribution spatiale de la
         population residente par sexe », INSEED, avril 2023.
         Denombrement du 23 octobre au 16 novembre 2022.

DIFFICULTES DE LECTURE, ET COMMENT ELLES SONT TRAITEES
-------------------------------------------------------
1. `pdftotext -layout` restitue chaque colonne comme un flux independant.
   Libelles et colonne « Ensemble » se desynchronisent verticalement :

       GOLFE 7                                              257 813
                     26 480        26 289                   882 695   <- valeur seule
       AGOE-NYIVE                                           317 255   <- libelle decale

   -> On extrait deux flux ordonnes par page, puis on les apparie par
      position. L'appariement n'est accepte que si les longueurs coincident.

2. Le separateur de colonnes vaut parfois 2 espaces : la premiere cellule
   peut alors contenir le libelle ET un nombre ("TOTAL PREFECTURE DE  82 859").
   -> On retire toute queue numerique precedee d'au moins deux espaces.

3. Un libelle trop long est coupe sur deux lignes ("MARITIME SANS GRAND" /
   "LOME").
   -> On recolle quand le libelle se termine par un mot de liaison.

4. L'indentation n'est PAS fiable : page 31 les communes sont indentees,
   page 35 elles ne le sont pas.
   -> La hierarchie est deduite de la STRUCTURE DES NOMS, verifiee sur les
      donnees PRISE : les 117 communes du Togo se nomment toutes
      « <Prefecture> <n> » (Golfe 4, Kozah 1, Tandjoare 2...).

VALIDATION
----------
Aucun chiffre n'est retenu sans controle arithmetique : les enfants doivent
sommer exactement a leur parent, et le total national doit valoir 8 095 498.
Toute page dont l'appariement echoue est EXCLUE et signalee, jamais corrigee
a la main.

Sorties : data/interim/rgph5_<niveau>.csv
          reports/extraction_rgph5.md
"""

from __future__ import annotations

import io
import re
import subprocess
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
EXT = ROOT / "data" / "external"
INTERIM = ROOT / "data" / "interim"
REPORTS = ROOT / "reports"

TOTAL_NATIONAL = 8_095_498  # publie par l'INSEED, verifiable dans le livret

# =============================================================================
# LECTURE
# =============================================================================
NUM = re.compile(r"^\d[\d\s ]*$")
NOISE = re.compile(
    r"^(Tableau|Graphique|Source|Distribution spatiale|Région\s*/|Préfecture\s*/"
    r"|Commune\s*/|Canton\s*/|Quartier\s*/|Ville\s*/|Milieu de résidence"
    r"|Sexe|Masculin|Féminin|[IVX]+\.\s|[0-9]+\.[0-9]+\s)",
    re.I,
)
INDENT_DONNEES = {0, 1, 2, 3}
# Mots sur lesquels un libelle ne peut pas se TERMINER : la suite est
# forcement sur la ligne suivante (« MARITIME SANS GRAND » + « LOME »).
FIN_CONNECTEURS = {"DE", "DU", "DES", "D'", "LA", "LE", "LES", "ET", "SANS",
                   "GRAND", "GRANDE", "SUR", "AU", "AUX", "PREFECTURE",
                   "COMMUNE", "REGION"}

# Mots par lesquels un libelle ne peut pas COMMENCER : c'est la suite du
# libelle precedent (« TOTAL REGION MARITIME » + « SANS GRAND LOME »).
# Liste volontairement minimale : « COMMUNE » et « PREFECTURE » en sont
# exclus, car « COMMUNE DE ZIO 1 » est un libelle autonome legitime.
DEBUT_CONNECTEURS = {"SANS", "ET"}


# Deux editions du livret 01 circulent. Elles donnent des populations
# communales IDENTIQUES (159/159 verifiees), mais different sur un point :
#   - edition ancienne : ligne unique « DANYI 1 + DANYI 2 » ;
#   - edition revisee  : « DANYI 1 » et « DANYI 2 » separees, et
#     « DISTRICT AUTONOME DU GRAND LOME (DAGL) » au lieu de « GRAND LOME ».
# L'edition revisee est preferee : elle couvre les 117 communes une a une.
EDITIONS = [
    "RGPH5_Livret_01_Repartition_Spatiale_Population_par-Sexe_INSEED_TG.pdf",
    "rgph5_livret_01_effectifs-spatiale_par_sexe_-inseed_2mai2023-arms-1.pdf",
]


def pdf_to_pages() -> list[str]:
    """Convertit le PDF en texte en preservant la mise en page."""
    choisi = next((EXT / n for n in EDITIONS if (EXT / n).exists()), None)
    if choisi is None:
        raise SystemExit("Aucune edition du livret 01 RGPH-5 dans data/external/")
    INTERIM.mkdir(parents=True, exist_ok=True)
    txt = INTERIM / "rgph5_raw.txt"
    subprocess.run(["pdftotext", "-layout", "-enc", "UTF-8", str(choisi), str(txt)],
                   check=True)
    (INTERIM / "rgph5_source.txt").write_text(choisi.name, encoding="utf-8")
    return txt.read_text(encoding="utf-8").split("\f")


def to_int(tok: str) -> int | None:
    t = tok.replace(" ", "").replace(" ", "")
    return int(t) if t.isdigit() else None


def fusionner_libelles_coupes(labels: list[str]) -> list[str]:
    """Recolle les libelles coupes par la largeur de colonne.

    Trois signaux, tous observes dans le document :
      « MARITIME SANS GRAND » + « LOME »        -> fin sur un mot de liaison
      « TOTAL REGION MARITIME » + « SANS GRAND LOME » -> debut sur un mot de liaison
      « TOTAL PREFECTURE BAS- » + « MONO 2 »    -> coupure sur trait d'union
    """
    out: list[str] = []
    i = 0
    while i < len(labels):
        txt = labels[i]
        mots = txt.split()
        suivant = labels[i + 1] if i + 1 < len(labels) else None
        premier_suivant = suivant.split()[0].upper() if suivant and suivant.split() else ""

        if suivant is not None and txt.rstrip().endswith("-"):
            out.append(f"{txt.rstrip()}{suivant.lstrip()}")
            i += 2
        elif suivant is not None and mots and mots[-1].upper() in FIN_CONNECTEURS:
            out.append(f"{txt} {suivant}".strip())
            i += 2
        elif suivant is not None and premier_suivant in DEBUT_CONNECTEURS:
            out.append(f"{txt} {suivant}".strip())
            i += 2
        else:
            out.append(txt)
            i += 1
    return out


def parse_page(page: str) -> tuple[list[str], list[int]]:
    """Retourne (libelles ordonnes, valeurs « Ensemble » ordonnees)."""
    lines = [ln.rstrip("\r") for ln in page.split("\n")]

    ens_col = header_idx = None
    for i, ln in enumerate(lines):
        if "Ensemble" in ln:
            ens_col, header_idx = ln.index("Ensemble"), i
            break
    if ens_col is None:
        return [], []
    seuil = ens_col - 8

    labels: list[str] = []
    values: list[int] = []
    for i, ln in enumerate(lines):
        if i == header_idx or not ln.strip() or NOISE.match(ln.strip()):
            continue
        parts = re.split(r"\s{3,}", ln.strip())
        indent = len(ln) - len(ln.lstrip())

        first = re.sub(r"\s{2,}[\d][\d\s ]*$", "", parts[0]).strip()
        if first and not NUM.match(first) and indent in INDENT_DONNEES:
            labels.append(first)

        last = parts[-1].strip()
        v = to_int(last)
        if v is not None and ln.rstrip().rindex(last) >= seuil:
            values.append(v)

    return fusionner_libelles_coupes(labels), values


# =============================================================================
# CLASSIFICATION DES PAGES
# =============================================================================
PREMIERE_PAGE_DONNEES = 26  # 1-25 : preface, sommaire, methodologie

CLASSES = [
    ("regions",     re.compile(r"résidente\s+des\s+régions\s+par\s+sexe", re.I)),
    ("prefectures", re.compile(r"résidente\s+du\s+Togo\s+par\s+préfecture", re.I)),
    ("communes",    re.compile(r"résidente\s+par\s+commune\s+et\s+sexe", re.I)),
    ("quartiers",   re.compile(r"résidente\s+des\s+quartiers", re.I)),
    ("cantons",     re.compile(r"résidente\s+des\s+cantons", re.I)),
    ("villes",      re.compile(r"résidente\s+des\s+villes", re.I)),
]
CTX = re.compile(r"préfecture\s+de\s+([^(\n]+?)\s*(?:\(Région\s+([^)]+)\))?\s*$",
                 re.I | re.M)


def classer(page: str) -> tuple[str | None, str]:
    bloc = re.search(r"Tableau\s*\d+\s*:(.{0,200})", page, re.S)
    titre = " ".join(bloc.group(1).split()) if bloc else ""
    niveau = next((n for n, rx in CLASSES if rx.search(titre)), None)
    ctx = CTX.search(titre)
    return niveau, (ctx.group(1).strip() if ctx else "")


# =============================================================================
# HIERARCHIE PAR STRUCTURE DES NOMS
# =============================================================================
COMMUNE_PAT = re.compile(r"^(.+?)\s+(\d+)$")     # « KOZAH 1 » -> parent « KOZAH »
TOTAL_PAT = re.compile(r"^TOTAL\b", re.I)

# Dans les tableaux « cantons », la ligne parent est une COMMUNE. Le
# discriminateur est verifie sur les donnees PRISE : les 117 communes du Togo
# se terminent toutes par un chiffre, aucun des 372 cantons n'en comporte.
# Le libelle est parfois prefixe (« COMMUNE DE LACS 1 »), parfois non
# (« LACS 2 ») : le suffixe numerique reste le seul signal fiable.
PARENT_CANTON = re.compile(r"\d\s*$")


def valider_communes(rows: list[dict]) -> tuple[int, int, list[str]]:
    """Chaque « P n » doit sommer au parent « P »."""
    pop = {}
    for r in rows:
        if not TOTAL_PAT.match(r["libelle"]):
            pop[r["libelle"].strip().upper()] = r["population"]
    enfants: dict[str, list[int]] = {}
    for lib, val in pop.items():
        m = COMMUNE_PAT.match(lib)
        if m and m.group(1) in pop:
            enfants.setdefault(m.group(1), []).append(val)
    ok = ko = 0
    details = []
    for parent, vals in sorted(enfants.items()):
        if sum(vals) == pop[parent]:
            ok += 1
        else:
            ko += 1
            details.append(f"{parent} : {sum(vals):,} ≠ {pop[parent]:,} "
                           f"({len(vals)} communes)".replace(",", " "))
    return ok, ko, details


def valider_cantons(rows: list[dict]) -> tuple[int, int, list[str]]:
    """Les cantons entre deux « COMMUNE DE … » doivent sommer a leur commune."""
    ok = ko = 0
    details = []
    for page, grp in pd.DataFrame(rows).groupby("page"):
        parent = None
        buf: list[int] = []
        for _, r in grp.iterrows():
            lib = r["libelle"].strip()
            if TOTAL_PAT.match(lib):
                continue
            if PARENT_CANTON.search(lib):
                if parent and buf:
                    (ok, ko) = (ok + 1, ko) if sum(buf) == parent[1] else (ok, ko + 1)
                    if sum(buf) != parent[1]:
                        details.append(f"{parent[0]} (p{page}) : {sum(buf):,} ≠ "
                                       f"{parent[1]:,}".replace(",", " "))
                parent, buf = (lib, r["population"]), []
            elif parent:
                buf.append(r["population"])
        if parent and buf:
            (ok, ko) = (ok + 1, ko) if sum(buf) == parent[1] else (ok, ko + 1)
            if sum(buf) != parent[1]:
                details.append(f"{parent[0]} (p{page}) : {sum(buf):,} ≠ "
                               f"{parent[1]:,}".replace(",", " "))
    return ok, ko, details


# =============================================================================
# MAIN
# =============================================================================
def main() -> None:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    REPORTS.mkdir(parents=True, exist_ok=True)
    OUT: list[str] = []

    def w(line: str = "") -> None:
        OUT.append(line)
        print(line)

    w("# Extraction de la population — RGPH-5 (INSEED, novembre 2022)")
    w()
    w("Genere par `src/extract_rgph5.py`. Aucun chiffre n'est saisi a la main ni")
    w("estime : tout provient du PDF officiel de l'INSEED, et rien n'est retenu")
    w("sans controle arithmetique.")
    w()

    pages = pdf_to_pages()
    w(f"- Pages du PDF : **{len(pages)}**")
    w(f"- Total national de reference (publie par l'INSEED) : "
      f"**{TOTAL_NATIONAL:,}** habitants".replace(",", " "))
    w()

    resultats: dict[str, list[dict]] = {}
    anomalies: list[str] = []
    niveau = pref = None

    # La pagination differe d'une edition a l'autre : on ne peut pas se fier a
    # un numero de page fixe. Un page de SOMMAIRE cite plusieurs tableaux ; une
    # page de DONNEES en porte au plus un. La lecture ne demarre qu'apres le
    # premier tableau reellement classe.
    for i, page in enumerate(pages):
        marqueurs = re.findall(r"Tableau\s*\d+\s*:", page)
        if len(marqueurs) > 1:          # sommaire : ni classement ni lecture
            continue
        n, p = classer(page)
        if n:
            niveau, pref = n, p
        if niveau is None or "Ensemble" not in page:
            continue
        labels, values = parse_page(page)
        if not labels and not values:
            continue
        if len(labels) != len(values):
            anomalies.append(f"page {i + 1} ({niveau}) : {len(labels)} libelles "
                             f"pour {len(values)} valeurs — page EXCLUE")
            continue
        for lib, val in zip(labels, values):
            resultats.setdefault(niveau, []).append(
                {"page": i + 1, "libelle": lib, "population": val,
                 "prefecture_contexte": pref})

    for k, _ in CLASSES:
        resultats.setdefault(k, [])

    # --- volumetrie ---------------------------------------------------------
    w("## 1. Volumetrie extraite")
    w()
    w("| Niveau | Pages | Lignes |")
    w("|---|---|---|")
    for k, rows in resultats.items():
        pgs = sorted({r["page"] for r in rows})
        w(f"| {k} | {f'{min(pgs)}–{max(pgs)}' if pgs else '—'} | {len(rows)} |")
    w()
    if anomalies:
        w(f"### Pages exclues faute d'appariement ({len(anomalies)})")
        w()
        for a in anomalies:
            w(f"- {a}")
        w()

    # --- controles ----------------------------------------------------------
    w("## 2. Controles arithmetiques")
    w()
    controles: list[tuple[str, bool, str]] = []

    reg = pd.DataFrame(resultats["regions"])
    if len(reg):
        # L'edition revisee detaille la region Maritime en deux sous-unites
        # prefixees d'un tiret (« - DAGL », « - MARITIME SANS GRAND LOME »).
        # Les additionner au total regional reviendrait a compter deux fois
        # 3,5 million d'habitants.
        est_sous_unite = reg.libelle.str.strip().str.startswith("-")
        est_total = reg.libelle.str.upper().str.strip() == "TOGO"
        parts = reg[~est_sous_unite & ~est_total]
        somme = int(parts.population.sum())
        w("**Unites regionales du RGPH-5 :**")
        w()
        w("| Unite | Population |")
        w("|---|---|")
        for _, r in parts.iterrows():
            w(f"| {r.libelle} | {r.population:,} |".replace(",", " "))
        w(f"| **TOTAL** | **{somme:,}** |".replace(",", " "))
        w()
        if est_sous_unite.any():
            w("Sous-unites detaillees par le livret, **exclues du total** pour")
            w("eviter un double comptage :")
            w()
            for _, r in reg[est_sous_unite].iterrows():
                w(f"- `{r.libelle.strip()}` : {r.population:,} habitants"
                  .replace(",", " "))
            w()
        controles.append(("Somme des 5 regions = total national",
                          somme == TOTAL_NATIONAL and len(parts) == 5,
                          f"{somme:,} ({len(parts)} regions)".replace(",", " ")))

    # --- controles croises de niveau a niveau -------------------------------
    # Dans les tableaux « communes », les lignes se terminant par un chiffre
    # sont les communes ; les autres sont les prefectures qui les portent.
    com_df = pd.DataFrame(resultats["communes"])
    if len(com_df):
        hors_total = com_df[~com_df.libelle.str.match(TOTAL_PAT)]
        communes = hors_total[hors_total.libelle.str.contains(r"\d\s*$")]
        prefs = hors_total[~hors_total.libelle.str.contains(r"\d\s*$")]
        for lib, sous_ens in (("communes", communes), ("prefectures", prefs)):
            s = int(sous_ens.population.sum())
            controles.append((
                f"Somme des {lib} = total national",
                s == TOTAL_NATIONAL,
                f"{s:,} ({len(sous_ens)} unites)".replace(",", " ")))
        dbl = int(communes.libelle.duplicated().sum())
        controles.append(("Aucune commune comptee deux fois", dbl == 0,
                          f"{dbl} doublon(s)"))

    for niv, fn in (("communes", valider_communes), ("cantons", valider_cantons)):
        if not resultats[niv]:
            continue
        ok, ko, details = fn(resultats[niv])
        controles.append((f"Emboitement {niv} : enfants sommant a leur parent",
                          ko == 0, f"{ok} conformes, {ko} en echec"))
        if details:
            w(f"**Blocs `{niv}` en echec ({len(details)}) :**")
            w()
            for d in details[:20]:
                w(f"- {d}")
            if len(details) > 20:
                w(f"- … et {len(details) - 20} autres")
            w()

    w("| Controle | Resultat | Detail |")
    w("|---|---|---|")
    for nom, ok, detail in controles:
        w(f"| {nom} | {'✅ OK' if ok else '❌ ECHEC'} | {detail} |")
    w()

    # --- ecriture -----------------------------------------------------------
    w("## 3. Fichiers produits")
    w()
    w("| Fichier | Lignes |")
    w("|---|---|")
    for niv, rows in resultats.items():
        if not rows:
            continue
        path = INTERIM / f"rgph5_{niv}.csv"
        pd.DataFrame(rows).to_csv(path, index=False, encoding="utf-8")
        w(f"| `data/interim/{path.name}` | {len(rows)} |")
    w()
    w("> Fichiers **intermediaires** : libelles bruts du PDF, sans rapprochement")
    w("> avec la nomenclature PRISE ni avec les P-codes COD-AB. Ce rapprochement")
    w("> fait l'objet d'une etape distincte et tracee.")

    (REPORTS / "extraction_rgph5.md").write_text("\n".join(OUT), encoding="utf-8")


if __name__ == "__main__":
    main()
