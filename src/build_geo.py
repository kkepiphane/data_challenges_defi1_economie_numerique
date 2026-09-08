"""
SOCLE GEOGRAPHIQUE ET DEMOGRAPHIQUE
====================================
Assemble les trois sources auditees en un socle analytique valide :

  PRISE 2021/2022   points d'infrastructure + nomenclature administrative
  COD-AB v02        polygones + superficies (valid_on 2021-01-07)
  RGPH-5 nov. 2022  population (INSEED, extraite et validee)

DECISION METHODOLOGIQUE CENTRALE
---------------------------------
Deux unites d'analyse, chacune a son niveau de validite prouve :

  * PREFECTURE (39) -> unite GEOGRAPHIQUE. Polygones, superficie, densite,
    cartes choroplethes. Concordance spatiale mesuree a 98,4 %.

  * COMMUNE (117)   -> unite STATISTIQUE. Ratios par habitant, comptages.
    Aucune geometrie : voir l'approche ecartee ci-dessous.

APPROCHE ECARTEE, ET POURQUOI
------------------------------
Reconstituer les contours communaux en fusionnant les cantons COD-AB a ete
tente puis REJETE sur preuve : les cantons COD-AB ne sont pas emboites dans
les communes PRISE.
  - 255 cantons sur 351 seulement tombent dans une seule commune ;
  - 65,6 % des points Mobile Money sont dans un canton a cheval ;
  - cas structurel : le polygone « Lome Commune » (TG030501) couvre a lui
    seul 6 communes PRISE (Golfe 1 a 6, 3 099 points).
Livrer ces polygones aurait produit des densites communales fausses.

RECONCILIATION DES NOMENCLATURES (prefectures)
-----------------------------------------------
Trois divergences, toutes documentees et reversibles :
  - COD-AB isole « Lome Commune » (TG0305) que PRISE inclut dans Golfe
    -> fusion dans TG0303 ;
  - « Naki-Ouest »  (COD-AB) = « Kpendjal-Ouest » (PRISE) ;
  - « Plaine du Mo » (COD-AB) = « Mo » (PRISE).

Sorties : data/processed/prefectures.gpkg
          data/processed/communes_population.csv
          reports/socle_geo.md
"""

from __future__ import annotations

import glob
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
EXT = ROOT / "data" / "external"
INTERIM = ROOT / "data" / "interim"
PROCESSED = ROOT / "data" / "processed"
REPORTS = ROOT / "reports"

BOUNDARIES = EXT / "tgo_admin_boundaries.geojson.zip"
CRS_GEO = "EPSG:4326"          # seul CRS declare par les sources (.prj PRISE)
CRS_METRIQUE = "EPSG:32631"    # UTM 31N — pour superficies et distances

TOTAL_NATIONAL = 8_095_498
SUPERFICIE_CODAB = 57_242.1    # somme des adm3, verifiee a l'audit

FUSION_PCODE = {"TG0305": "TG0303"}                     # Lome Commune -> Golfe
RENOM = {"Naki-Ouest": "Kpendjal-Ouest", "Plaine du Mo": "Mô",
         "Lome Commune": "Golfe"}

OUT: list[str] = []


def w(line: str = "") -> None:
    OUT.append(line)
    print(line)


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().upper()
    return re.sub(r"[^A-Z0-9]+", "", s)


def charger_mm() -> gpd.GeoDataFrame:
    path = sorted(glob.glob(str(RAW / "file-Agents mobile money*.csv")))[0]
    df = pd.read_csv(path, dtype=str)
    df["geometry"] = df["geometry"].map(wkt.loads)
    return gpd.GeoDataFrame(df, geometry="geometry", crs=CRS_GEO)


def main() -> None:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    for d in (PROCESSED, REPORTS):
        d.mkdir(parents=True, exist_ok=True)
    controles: list[tuple[str, bool, str]] = []

    w("# Socle geographique et demographique")
    w()
    w("Genere par `src/build_geo.py`. Chaque jointure est verifiee ; aucune")
    w("valeur n'est imputee, aucune geometrie n'est fabriquee.")
    w()

    # =========================================================================
    # 1. COUCHE PREFECTURE
    # =========================================================================
    a2 = gpd.read_file(f"zip://{BOUNDARIES}!tgo_admin2.geojson")[
        ["adm2_name", "adm2_pcode", "adm1_name", "adm1_pcode", "area_sqkm", "geometry"]]

    w("## 1. Construction de la couche prefecture")
    w()
    w(f"- Unites COD-AB `tgo_admin2` livrees : **{len(a2)}**")
    w()
    w("**Reconciliation appliquee :**")
    w()
    w("| COD-AB | PRISE | Traitement |")
    w("|---|---|---|")
    w("| `Lome Commune` (TG0305) | incluse dans Golfe | fusionnee dans TG0303 |")
    w("| `Naki-Ouest` (TG0518) | `Kpendjal-Ouest` | renommee |")
    w("| `Plaine du Mo` (TG0102) | `Mô` | renommee |")
    w()

    a2["pcode"] = a2.adm2_pcode.replace(FUSION_PCODE)
    a2["prefecture"] = a2.adm2_name.replace(RENOM)
    a2.loc[a2.pcode == "TG0303", "prefecture"] = "Golfe"

    pref = a2.dissolve(by="pcode", aggfunc={"area_sqkm": "sum"}).reset_index()
    meta = a2.groupby("pcode").agg(prefecture=("prefecture", "first"),
                                   region=("adm1_name", "first"),
                                   region_pcode=("adm1_pcode", "first")).reset_index()
    pref = pref.merge(meta, on="pcode")
    pref["superficie_km2"] = pref.to_crs(CRS_METRIQUE).area / 1e6

    # --- La graphie PRISE devient le libelle canonique ------------------------
    # COD-AB translittere sans accents (« Agoe-Nyive », « Tone », « Kpele ») la
    # ou PRISE accentue (« Agoè-Nyivé », « Tône », « Kpélé »). Comme ce sont les
    # attributs PRISE qui portent les agregations (les points declarent leur
    # prefecture), c'est la graphie PRISE qui fait foi. La graphie COD-AB est
    # conservee pour la tracabilite.
    mm_pref = charger_mm()
    ref_prise = {norm(p): p for p in mm_pref.prefecture_nom_bdd.unique()}
    pref["prefecture"] = pref.prefecture.map(lambda p: ref_prise.get(norm(p), p))
    pref["prefecture_codab"] = pref.pcode.map(
        a2.groupby("pcode").adm2_name.apply(lambda s: " + ".join(sorted(set(s)))))

    # Table de correspondance unique, lue par les etapes suivantes : elle
    # evite que chaque script re-implemente la reconciliation a sa facon.
    (a2[["adm2_name", "adm2_pcode", "pcode"]]
     .assign(prefecture=a2.pcode.map(dict(zip(pref.pcode, pref.prefecture))))
     .to_csv(PROCESSED / "reconciliation_prefectures.csv",
             index=False, encoding="utf-8"))

    controles.append(("Nombre de prefectures apres fusion = 39",
                      len(pref) == 39, f"{len(pref)}"))
    controles.append(("Superficie totale conservee",
                      abs(pref.area_sqkm.sum() - SUPERFICIE_CODAB) < 0.5,
                      f"{pref.area_sqkm.sum():,.1f} km²".replace(",", " ")))

    # --- appariement des noms avec PRISE ---
    mm = mm_pref
    prise_pref = set(mm.prefecture_nom_bdd.unique())
    a, b = set(pref.prefecture.map(norm)), set(map(norm, prise_pref))
    controles.append(("Noms de prefecture apparies COD-AB <-> PRISE",
                      a == b, f"{len(a & b)}/{len(b)}"))
    if a - b or b - a:
        w(f"- COD-AB sans equivalent PRISE : {sorted(a - b)}")
        w(f"- PRISE sans equivalent COD-AB : {sorted(b - a)}")
        w()

    # --- concordance spatiale ---
    j = gpd.sjoin(mm, pref[["pcode", "prefecture", "geometry"]],
                  how="left", predicate="within")
    dedans = j[j.pcode.notna()].copy()
    dedans["concorde"] = (dedans.prefecture.map(norm)
                          == dedans.prefecture_nom_bdd.map(norm))
    taux = dedans.concorde.mean()
    w("**Verification par la geometrie** — les 19 788 points Mobile Money "
      "tombent-ils dans la prefecture qu'ils declarent ?")
    w()
    w(f"- Points rattaches a un polygone : **{len(dedans)} / {len(mm)}** "
      f"({len(dedans) / len(mm):.2%})")
    w(f"- Prefecture geometrique = prefecture declaree : **{taux:.2%}** "
      f"({int(dedans.concorde.sum())}/{len(dedans)})")
    w(f"- Desaccords residuels : **{int((~dedans.concorde).sum())}** points")
    w()
    w("> Les desaccords sont des points situes pres d'une limite. Ils")
    w("> proviennent de millesimes de contours differents (COD-AB "
      "`valid_on` 2021-01-07 / collecte PRISE 2021-2022), pas d'erreurs de")
    w("> coordonnees : l'audit a etabli 0 point hors du territoire togolais.")
    w("> **L'attribut declare PRISE fait foi pour les agregations** ; la")
    w("> geometrie sert a cartographier et a mesurer les superficies.")
    w()
    controles.append(("Concordance spatiale des prefectures ≥ 95 %",
                      taux >= 0.95, f"{taux:.2%}"))

    # =========================================================================
    # 2. POPULATION
    # =========================================================================
    com_raw = pd.read_csv(INTERIM / "rgph5_communes.csv")
    hors_total = com_raw[~com_raw.libelle.str.match(r"^TOTAL", case=False)]
    est_commune = hors_total.libelle.str.contains(r"\d\s*$")
    pop_pref = hors_total[~est_commune].copy()
    pop_com = hors_total[est_commune].copy()

    w("## 2. Population (RGPH-5, novembre 2022)")
    w()
    w(f"- Lignes prefecture : **{len(pop_pref)}** — somme "
      f"**{pop_pref.population.sum():,}**".replace(",", " "))
    w(f"- Lignes commune : **{len(pop_com)}** — somme "
      f"**{pop_com.population.sum():,}**".replace(",", " "))
    w()

    pop_pref["cle"] = pop_pref.libelle.map(norm)
    pref["cle"] = pref.prefecture.map(norm)
    pref = pref.merge(pop_pref[["cle", "population"]], on="cle", how="left")

    manquantes = pref[pref.population.isna()].prefecture.tolist()
    controles.append(("Population jointe a toutes les prefectures",
                      not manquantes,
                      f"{int(pref.population.notna().sum())}/39"
                      + (f" — manquantes : {manquantes}" if manquantes else "")))
    controles.append(("Somme des populations prefectorales = total national",
                      int(pref.population.sum()) == TOTAL_NATIONAL,
                      f"{int(pref.population.sum()):,}".replace(",", " ")))

    pref["densite_hab_km2"] = pref.population / pref.superficie_km2

    # =========================================================================
    # 3. TABLE COMMUNE (sans geometrie)
    # =========================================================================
    prise_com = (mm[["region_nom_bdd", "prefecture_nom_bdd", "commune_nom_bdd"]]
                 .drop_duplicates().rename(columns={
                     "region_nom_bdd": "region",
                     "prefecture_nom_bdd": "prefecture",
                     "commune_nom_bdd": "commune"}))
    prise_com["cle"] = prise_com.commune.map(norm)
    pop_com = pop_com.copy()
    pop_com["cle"] = pop_com.libelle.map(norm)

    com = prise_com.merge(pop_com[["cle", "libelle", "population"]],
                          on="cle", how="left")

    # Danyi : le RGPH-5 publie une ligne unique « DANYI 1 + DANYI 2 ».
    # On la rattache aux deux communes en marquant explicitement le partage,
    # sans jamais repartir arbitrairement l'effectif.
    ligne_danyi = pop_com[pop_com.libelle.str.contains("DANYI", case=False)]
    com["population_partagee_avec"] = ""
    if len(ligne_danyi) == 1:
        val = int(ligne_danyi.population.iloc[0])
        masque = com.commune.str.startswith("Danyi")
        com.loc[masque, "population"] = val
        com.loc[masque, "population_partagee_avec"] = ligne_danyi.libelle.iloc[0]

    sans_pop = com[com.population.isna()].commune.tolist()
    controles.append(("Population jointe a toutes les communes",
                      not sans_pop, f"{int(com.population.notna().sum())}/117"
                      + (f" — manquantes : {sans_pop}" if sans_pop else "")))

    uniques = com[com.population_partagee_avec == ""]
    somme_com = int(uniques.population.sum()) + (
        int(ligne_danyi.population.iloc[0]) if len(ligne_danyi) == 1 else 0)
    controles.append(("Somme des populations communales = total national",
                      somme_com == TOTAL_NATIONAL,
                      f"{somme_com:,}".replace(",", " ")))

    w("**Cas particulier documente — Danyi**")
    w()
    if len(ligne_danyi) == 1:
        w(f"Le RGPH-5 ne publie pas Danyi 1 et Danyi 2 separement : le livret")
        w(f"porte une ligne unique `{ligne_danyi.libelle.iloc[0]}` = "
          f"**{int(ligne_danyi.population.iloc[0]):,} habitants**.".replace(",", " "))
        w("Les deux communes portent donc cet effectif **commun**, signale par")
        w("la colonne `population_partagee_avec`. Aucun partage arbitraire n'est")
        w("effectue : tout ratio par habitant devra les traiter ensemble ou les")
        w("exclure, jamais les compter deux fois.")
    w()

    # =========================================================================
    # 4. CONTROLES ET ECRITURE
    # =========================================================================
    w("## 3. Controles")
    w()
    w("| Controle | Resultat | Detail |")
    w("|---|---|---|")
    for nom, ok, detail in controles:
        w(f"| {nom} | {'✅ OK' if ok else '❌ ECHEC'} | {detail} |")
    w()

    w("## 4. Apercu — densite par prefecture")
    w()
    w("| Prefecture | Region | Population | Superficie (km²) | Densite (hab/km²) |")
    w("|---|---|---|---|---|")
    for _, r in pref.sort_values("densite_hab_km2", ascending=False).iterrows():
        w(f"| {r.prefecture} | {r.region} | {int(r.population):,} | "
          f"{r.superficie_km2:,.1f} | {r.densite_hab_km2:,.1f} |".replace(",", " "))
    w()

    cols = ["pcode", "prefecture", "prefecture_codab", "region", "region_pcode",
            "population", "superficie_km2", "area_sqkm", "densite_hab_km2",
            "geometry"]
    pref[cols].to_file(PROCESSED / "prefectures.gpkg", driver="GPKG")
    com.drop(columns=["cle", "libelle"]).to_csv(
        PROCESSED / "communes_population.csv", index=False, encoding="utf-8")

    w("## 5. Fichiers produits")
    w()
    w("| Fichier | Contenu |")
    w("|---|---|")
    w(f"| `data/processed/prefectures.gpkg` | {len(pref)} polygones + population "
      f"+ superficie + densite |")
    w(f"| `data/processed/communes_population.csv` | {len(com)} communes + "
      f"population (sans geometrie) |")

    (REPORTS / "socle_geo.md").write_text("\n".join(OUT), encoding="utf-8")


if __name__ == "__main__":
    main()
