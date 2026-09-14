"""
PLAN D'ACTION
=============
La page qui repond a « et maintenant, on fait quoi ? ».

Principe : chaque intervention proposee est DEDUITE d'un deficit mesure, avec
son seuil de declenchement affiche. Aucune recommandation n'apparait sans le
chiffre qui la justifie. Un score eleve signale un besoin — jamais un cout,
une faisabilite ou une rentabilite, qui ne sont pas dans les donnees.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import data as D
import theme as T

# Chaque levier : (libelle, condition, seuil affiche, couleur, delai)
LEVIERS = [
    ("Implanter un point de présence opérateur",
     lambda r: r.agences_actives == 0,
     "aucune agence active sur la préfecture",
     T.SERIE_2,
     "Structurel",
     "Agence ou point relais agréé. C'est le seul levier qui crée un guichet "
     "là où il n'en existe aucun."),
    ("Densifier le réseau d'agents Mobile Money",
     lambda r: r.hab_par_point_mm > 800,
     "plus de 800 habitants par point (moyenne nationale : 409)",
     T.SERIE_1,
     "Rapide",
     "Levier le plus rapide et le moins capitalistique : il s'appuie sur des "
     "commerces existants plutôt que sur une construction."),
    ("Répartir le maillage plutôt qu'un point unique",
     lambda r: r.dist_agence_med_canton_km >= 25,
     "25 km ou plus en médiane jusqu'à une agence",
     T.SERIE_3,
     "Structurel",
     "Quand l'éloignement domine, ajouter un guichet au chef-lieu ne règle "
     "rien : c'est la répartition qui doit changer."),
    ("Ouvrir la concurrence entre opérateurs",
     lambda r: (r.mm_moov == 0) or (r.mm_togocom == 0),
     "un seul opérateur présent sur le territoire",
     T.STATUT["attention"],
     "Réglementaire",
     "Sans alternative, l'usager subit toute panne, tout tarif et toute "
     "rupture de liquidité."),
    ("Fiabiliser le recensement local",
     lambda r: r.points_mm > 0 and r.mm_operateur_inconnu / r.points_mm > 0.15,
     "plus de 15 % des points à opérateur non renseigné",
     T.ENCRE_MUET,
     "Préalable",
     "Dimensionner un investissement sur un recensement incertain, c'est "
     "risquer de le calibrer faux."),
]


def afficher(ctx: dict) -> None:
    pref = D.prefectures()
    sens = pd.read_csv(D.PROCESSED / "dcpi_sensibilite.csv")
    stables = set(sens[sens.frequence_top10 >= 0.90].prefecture)
    vue = pref[pref.prefecture.isin(ctx["prefectures"])]

    st.markdown(T.bandeau(
        "Décision · 06", "Plan d'action",
        "Quelles interventions les déficits mesurés appellent-ils, sur quels "
        "territoires, et pour combien d'habitants ?"), unsafe_allow_html=True)

    # ------------------------------------------------- application des leviers
    lignes = []
    for _, r in pref.iterrows():
        for nom, cond, seuil, coul, delai, _ in LEVIERS:
            if cond(r):
                lignes.append({"prefecture": r.prefecture, "region": r.region,
                               "levier": nom, "couleur": coul, "delai": delai,
                               "population": r.population,
                               "rang": r.rang_DCPI,
                               "prioritaire": r.prefecture in stables})
    actions = pd.DataFrame(lignes)

    # ============================================== ce qu'il faut retenir
    prio = pref[pref.prefecture.isin(stables)].sort_values("rang_DCPI")
    k = st.columns(4, gap="small")
    k[0].markdown(T.kpi("Territoires où agir en priorité", f"{len(stables)}",
                        "/ 39", "priorité stable quelles que soient les "
                        "pondérations", T.VERT), unsafe_allow_html=True)
    k[1].markdown(T.kpi("Habitants directement concernés",
                        f"{int(prio.population.sum()):,}".replace(",", " "), "",
                        f"{prio.population.sum() / D.POPULATION_NATIONALE:.0%} "
                        "de la population", T.SERIE_1), unsafe_allow_html=True)
    rapide = actions[(actions.delai == "Rapide") & actions.prioritaire]
    k[2].markdown(T.kpi("Territoires à levier rapide",
                        f"{rapide.prefecture.nunique()}", "",
                        "densification d'agents, sans construction",
                        T.STATUT["bon"]), unsafe_allow_html=True)
    struct = actions[(actions.delai == "Structurel") & actions.prioritaire]
    k[3].markdown(T.kpi("Territoires à levier structurel",
                        f"{struct.prefecture.nunique()}", "",
                        "implantation ou remaillage nécessaire",
                        T.STATUT["serieux"]), unsafe_allow_html=True)

    # ================================================= séquence proposée
    st.markdown("")
    st.markdown(T.etiquette("Séquence proposée", "1.1rem"), unsafe_allow_html=True)

    g, d = st.columns([1.25, 1], gap="medium")

    with g:
        with T.bloc("Les dix premiers territoires et leur levier dominant"):
            for _, r in pref.nsmallest(10, "rang_DCPI").sort_values(
                    "rang_DCPI").iterrows():
                mes = actions[actions.prefecture == r.prefecture]
                puces = " &nbsp;·&nbsp; ".join(
                    f'<span style="color:{c}">●</span> {n}'
                    for n, c in zip(mes.levier, mes.couleur))
                detail = (
                    f"<b>{int(r.population):,}</b> hab. &nbsp;·&nbsp; "
                    f"<b>{r.hab_par_point_mm:,.0f}</b> hab./point &nbsp;·&nbsp; "
                    f"<b>{int(r.agences_actives)}</b> agence(s) &nbsp;·&nbsp; "
                    f"<b>{r.dist_agence_med_canton_km:.0f} km</b><br>"
                    f'<span style="font-size:0.76rem">{puces}</span>'
                ).replace(",", " ")
                st.markdown(T.ligne_priorite(int(r.rang_DCPI), r.prefecture, detail),
                            unsafe_allow_html=True)

    with d:
        with T.bloc(
                "Population atteinte par levier · territoires prioritaires"):
            par_levier = (actions[actions.prioritaire].groupby("levier")
                          .agg(population=("population", "sum"),
                               n=("prefecture", "nunique"),
                               couleur=("couleur", "first"))
                          .reset_index().sort_values("population"))
            fig = go.Figure(go.Bar(
                x=par_levier.population, y=par_levier.levier, orientation="h",
                marker=dict(color=par_levier.couleur),
                text=[f"{int(v):,}".replace(",", " ") for v in par_levier.population],
                textposition="outside", textfont=dict(size=10.5, color=T.ENCRE_2),
                customdata=par_levier.n,
                hovertemplate=("<b>%{y}</b><br>%{x:,.0f} habitants<br>"
                               "%{customdata} préfecture(s)<extra></extra>")))
            fig.update_layout(height=340, showlegend=False,
                              xaxis_title="Habitants concernés", yaxis_title=None,
                              margin=dict(l=4, r=90, t=6, b=34))
            st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})
            st.markdown(
                T.action(
                    "Un même territoire peut relever de plusieurs leviers : les "
                    "populations ne s'additionnent donc pas d'une barre à "
                    "l'autre."), unsafe_allow_html=True)

    # ================================================= détail des leviers
    st.markdown("")
    st.markdown(T.etiquette("Les cinq leviers, et ce qui les déclenche", "1.1rem"), unsafe_allow_html=True)

    cols = st.columns(len(LEVIERS), gap="small")
    for col, (nom, cond, seuil, coul, delai, pourquoi) in zip(cols, LEVIERS):
        concernes = pref[pref.apply(cond, axis=1)]
        col.markdown(
            f'<div class="carte" style="border-top:3px solid {coul}">'
            f'<div class="carte-t">{delai}</div>'
            f'<div style="font-size:0.95rem;font-weight:620;color:{T.ENCRE};'
            f'line-height:1.35;margin-bottom:0.6rem">{nom}</div>'
            f'<div style="font-size:1.5rem;font-weight:660;color:{T.ENCRE}">'
            f'{len(concernes)}<span style="font-size:0.8rem;font-weight:500;'
            f'color:{T.ENCRE_2}"> préfectures</span></div>'
            f'<div style="font-size:0.76rem;color:{T.ENCRE_2};'
            f'margin-top:0.5rem;line-height:1.5">'
            f'<b>Seuil :</b> {seuil}</div>'
            f'<div style="font-size:0.76rem;color:{T.ENCRE_2};'
            f'margin-top:0.5rem;line-height:1.5">{pourquoi}</div></div>',
            unsafe_allow_html=True)

    # ======================================================== tableau complet
    st.markdown("")
    with st.expander("Voir le détail par territoire", expanded=ctx["filtre_actif"]):
        # Tous les territoires du filtre, y compris ceux qu'aucun levier ne
        # declenche : une ligne vide est une information (rien d'urgent).
        national = D.POPULATION_NATIONALE / pref.points_mm.sum()
        base = vue[["rang_DCPI", "prefecture", "region", "population",
                    "points_mm"]].rename(columns={"rang_DCPI": "rang"})
        # Volume d'equipement pour ramener chaque territoire a la moyenne
        # nationale : meme regle arithmetique que la page Arbitrage.
        base["a_ouvrir"] = (np.ceil(base.population / national)
                            - base.points_mm).clip(lower=0).astype(int)
        coches = (pd.crosstab(actions.prefecture, actions.levier)
                  .gt(0).replace({True: "●", False: ""}))
        t = (base.merge(coches, left_on="prefecture", right_index=True,
                        how="left").fillna("").sort_values("rang"))
        t = t.rename(columns={
            "rang": "Rang", "prefecture": "Préfecture", "region": "Région",
            "population": "Population", "points_mm": "Points MM",
            "a_ouvrir": f"Points à ouvrir (moy. {national:,.0f} hab./pt)"
            .replace(",", " ")})
        st.dataframe(t.style.format(
            {"Population": "{:,.0f}", "Rang": "{:.0f}", "Points MM": "{:,.0f}",
             t.columns[5]: "{:,.0f}"}, thousands=" ", decimal=","),
            width="stretch", hide_index=True)
        manque = int(base.a_ouvrir.sum())
        st.markdown(T.source(
            f"Ramener chaque territoire du périmètre à la moyenne nationale "
            f"demanderait <b>{manque:,} points Mobile Money</b> supplémentaires "
            f"(+{manque / max(int(base.points_mm.sum()), 1):.0%} du parc du "
            "périmètre). Pour d'autres objectifs, voir la page Arbitrage."
            .replace(",", " ")), unsafe_allow_html=True)
        st.download_button("Télécharger le plan par territoire (CSV)",
                           D.csv(t, ctx), "plan_action.csv", "text/csv",
                           icon=":material/download:", key="dl_plan")

    st.markdown(
        T.lecture(
            "<b>Ce que ce plan ne dit pas.</b> Ni le coût d'une intervention, "
            "ni sa faisabilité technique, ni sa rentabilité — aucune de ces "
            "dimensions n'existe dans les données mobilisées. Il hiérarchise "
            "des <i>besoins mesurés</i>, ce qui est le préalable à un "
            "arbitrage budgétaire, pas son substitut."),
        unsafe_allow_html=True)
