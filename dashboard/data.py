"""
Chargement des donnees du tableau de bord.

Le tableau de bord ne calcule RIEN : il lit les fichiers produits par la chaine
`src/`, deja controles. Toute valeur affichee est donc tracable jusqu'a son
controle arithmetique dans `reports/`.

Chaine amont :
    audit_raw -> extract_rgph5 -> build_geo -> build_indicators
              -> spatial_access -> priority_index
"""

from __future__ import annotations

import json
from pathlib import Path

import geopandas as gpd
import pandas as pd
import streamlit as st
from shapely import wkt

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
REPORTS = ROOT / "reports"

CRS_GEO = "EPSG:4326"

# Reperes nationaux, tous verifies par la chaine (cf. reports/)
POPULATION_NATIONALE = 8_095_498      # RGPH-5, novembre 2022
SUPERFICIE_NATIONALE = 57_242.1       # km2, somme COD-AB
DATE_INFRA = "collecte PRISE 2021-2022"
DATE_POP = "RGPH-5, novembre 2022"
DATE_CONTOURS = "COD-AB v02, valide au 07/01/2021"


@st.cache_data(show_spinner=False)
def prefectures() -> pd.DataFrame:
    """39 prefectures : indicateurs, accessibilite, score DCPI et point
    representatif (pour poser les etiquettes sur la carte)."""
    acc = pd.read_csv(PROCESSED / "acces_prefecture.csv")
    dcpi = pd.read_csv(PROCESSED / "dcpi_prefecture.csv")
    garder = ["prefecture", "DCPI", "DCPI_rang", "rang_DCPI",
              "n_D1_deficit_mm", "n_D2_deficit_agences",
              "n_D3_eloignement", "n_D4_enjeu_demographique"]
    t = acc.merge(dcpi[garder], on="prefecture", how="left")

    # `representative_point` garantit un point A L'INTERIEUR du polygone,
    # contrairement au centroide qui peut tomber dehors sur une forme concave.
    g = gpd.read_file(PROCESSED / "prefectures.gpkg")
    pts = g.geometry.representative_point()
    centres = pd.DataFrame({"prefecture": g.prefecture,
                            "centre_lon": pts.x, "centre_lat": pts.y})
    return t.merge(centres, on="prefecture", how="left")


@st.cache_data(show_spinner=False)
def geometrie_prefectures() -> gpd.GeoDataFrame:
    return gpd.read_file(PROCESSED / "prefectures.gpkg")


@st.cache_data(show_spinner=False)
def geojson_prefectures() -> dict:
    """GeoJSON simplifie : allege l'affichage sans deplacer les limites."""
    g = geometrie_prefectures().copy()
    # Tolerance 0.002 degre (~200 m) : invisible a l'echelle nationale.
    g["geometry"] = g.geometry.simplify(0.002, preserve_topology=True)
    return json.loads(g.to_json())


@st.cache_data(show_spinner=False)
def communes() -> pd.DataFrame:
    ind = pd.read_csv(PROCESSED / "indicateurs_commune.csv")
    dcpi = pd.read_csv(PROCESSED / "dcpi_commune.csv")
    garder = ["commune", "DCPI", "rang_DCPI", "dist_agence_km"]
    return ind.merge(dcpi[garder], on="commune", how="left")


@st.cache_data(show_spinner=False)
def etablissements() -> pd.DataFrame:
    """90 agences dedupliquees + 3 data centers, avec longitude/latitude."""
    df = pd.read_csv(PROCESSED / "etablissements.csv")
    g = df.geometry.map(wkt.loads)
    df["lon"] = g.map(lambda p: p.x)
    df["lat"] = g.map(lambda p: p.y)
    df["categorie"] = df.apply(
        lambda r: "Data center" if r.type_infrastructure == "Data center"
        else f"Agence {r.operateur}", axis=1)
    return df.drop(columns="geometry")


@st.cache_data(show_spinner=False)
def mobile_money() -> pd.DataFrame:
    """19 788 points (table courte : un point = une ligne)."""
    df = pd.read_csv(PROCESSED / "mobile_money_operateurs.csv")
    df = df.drop_duplicates("FID").copy()
    g = df.geometry.map(wkt.loads)
    df["lon"] = g.map(lambda p: p.x)
    df["lat"] = g.map(lambda p: p.y)
    return df.drop(columns=["geometry", "operateur_unitaire"])


@st.cache_data(show_spinner=False)
def mobile_money_operateurs() -> pd.DataFrame:
    """Table longue point x operateur : un point servi par deux operateurs
    y figure deux fois. A n'utiliser QUE pour les analyses par operateur."""
    return pd.read_csv(PROCESSED / "mobile_money_operateurs.csv")


@st.cache_data(show_spinner=False)
def cantons_acces() -> pd.DataFrame:
    return pd.read_csv(PROCESSED / "acces_canton.csv")


@st.cache_data(show_spinner=False)
def rapport(nom: str) -> str:
    chemin = REPORTS / f"{nom}.md"
    return chemin.read_text(encoding="utf-8") if chemin.exists() else ""


def controles_chaine() -> pd.DataFrame:
    """Extrait les tableaux de controle de tous les rapports de la chaine."""
    etapes = {
        "extraction_rgph5": "Extraction population",
        "socle_geo": "Socle geographique",
        "indicateurs": "Indicateurs",
        "acces_spatial": "Analyse spatiale",
        "dcpi": "Indice de priorite",
    }
    lignes = []
    for fichier, etape in etapes.items():
        texte = rapport(fichier)
        dans = False
        for ligne in texte.split("\n"):
            if ligne.startswith("| Controle |"):
                dans = True
                continue
            if dans:
                if not ligne.startswith("|"):
                    break
                cells = [c.strip() for c in ligne.strip("|").split("|")]
                if len(cells) >= 3 and not set(cells[0]) <= {"-", " "}:
                    lignes.append({"Etape": etape, "Controle": cells[0],
                                   "Resultat": cells[1], "Detail": cells[2]})
    return pd.DataFrame(lignes)
