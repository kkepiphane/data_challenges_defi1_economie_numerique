"""
DESSERTE & POPULATION
=====================
Trois questions :
    1. Quels territoires cumulent beaucoup d'habitants et peu de services ?
    2. A quel point l'equipement est-il concentre ?
    3. La concurrence entre operateurs couvre-t-elle tout le pays ?

La courbe de concentration et l'indice de Gini sont une TRANSFORMATION de
presentation de valeurs deja controlees, pas une donnee nouvelle ; la
formule est indiquee sous le graphique.
"""

from __future__ import annotations

import numpy as np
import plotly.graph_objects as go
import streamlit as st

import data as D
import theme as T


def _gini(valeurs: np.ndarray, poids: np.ndarray) -> float:
    o = np.argsort(valeurs)
    v, p = valeurs[o], poids[o]
    cp = np.cumsum(p) / p.sum()
    cv = np.cumsum(v * p) / (v * p).sum()
    return float(1 - np.sum((cv[1:] + cv[:-1]) * np.diff(cp)))


def afficher(ctx: dict) -> None:
    pref = D.prefectures()
    vue = pref[pref.prefecture.isin(ctx["prefectures"])].copy()

    st.markdown(T.bandeau(
        "Axes d'analyse", "Desserte & population",
        "Les services numériques sont-ils répartis à la mesure de la "
        "population, ou concentrés sur une fraction du pays ?"),
        unsafe_allow_html=True)

    national = D.POPULATION_NATIONALE / pref.points_mm.sum()
    med_pop = pref.population.median()
    base = pref.dropna(subset=["hab_par_point_mm"]).sort_values(
        "points_mm_pour_10k_hab")
    cum_pop = np.concatenate([[0], np.cumsum(base.population) / base.population.sum()])
    cum_mm = np.concatenate([[0], np.cumsum(base.points_mm) / base.points_mm.sum()])
    gini = _gini(base.points_mm_pour_10k_hab.values, base.population.values)
    moitie = np.interp(0.5, cum_pop, cum_mm)

    c = vue.dropna(subset=["hab_par_point_mm"]).copy()
    c["critique"] = (c.hab_par_point_mm > national) & (c.population > med_pop)
    quadrant = c[c.critique].sort_values("hab_par_point_mm", ascending=False)

    # =========================================================== indicateurs
    k = st.columns(4, gap="small")
    k[0].markdown(T.kpi("Indice de Gini de la desserte", f"{gini:.3f}", "",
                        "0 = strictement proportionnel à la population",
                        T.SERIE_1), unsafe_allow_html=True)
    k[1].markdown(T.kpi("Part des points pour la moitié la moins desservie",
                        f"{moitie:.0%}", "",
                        "au lieu de 50 % si la répartition suivait la population",
                        T.STATUT["critique"]), unsafe_allow_html=True)
    k[2].markdown(T.kpi("Territoires peuplés et sous-desservis",
                        f"{len(quadrant)}", "/ 39",
                        f"{int(quadrant.population.sum()):,} habitants concernés"
                        .replace(",", " "), T.STATUT["serieux"]),
                  unsafe_allow_html=True)
    k[3].markdown(T.kpi("Écart entre extrêmes",
                        f"×{c.hab_par_point_mm.max() / c.hab_par_point_mm.min():.1f}",
                        "", "de Tchaoudjo à Kpendjal", T.SERIE_2),
                  unsafe_allow_html=True)

    # ==================================================== quadrant critique
    st.markdown("")
    g, d = st.columns([1.45, 1], gap="medium")

    with g:
        st.markdown(T.carte_ouvre(
            "Population élevée et desserte faible · le quadrant critique"),
            unsafe_allow_html=True)
        fig = go.Figure()
        for etat, couleur, nom in ((False, T.GRIS_FOND, "Autres préfectures"),
                                   (True, T.SERIE_1,
                                    "Population et déficit élevés")):
            s = c[c.critique == etat]
            if s.empty:
                continue
            fig.add_trace(go.Scatter(
                x=s.population, y=s.hab_par_point_mm, mode="markers+text",
                marker=dict(size=12, color=couleur,
                            line=dict(width=2, color=T.SURFACE)),
                text=[n if e else "" for n, e in zip(s.prefecture, s.critique)],
                textposition="top center",
                textfont=dict(size=10, color=T.ENCRE_2),
                name=nom,
                customdata=np.stack([s.prefecture, s.region,
                                     s.agences_actives], axis=-1),
                hovertemplate=("<b>%{customdata[0]}</b> — %{customdata[1]}<br>"
                               "Population : %{x:,.0f}<br>"
                               "%{y:,.0f} habitants par point<br>"
                               "Agences actives : %{customdata[2]}"
                               "<extra></extra>")))
        fig.add_hline(y=national, line=dict(color=T.AXE, width=1.2))
        fig.add_vline(x=med_pop, line=dict(color=T.AXE, width=1.2))
        fig.update_layout(
            height=470, xaxis_type="log",
            xaxis_title="Population (échelle logarithmique)",
            yaxis_title="Habitants par point Mobile Money",
            margin=dict(l=4, r=4, t=6, b=36))
        st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})
        st.markdown(
            T.lecture(
                f"<b>{len(quadrant)} préfectures</b> sont à la fois plus "
                "peuplées que la médiane nationale et moins bien desservies "
                "que la moyenne. Ce sont elles qu'un investissement toucherait "
                "le plus efficacement. L'axe des abscisses est logarithmique — "
                "sans quoi le Golfe et ses 1,3 million d'habitants écraserait "
                "les 38 autres."), unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with d:
        st.markdown(T.carte_ouvre("Concentration de l'équipement"),
                    unsafe_allow_html=True)
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(
            x=[0, 1], y=[0, 1], mode="lines",
            name="Répartition proportionnelle",
            line=dict(color=T.AXE, width=1.8)))
        fig2.add_trace(go.Scatter(
            x=cum_pop, y=cum_mm, mode="lines", name="Répartition observée",
            line=dict(color=T.SERIE_1, width=2.6),
            fill="tonexty", fillcolor="rgba(42,120,214,0.09)",
            hovertemplate=("%{x:.0%} de la population cumulée<br>"
                           "%{y:.0%} des points<extra></extra>")))
        fig2.update_layout(
            height=470, xaxis_title="Part cumulée de la population",
            yaxis_title="Part cumulée des points Mobile Money",
            xaxis=dict(tickformat=".0%"), yaxis=dict(tickformat=".0%"),
            margin=dict(l=4, r=4, t=6, b=36))
        st.plotly_chart(fig2, width="stretch", config={"displayModeBar": False})
        st.markdown(
            T.lecture(
                "Les préfectures sont classées du plus faible au plus fort "
                "taux d'équipement par habitant. L'écart à la diagonale "
                "mesure l'inégalité. <b>Transformation de présentation</b> "
                "appliquée à des valeurs déjà contrôlées."),
            unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # ======================================================== opérateurs
    st.markdown("")
    mmo = D.mobile_money_operateurs()
    mmo = mmo[mmo.prefecture.isin(ctx["prefectures"])]
    brut = mmo.drop_duplicates("FID")
    libelles = {"Moov, Togocom": "Les deux opérateurs",
                "Togocom": "Togocom seul", "Moov": "Moov seul",
                "Nsp": "Opérateur non renseigné"}
    rep = (brut.operateur.value_counts().rename_axis("modalite")
           .reset_index(name="points"))
    rep["libelle"] = rep.modalite.map(libelles).fillna(rep.modalite)
    couleurs = {"Les deux opérateurs": T.SERIE_1, "Togocom seul": T.SERIE_2,
                "Moov seul": T.SERIE_3, "Opérateur non renseigné": T.GRIS_FOND}

    g2, d2 = st.columns([1.45, 1], gap="medium")
    with g2:
        st.markdown(T.carte_ouvre(
            "Présence des opérateurs sur les points de service"),
            unsafe_allow_html=True)
        fig3 = go.Figure(go.Bar(
            x=rep.points, y=rep.libelle, orientation="h",
            marker=dict(color=[couleurs.get(l, T.GRIS_FOND)
                               for l in rep.libelle]),
            text=[f"{v:,}".replace(",", " ") + f"   ({v / len(brut):.1%})"
                  for v in rep.points],
            textposition="outside", textfont=dict(size=11, color=T.ENCRE_2),
            hovertemplate="<b>%{y}</b><br>%{x:,.0f} points<extra></extra>"))
        fig3.update_layout(height=250, showlegend=False,
                           xaxis_title="Points Mobile Money", yaxis_title=None,
                           margin=dict(l=4, r=140, t=6, b=34))
        st.plotly_chart(fig3, width="stretch", config={"displayModeBar": False})
        st.markdown("</div>", unsafe_allow_html=True)

    n_tgc = int(rep.loc[rep.libelle == "Togocom seul", "points"].sum())
    n_moov = int(rep.loc[rep.libelle == "Moov seul", "points"].sum())
    n_nsp = int(rep.loc[rep.libelle == "Opérateur non renseigné",
                        "points"].sum())
    with d2:
        st.markdown(
            T.action(
                f"<b>{n_tgc:,} points ne servent que Togocom</b>, contre "
                f"<b>{n_moov:,} pour Moov seul</b> — un rapport de "
                f"{n_tgc / max(n_moov, 1):.1f} à 1. Là où un seul opérateur "
                "est présent, l'usager n'a aucune alternative en cas de "
                "panne, de tarif ou de rupture de liquidité. "
                "<b>Ouvrir la concurrence est un objectif en soi.</b>"
                .replace(",", " ")), unsafe_allow_html=True)
        st.markdown("")
        st.markdown(
            T.lecture(
                f"Les <b>{n_nsp:,} points à opérateur non renseigné</b> "
                "forment une catégorie propre : ils ne sont ni réaffectés, ni "
                "supprimés. La variable source est multivaluée — un point "
                "servi par deux opérateurs n'est pas deux points."
                .replace(",", " ")), unsafe_allow_html=True)

    with st.expander("Voir les données par préfecture"):
        t = vue[["prefecture", "region", "population", "points_mm", "mm_moov",
                 "mm_togocom", "mm_operateur_inconnu",
                 "points_mm_pour_10k_hab"]].copy()
        t.columns = ["Préfecture", "Région", "Population", "Points MM",
                     "Présence Moov", "Présence Togocom", "Opérateur inconnu",
                     "Points / 10 000 hab."]
        st.dataframe(t.sort_values("Points / 10 000 hab.").style.format({
            "Population": "{:,.0f}", "Points MM": "{:,.0f}",
            "Présence Moov": "{:,.0f}", "Présence Togocom": "{:,.0f}",
            "Points / 10 000 hab.": "{:,.1f}"}),
            width="stretch", hide_index=True)
        st.caption("« Présence » compte les points où l'opérateur est "
                   "disponible : un point servi par les deux figure dans les "
                   "deux colonnes.")
