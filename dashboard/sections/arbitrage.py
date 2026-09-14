"""
ARBITRAGE — LA PAGE OU LE DECIDEUR REPREND LA MAIN
===================================================
Les autres pages presentent un diagnostic. Celle-ci le rend CONTESTABLE et
CHIFFRABLE, parce que c'est ce qui separe un rapport d'un outil de decision.

Deux objections reviennent devant tout classement territorial. Cette page y
repond en laissant l'utilisateur agir, pas en argumentant :

  « VOS PONDERATIONS SONT ARBITRAIRES. »
      Exact — ce sont des choix. Alors reglez-les vous-meme. L'indice est une
      somme ponderee de quatre composantes deja normalisees : le reclassement
      est donc EXACT, pas une approximation. Vous verrez ce qui bouge, et
      surtout ce qui ne bouge pas.

  « UN CLASSEMENT NE ME DIT PAS QUOI FINANCER. »
      Exact aussi. Le simulateur convertit un OBJECTIF DE DESSERTE en nombre
      de points a ouvrir, territoire par territoire, et en population atteinte.

CE QUE CETTE PAGE NE FAIT PAS
------------------------------
Elle ne produit aucun cout, aucun delai, aucune rentabilite : ces grandeurs ne
figurent dans aucune source du projet, et les inventer ruinerait tout le reste.
Elle transforme un objectif en VOLUME D'EQUIPEMENT — la conversion en budget
appartient a qui detient les prix.

Rien n'est recalcule depuis les donnees brutes : les quatre composantes sont
lues telles que la chaine `src/priority_index.py` les a produites et controlees.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st

import data as D
import theme as T

# Composantes de l'indice, dans l'ordre ou elles sont presentees.
# Les poids de reference sont ceux de `src/priority_index.py` — la page les
# rappelle mais ne les impose pas.
COMPOSANTES = [
    ("n_D1_deficit_mm", "Déficit Mobile Money", 30, T.SERIE_1,
     "Habitants par point de service, rapporté aux autres préfectures."),
    ("n_D2_deficit_agences", "Déficit d'agences", 25, T.SERIE_2,
     "Agences d'opérateur actives pour 100 000 habitants."),
    ("n_D3_eloignement", "Éloignement", 25, T.SERIE_3,
     "Distance médiane, par canton, jusqu'à l'agence la plus proche."),
    ("n_D4_enjeu_demographique", "Enjeu démographique", 20, T.ENCRE_MUET,
     "Population concernée : à déficit égal, le nombre d'habitants tranche."),
]

# Departs rapides : (poids, ce que ce reglage privilegie).
PRESETS = {
    "Référence": ((30, 25, 25, 20),
                  "Les poids publiés par la chaîne d'analyse."),
    "Poids égaux": ((25, 25, 25, 25),
                    "Aucune composante privilégiée — le test le plus sévère."),
    # Libelles courts : quatre boutons partagent la largeur d'une colonne, et
    # un mot long s'y couperait en plein milieu. Le detail est en infobulle.
    "Distance": ((20, 20, 45, 15),
                 "Éloignement d'abord : priorité aux territoires les plus "
                 "isolés d'un guichet."),
    "Population": ((25, 15, 15, 45),
                   "Enjeu démographique d'abord : priorité au nombre "
                   "d'habitants effectivement touchés."),
}

SEUIL_ROBUSTE = 0.90


# =============================================================================
# CALCULS — arithmetique pure, aucune source retouchee
# =============================================================================
def _reponderer(pref: pd.DataFrame, poids: dict[str, float]) -> pd.DataFrame:
    """Recalcule le score et le rang. Les composantes etant deja normalisees
    sur 0-100, le score repondere est EXACTEMENT la somme ponderee."""
    total = sum(poids.values())
    t = pref.copy()
    t["DCPI_perso"] = sum(t[c] * (p / total) for c, p in poids.items())
    t["rang_perso"] = t.DCPI_perso.rank(ascending=False, method="min").astype(int)
    t["mouvement"] = t.rang_DCPI - t.rang_perso       # positif = gagne des rangs
    return t.sort_values("rang_perso")


def _plan_couverture(sel: pd.DataFrame, objectif: int) -> pd.DataFrame:
    """Convertit un objectif d'habitants par point en volume d'equipement.

    Une seule regle, et elle est arithmetique : atteindre `objectif` habitants
    par point sur un territoire de P habitants demande ceil(P / objectif)
    points. On retranche l'existant ; on ne descend jamais sous zero, car un
    territoire deja mieux desservi que l'objectif n'a rien a rendre.
    """
    t = sel.copy()
    t["points_cibles"] = np.ceil(t.population / objectif).astype(int)
    t["points_a_creer"] = (t.points_cibles - t.points_mm).clip(lower=0).astype(int)
    t["agences_a_ouvrir"] = (t.agences_actives == 0).astype(int)
    return t


# =============================================================================
# AFFICHAGE
# =============================================================================
def afficher(ctx: dict) -> None:
    pref = D.prefectures()
    sens = pd.read_csv(D.PROCESSED / "dcpi_sensibilite.csv")
    robustes = set(sens[sens.frequence_top10 >= SEUIL_ROBUSTE].prefecture)

    st.markdown(T.bandeau(
        "Décision · 05", "Arbitrage",
        "Le classement dépend de ce que vous décidez de faire compter. "
        "Réglez les quatre poids, observez ce qui bouge — puis convertissez "
        "un objectif de desserte en nombre de points à ouvrir."),
        unsafe_allow_html=True)

    # =========================================================== 1. PONDERATION
    st.markdown(T.etiquette("1 · Ce que vous faites compter"), unsafe_allow_html=True)

    for cle, _, defaut, _, _ in COMPOSANTES:
        st.session_state.setdefault(f"poids_{cle}", defaut)

    reglages, effet = st.columns([1, 1.55], gap="medium")

    with reglages, T.bloc("Pondération des quatre composantes"):
        # Des BOUTONS, et non un groupe radio : le depart rapide est une
        # action, pas un etat a conserver. Un radio aurait fallu remettre a
        # blanc apres usage — or Streamlit interdit d'ecrire dans l'etat d'un
        # widget une fois celui-ci instancie dans le rendu courant.
        # Les boutons, eux, precedent les curseurs : au moment ou ils fixent
        # les poids, aucun curseur n'existe encore dans ce rendu.
        depart = st.columns(len(PRESETS), gap="small")
        for colonne, (nom, (valeurs, aide)) in zip(depart, PRESETS.items()):
            if colonne.button(nom, key=f"preset_{nom}", help=aide,
                              width="stretch"):
                for (cle, *_), v in zip(COMPOSANTES, valeurs):
                    st.session_state[f"poids_{cle}"] = v
                st.rerun()

        poids = {}
        for cle, libelle, defaut, couleur, aide in COMPOSANTES:
            poids[cle] = st.slider(libelle, 0, 60,
                                   key=f"poids_{cle}", help=aide)
        somme = sum(poids.values()) or 1
        parts = " &nbsp;·&nbsp; ".join(
            f'<span style="color:{c}">■</span> {lib} '
            f'<b>{poids[cle] / somme:.0%}</b>'
            for cle, lib, _, c, _ in COMPOSANTES)
        st.markdown(T.source(
            "Poids effectifs, ramenés à 100 % : " + parts),
            unsafe_allow_html=True)

    classe = _reponderer(pref, poids)
    reference = set(pref.nsmallest(10, "rang_DCPI").prefecture)
    nouveau = set(classe.head(10).prefecture)
    # L'appariement se fait sur le NOM du territoire, jamais sur la position :
    # `classe` est trie par le rang repondere, donc sa n-ieme ligne ne decrit
    # pas la meme prefecture que la n-ieme ligne de `pref`. Comparer les deux
    # colonnes dans l'ordre revient a correler des paires sans rapport — et
    # produit une correlation quelconque la ou elle doit valoir exactement 1.
    apparie = pref[["prefecture", "rang_DCPI"]].merge(
        classe[["prefecture", "rang_perso"]], on="prefecture", how="inner")
    assert len(apparie) == len(pref), "appariement incomplet des préfectures"
    # Spearman = Pearson sur les rangs. `method="spearman"` importerait scipy,
    # absent de l'application (voir requirements.txt).
    spearman = apparie.rang_DCPI.rank().corr(apparie.rang_perso.rank())
    identiques = len(reference & nouveau)
    robustes_tenus = len(robustes & nouveau)

    with effet:
        with T.bloc("Effet sur le classement"):
            k = st.columns(3, gap="small")
            k[0].markdown(T.kpi(
                "Top 10 inchangé", f"{identiques}", "/ 10",
                "territoires communs avec la pondération de référence",
                T.VERT if identiques >= 8 else T.STATUT["attention"]),
                unsafe_allow_html=True)
            k[1].markdown(T.kpi(
                "Corrélation des rangs", f"{spearman:.3f}".replace(".", ","), "",
                "Spearman, sur les 39 préfectures",
                T.STATUT["bon"] if spearman >= 0.9 else T.STATUT["attention"]),
                unsafe_allow_html=True)
            k[2].markdown(T.kpi(
                "Priorités robustes retenues", f"{robustes_tenus}",
                f"/ {len(robustes)}",
                "parmi les 9 stables sur 2 000 pondérations", T.SERIE_1),
                unsafe_allow_html=True)

            st.markdown("")
            haut = classe.head(12)[
                ["rang_perso", "rang_DCPI", "mouvement", "prefecture", "region",
                 "population", "DCPI_perso"]].copy()
            haut["mouvement"] = haut.mouvement.map(
                lambda m: "—" if m == 0 else (f"▲ {m}" if m > 0 else f"▼ {-m}"))
            haut.columns = ["Rang", "Réf.", "Écart", "Préfecture", "Région",
                            "Population", "Score"]
            st.dataframe(haut.style.format({"Population": "{:,.0f}",
                                            "Score": "{:.1f}"}, thousands=" ", decimal=","),
                         width="stretch", hide_index=True, height=458)

    message = (
        f"Avec vos poids, <b>{identiques} des 10</b> territoires prioritaires "
        f"restent les mêmes, et la corrélation des rangs avec le classement de "
        f"référence est de <b>{spearman:.3f}</b>".replace(".", ",") +
        ". Le classement n'est donc pas un artefact de pondération : ce sont "
        "les mêmes territoires qui remontent, quelle que soit la priorité "
        "politique retenue."
        if identiques >= 7 else
        f"Vos poids déplacent nettement le classement : <b>{identiques} "
        f"territoires sur 10</b> seulement restent communs. Un tel écart "
        "mérite d'être assumé explicitement dans la décision.")
    st.markdown(T.action(message), unsafe_allow_html=True)

    # ============================================================ 2. COUVERTURE
    st.markdown(T.etiquette("2 · Ce que cela demanderait d'équiper", "1.5rem"), unsafe_allow_html=True)

    cadrage, resultat = st.columns([1, 1.55], gap="medium")

    with cadrage:
        with T.bloc("Hypothèses de l'exercice"):
            objectif = st.slider(
                "Objectif : habitants par point de service", 150, 900, 409, 10,
                help="409 est la moyenne nationale actuelle. Viser plus bas, "
                     "c'est viser mieux que la moyenne d'aujourd'hui.")
            combien = st.slider(
                "Nombre de territoires retenus", 1, 39, min(9, len(classe)),
                help="Les N premiers du classement que vous venez de régler.")
            st.markdown(T.lecture(
                "Une seule règle, arithmétique : atteindre un point pour "
                f"<b>{objectif}</b> habitants sur un territoire de P habitants "
                f"demande ⌈P / {objectif}⌉ points. L'existant est déduit. "
                "Aucun coût n'est produit ici — <b>les prix ne figurent dans "
                "aucune source du projet</b>."), unsafe_allow_html=True)

    plan = _plan_couverture(classe.head(combien), objectif)
    pop_touchee = int(plan.population.sum())
    a_creer = int(plan.points_a_creer.sum())
    guichets = int(plan.agences_a_ouvrir.sum())
    parc = int(pref.points_mm.sum())

    with resultat:
        with T.bloc(
                f"Ce que représenterait l'objectif sur {combien} territoire"
                f"{'s' if combien > 1 else ''}"):
            k2 = st.columns(4, gap="small")
            k2[0].markdown(T.kpi(
                "Population atteinte", f"{pop_touchee:,}".replace(",", " "), "",
                f"{pop_touchee / D.POPULATION_NATIONALE:.0%} de la population "
                "nationale", T.VERT), unsafe_allow_html=True)
            k2[1].markdown(T.kpi(
                "Points à ouvrir", f"{a_creer:,}".replace(",", " "), "",
                f"+{a_creer / parc:.0%} du parc national actuel", T.SERIE_1),
                unsafe_allow_html=True)
            k2[2].markdown(T.kpi(
                "Guichets d'opérateur à implanter", f"{guichets}", "",
                "territoires retenus sans aucune agence active", T.SERIE_2),
                unsafe_allow_html=True)
            k2[3].markdown(T.kpi(
                "Effort par habitant atteint",
                f"{a_creer / max(pop_touchee, 1) * 10000:,.1f}".replace(".", ","),
                "pts/10 000 hab.", "mesure la concentration de l'effort",
                T.SERIE_3), unsafe_allow_html=True)

            st.markdown("")
            courbe = _plan_couverture(classe, objectif)
            cum_pop = courbe.population.cumsum() / D.POPULATION_NATIONALE
            cum_pts = courbe.points_a_creer.cumsum()
            import plotly.graph_objects as go
            fig = go.Figure(go.Scatter(
                x=cum_pts, y=cum_pop, mode="lines",
                line=dict(color=T.SERIE_1, width=2.2),
                hovertemplate=("%{x:,.0f} points à ouvrir<br>"
                               "%{y:.1%} de la population<extra></extra>")))
            fig.add_trace(go.Scatter(
                x=[cum_pts.iloc[combien - 1]], y=[cum_pop.iloc[combien - 1]],
                mode="markers+text", marker=dict(color=T.STATUT["critique"], size=11),
                text=[f"  {combien} territoires"], textposition="middle right",
                textfont=dict(size=11, color=T.ENCRE),
                hovertemplate="<extra></extra>", showlegend=False))
            fig.update_layout(
                height=250, showlegend=False,
                xaxis_title="Points de service à ouvrir, cumulés",
                yaxis=dict(tickformat=".0%", title="Population atteinte"),
                margin=dict(l=4, r=80, t=10, b=34))
            st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})
            st.markdown(T.source(
                "Lecture : la pente s'aplatit quand on descend le classement — "
                "les premiers territoires coûtent peu de points pour beaucoup "
                "d'habitants atteints. C'est l'argument chiffré du ciblage."),
                unsafe_allow_html=True)

    # ------------------------------------------------------------ le detail
    st.markdown("")
    detail = plan[["rang_perso", "prefecture", "region", "population",
                   "hab_par_point_mm", "points_mm", "points_cibles",
                   "points_a_creer", "agences_actives",
                   "dist_agence_med_canton_km", "DCPI_perso"]].copy()
    detail.columns = ["Rang", "Préfecture", "Région", "Population",
                      "Hab./point", "Points existants", "Points cibles",
                      "Points à ouvrir", "Agences", "Dist. méd. (km)", "Score"]
    with T.bloc("Plan de couverture, territoire par territoire"):
        st.dataframe(detail.style.format({
            "Population": "{:,.0f}", "Hab./point": "{:,.0f}",
            "Points existants": "{:,.0f}", "Points cibles": "{:,.0f}",
            "Points à ouvrir": "{:,.0f}", "Dist. méd. (km)": "{:,.0f}",
            "Score": "{:.1f}"}, thousands=" ", decimal=","), width="stretch", hide_index=True,
            height=min(430, 40 + 35 * len(detail)))

    # =============================================================== 3. EMPORTER
    st.markdown(T.etiquette("3 · Emporter le résultat", "1.5rem"), unsafe_allow_html=True)
    st.markdown(T.lecture(
        "Les trois fichiers ci-dessous portent <b>vos</b> réglages, pas ceux "
        "par défaut : ils sont régénérés à chaque mouvement d'un curseur. "
        "L'en-tête de chacun rappelle les poids et l'objectif employés — un "
        "tableau sorti d'ici reste interprétable une fois détaché de l'outil."),
        unsafe_allow_html=True)

    entete = (f"# Défi 1 — Togo · export du tableau de bord\n"
              f"# Pondération : " + ", ".join(
                  f"{lib} {poids[cle] / somme:.0%}"
                  for cle, lib, _, _, _ in COMPOSANTES) +
              f"\n# Objectif de desserte : {objectif} habitants par point\n"
              f"# Sources : PRISE 2021-2022, RGPH-5 2022, COD-AB 2021\n")

    def _csv(df: pd.DataFrame) -> bytes:
        return (entete + df.to_csv(index=False)).encode("utf-8-sig")

    b = st.columns(3, gap="small")
    b[0].download_button(
        "Classement reponderé · 39 préfectures",
        _csv(classe[["rang_perso", "rang_DCPI", "prefecture", "region",
                     "population", "DCPI_perso", "DCPI"]]),
        "classement_repondere.csv", "text/csv", width="stretch")
    b[1].download_button(
        f"Plan de couverture · {combien} territoires",
        _csv(detail), "plan_couverture.csv", "text/csv", width="stretch")
    b[2].download_button(
        "Table complète des indicateurs",
        _csv(pref), "indicateurs_prefectures.csv", "text/csv",
        width="stretch")
