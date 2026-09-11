"""
ACCES AUX TELECOMMUNICATIONS ET AUX SERVICES NUMERIQUES — TOGO
===============================================================
Lancement :  streamlit run streamlit_app.py

Tableau de bord d'aide a la decision publique. Les sept pages suivent le
raisonnement d'un rapport, pas l'arborescence des donnees :

    VUE D'ENSEMBLE  ce qu'il faut retenir en trente secondes
    INFRASTRUCTURES  ce qui existe, apres deduplication
    DESSERTE        ce que cela donne par habitant
    PRIORITES       ou le manque est le plus fort, et si le classement tient
    ARBITRAGE       reglez les ponderations, chiffrez la couverture
    PLAN D'ACTION   quelles interventions les deficits mesures appellent
    METHODE         sources, controles, pistes ecartees, limites

La navigation est laterale et groupee par INTENTION : etablir le diagnostic,
puis decider. Sept entrees tiennent verticalement sans se serrer, ce qu'une
barre horizontale n'aurait pas permis sans rogner les intitules.

Le tableau de bord ne recalcule rien : il lit les fichiers produits et
controles par la chaine `src/`.
"""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent))

import data as D                                       # noqa: E402
import theme as T                                      # noqa: E402
from sections import (apercu, arbitrage, desserte,  # noqa: E402
                      infrastructures, methode, plan_action, priorites)

# L'ordre est celui de la demonstration : les quatre premieres pages etablissent
# le diagnostic, les trois dernieres en tirent les consequences.
NAVIGATION = [
    ("Diagnostic", [
        ("Vue d'ensemble", apercu.afficher),
        ("Infrastructures", infrastructures.afficher),
        ("Desserte & population", desserte.afficher),
        ("Territoires prioritaires", priorites.afficher),
    ]),
    ("Décider", [
        ("Arbitrage", arbitrage.afficher),
        ("Plan d'action", plan_action.afficher),
        ("Méthode & limites", methode.afficher),
    ]),
]
PAGES = {nom: fn for _, items in NAVIGATION for nom, fn in items}
DEFAUT = "Vue d'ensemble"


def main() -> None:
    # TOUT ce qui doit exister a l'ecran est emis ICI, jamais au niveau module.
    #
    # Streamlit rejoue le script d'entree a chaque interaction, mais Python ne
    # reimporte PAS un module deja charge : du code place au niveau module de
    # `app.py` ne s'executerait qu'au tout premier rendu quand l'application est
    # lancee via `streamlit_app.py`. La feuille de style disparaitrait alors des
    # le premier clic, et la page s'afficherait nue.
    #
    # Appeler `set_page_config` en tete de `main()` reste conforme : c'est bien
    # la premiere commande Streamlit de chaque execution.
    st.set_page_config(
        page_title="Accès aux services numériques — Togo",
        page_icon="📶", layout="wide", initial_sidebar_state="expanded")
    T.enregistrer_template()
    st.markdown(T.CSS, unsafe_allow_html=True)

    pref = D.prefectures()
    st.session_state.setdefault("page", DEFAUT)

    st.markdown(T.entete(), unsafe_allow_html=True)

    with st.sidebar:
        st.markdown(T.marque_laterale(), unsafe_allow_html=True)

        # Chaque groupe vit dans son propre conteneur : c'est lui qui porte
        # l'air au-dessus de l'intertitre. Une marge posee sur le texte
        # deborderait du conteneur que Streamlit dimensionne sur son contenu,
        # et l'intertitre chevaucherait l'entree suivante.
        for indice, (groupe, items) in enumerate(NAVIGATION):
            with st.container(key=f"navgrp{indice}"):
                st.markdown(T.etiquette(groupe), unsafe_allow_html=True)
                for nom, _ in items:
                    actif = st.session_state.page == nom
                    if st.button(nom, key=f"nav_{nom}", width="stretch",
                                 type="primary" if actif else "secondary"):
                        st.session_state.page = nom
                        st.rerun()

        filtres = st.container(key="navgrp_filtres")
        filtres.markdown(T.etiquette("Filtres"), unsafe_allow_html=True)
        regions = sorted(pref.region.unique())
        # Le filtre part VIDE, et non prerempli des cinq regions : « vide » vaut
        # deja « toutes » deux lignes plus bas. Afficher cinq pastilles pour
        # dire « aucun filtre » occupe de la place sans porter d'information.
        sel_regions = filtres.multiselect("Région", regions, default=[],
                                          label_visibility="collapsed",
                                          placeholder="Toutes les régions")
        if not sel_regions:
            sel_regions = regions
        prefs_dispo = sorted(pref[pref.region.isin(sel_regions)].prefecture)
        sel_prefs = filtres.multiselect("Préfecture", prefs_dispo, default=[],
                                        label_visibility="collapsed",
                                        placeholder="Toutes les préfectures")

    ctx = {
        "regions": sel_regions,
        "prefectures": sel_prefs if sel_prefs else prefs_dispo,
        "filtre_actif": bool(sel_prefs) or len(sel_regions) < len(regions),
    }

    # Les cles des blocs sont un numero d'ordre : il doit repartir de zero a
    # chaque rendu, sinon Streamlit remonterait tout l'arbre a chaque clic.
    T.reinitialiser_blocs()
    PAGES[st.session_state.page](ctx)

    st.markdown(T.pied(
        "3 sources · 39 préfectures · 117 communes · infrastructures "
        "2021-2022, population 2022, contours 2021 · 25 contrôles "
        "arithmétiques au vert · aucune valeur n'est imputée : une donnée "
        "manquante est déclarée manquante."), unsafe_allow_html=True)


if __name__ == "__main__":
    main()
