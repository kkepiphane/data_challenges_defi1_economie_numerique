"""
TERRITOIRES PRIORITAIRES — DIGITAL CONNECTIVITY PRIORITY INDEX
==============================================================
Trois exigences tenues :
  1. montrer le CLASSEMENT ;
  2. montrer POURQUOI chaque territoire est classe la ;
  3. montrer que le classement NE DEPEND PAS des ponderations retenues.

Aucune valeur n'est calculee ici : tout est lu dans `data/processed/`.
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import cartes
import data as D
import theme as T

COMPOSANTES = {
    "n_D1_deficit_mm": ("Déficit Mobile Money", 0.30, T.SERIE_1),
    "n_D2_deficit_agences": ("Déficit d'agences", 0.25, T.SERIE_2),
    "n_D3_eloignement": ("Éloignement", 0.25, T.SERIE_3),
    "n_D4_enjeu_demographique": ("Enjeu démographique", 0.20, T.GRIS_FOND),
}
SEUIL = 0.90


def afficher(ctx: dict) -> None:
    pref = D.prefectures()
    sens = pd.read_csv(D.PROCESSED / "dcpi_sensibilite.csv")
    variantes = pd.read_csv(D.PROCESSED / "dcpi_variantes.csv")
    com = D.communes()
    geo = D.geojson_prefectures()
    vue = pref[pref.prefecture.isin(ctx["prefectures"])]
    stables = set(sens[sens.frequence_top10 >= SEUIL].prefecture)

    st.markdown(T.bandeau(
        "Axes d'analyse", "Territoires prioritaires",
        "L'indice ne mesure pas « la qualité du numérique ». Il répond à une "
        "question de décision : où un investissement toucherait-il le plus "
        "d'habitants aujourd'hui mal desservis ?"), unsafe_allow_html=True)

    pop_stable = int(pref[pref.prefecture.isin(stables)].population.sum())
    k = st.columns(4, gap="small")
    k[0].markdown(T.kpi("Territoires prioritaires robustes",
                        f"{len(stables)}", "/ 39",
                        "présents dans le top 10 pour ≥ 90 % des pondérations",
                        T.VERT), unsafe_allow_html=True)
    k[1].markdown(T.kpi("Population concernée",
                        f"{pop_stable:,}".replace(",", " "), "",
                        f"{pop_stable / D.POPULATION_NATIONALE:.0%} de la "
                        "population nationale", T.SERIE_1),
                  unsafe_allow_html=True)
    k[2].markdown(T.kpi("Stabilité du classement", "0,971", "",
                        "corrélation moyenne sur 2 000 pondérations",
                        T.STATUT["bon"]), unsafe_allow_html=True)
    k[3].markdown(T.kpi("Pondérations testées", "2 000", "+ 8 variantes",
                        "retrait de composante, poids égaux, rangs",
                        T.STATUT["bon"]), unsafe_allow_html=True)

    # ================================================== carte + classement
    st.markdown("")
    g, d = st.columns([1, 1.1], gap="medium")

    with g:
        st.markdown(T.carte_ouvre("Score de priorité par préfecture"),
                    unsafe_allow_html=True)
        st.plotly_chart(
            cartes.choroplethe(vue, geo, "DCPI", "Score DCPI", ".1f", 560),
            width="stretch", config={"displayModeBar": False})
        st.markdown("</div>", unsafe_allow_html=True)

    with d:
        st.markdown(T.carte_ouvre("Classement · en bleu, les priorités robustes"),
                    unsafe_allow_html=True)
        c = vue.nlargest(18, "DCPI").sort_values("DCPI")
        fig = go.Figure(go.Bar(
            x=c.DCPI, y=c.prefecture, orientation="h",
            marker=dict(color=[T.SERIE_1 if p in stables else T.GRIS_FOND
                               for p in c.prefecture]),
            text=[f"{v:.1f}" for v in c.DCPI], textposition="outside",
            textfont=dict(size=10.5, color=T.ENCRE_2),
            customdata=c[["region", "population", "hab_par_point_mm",
                          "agences_actives",
                          "dist_agence_med_canton_km"]].values,
            hovertemplate=("<b>%{y}</b> — %{customdata[0]}<br><br>"
                           "Population : %{customdata[1]:,.0f}<br>"
                           "%{customdata[2]:,.0f} hab. par point<br>"
                           "Agences actives : %{customdata[3]}<br>"
                           "Distance médiane : %{customdata[4]:.0f} km"
                           "<extra></extra>")))
        fig.update_layout(height=560, showlegend=False,
                          xaxis_title="Score DCPI", yaxis_title=None,
                          margin=dict(l=4, r=40, t=6, b=34))
        st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})
        st.markdown("</div>", unsafe_allow_html=True)

    # ======================================================== sensibilité
    st.markdown("")
    st.markdown('<div class="sb-groupe" style="margin-top:1.2rem">'
                'Robustesse</div>', unsafe_allow_html=True)
    g2, d2 = st.columns([1.3, 1], gap="medium")

    with g2:
        st.markdown(T.carte_ouvre(
            "Présence dans le top 10 sur 2 000 pondérations aléatoires"),
            unsafe_allow_html=True)
        s = sens.head(14).sort_values("frequence_top10")
        fig2 = go.Figure(go.Bar(
            x=s.frequence_top10, y=s.prefecture, orientation="h",
            marker=dict(color=[T.SERIE_1 if f >= SEUIL else T.GRIS_FOND
                               for f in s.frequence_top10]),
            text=[f"{f:.0%}" for f in s.frequence_top10],
            textposition="outside", textfont=dict(size=10.5, color=T.ENCRE_2),
            customdata=s[["rang_median", "rang_min", "rang_max"]].values,
            hovertemplate=("<b>%{y}</b><br>Top 10 dans %{x:.0%} des cas<br>"
                           "Rang médian %{customdata[0]:.0f} "
                           "(de %{customdata[1]:.0f} à %{customdata[2]:.0f})"
                           "<extra></extra>")))
        fig2.add_vline(x=SEUIL, line=dict(color=T.STATUT["critique"], width=1.8))
        fig2.update_layout(height=420, showlegend=False,
                           xaxis=dict(tickformat=".0%", range=[0, 1.14]),
                           xaxis_title=None, yaxis_title=None,
                           margin=dict(l=4, r=44, t=6, b=24))
        st.plotly_chart(fig2, width="stretch", config={"displayModeBar": False})
        st.markdown("</div>", unsafe_allow_html=True)

    with d2:
        st.markdown(T.carte_ouvre("Variantes méthodologiques"),
                    unsafe_allow_html=True)
        t = variantes.copy()
        t.columns = ["Variante", "Corrélation", "Top 10"]
        t["Top 10"] = t["Top 10"].map(lambda v: f"{v}/10")
        st.dataframe(t.style.format({"Corrélation": "{:.3f}"}),
                     width="stretch", hide_index=True, height=352)
        st.markdown(
            T.lecture(
                "Aucun écrêtage n'a été appliqué : Kpendjal a réellement "
                "2 155 habitants par point. La variante « rangs », insensible "
                "aux valeurs extrêmes, donne 0,953 — les extrêmes ne pilotent "
                "donc pas le classement."), unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # ===================================================== fiche territoire
    st.markdown("")
    st.markdown('<div class="sb-groupe" style="margin-top:1.2rem">'
                'Fiche de territoire</div>', unsafe_allow_html=True)
    ordre = vue.sort_values("DCPI", ascending=False).prefecture.tolist()
    choix = st.selectbox("Préfecture", ordre, index=0,
                         label_visibility="collapsed")
    r = pref[pref.prefecture == choix].iloc[0]
    f = sens[sens.prefecture == choix]

    k2 = st.columns(5, gap="small")
    k2[0].markdown(T.kpi("Rang national", f"{int(r.rang_DCPI)}", "/ 39",
                         f"score {r.DCPI:.1f} sur 100", T.VERT),
                   unsafe_allow_html=True)
    k2[1].markdown(T.kpi("Habitants concernés",
                         f"{int(r.population):,}".replace(",", " "), "",
                         r.region, T.SERIE_1), unsafe_allow_html=True)
    k2[2].markdown(T.kpi("Habitants par point Mobile Money",
                         f"{r.hab_par_point_mm:,.0f}".replace(",", " "), "",
                         f"{int(r.points_mm)} points recensés", T.SERIE_1),
                   unsafe_allow_html=True)
    k2[3].markdown(T.kpi("Agences actives", f"{int(r.agences_actives)}", "",
                         f"{r.agences_pour_100k_hab:.2f} pour 100 000 hab.",
                         T.SERIE_2), unsafe_allow_html=True)
    k2[4].markdown(T.kpi("Distance à une agence",
                         f"{r.dist_agence_med_canton_km:.0f}", "km",
                         f"jusqu'à {r.dist_agence_max_canton_km:.0f} km au plus loin",
                         T.SERIE_3), unsafe_allow_html=True)

    st.markdown("")
    g3, d3 = st.columns([1, 1.35], gap="medium")
    with g3:
        st.markdown(T.carte_ouvre("De quoi ce score est-il fait ?"),
                    unsafe_allow_html=True)
        contribs = [(lib, r[col] * poids, coul)
                    for col, (lib, poids, coul) in COMPOSANTES.items()]
        total = sum(v for _, v, _ in contribs)
        fig3 = go.Figure()
        for lib, val, coul in contribs:
            fig3.add_trace(go.Bar(
                x=[val], y=["Score"], orientation="h", name=lib,
                marker=dict(color=coul, line=dict(width=2, color=T.SURFACE)),
                text=[f"{val:.1f}"], textposition="inside",
                insidetextanchor="middle",
                textfont=dict(size=11, color=T.SURFACE),
                hovertemplate=f"<b>{lib}</b><br>%{{x:.1f}} points sur "
                              f"{total:.1f}<extra></extra>"))
        fig3.update_layout(barmode="stack", height=170, yaxis_title=None,
                           xaxis_title=None, margin=dict(l=4, r=4, t=4, b=4),
                           legend=dict(orientation="h", y=-0.42,
                                       font=dict(size=10.5)))
        st.plotly_chart(fig3, width="stretch", config={"displayModeBar": False})
        if len(f):
            fr = f.iloc[0]
            st.markdown(T.lecture(
                f"Sur 2 000 pondérations, <b>{choix}</b> figure dans le top 10 "
                f"dans <b>{fr.frequence_top10:.0%}</b> des cas ; son rang varie "
                f"de {int(fr.rang_min)} à {int(fr.rang_max)}."),
                unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with d3:
        st.markdown(T.carte_ouvre(f"Communes de {choix}"),
                    unsafe_allow_html=True)
        sous = com[com.prefecture == choix].sort_values("DCPI", ascending=False)
        t = sous[["rang_DCPI", "commune", "population", "points_mm",
                  "hab_par_point_mm", "agences_actives", "dist_agence_km",
                  "DCPI"]].copy()
        t.columns = ["Rang", "Commune", "Population", "Points MM",
                     "Hab./point", "Agences", "Dist. (km)", "DCPI"]
        st.dataframe(t.style.format({
            "Population": "{:,.0f}", "Points MM": "{:,.0f}",
            "Hab./point": "{:,.0f}", "Dist. (km)": "{:,.0f}",
            "DCPI": "{:.1f}", "Rang": "{:.0f}"}),
            width="stretch", hide_index=True, height=280)
        st.markdown(T.source(
            "Rang établi sur les 117 communes. Les scores communaux et "
            "préfectoraux ne sont pas comparables : la composante "
            "d'éloignement n'y repose pas sur la même mesure."),
            unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
