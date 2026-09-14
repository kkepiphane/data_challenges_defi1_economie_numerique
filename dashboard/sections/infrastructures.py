"""
INFRASTRUCTURES
===============
Deux questions, deux cartes :
    1. Ou sont physiquement les agences et les centres de donnees ?
    2. Cette implantation suit-elle la population ?

Trois categories au maximum sur une carte : au-dela, les teintes cessent
d'etre distinguables pour un lecteur daltonien. Les 19 788 points Mobile
Money servent donc de toile de fond grise, pas de quatrieme serie.
"""

from __future__ import annotations

import streamlit as st

import cartes
import data as D
import theme as T

INDICATEURS = {
    "Priorité d'intervention": (
        "DCPI", "Score DCPI", ".1f",
        "Où faut-il agir en priorité ?",
        "Le score combine trois déficits mesurés et le nombre d'habitants "
        "concernés. Plus la teinte est foncée, plus l'intervention toucherait "
        "d'habitants aujourd'hui mal desservis."),
    "Desserte Mobile Money": (
        "hab_par_point_mm", "Hab. par point", ",.0f",
        "La desserte suit-elle la population ?",
        "Nombre d'habitants pour un point de service. Plus la teinte est "
        "foncée, moins le territoire est desservi. Le Grand Lomé et les "
        "marges du pays s'opposent nettement."),
    "Éloignement des agences": (
        "dist_agence_med_canton_km", "Distance médiane (km)", ",.0f",
        "À quelle distance est l'agence la plus proche ?",
        "Distance médiane depuis les cantons du territoire. Quatre "
        "préfectures dépassent 40 km : l'éloignement y est le frein "
        "principal, avant même le nombre de guichets."),
    "Densité de population": (
        "densite_hab_km2", "Hab. par km²", ",.0f",
        "Où vivent les Togolais ?",
        "De 42 habitants au km² à Mô jusqu'à 5 423 dans le Golfe, soit un "
        "rapport de 1 à 130. Une infrastructure absente n'a pas le même "
        "poids selon la densité qu'elle laisse sans service."),
    "Agences par habitant": (
        "agences_pour_100k_hab", "Agences / 100 000 hab.", ",.2f",
        "L'offre est-elle proportionnée à la population ?",
        "Treize préfectures affichent zéro. Ce sont de vrais zéros : le "
        "référentiel administratif est complet, une absence de valeur "
        "signifie bien une absence d'agence."),
}


def afficher(ctx: dict) -> None:
    pref = D.prefectures_operateur(ctx["operateur"])
    op = D.libelle_operateur(ctx)
    vue = pref[pref.prefecture.isin(ctx["prefectures"])]
    geo = D.geojson_prefectures()
    etab = D.etablissements()
    etab_vue = etab[etab.prefecture.isin(ctx["prefectures"])]

    st.markdown(T.bandeau(
        "Diagnostic · 02", "Infrastructures",
        "Où sont les agences d'opérateur et les centres de données, et cette "
        "implantation suit-elle la population ?"), unsafe_allow_html=True)

    # =============================================== carte des équipements
    g, d = st.columns([1, 3.1], gap="medium")

    with g:
        with T.bloc("Ce que la carte affiche"):
            couleurs = dict(zip(["Agence Moov", "Agence Togocom", "Data center"],
                                T.CATEGORIEL))
            # Les centres de donnees n'appartiennent a aucun operateur : ils
            # restent affiches quel que soit le filtre.
            cats = [c for c in couleurs if ctx["operateur"] == "Tous"
                    or c in (f"Agence {ctx['operateur']}", "Data center")]
            sel = st.multiselect("Type", cats, default=cats,
                                 label_visibility="collapsed")
            mm = D.mobile_money_operateur(ctx["operateur"])
            fond = st.toggle(
                f"Fond des {len(mm):,} points Mobile Money".replace(",", " ")
                + ("" if ctx["operateur"] == "Tous" else f" {op}"), value=True)

        pts = etab_vue[etab_vue.categorie.isin(sel)]
        st.markdown("")
        for cat in cats:
            coul = couleurs[cat]
            n = int((pts.categorie == cat).sum())
            st.markdown(T.kpi(cat, f"{n}", "",
                              "sur le territoire sélectionné", coul),
                        unsafe_allow_html=True)
            st.markdown("")

    with d:
        with T.bloc(
                "Implantation des équipements télécoms · limites régionales en "
                "trait sombre, préfectorales en liseré blanc"):
            couches = []
            for cat in cats:
                coul = couleurs[cat]
                s = pts[pts.categorie == cat]
                couches.append({
                    "nom": cat, "couleur": coul,
                    "lat": s.lat.tolist(), "lon": s.lon.tolist(),
                    "texte": [f"<b>{n}</b><br>{c}, {p}<br>"
                              f"<span style='color:#8b8a84'>{r}</span>"
                              for n, c, p, r in zip(s.etab_nom, s.commune,
                                                    s.prefecture, s.region)]})
            fond_mm = mm[mm.prefecture.isin(ctx["prefectures"])] if fond else None
            st.plotly_chart(cartes.carte_points(couches, geo, vue, 620, fond_mm),
                            width="stretch", config={"displayModeBar": False})

    st.markdown(
        T.action(
            "<b>Les trois centres de données du pays sont dans la seule "
            "préfecture du Golfe.</b> L'hébergement numérique national est "
            "entièrement concentré à Lomé — aucune redondance géographique "
            "hors de la capitale."), unsafe_allow_html=True)

    # ================================================ choroplèthe pilotée
    st.markdown("")
    st.markdown(T.etiquette("Lecture territoriale", "1.4rem"), unsafe_allow_html=True)
    choix = st.radio("Indicateur", list(INDICATEURS), horizontal=True,
                     label_visibility="collapsed")
    col, titre_ech, fmt, question, lecture = INDICATEURS[choix]

    g2, d2 = st.columns([3.1, 1], gap="medium")
    with g2:
        with T.bloc(f"{choix} · cliquez un territoire pour ouvrir sa fiche"):
            st.plotly_chart(
                cartes.choroplethe(vue, geo, col, titre_ech, fmt, 600),
                width="stretch", key="carte_infra",
                on_select=D.ouvrir_fiche(
                    "carte_infra", vue.dropna(subset=[col]).prefecture.tolist(),
                    True),
                selection_mode="points", config={"displayModeBar": False})
    with d2:
        st.markdown(T.question(question), unsafe_allow_html=True)
        st.markdown(T.lecture(lecture), unsafe_allow_html=True)
        if ctx["operateur"] != "Tous" and col != "densite_hab_km2":
            st.markdown(T.source(
                "Score calculé tous opérateurs confondus : le filtre "
                "opérateur ne s'y applique pas." if col == "DCPI" else
                f"Valeurs calculées pour <b>{op}</b> seul. Le commentaire "
                "ci-dessus décrit l'ensemble des opérateurs."),
                unsafe_allow_html=True)
        t = vue.dropna(subset=[col]).nlargest(6, col)[["prefecture", col]]
        st.markdown('<div class="carte-t" style="margin-top:1.1rem">'
                    'Six valeurs les plus élevées</div>', unsafe_allow_html=True)
        for _, r in t.iterrows():
            st.markdown(
                f'<div style="display:flex;justify-content:space-between;'
                f'padding:0.38rem 0;border-bottom:1px solid {T.BORDURE};'
                f'font-size:0.86rem">'
                f'<span style="color:{T.ENCRE}">{r.prefecture}</span>'
                f'<span style="font-weight:600;color:{T.ENCRE}">'
                f'{r[col]:{fmt}}</span></div>'.replace(",", " "),
                unsafe_allow_html=True)

    with st.expander("Voir toutes les données"):
        t = vue[["prefecture", "region", "population", "superficie_km2",
                 "densite_hab_km2", "points_mm", "hab_par_point_mm",
                 "agences_actives", "data_centers",
                 "dist_agence_med_canton_km", "DCPI"]].copy()
        t.columns = ["Préfecture", "Région", "Population", "Superficie (km²)",
                     "Densité (hab/km²)", "Points MM", "Hab./point MM",
                     "Agences actives", "Data centers", "Dist. médiane (km)",
                     "DCPI"]
        t = t.sort_values("DCPI", ascending=False)
        st.dataframe(t.style.format({
            "Population": "{:,.0f}", "Superficie (km²)": "{:,.0f}",
            "Densité (hab/km²)": "{:,.0f}", "Points MM": "{:,.0f}",
            "Hab./point MM": "{:,.0f}", "Dist. médiane (km)": "{:,.0f}",
            "DCPI": "{:.1f}"}, thousands=" ", decimal=","), width="stretch", hide_index=True)
        st.download_button("Télécharger ce tableau (CSV)", D.csv(t, ctx),
                           "infrastructures_prefectures.csv", "text/csv",
                           icon=":material/download:", key="dl_infra")
