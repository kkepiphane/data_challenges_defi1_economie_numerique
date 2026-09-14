"""
CONSTRUCTION DES CARTES
=======================
Objectif : des limites administratives REELLEMENT lisibles.

Le probleme d'une choroplethe par defaut est que les polygones se touchent
sans separation nette : on voit des taches de couleur, pas des territoires.
Trois corrections sont appliquees ici :

  1. un LISERE BLANC de 1,4 px entre chaque prefecture — l'equivalent
     cartographique de la regle « 2 px de surface entre deux aplats » ;
  2. un TRACE DES LIMITES REGIONALES par-dessus, plus epais et sombre :
     le lecteur distingue d'un coup d'oeil les 5 regions et les 39
     prefectures, deux niveaux de lecture au lieu d'un ;
  3. des ETIQUETTES de prefecture posees sur les centroides, en halo blanc,
     pour que la carte se lise sans survol.

La rampe reste sequentielle a une seule teinte : la magnitude est portee par
la luminosite, jamais par la teinte.
"""

from __future__ import annotations

import numpy as np
import plotly.graph_objects as go

import theme as T

CENTRE = {"lat": 8.68, "lon": 0.98}
ZOOM = 6.05
STYLE_FOND = "carto-positron"


def _lignes(geometry: dict) -> tuple[list, list]:
    """Extrait les coordonnees de contour d'une geometrie GeoJSON."""
    lons: list[float | None] = []
    lats: list[float | None] = []
    polys = (geometry["coordinates"] if geometry["type"] == "MultiPolygon"
             else [geometry["coordinates"]])
    for poly in polys:
        for anneau in poly:
            lons.extend([p[0] for p in anneau] + [None])
            lats.extend([p[1] for p in anneau] + [None])
    return lons, lats


def contours(geojson: dict, cle: str | None = None,
             valeurs: set | None = None) -> tuple[list, list]:
    """Contours de toutes les entites, ou seulement de celles retenues."""
    lons: list = []
    lats: list = []
    for f in geojson["features"]:
        if valeurs is not None and f["properties"].get(cle) not in valeurs:
            continue
        a, b = _lignes(f["geometry"])
        lons += a
        lats += b
    return lons, lats


def _limites_regionales(geojson: dict, table) -> tuple[list, list]:
    """Contours agreges par region : on trace l'union approchee en
    superposant les prefectures d'une meme region, ce qui fait ressortir
    l'enveloppe regionale sans calcul geometrique supplementaire."""
    lons: list = []
    lats: list = []
    for region in table.region.unique():
        membres = set(table.loc[table.region == region, "prefecture"])
        a, b = contours(geojson, "prefecture", membres)
        lons += a
        lats += b
    return lons, lats


def choroplethe(table, geojson: dict, colonne: str, titre_echelle: str,
                format_valeur: str = ",.0f", hauteur: int = 640,
                etiquettes: bool = True, inverser: bool = False) -> go.Figure:
    """Choroplethe par prefecture, avec limites lisibles et etiquettes."""
    echelle = list(reversed(T.SEQUENTIEL)) if inverser else T.SEQUENTIEL
    t = table.dropna(subset=[colonne])

    fig = go.Figure(go.Choroplethmap(
        geojson=geojson, locations=t.prefecture, featureidkey="properties.prefecture",
        z=t[colonne], colorscale=[[i / (len(echelle) - 1), c]
                                  for i, c in enumerate(echelle)],
        marker=dict(line=dict(color="#ffffff", width=1.4), opacity=0.9),
        # Le nom en DERNIERE position : c'est lui que lit
        # `data.territoire_selectionne` quand la carte est cliquee.
        customdata=np.stack([t.region, t.population, t.points_mm,
                             t.agences_actives, t[colonne], t.prefecture],
                            axis=-1),
        hovertemplate=("<b>%{location}</b><br>"
                       "<span style='color:#8b8a84'>%{customdata[0]}</span><br>"
                       "<br>Population&nbsp;: %{customdata[1]:,.0f}<br>"
                       "Points Mobile Money&nbsp;: %{customdata[2]:,.0f}<br>"
                       "Agences actives&nbsp;: %{customdata[3]}<br>"
                       f"<b>{titre_echelle}&nbsp;: "
                       f"%{{customdata[4]:{format_valeur}}}</b><extra></extra>"),
        colorbar=dict(title=dict(text=titre_echelle, side="right",
                                 font=dict(size=11, color=T.ENCRE_2)),
                      thickness=11, len=0.62, x=0.985, xanchor="right",
                      y=0.5, outlinewidth=0, ticks="outside", ticklen=3,
                      tickfont=dict(size=10, color=T.ENCRE_MUET),
                      bgcolor="rgba(255,255,255,0.85)"),
    ))

    # Limites régionales : second niveau de lecture
    lr_lon, lr_lat = _limites_regionales(geojson, table)
    fig.add_trace(go.Scattermap(
        lon=lr_lon, lat=lr_lat, mode="lines",
        line=dict(color="rgba(18,18,15,0.55)", width=1.6),
        hoverinfo="skip", showlegend=False))

    if etiquettes:
        e = table.dropna(subset=[colonne])
        fig.add_trace(go.Scattermap(
            lon=e.centre_lon, lat=e.centre_lat, mode="text",
            text=e.prefecture,
            textfont=dict(size=9.5, color="#12120f", family=T.SANS),
            hoverinfo="skip", showlegend=False))

    fig.update_layout(
        map=dict(style=STYLE_FOND, center=CENTRE, zoom=ZOOM),
        height=hauteur, margin=dict(l=0, r=0, t=0, b=0),
        showlegend=False)
    return fig


def carte_points(couches: list[dict], geojson: dict, table,
                 hauteur: int = 640, fond_mm=None) -> go.Figure:
    """Carte de points d'infrastructure, sur un fond de limites lisibles.

    `couches` : liste de dicts {nom, lat, lon, couleur, texte}.
    """
    fig = go.Figure()

    # 1. Aplat clair des prefectures : donne du corps au territoire
    fig.add_trace(go.Choroplethmap(
        geojson=geojson, locations=table.prefecture,
        featureidkey="properties.prefecture",
        z=[1] * len(table), colorscale=[[0, "#f2f1ec"], [1, "#f2f1ec"]],
        marker=dict(line=dict(color="#ffffff", width=1.2), opacity=0.85),
        showscale=False, hoverinfo="skip"))

    # 2. Limites régionales par-dessus
    lr_lon, lr_lat = _limites_regionales(geojson, table)
    fig.add_trace(go.Scattermap(
        lon=lr_lon, lat=lr_lat, mode="lines",
        line=dict(color="rgba(18,18,15,0.5)", width=1.5),
        hoverinfo="skip", showlegend=False))

    # 3. Toile de fond Mobile Money, si demandée
    if fond_mm is not None and len(fond_mm):
        fig.add_trace(go.Scattermap(
            lat=fond_mm.lat, lon=fond_mm.lon, mode="markers",
            marker=dict(size=3.2, color="#9b9a94", opacity=0.5),
            name=f"Points Mobile Money ({len(fond_mm):,})".replace(",", " "),
            hoverinfo="skip", showlegend=True))

    # 4. Infrastructures — anneau blanc de séparation sur marques superposées
    for c in couches:
        if not len(c["lat"]):
            continue
        fig.add_trace(go.Scattermap(
            lat=c["lat"], lon=c["lon"], mode="markers",
            marker=dict(size=12, color=c["couleur"], opacity=0.95),
            name=f"{c['nom']} ({len(c['lat'])})",
            text=c["texte"],
            hovertemplate="%{text}<extra></extra>"))

    fig.update_layout(
        map=dict(style=STYLE_FOND, center=CENTRE, zoom=ZOOM),
        height=hauteur, margin=dict(l=0, r=0, t=0, b=0),
        legend=dict(orientation="v", yanchor="top", y=0.98, x=0.012,
                    bgcolor="rgba(255,255,255,0.92)", bordercolor=T.BORDURE,
                    borderwidth=1, font=dict(size=11.5, color=T.ENCRE_2)))
    return fig
