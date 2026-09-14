"""
ACCES AUX TELECOMMUNICATIONS ET AUX SERVICES NUMERIQUES — TOGO
===============================================================
Lancement :  streamlit run streamlit_app.py

Tableau de bord d'aide a la decision publique. Les huit pages suivent le
raisonnement d'un rapport, pas l'arborescence des donnees :

    VUE D'ENSEMBLE  ce qu'il faut retenir en trente secondes
    INFRASTRUCTURES  ce qui existe, apres deduplication
    DESSERTE        ce que cela donne par habitant
    PRIORITES       ou le manque est le plus fort, et si le classement tient
    COUVERTURE      la donnee absente, et les zones a investiguer (proxy)
    ARBITRAGE       reglez les ponderations, chiffrez la couverture
    PLAN D'ACTION   quelles interventions les deficits mesures appellent
    METHODE         sources, controles, pistes ecartees, limites

La navigation est laterale et groupee par INTENTION : etablir le diagnostic,
puis decider. Huit entrees tiennent verticalement sans se serrer, ce qu'une
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
from sections import (apercu, arbitrage, couverture,  # noqa: E402
                      desserte, infrastructures, methode, plan_action,
                      priorites)

# L'ordre est celui de la demonstration : les cinq premieres pages etablissent
# le diagnostic, les trois dernieres en tirent les consequences.
# Chaque entree : (intitule, icone, fonction d'affichage).
#
# L'icone dit CE QUE LA PAGE MONTRE, jamais « une page ». Un jeu de pictogrammes
# decoratifs n'aiderait personne : ici l'antenne annonce des infrastructures, la
# carte un decoupage territorial, les curseurs un reglage. Le trait reste fin et
# la couleur suit celle du texte — l'icone accompagne l'intitule, elle ne le
# concurrence pas.
NAVIGATION = [
    ("Diagnostic", [
        ("Vue d'ensemble", ":material/summarize:", apercu.afficher),
        ("Infrastructures", ":material/cell_tower:", infrastructures.afficher),
        ("Desserte & population", ":material/groups:", desserte.afficher),
        ("Territoires prioritaires", ":material/map:", priorites.afficher),
        ("Couverture & zones blanches", ":material/signal_cellular_off:",
         couverture.afficher),
    ]),
    ("Décider", [
        ("Arbitrage", ":material/tune:", arbitrage.afficher),
        ("Plan d'action", ":material/checklist:", plan_action.afficher),
        ("Méthode & limites", ":material/rule:", methode.afficher),
    ]),
]
PAGES = {nom: fn for _, items in NAVIGATION for nom, _, fn in items}
DEFAUT = "Vue d'ensemble"


def _retirer_filtre() -> None:
    # Dans un rappel : c'est le seul moment ou l'etat d'un widget deja
    # instancie peut etre reecrit.
    st.session_state["filtre_regions"] = []
    st.session_state["filtre_prefs"] = []
    st.session_state["filtre_operateur"] = "Tous"


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
                for nom, icone, _ in items:
                    actif = st.session_state.page == nom
                    if st.button(nom, icon=icone, key=f"nav_{nom}",
                                 width="stretch",
                                 type="primary" if actif else "secondary"):
                        st.session_state.page = nom
                        st.rerun()

        filtres = st.container(key="navgrp_filtres")
        filtres.markdown(T.etiquette("Filtres"), unsafe_allow_html=True)
        regions = sorted(pref.region.unique())
        # Le filtre part VIDE, et non prerempli des cinq regions : « vide » vaut
        # deja « toutes » deux lignes plus bas. Afficher cinq pastilles pour
        # dire « aucun filtre » occupe de la place sans porter d'information.
        # Pas de `default` : la valeur vit dans `st.session_state`, que le
        # bouton « Retirer le filtre » reecrit. Les deux ensemble declenchent
        # un avertissement Streamlit a l'ecran.
        sel_regions = filtres.multiselect("Région", regions,
                                          key="filtre_regions",
                                          label_visibility="collapsed",
                                          placeholder="Toutes les régions")
        if not sel_regions:
            sel_regions = regions
        prefs_dispo = sorted(pref[pref.region.isin(sel_regions)].prefecture)
        # Une prefecture retenue puis exclue par un changement de region
        # sortirait des options : Streamlit leverait une erreur.
        st.session_state["filtre_prefs"] = [
            p for p in st.session_state.get("filtre_prefs", [])
            if p in prefs_dispo]
        sel_prefs = filtres.multiselect("Préfecture", prefs_dispo,
                                        key="filtre_prefs",
                                        label_visibility="collapsed",
                                        placeholder="Toutes les préfectures")

        st.session_state.setdefault("filtre_operateur", "Tous")
        operateur = filtres.radio(
            "Opérateur", D.OPERATEURS, key="filtre_operateur", horizontal=True,
            help="Restreint agences et agents Mobile Money à un opérateur. Un "
                 "point servi par Moov et Togocom compte pour chacun. Sans "
                 "effet sur l'indice de priorité, calculé tous opérateurs "
                 "confondus.")

        ctx = {
            "regions": sel_regions,
            "prefectures": sel_prefs if sel_prefs else prefs_dispo,
            "filtre_actif": bool(sel_prefs) or len(sel_regions) < len(regions),
            "operateur": operateur,
        }
        # Le filtre suit l'utilisateur de page en page : il doit donc rester
        # VISIBLE, et se lever d'un geste.
        if ctx["filtre_actif"] or operateur != "Tous":
            morceaux = []
            if ctx["filtre_actif"]:
                n = len(ctx["prefectures"])
                pop = int(pref[pref.prefecture.isin(ctx["prefectures"])]
                          .population.sum())
                morceaux.append(
                    f"**{n} préfecture{'s' if n > 1 else ''}**, {pop:,} "
                    f"habitants ({pop / D.POPULATION_NATIONALE:.0%})"
                    .replace(",", " "))
            if operateur != "Tous":
                morceaux.append(f"opérateur **{operateur}**")
            filtres.caption("Filtre actif sur toutes les pages : "
                            + " · ".join(morceaux))
            filtres.button("Retirer les filtres", icon=":material/filter_alt_off:",
                           width="stretch", on_click=_retirer_filtre)
        else:
            filtres.caption("Astuce : cliquez une préfecture sur une carte ou "
                            "un classement pour ouvrir sa fiche.")

    # Les cles des blocs sont un numero d'ordre : il doit repartir de zero a
    # chaque rendu, sinon Streamlit remonterait tout l'arbre a chaque clic.
    T.reinitialiser_blocs()
    if ctx["operateur"] != "Tous" and st.session_state.page in D.PAGES_SANS_OPERATEUR:
        st.warning(
            f"**Filtre opérateur « {ctx['operateur']} » sans effet sur cette "
            "page.** L'indice de priorité et sa robustesse sont calculés tous "
            "opérateurs confondus : l'usager peut se tourner vers l'un ou "
            "l'autre réseau. Le filtre s'applique aux pages Vue d'ensemble, "
            "Infrastructures, Desserte et Couverture.",
            icon=":material/info:")
    PAGES[st.session_state.page](ctx)

    ok, total = D.nombre_controles()
    st.markdown(T.pied(
        "3 sources · 39 préfectures · 117 communes · "
        f"{D.libelle_agences()} · infrastructures 2021-2022, population 2022, "
        f"contours 2021 · {ok} contrôles arithmétiques sur {total} au vert · "
        "aucune valeur n'est imputée : une donnée manquante est déclarée "
        "manquante."), unsafe_allow_html=True)


if __name__ == "__main__":
    main()
