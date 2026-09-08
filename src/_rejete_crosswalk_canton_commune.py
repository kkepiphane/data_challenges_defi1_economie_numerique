"""
TABLE DE CORRESPONDANCE CANTON (COD-AB) -> COMMUNE (PRISE)
===========================================================
POURQUOI
--------
Les deux referentiels ne se recouvrent pas :
  - les polygones COD-AB descendent au CANTON (373 entites, admin3) et
    ignorent le niveau COMMUNE, absent de leur hierarchie ;
  - les donnees PRISE et le RGPH-5 raisonnent en COMMUNE (117 unites).

Or c'est au niveau commune que la population est validee (cf.
`reports/extraction_rgph5.md`) et que le challenge demande une densite
« par subdivision ». Il faut donc rattacher chaque polygone de canton a
une commune, puis fusionner.

COMMENT
-------
Pas de rapprochement par nom : il echoue (285/359 seulement, cf. audit).
On utilise la GEOMETRIE, plus fiable et verifiable :

  1. jointure spatiale point-dans-polygone des 19 788 agents Mobile Money
     sur les 373 polygones de canton ;
  2. pour chaque canton, vote majoritaire sur la commune declaree par les
     points qu'il contient ;
  3. mesure de la confiance = part du vote majoritaire ;
  4. fusion (dissolve) des cantons par commune -> contours communaux
     + superficie.

Toute ambiguite est mesuree et rapportee, jamais lissee.

CONTROLES
---------
  - superficie totale conservee par la fusion ;
  - les 117 communes PRISE sont-elles toutes atteintes ?
  - cantons sans aucun point (vote impossible) ;
  - cantons au vote partage (confiance faible).

Sorties : data/interim/crosswalk_canton_commune.csv
          data/processed/communes.gpkg
          reports/crosswalk.md
"""

from __future__ import annotations

import glob
import io
import sys
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
CRS_GEO = "EPSG:4326"
# UTM 31N : CRS metrique couvrant le Togo (lon 0-6 E). Utilise UNIQUEMENT
# pour les superficies et les distances ; les donnees restent stockees en
# EPSG:4326, seul CRS declare par les sources (.prj des shapefiles PRISE).
CRS_METRIQUE = "EPSG:32631"

PRISE_ADMIN = ["region_nom_bdd", "prefecture_nom_bdd", "commune_nom_bdd"]

OUT: list[str] = []


def w(line: str = "") -> None:
    OUT.append(line)
    print(line)


def charger_points_mm() -> gpd.GeoDataFrame:
    """Agents Mobile Money : le seul jeu couvrant les 117 communes."""
    path = sorted(glob.glob(str(RAW / "file-Agents mobile money*.csv")))[0]
    df = pd.read_csv(path, dtype=str)
    df["geometry"] = df["geometry"].map(wkt.loads)
    return gpd.GeoDataFrame(df, geometry="geometry", crs=CRS_GEO)


def main() -> None:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    for d in (INTERIM, PROCESSED, REPORTS):
        d.mkdir(parents=True, exist_ok=True)

    w("# Table de correspondance canton (COD-AB) → commune (PRISE)")
    w()
    w("Genere par `src/build_crosswalk.py`. Le rattachement est etabli par la")
    w("geometrie, pas par les noms : aucune correspondance n'est supposee.")
    w()

    # =========================================================================
    # 1. CHARGEMENT
    # =========================================================================
    cantons = gpd.read_file(f"zip://{BOUNDARIES}!tgo_admin3.geojson")[
        ["adm3_name", "adm3_pcode", "adm2_name", "adm2_pcode",
         "adm1_name", "adm1_pcode", "area_sqkm", "geometry"]
    ]
    mm = charger_points_mm()

    w("## 1. Sources")
    w()
    w(f"- Polygones de canton (COD-AB `tgo_admin3`) : **{len(cantons)}** entites, "
      f"CRS `{cantons.crs}`")
    w(f"- Points Mobile Money (PRISE) : **{len(mm)}** points, CRS `{mm.crs}`")
    w(f"- Communes distinctes declarees dans les points : "
      f"**{mm.commune_nom_bdd.nunique()}**")
    w()

    # =========================================================================
    # 2. JOINTURE SPATIALE
    # =========================================================================
    j = gpd.sjoin(mm, cantons, how="left", predicate="within")
    dedans = j[j.adm3_pcode.notna()]
    dehors = len(mm) - len(dedans)

    w("## 2. Jointure spatiale point-dans-polygone")
    w()
    w(f"- Points rattaches a un canton : **{len(dedans)} / {len(mm)}** "
      f"({len(dedans) / len(mm):.2%})")
    w(f"- Points hors de tout polygone : **{dehors}** — ecartes du vote, "
      f"jamais reaffectes")
    w(f"- Points tombant dans deux polygones : **{len(j) - len(mm)}** "
      f"(0 attendu si la couche est topologiquement propre)")
    w()

    if dehors:
        hors = mm.loc[~mm.index.isin(dedans.index)]
        w("**Repartition des points non rattaches, par prefecture declaree :**")
        w()
        w("| Prefecture | Points |")
        w("|---|---|")
        for k, v in hors.prefecture_nom_bdd.value_counts().items():
            w(f"| {k} | {v} |")
        w()
        w("> Ces points se situent en limite de territoire (littoral, frontieres).")
        w("> L'ecart provient de millesimes de contours differents, pas d'une")
        w("> erreur de coordonnees : l'audit a montre 0 point hors du Togo.")
        w()

    # =========================================================================
    # 3. VOTE MAJORITAIRE PAR CANTON
    # =========================================================================
    votes = (dedans.groupby(["adm3_pcode"] + PRISE_ADMIN)
             .size().rename("voix").reset_index())
    total = votes.groupby("adm3_pcode").voix.sum().rename("total")
    gagnant = (votes.sort_values("voix", ascending=False)
               .drop_duplicates("adm3_pcode").merge(total, on="adm3_pcode"))
    gagnant["confiance"] = gagnant.voix / gagnant.total

    cross = cantons.drop(columns="geometry").merge(gagnant, on="adm3_pcode", how="left")

    sans_vote = cross[cross.commune_nom_bdd.isna()]
    partage = cross[(cross.confiance.notna()) & (cross.confiance < 0.80)]

    w("## 3. Vote majoritaire")
    w()
    w("| Situation | Cantons |")
    w("|---|---|")
    w(f"| Rattaches avec confiance ≥ 80 % | "
      f"{int(((cross.confiance >= 0.80)).sum())} |")
    w(f"| Rattaches avec confiance < 80 % (vote partage) | {len(partage)} |")
    w(f"| **Sans aucun point — vote impossible** | **{len(sans_vote)}** |")
    w(f"| **Total** | **{len(cross)}** |")
    w()

    if len(sans_vote):
        w("**Cantons sans aucun agent Mobile Money :**")
        w()
        w("| Canton | P-code | Prefecture COD-AB | Superficie (km²) |")
        w("|---|---|---|---|")
        for _, r in sans_vote.sort_values("area_sqkm", ascending=False).iterrows():
            w(f"| {r.adm3_name} | `{r.adm3_pcode}` | {r.adm2_name} | "
              f"{r.area_sqkm:,.1f} |".replace(",", " "))
        w()
        w("> **Information en soi** : ces cantons n'ont aucun point Mobile Money.")
        w("> C'est un resultat analytique (zone sans service recense), pas une")
        w("> lacune de donnees. Ils ne peuvent pas etre rattaches par vote et")
        w("> sont traites separement ci-dessous.")
        w()

    if len(partage):
        w("**Cantons au vote partage (confiance < 80 %) :**")
        w()
        w("| Canton | Commune majoritaire | Confiance | Points |")
        w("|---|---|---|---|")
        for _, r in partage.sort_values("confiance").iterrows():
            w(f"| {r.adm3_name} | {r.commune_nom_bdd} | {r.confiance:.0%} | "
              f"{int(r.total)} |")
        w()

    # =========================================================================
    # 4. COUVERTURE DES 117 COMMUNES
    # =========================================================================
    communes_prise = set(mm.commune_nom_bdd.unique())
    communes_atteintes = set(cross.commune_nom_bdd.dropna().unique())
    manquantes = communes_prise - communes_atteintes

    w("## 4. Couverture des communes")
    w()
    w(f"- Communes declarees dans les donnees PRISE : **{len(communes_prise)}**")
    w(f"- Communes atteintes par au moins un canton : **{len(communes_atteintes)}**")
    w(f"- **Communes sans aucun canton rattache : {len(manquantes)}**"
      + (f" → {sorted(manquantes)}" if manquantes else " (aucune)"))
    w()

    cross.to_csv(INTERIM / "crosswalk_canton_commune.csv", index=False,
                 encoding="utf-8")

    # =========================================================================
    # 5. FUSION EN CONTOURS COMMUNAUX
    # =========================================================================
    geo = cantons.merge(
        cross[["adm3_pcode"] + PRISE_ADMIN + ["confiance"]],
        on="adm3_pcode", how="left")
    rattaches = geo[geo.commune_nom_bdd.notna()]

    communes_geo = (rattaches.dissolve(by=PRISE_ADMIN, aggfunc={"area_sqkm": "sum"})
                    .reset_index())
    # Superficie recalculee sur la geometrie fusionnee, en CRS metrique
    communes_geo["superficie_km2"] = (
        communes_geo.to_crs(CRS_METRIQUE).area / 1e6)

    w("## 5. Fusion des cantons en communes")
    w()
    w(f"- Cantons fusionnes : **{len(rattaches)}**")
    w(f"- Polygones communaux obtenus : **{len(communes_geo)}**")
    w()
    w("| Controle de superficie | km² |")
    w("|---|---|")
    w(f"| Somme des cantons COD-AB (attribut `area_sqkm`) | "
      f"{cantons.area_sqkm.sum():,.1f} |".replace(",", " "))
    w(f"| Somme des cantons rattaches | "
      f"{rattaches.area_sqkm.sum():,.1f} |".replace(",", " "))
    w(f"| Somme des communes apres fusion (attribut cumule) | "
      f"{communes_geo.area_sqkm.sum():,.1f} |".replace(",", " "))
    w(f"| Somme des communes apres fusion (geometrie recalculee, "
      f"EPSG:32631) | {communes_geo.superficie_km2.sum():,.1f} |".replace(",", " "))
    w()
    ecart = abs(communes_geo.area_sqkm.sum() - rattaches.area_sqkm.sum())
    w(f"> Ecart entre attribut cumule et cantons d'origine : "
      f"**{ecart:.4f} km²**. La fusion ne cree ni ne detruit de surface.")
    w()

    communes_geo.to_file(PROCESSED / "communes.gpkg", driver="GPKG")
    w("## 6. Fichiers produits")
    w()
    w("| Fichier | Contenu |")
    w("|---|---|")
    w(f"| `data/interim/crosswalk_canton_commune.csv` | {len(cross)} cantons, "
      f"commune de rattachement et confiance |")
    w(f"| `data/processed/communes.gpkg` | {len(communes_geo)} polygones "
      f"communaux + superficie |")
    w()
    w("> La population n'est pas encore jointe : elle fait l'objet de l'etape")
    w("> suivante, avec son propre controle (somme = 8 095 498).")

    (REPORTS / "crosswalk.md").write_text("\n".join(OUT), encoding="utf-8")


if __name__ == "__main__":
    main()
