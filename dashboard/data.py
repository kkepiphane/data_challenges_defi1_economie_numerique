"""
Chargement des donnees du tableau de bord.

Le tableau de bord ne calcule RIEN : il lit les fichiers produits par la chaine
`src/`, deja controles. Toute valeur affichee est donc tracable jusqu'a son
controle arithmetique dans `reports/`.

Chaine amont :
    audit_raw -> extract_rgph5 -> build_geo -> build_indicators
              -> spatial_access -> priority_index -> build_app_data

AUCUNE BIBLIOTHEQUE GEOSPATIALE ICI, ET C'EST VOULU
----------------------------------------------------
Les contours arrivent deja simplifies, les points deja en longitude/latitude :
`build_app_data.py` a fait ce travail une fois pour toutes, sur le poste ou la
chaine tourne. L'application se contente de `json` et de `pandas`.

Consequence directe : elle se deploie sur Streamlit Cloud sans geopandas,
shapely ni pyproj — trois bibliotheques compilees qu'il aurait fallu batir
pour n'executer aucun calcul geometrique.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st

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

    props = [f["properties"] for f in geojson_prefectures()["features"]]
    centres = pd.DataFrame([{"prefecture": p["prefecture"],
                             "centre_lon": p["centre_lon"],
                             "centre_lat": p["centre_lat"]} for p in props])
    return t.merge(centres, on="prefecture", how="left")


@st.cache_data(show_spinner=False)
def geojson_prefectures() -> dict:
    """Contours simplifies, produits par `src/build_app_data.py`."""
    with open(PROCESSED / "prefectures.geojson", encoding="utf-8") as f:
        return json.load(f)


@st.cache_data(show_spinner=False)
def communes() -> pd.DataFrame:
    ind = pd.read_csv(PROCESSED / "indicateurs_commune.csv")
    dcpi = pd.read_csv(PROCESSED / "dcpi_commune.csv")
    garder = ["commune", "DCPI", "rang_DCPI", "dist_agence_km"]
    return ind.merge(dcpi[garder], on="commune", how="left")


@st.cache_data(show_spinner=False)
def etablissements() -> pd.DataFrame:
    """90 agences dedupliquees + 3 data centers, avec longitude/latitude."""
    df = pd.read_csv(PROCESSED / "etablissements_pts.csv")
    df["categorie"] = df.apply(
        lambda r: "Data center" if r.type_infrastructure == "Data center"
        else f"Agence {r.operateur}", axis=1)
    return df


@st.cache_data(show_spinner=False)
def mobile_money() -> pd.DataFrame:
    """19 788 points (table courte : un point = une ligne)."""
    df = pd.read_csv(PROCESSED / "points_mobile_money.csv")
    return df.drop_duplicates("FID").drop(columns="operateur_unitaire")


@st.cache_data(show_spinner=False)
def mobile_money_operateurs() -> pd.DataFrame:
    """Table longue point x operateur : un point servi par deux operateurs
    y figure deux fois. A n'utiliser QUE pour les analyses par operateur."""
    return pd.read_csv(PROCESSED / "points_mobile_money.csv")


# =============================================================================
# FILTRE OPERATEUR
# =============================================================================
OPERATEURS = ["Tous", "Moov", "Togocom"]

# Pages construites sur l'indice DCPI, calcule tous operateurs confondus : le
# filtre operateur ne peut pas s'y appliquer sans recalculer l'indice et sa
# sensibilite dans la chaine. Elles le DISENT plutot que de l'ignorer en silence.
PAGES_SANS_OPERATEUR = {"Territoires prioritaires", "Arbitrage",
                        "Plan d'action"}


@st.cache_data(show_spinner=False)
def prefectures_operateur(operateur: str) -> pd.DataFrame:
    """Table prefectorale dont les indicateurs d'offre ne portent que sur
    `operateur`. Population, superficie et score DCPI sont inchanges.

    Un point servi par les deux operateurs compte pour chacun : c'est la
    PRESENCE de l'operateur qui est mesuree. Les points a operateur non
    renseigne n'appartiennent a aucun des deux.
    """
    t = prefectures()
    if operateur == "Tous":
        return t
    t = t.copy()
    s = operateur.lower()
    et = etablissements()
    actives = et[(et.type_infrastructure == "Agence operateur") & et.actif
                 & (et.operateur == operateur)].groupby("prefecture").size()
    t["points_mm"] = t[f"mm_{s}"]
    t["agences_actives"] = t.prefecture.map(actives).fillna(0).astype(int)
    t["hab_par_point_mm"] = t.population / t.points_mm.where(t.points_mm > 0)
    t["points_mm_pour_10k_hab"] = t.points_mm / t.population * 1e4
    t["agences_pour_100k_hab"] = t.agences_actives / t.population * 1e5
    dist = pd.read_csv(PROCESSED / "acces_operateur_prefecture.csv").query(
        "operateur == @operateur")
    t = t.drop(columns=["dist_agence_med_canton_km", "dist_agence_max_canton_km"])
    return t.merge(dist.drop(columns="operateur"), on="prefecture", how="left")


@st.cache_data(show_spinner=False)
def mobile_money_operateur(operateur: str) -> pd.DataFrame:
    """Points ou `operateur` est present (un point par ligne)."""
    if operateur == "Tous":
        return mobile_money()
    df = mobile_money_operateurs()
    return (df[df.operateur_unitaire == operateur].drop_duplicates("FID")
            .drop(columns="operateur_unitaire"))


def libelle_operateur(ctx: dict) -> str:
    """« tous opérateurs » ou « Moov » : pour les titres et les notes."""
    return ("tous opérateurs" if ctx.get("operateur", "Tous") == "Tous"
            else ctx["operateur"])


@st.cache_data(show_spinner=False)
def zones_blanches() -> pd.DataFrame:
    """373 cantons : temoins de couverture, score de risque, classe.
    Produit par `src/zones_blanches.py` — un PROXY, pas une mesure radio."""
    return pd.read_csv(PROCESSED / "zones_blanches_canton.csv")


@st.cache_data(show_spinner=False)
def zones_blanches_variantes() -> pd.DataFrame:
    return pd.read_csv(PROCESSED / "zones_blanches_variantes.csv")


@st.cache_data(show_spinner=False)
def geojson_cantons() -> dict:
    with open(PROCESSED / "cantons.geojson", encoding="utf-8") as f:
        return json.load(f)


@st.cache_data(show_spinner=False)
def vide_temoins() -> pd.DataFrame:
    """Mailles de 2 km situees a plus de 10 km de tout agent Mobile Money."""
    return pd.read_csv(PROCESSED / "vide_temoins.csv")


@st.cache_data(show_spinner=False)
def cantons_acces() -> pd.DataFrame:
    return pd.read_csv(PROCESSED / "acces_canton.csv")


def csv(df: pd.DataFrame, ctx: dict | None = None) -> bytes:
    """Export CSV lisible par Excel (BOM UTF-8), avec en-tete de provenance.
    Le filtre actif est rappele : un tableau detache de l'outil doit dire
    sur quel perimetre il porte."""
    perimetre = "39 préfectures"
    if ctx and ctx.get("filtre_actif"):
        perimetre = f"{len(ctx['prefectures'])} préfecture(s) : " + ", ".join(
            ctx["prefectures"])
    entete = ("# Défi 1 — Togo · export du tableau de bord\n"
              f"# Périmètre : {perimetre}\n"
              f"# Opérateur : {libelle_operateur(ctx or {})}\n"
              "# Sources : PRISE 2021-2022, RGPH-5 2022, COD-AB 2021\n")
    return (entete + df.to_csv(index=False)).encode("utf-8-sig")


def territoire_selectionne(cle: str, noms: list[str]) -> str | None:
    """Prefecture cliquee sur le graphique Plotly de cle `cle`.

    `noms` est la liste des prefectures dans l'ORDRE de la premiere trace :
    c'est le repli quand le point ne porte ni `location` (cartes) ni libelle
    d'axe (barres) — l'indice du point suffit alors a retrouver le territoire.
    """
    etat = st.session_state.get(cle) or {}
    points = (etat.get("selection") or {}).get("points") or []
    connus = set(noms)
    for p in points:
        for champ in ("location", "y", "x", "hovertext", "text"):
            if p.get(champ) in connus:
                return p[champ]
        donnees = p.get("customdata")
        if isinstance(donnees, list) and donnees and donnees[-1] in connus:
            return donnees[-1]
        i = p.get("point_index")
        if p.get("curve_number", 0) == 0 and isinstance(i, int) and i < len(noms):
            return noms[i]
    return None


PAGE_FICHE = "Territoires prioritaires"
CLE_FICHE = "fiche_territoire"


def ouvrir_fiche(cle: str, noms: list[str], changer_de_page: bool = False):
    """Rappel `on_select` : un clic sur un territoire ouvre sa fiche.

    Un RAPPEL, et non la lecture de la selection au fil du rendu : il ne
    s'execute qu'au clic. Lue a chaque rendu, la selection — qui persiste sur
    le graphique — ecraserait a chaque interaction le choix fait ensuite dans
    la liste deroulante de la fiche.
    """
    def _rappel() -> None:
        nom = territoire_selectionne(cle, noms)
        if nom:
            st.session_state[CLE_FICHE] = nom
            if changer_de_page:
                st.session_state.page = PAGE_FICHE
    return _rappel


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
        "zones_blanches": "Zones a risque",
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
