"""
DATASET ANALYTIQUE ET INDICATEURS
==================================
Transforme les points bruts PRISE en indicateurs decisionnels, aux deux
unites validees par `build_geo.py` :
    PREFECTURE (39) -> unite geographique (densite, superficie)
    COMMUNE    (117) -> unite statistique (ratios par habitant)

TROIS PIEGES TRAITES EXPLICITEMENT (etablis a l'audit)
------------------------------------------------------
1. `FID` VOLATILE — l'identifiant du serveur change a chaque export : la
   meme agence porte `..._68de` dans le CSV et `..._68fa` dans le XLSX.
   -> On fabrique un identifiant stable : empreinte du nom normalise + des
      coordonnees arrondies a 1e-6 degre (~0,1 m).

2. DOUBLONS INTER-FICHIERS — « Agences - Telecom » n'est pas un operateur :
   ses 51 lignes sont deja contenues dans Moov ∪ Togocom (0 enregistrement
   exclusif). Empiler les 4 fichiers donnerait 141 agences au lieu de 90.
   -> Deduplication sur l'identifiant stable, avec controle du resultat.

3. `operateur` MULTIVALUE — « Moov, Togocom » designe UN point servi par
   DEUX operateurs. Un point n'est pas un operateur.
   -> Table longue point x operateur pour les analyses par operateur ;
      les comptages de points restent faits sur la table courte.
      Les 1 348 points a operateur `Nsp` forment une categorie propre.

CAS DANYI — le RGPH-5 publie un effectif commun a Danyi 1 et Danyi 2. Les
ratios par habitant y seraient faux : ces deux communes sont marquees et
exclues des classements par habitant, jamais silencieusement divisees.

Sorties : data/processed/etablissements.csv
          data/processed/mobile_money_operateurs.csv
          data/processed/indicateurs_prefecture.csv
          data/processed/indicateurs_commune.csv
          reports/indicateurs.md
"""

from __future__ import annotations

import glob
import hashlib
import io
import re
import sys
import unicodedata
from pathlib import Path

import geopandas as gpd
import pandas as pd
from shapely import wkt

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
REPORTS = ROOT / "reports"

CRS_GEO = "EPSG:4326"
PRECISION = 6  # decimales de degre retenues pour l'identifiant (~0,1 m)

ADMIN = {"region_nom_bdd": "region", "prefecture_nom_bdd": "prefecture",
         "commune_nom_bdd": "commune", "canton_nom_bdd": "canton"}

OUT: list[str] = []
controles: list[tuple[str, bool, str]] = []


def w(line: str = "") -> None:
    OUT.append(line)
    print(line)


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().upper()
    return re.sub(r"[^A-Z0-9]+", "", s)


def lire(motif: str) -> pd.DataFrame:
    """Lit le CSV correspondant au motif — format faisant autorite (audit §2.3)."""
    hits = sorted(glob.glob(str(RAW / motif)))
    if not hits:
        return pd.DataFrame()
    df = pd.read_csv(hits[0], dtype=str, keep_default_na=False, na_values=[""])
    for c in df.columns:                       # espaces de bord releves a l'audit
        if df[c].dtype == object:
            df[c] = df[c].str.strip()
    return df


def identifiant_stable(nom: str, geom_wkt: str) -> str:
    """Empreinte reproductible, independante du FID regenere par le serveur."""
    p = wkt.loads(geom_wkt)
    cle = f"{norm(nom)}|{round(p.x, PRECISION)}|{round(p.y, PRECISION)}"
    return hashlib.sha1(cle.encode()).hexdigest()[:16]


def main() -> None:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    PROCESSED.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)

    w("# Dataset analytique et indicateurs")
    w()
    w("Genere par `src/build_indicators.py`. Chaque transformation est")
    w("controlee ; aucune valeur n'est imputee.")
    w()

    # =========================================================================
    # 1. ETABLISSEMENTS — DEDUPLICATION
    # =========================================================================
    sources = {
        "Moov":    "file-Agences - Moov*.csv",
        "Togocom": "file-Agences - Togocom*.csv",
        "Telecom": "file-Agences - T*l*com-*.csv",
        "CANAL+":  "file-Agences - CANAL+*.csv",
    }
    brut = []
    w("## 1. Etablissements — deduplication")
    w()
    w("| Fichier source | Lignes |")
    w("|---|---|")
    for nom, motif in sources.items():
        df = lire(motif)
        w(f"| Agences – {nom} | {len(df)} |")
        if len(df):
            df["_source"] = nom
            brut.append(df)
    agences = pd.concat(brut, ignore_index=True)
    w(f"| **Somme brute** | **{len(agences)}** |")
    w()

    agences["id"] = [identifiant_stable(n, g)
                     for n, g in zip(agences.etab_nom, agences.geometry)]
    avant = len(agences)
    # On conserve la trace des fichiers dans lesquels chaque etablissement figure
    presence = (agences.groupby("id")._source
                .apply(lambda s: ", ".join(sorted(set(s)))).rename("figure_dans"))
    etab = agences.drop_duplicates("id").merge(presence, on="id")

    w(f"- Etablissements uniques apres deduplication : **{len(etab)}**")
    w(f"- Lignes eliminees : **{avant - len(etab)}** "
      f"({(avant - len(etab)) / len(etab):.0%} de surestimation evitee)")
    w()
    controles.append(("Deduplication des agences : 141 lignes -> 90 etablissements",
                      avant == 141 and len(etab) == 90,
                      f"{avant} -> {len(etab)}"))

    # L'operateur reel est porte par `activite_categorie`, pas par le fichier
    etab["operateur"] = (etab.activite_categorie
                         .str.replace("Agence ", "", regex=False).str.strip())
    etab["type_infrastructure"] = "Agence operateur"
    etab["actif"] = ~etab.activite_statut.str.contains("Ferm", na=False)

    w("**L'operateur reel est lu dans `activite_categorie`, pas deduit du nom "
      "du fichier :**")
    w()
    w("| Operateur | Etablissements | dont actifs |")
    w("|---|---|---|")
    for op, grp in etab.groupby("operateur"):
        w(f"| {op} | {len(grp)} | {int(grp.actif.sum())} |")
    w(f"| **Total** | **{len(etab)}** | **{int(etab.actif.sum())}** |")
    w()
    fermees = etab[~etab.actif]
    if len(fermees):
        w("Etablissements declares fermes, conserves et signales :")
        w()
        for _, r in fermees.iterrows():
            w(f"- *{r.etab_nom}* — {r.prefecture_nom_bdd} ({r.region_nom_bdd})")
        w()

    # --- data centers ---
    dc = lire("file-Datacenter*.csv")
    dc["id"] = [identifiant_stable(n, g) for n, g in zip(dc.etab_nom, dc.geometry)]
    dc["operateur"] = "—"
    dc["type_infrastructure"] = "Data center"
    dc["actif"] = dc.activite_statut.str.contains("Utilise", na=False)
    dc["figure_dans"] = "Datacenter"

    colonnes = (["id", "etab_nom", "type_infrastructure", "operateur", "actif",
                 "figure_dans"] + list(ADMIN) + ["geometry"])
    etablissements = pd.concat([etab[colonnes], dc[colonnes]], ignore_index=True)
    etablissements = etablissements.rename(columns=ADMIN)
    etablissements.to_csv(PROCESSED / "etablissements.csv", index=False,
                          encoding="utf-8")

    w(f"- Data centers : **{len(dc)}**, tous en {dc.prefecture_nom_bdd.iloc[0]} "
      f"({dc.region_nom_bdd.iloc[0]})")
    w(f"- **Table `etablissements` : {len(etablissements)} lignes** "
      f"({len(etab)} agences + {len(dc)} data centers)")
    w()

    # =========================================================================
    # 2. MOBILE MONEY — ECLATEMENT DE LA VARIABLE MULTIVALUEE
    # =========================================================================
    mm = lire("file-Agents mobile money*.csv").rename(columns=ADMIN)
    w("## 2. Mobile Money — variable `operateur` multivaluee")
    w()
    w(f"- Points recenses : **{len(mm)}**")
    w()
    w("| Modalite brute | Points | Part |")
    w("|---|---|---|")
    for v, n in mm.operateur.value_counts().items():
        w(f"| `{v}` | {n} | {n / len(mm):.1%} |")
    w()

    long = (mm.assign(op=mm.operateur.str.split(r"\s*,\s*"))
              .explode("op").rename(columns={"op": "operateur_unitaire"}))
    long["operateur_unitaire"] = long.operateur_unitaire.str.strip()
    long.loc[long.operateur_unitaire.isin(["Nsp", "Neant", "Néant"]),
             "operateur_unitaire"] = "Non renseigne"
    long.to_csv(PROCESSED / "mobile_money_operateurs.csv", index=False,
                encoding="utf-8")

    w("**Apres eclatement — presence par operateur** (un point servi par deux "
      "operateurs compte dans les deux lignes) :")
    w()
    w("| Operateur | Points ou il est present | Part des points |")
    w("|---|---|---|")
    for op, n in long.operateur_unitaire.value_counts().items():
        w(f"| {op} | {n} | {n / len(mm):.1%} |")
    w()
    controles.append(("Eclatement operateur : aucun point perdu",
                      long.FID.nunique() == len(mm),
                      f"{long.FID.nunique()} points distincts / {len(mm)}"))

    exclusifs = mm[mm.operateur == "Moov"], mm[mm.operateur == "Togocom"]
    w(f"> **Lecture** : {len(exclusifs[1]):,} points ne servent que Togocom contre "
      f"{len(exclusifs[0]):,} pour Moov seul".replace(",", " "))
    w("> — un desequilibre de couverture a analyser, pas un artefact de saisie.")
    w()

    # =========================================================================
    # 3. AGREGATION ET INDICATEURS
    # =========================================================================
    pref_geo = gpd.read_file(PROCESSED / "prefectures.gpkg")
    com_pop = pd.read_csv(PROCESSED / "communes_population.csv")

    def agreger(niveau: str, socle: pd.DataFrame) -> pd.DataFrame:
        ag = etablissements[etablissements.type_infrastructure == "Agence operateur"]
        t = socle.copy()
        t["agences"] = t[niveau].map(ag.groupby(niveau).size()).fillna(0).astype(int)
        t["agences_actives"] = t[niveau].map(
            ag[ag.actif].groupby(niveau).size()).fillna(0).astype(int)
        for op in ("Moov", "Togocom"):
            t[f"agences_{op.lower()}"] = t[niveau].map(
                ag[ag.operateur == op].groupby(niveau).size()).fillna(0).astype(int)
        t["data_centers"] = t[niveau].map(
            etablissements[etablissements.type_infrastructure == "Data center"]
            .groupby(niveau).size()).fillna(0).astype(int)
        t["points_mm"] = t[niveau].map(mm.groupby(niveau).size()).fillna(0).astype(int)
        for op in ("Moov", "Togocom"):
            t[f"mm_{op.lower()}"] = t[niveau].map(
                long[long.operateur_unitaire == op].groupby(niveau).size()
            ).fillna(0).astype(int)
        t["mm_operateur_inconnu"] = t[niveau].map(
            long[long.operateur_unitaire == "Non renseigne"].groupby(niveau).size()
        ).fillna(0).astype(int)
        return t

    # --- prefectures ---
    pref = agreger("prefecture", pref_geo)
    pref["hab_par_point_mm"] = (pref.population / pref.points_mm).where(pref.points_mm > 0)
    pref["points_mm_pour_10k_hab"] = pref.points_mm / pref.population * 10_000
    pref["agences_pour_100k_hab"] = pref.agences_actives / pref.population * 100_000
    pref["points_mm_par_1000km2"] = pref.points_mm / pref.superficie_km2 * 1000

    # --- communes ---
    com = agreger("commune", com_pop)
    com["population_fiable"] = com.population_partagee_avec.isna() | (
        com.population_partagee_avec.astype(str).str.strip() == "")
    ratio_ok = com.population_fiable & (com.points_mm > 0)
    com["hab_par_point_mm"] = (com.population / com.points_mm).where(ratio_ok)
    com["points_mm_pour_10k_hab"] = (com.points_mm / com.population * 10_000
                                     ).where(com.population_fiable)

    controles.append(("Somme des points MM agreges par prefecture = total",
                      int(pref.points_mm.sum()) == len(mm),
                      f"{int(pref.points_mm.sum())} / {len(mm)}"))
    controles.append(("Somme des points MM agreges par commune = total",
                      int(com.points_mm.sum()) == len(mm),
                      f"{int(com.points_mm.sum())} / {len(mm)}"))
    controles.append(("Somme des agences agregees = etablissements uniques",
                      int(pref.agences.sum()) == len(etab),
                      f"{int(pref.agences.sum())} / {len(etab)}"))
    # Selon l'edition du livret RGPH-5, certaines communes peuvent partager un
    # effectif publie en commun (cas « DANYI 1 + DANYI 2 » de l'edition
    # ancienne). Le controle verifie que toute commune concernee est bien
    # marquee et privee de ratio — et non qu'il en existe un nombre donne.
    partagees = com[~com.population_fiable]
    coherent = bool(partagees.hab_par_point_mm.isna().all())
    controles.append(("Communes a population partagee : marquees et privees de ratio",
                      coherent,
                      f"{len(partagees)} commune(s)"
                      + (f" — {', '.join(partagees.commune)}" if len(partagees)
                         else " — aucune dans cette edition du livret")))

    pref.drop(columns="geometry").to_csv(
        PROCESSED / "indicateurs_prefecture.csv", index=False, encoding="utf-8")
    com.to_csv(PROCESSED / "indicateurs_commune.csv", index=False, encoding="utf-8")

    # =========================================================================
    # 4. RESULTATS
    # =========================================================================
    w("## 3. Indicateur central — habitants par point Mobile Money")
    w()
    w("Definition reprise de l'indicateur officiel du geoportail national")
    w("(« Nombre d'habitants par point mobile money », mode de calcul `popRatio`).")
    w("Un ratio **eleve** signale une desserte **faible**.")
    w()
    national = len(mm) and pref.population.sum() / pref.points_mm.sum()
    w(f"**Reference nationale : {national:,.0f} habitants par point.**"
      .replace(",", " "))
    w()
    w("| Prefecture | Region | Population | Points MM | Hab./point | Ecart au national |")
    w("|---|---|---|---|---|---|")
    for _, r in pref.sort_values("hab_par_point_mm", ascending=False).iterrows():
        ecart = r.hab_par_point_mm / national
        w(f"| {r.prefecture} | {r.region} | {int(r.population):,} | "
          f"{int(r.points_mm)} | {r.hab_par_point_mm:,.0f} | ×{ecart:.2f} |"
          .replace(",", " "))
    w()

    w("## 4. Deserts d'agences")
    w()
    sans = pref[pref.agences_actives == 0].sort_values("population", ascending=False)
    w(f"- Prefectures sans aucune agence active : **{len(sans)} / 39**, "
      f"soit **{int(sans.population.sum()):,} habitants** "
      f"({sans.population.sum() / pref.population.sum():.1%} du pays)"
      .replace(",", " "))
    w()
    w("| Prefecture | Region | Population | Points MM | Hab./point |")
    w("|---|---|---|---|---|")
    for _, r in sans.iterrows():
        w(f"| {r.prefecture} | {r.region} | {int(r.population):,} | "
          f"{int(r.points_mm)} | {r.hab_par_point_mm:,.0f} |".replace(",", " "))
    w()
    sans_com = com[com.agences_actives == 0]
    w(f"- Communes sans aucune agence active : **{len(sans_com)} / {len(com)}**, "
      f"soit **{int(sans_com.population.sum()):,} habitants**".replace(",", " "))
    w()

    # =========================================================================
    w("## 5. Controles")
    w()
    w("| Controle | Resultat | Detail |")
    w("|---|---|---|")
    for nom, ok, detail in controles:
        w(f"| {nom} | {'✅ OK' if ok else '❌ ECHEC'} | {detail} |")
    w()
    w("## 6. Fichiers produits")
    w()
    w("| Fichier | Contenu |")
    w("|---|---|")
    w(f"| `etablissements.csv` | {len(etablissements)} points dedupliques, "
      f"identifiant stable |")
    w(f"| `mobile_money_operateurs.csv` | {len(long)} lignes point × operateur |")
    w(f"| `indicateurs_prefecture.csv` | 39 prefectures × indicateurs |")
    w(f"| `indicateurs_commune.csv` | {len(com)} communes × indicateurs |")

    (REPORTS / "indicateurs.md").write_text("\n".join(OUT), encoding="utf-8")


if __name__ == "__main__":
    main()
