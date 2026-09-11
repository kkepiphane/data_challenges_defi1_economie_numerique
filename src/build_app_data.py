"""
PAQUET DE DONNEES DU TABLEAU DE BORD
=====================================
Derive, depuis `data/processed/`, les SEULS fichiers dont l'application a
besoin — dans des formats que Python lit sans bibliotheque geospatiale.

POURQUOI CETTE ETAPE EXISTE
---------------------------
La chaine d'analyse a besoin de geopandas, shapely, pyproj : reprojeter en
EPSG:32631 pour mesurer des distances en metres n'est pas negociable.
L'APPLICATION, elle, ne calcule plus rien : elle affiche des contours deja
simplifies et des points deja projetes en longitude/latitude.

Lui imposer la meme pile serait payer trois bibliotheques compilees — et les
echecs de build qui vont avec — pour zero calcul. Cette etape coupe le lien :

    chaine d'analyse   geopandas + shapely + pyproj + scipy   (poste de travail)
    application        pandas + numpy + plotly + streamlit    (Streamlit Cloud)

Sorties (toutes dans data/processed/, lues telles quelles par le dashboard) :
    prefectures.geojson        contours simplifies + point interieur en propriete
    points_mobile_money.csv    19 788 points, longitude/latitude, sans WKT
    etablissements_pts.csv     93 etablissements, longitude/latitude, sans WKT

Prerequis : `python src/build_geo.py` et `python src/build_indicators.py`.
"""

from __future__ import annotations

import io
import json
import sys
from pathlib import Path

import geopandas as gpd
import pandas as pd
from shapely import wkt

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"

# Tolerance de simplification, en degres. 0,002 deg ~ 200 m a cette latitude :
# invisible a l'echelle nationale, ou un pixel vaut deja plus d'un kilometre.
TOLERANCE = 0.002


def _pts(df: pd.DataFrame) -> pd.DataFrame:
    """Remplace la colonne WKT par deux colonnes numeriques."""
    g = df.geometry.map(wkt.loads)
    df = df.drop(columns="geometry").copy()
    df["lon"] = g.map(lambda p: p.x).round(6)   # 6 decimales ~ 0,1 m
    df["lat"] = g.map(lambda p: p.y).round(6)
    return df


def main() -> None:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                                  errors="replace")
    controles: list[tuple[str, bool, str]] = []

    # ---------------------------------------------------------- contours
    g = gpd.read_file(PROCESSED / "prefectures.gpkg")
    n_avant = len(g)

    # `representative_point` garantit un point A L'INTERIEUR du polygone,
    # contrairement au centroide qui peut tomber dehors sur une forme concave.
    pts = g.geometry.representative_point()
    g["centre_lon"] = pts.x
    g["centre_lat"] = pts.y
    g["geometry"] = g.geometry.simplify(TOLERANCE, preserve_topology=True)

    geojson = json.loads(g.to_json())
    (PROCESSED / "prefectures.geojson").write_text(
        json.dumps(geojson, ensure_ascii=False), encoding="utf-8")

    controles.append(("39 prefectures conservees", len(geojson["features"]) == n_avant == 39,
                      f"{len(geojson['features'])} entites"))
    controles.append(("Aucune geometrie vide apres simplification",
                      all(f["geometry"] is not None for f in geojson["features"]),
                      "preserve_topology=True"))
    controles.append(("Point interieur present sur chaque entite",
                      all(f["properties"].get("centre_lon") is not None
                          for f in geojson["features"]), "representative_point"))

    # ------------------------------------------------------------ points
    mm = pd.read_csv(PROCESSED / "mobile_money_operateurs.csv")
    mm_out = _pts(mm)[["FID", "region", "prefecture", "commune", "canton",
                       "operateur", "operateur_unitaire", "lon", "lat"]]
    mm_out.to_csv(PROCESSED / "points_mobile_money.csv", index=False)

    controles.append(("Table Mobile Money : aucune ligne perdue",
                      len(mm_out) == len(mm), f"{len(mm_out)} lignes"))
    controles.append(("Points uniques conserves",
                      mm_out.FID.nunique() == mm.FID.nunique(),
                      f"{mm_out.FID.nunique()} points distincts"))

    et = pd.read_csv(PROCESSED / "etablissements.csv")
    et_out = _pts(et)
    et_out.to_csv(PROCESSED / "etablissements_pts.csv", index=False)
    controles.append(("Etablissements : aucune ligne perdue",
                      len(et_out) == len(et), f"{len(et_out)} etablissements"))

    # --------------------------------------------------------- empreinte
    poids = sum((PROCESSED / f).stat().st_size for f in
                ["prefectures.geojson", "points_mobile_money.csv",
                 "etablissements_pts.csv"])
    controles.append(("Paquet applicatif sous 8 Mo", poids < 8 * 1024 ** 2,
                      f"{poids / 1024 ** 2:.1f} Mo"))

    # ----------------------------------------------------------- rapport
    lignes = ["# Paquet de donnees du tableau de bord", "",
              "Genere par `src/build_app_data.py`. L'application lit ces trois",
              "fichiers et n'a besoin d'aucune bibliotheque geospatiale.", "",
              "| Controle | Resultat | Detail |", "|---|---|---|"]
    for nom, ok, detail in controles:
        lignes.append(f"| {nom} | {'OK' if ok else 'ECHEC'} | {detail} |")
    (ROOT / "reports" / "paquet_app.md").write_text(
        "\n".join(lignes) + "\n", encoding="utf-8")

    for nom, ok, detail in controles:
        print(f"[{'OK ' if ok else 'ECHEC'}] {nom} — {detail}")
    if not all(ok for _, ok, _ in controles):
        sys.exit(1)
    print(f"\nPaquet applicatif : {poids / 1024 ** 2:.1f} Mo")


if __name__ == "__main__":
    main()
