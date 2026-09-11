"""
VUE D'ENSEMBLE
==============
Ce qu'un decideur doit retenir en trente secondes, dans cet ordre :
    1. le chiffre national et ce qu'il cache ;
    2. cinq reperes ;
    3. les cinq territoires ou agir, nommes ;
    4. la carte qui montre ou ils sont.

Aucune information de methode sur cette page : elle est ailleurs.
"""

from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st

import cartes
import data as D
import theme as T


def afficher(ctx: dict) -> None:
    pref = D.prefectures()
    vue = pref[pref.prefecture.isin(ctx["prefectures"])]
    geo = D.geojson_prefectures()

    st.markdown(T.bandeau(
        "Diagnostic · 01", "Vue d'ensemble",
        "Où faut-il investir en priorité pour réduire les inégalités d'accès "
        "aux télécommunications et aux services numériques au Togo ?"),
        unsafe_allow_html=True)

    national = D.POPULATION_NATIONALE / pref.points_mm.sum()
    pire = pref.loc[pref.hab_par_point_mm.idxmax()]
    mieux = pref.loc[pref.hab_par_point_mm.idxmin()]
    sans_agence = pref[pref.agences_actives == 0]
    top = pref.nsmallest(5, "rang_DCPI").sort_values("rang_DCPI")

    # ======================================================= hero + carte
    g, d = st.columns([1, 1.42], gap="medium")

    with g:
        st.markdown(
            f'<div class="carte" style="padding:1.5rem 1.6rem 1.6rem 1.6rem">'
            f'<div class="carte-t">Desserte en services numériques · 2022</div>'
            f'<div class="hero-val">{national:,.0f}'
            f'<span class="hero-un">habitants / point</span></div>'
            f'<div class="hero-txt">'
            f"C'est la moyenne nationale d'habitants par point Mobile&nbsp;Money. "
            f"Elle masque un rapport de <b>1 à "
            f"{pire.hab_par_point_mm / mieux.hab_par_point_mm:.1f}</b> : "
            f"<b>{pire.prefecture}</b> compte {pire.hab_par_point_mm:,.0f} "
            f"habitants par point, <b>{mieux.prefecture}</b> en compte "
            f"{mieux.hab_par_point_mm:,.0f}.<br><br>"
            f"<b>{len(sans_agence)} préfectures sur 39</b> n'ont aucune agence "
            f"d'opérateur active — soit "
            f"<b>{sans_agence.population.sum() / D.POPULATION_NATIONALE:.0%} "
            f"de la population</b>."
            f'</div></div>'.replace(",", " "),
            unsafe_allow_html=True)

    with d:
        with T.bloc("Priorité d'intervention par préfecture"):
            fig = cartes.choroplethe(vue, geo, "DCPI", "Score DCPI",
                                     format_valeur=".1f", hauteur=372)
            st.plotly_chart(fig, width="stretch",
                            config={"displayModeBar": False})

    # ================================================================ KPI
    st.markdown("")
    k = st.columns(5, gap="small")
    donnees = [
        ("Population résidente", f"{D.POPULATION_NATIONALE:,}".replace(",", " "),
         "", "Recensement RGPH-5, novembre 2022", T.VERT),
        ("Points Mobile Money recensés",
         f"{int(pref.points_mm.sum()):,}".replace(",", " "), "",
         "tous géolocalisés, dans les 117 communes", T.VERT),
        ("Agences d'opérateur actives", f"{int(pref.agences_actives.sum())}", "",
         "2 opérateurs — Moov et Togocom", T.SERIE_1),
        ("Préfectures sans aucune agence", f"{len(sans_agence)}", "/ 39",
         f"{int(sans_agence.population.sum()):,} habitants".replace(",", " "),
         T.STATUT["critique"]),
        ("Centres de données", f"{int(pref.data_centers.sum())}", "",
         "les trois sont à Lomé", T.STATUT["attention"]),
    ]
    for col, (lib, val, un, note, coul) in zip(k, donnees):
        col.markdown(T.kpi(lib, val, un, note, coul), unsafe_allow_html=True)

    # ===================================================== zones à agir
    st.markdown("")
    g2, d2 = st.columns([1.28, 1], gap="medium")

    with g2:
        with T.bloc("Les cinq territoires prioritaires"):
            for _, r in top.iterrows():
                detail = (
                    f"<b>{int(r.population):,}</b> habitants &nbsp;·&nbsp; "
                    f"<b>{r.hab_par_point_mm:,.0f}</b> hab./point &nbsp;·&nbsp; "
                    f"<b>{int(r.agences_actives)}</b> agence"
                    f"{'s' if r.agences_actives > 1 else ''} &nbsp;·&nbsp; "
                    f"agence la plus proche à <b>{r.dist_agence_med_canton_km:.0f} km</b>"
                ).replace(",", " ")
                st.markdown(T.ligne_priorite(int(r.rang_DCPI), r.prefecture, detail),
                            unsafe_allow_html=True)
            st.markdown(
                T.action(
                    "Ces cinq territoires restent dans les dix premiers pour "
                    "<b>au moins 91 % de 2 000 pondérations testées</b>. Leur "
                    "priorité ne dépend donc pas des choix méthodologiques."),
                unsafe_allow_html=True)

    with d2:
        with T.bloc("Écart à la moyenne nationale"):
            c = vue.dropna(subset=["hab_par_point_mm"]).nlargest(12, "hab_par_point_mm")
            c = c.sort_values("hab_par_point_mm")
            prio = set(top.prefecture)
            fig2 = go.Figure(go.Bar(
                x=c.hab_par_point_mm, y=c.prefecture, orientation="h",
                marker=dict(color=[T.SERIE_1 if p in prio else T.GRIS_FOND
                                   for p in c.prefecture]),
                text=[f"×{v / national:.1f}" for v in c.hab_par_point_mm],
                textposition="outside", textfont=dict(size=10.5, color=T.ENCRE_2),
                hovertemplate=("<b>%{y}</b><br>%{x:,.0f} habitants par point"
                               "<extra></extra>")))
            fig2.add_vline(x=national, line=dict(color=T.STATUT["critique"], width=1.8))
            fig2.update_layout(
                height=372, showlegend=False,
                xaxis_title="Habitants par point Mobile Money",
                yaxis_title=None, margin=dict(l=4, r=42, t=4, b=34))
            st.plotly_chart(fig2, width="stretch",
                            config={"displayModeBar": False})
            st.markdown(
                T.source("Trait rouge : moyenne nationale de "
                         f"{national:,.0f} habitants par point."
                         .replace(",", " ")), unsafe_allow_html=True)
