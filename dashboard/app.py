"""
ATLAS DE LA CONNECTIVITE NUMERIQUE — TOGO
==========================================
Lancement :  streamlit run dashboard/app.py

Tableau de bord d'aide a la decision publique. La navigation suit l'INTENTION
du lecteur, pas la structure des donnees :

    SYNTHESE        ce qu'il faut retenir en trente secondes
    AXES D'ANALYSE  de quoi ce diagnostic est fait
    DECISION        ou agir, sur quelles bases, et a quel volume d'equipement

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

st.set_page_config(page_title="Atlas de la connectivité numérique — Togo",
                   page_icon="📶", layout="wide",
                   initial_sidebar_state="expanded")
T.enregistrer_template()
st.markdown(T.CSS, unsafe_allow_html=True)

NAVIGATION = [
    ("Synthèse", [("Vue d'ensemble", apercu.afficher)]),
    ("Axes d'analyse", [
        ("Infrastructures", infrastructures.afficher),
        ("Desserte & population", desserte.afficher),
        ("Territoires prioritaires", priorites.afficher),
    ]),
    ("Décision", [
        ("Arbitrage", arbitrage.afficher),
        ("Plan d'action", plan_action.afficher),
        ("Méthode & limites", methode.afficher),
    ]),
]
PAGES = {nom: fn for _, items in NAVIGATION for nom, fn in items}


def main() -> None:
    pref = D.prefectures()
    st.session_state.setdefault("page", "Vue d'ensemble")

    with st.sidebar:
        st.markdown(
            '<div class="sb-titre">Atlas de la connectivité</div>'
            '<div class="sb-sous">Togo · Défi 1</div>',
            unsafe_allow_html=True)

        for groupe, items in NAVIGATION:
            st.markdown(f'<div class="sb-groupe">{groupe}</div>',
                        unsafe_allow_html=True)
            for nom, _ in items:
                actif = st.session_state.page == nom
                if st.button(nom, key=f"nav_{nom}", width="stretch",
                             type="primary" if actif else "secondary"):
                    st.session_state.page = nom
                    st.rerun()

        st.markdown('<div class="sb-groupe">Filtres</div>',
                    unsafe_allow_html=True)
        regions = sorted(pref.region.unique())
        sel_regions = st.multiselect("Région", regions, default=regions,
                                     label_visibility="collapsed",
                                     placeholder="Toutes les régions")
        if not sel_regions:
            sel_regions = regions
        prefs_dispo = sorted(pref[pref.region.isin(sel_regions)].prefecture)
        sel_prefs = st.multiselect("Préfecture", prefs_dispo, default=[],
                                   label_visibility="collapsed",
                                   placeholder="Toutes les préfectures")

        st.markdown(
            '<div class="sb-pied">'
            '3 sources · 39 préfectures · 117 communes<br>'
            'Infrastructures 2021-2022 · Population 2022<br>'
            '25 contrôles arithmétiques au vert'
            '</div>', unsafe_allow_html=True)

    ctx = {
        "regions": sel_regions,
        "prefectures": sel_prefs if sel_prefs else prefs_dispo,
        "filtre_actif": bool(sel_prefs) or len(sel_regions) < len(regions),
    }
    PAGES[st.session_state.page](ctx)


if __name__ == "__main__":
    main()
