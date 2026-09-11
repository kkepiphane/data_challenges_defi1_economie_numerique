"""
METHODE & LIMITES
=================
Page de confiance, pas de documentation technique. Elle repond a trois
questions qu'un decideur se pose avant de s'appuyer sur un chiffre :

    d'ou viennent ces donnees ?
    puis-je m'y fier ?
    que ne disent-elles pas ?

Le detail d'implementation (arborescence, noms de scripts, systemes de
projection) n'a pas sa place ici : il est dans `reports/` et le README.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

import data as D
import theme as T

SOURCES = pd.DataFrame([
    {"Donnée": "Agences d'opérateur, agents Mobile Money, centres de données",
     "Origine": "Géoportail national du Togo",
     "Période": "Collecte 2021-2022",
     "Ce qu'elle apporte": "Localisation de chaque équipement"},
    {"Donnée": "Population résidente",
     "Origine": "INSEED — 5ᵉ recensement général (RGPH-5)",
     "Période": "Dénombrement 23 oct. – 16 nov. 2022",
     "Ce qu'elle apporte": "Le dénominateur de tous les ratios"},
    {"Donnée": "Limites administratives et superficies",
     "Origine": "Common Operational Datasets (OCHA)",
     "Période": "Valides au 7 janvier 2021",
     "Ce qu'elle apporte": "Contours, densités, distances"},
])

LIMITES = [
    ("La couverture réseau mobile n'est pas mesurée",
     "Aucune donnée de couverture radio n'existe dans les sources ouvertes "
     "mobilisées, et les couches d'antennes du catalogue national ne sont pas "
     "publiques. **L'objectif « identifier les zones blanches » n'est donc pas "
     "traité comme tel.** Ce qui est mesuré est un déficit d'accès aux "
     "services : *une zone sans agence ni agent Mobile Money n'est pas "
     "nécessairement une zone sans réseau mobile.* C'est la limite la plus "
     "importante de ce travail.",
     T.STATUT["critique"]),
    ("Les agences CANAL+ sont absentes",
     "Le fichier source est vide — le serveur du géoportail joint lui-même la "
     "mention « the query result is empty ». C'est une **donnée non "
     "disponible**, et non une absence d'agences sur le terrain. Le déficit "
     "d'agences ne porte donc que sur Moov et Togocom.",
     T.STATUT["attention"]),
    ("Le diagnostic décrit 2021-2022",
     "Infrastructures relevées en 2021-2022, population de novembre 2022. "
     "**Tout déploiement postérieur est invisible** dans ces résultats. La "
     "hiérarchie des besoins reste valable tant que les écarts constatés "
     "n'ont pas été comblés, mais les valeurs absolues vieillissent.",
     T.STATUT["attention"]),
    ("Les pondérations de l'indice sont un choix",
     "30 / 25 / 25 / 20 est un arbitrage assumé, pas un résultat. C'est "
     "exactement pourquoi 2 000 pondérations alternatives ont été testées et "
     "publiées : les neuf territoires prioritaires le restent dans au moins "
     "90 % des cas. **Le classement ne doit rien à ce choix particulier.**",
     T.SERIE_1),
    ("Un score élevé signale un besoin, pas une solution",
     "L'indice ne dit rien du coût d'une intervention, de sa faisabilité "
     "technique ni de sa rentabilité. Il hiérarchise des besoins mesurés — "
     "préalable à un arbitrage budgétaire, jamais son substitut.",
     T.SERIE_1),
    ("La structure par âge n'est pas prise en compte",
     "Un dénominateur « 15 ans et plus » serait plus juste pour le Mobile "
     "Money, le Togo ayant une population très jeune. Les tableaux d'âges "
     "publiés n'ont pas pu être extraits avec une garantie arithmétique "
     "suffisante, et ont donc été écartés plutôt que repris sans contrôle. "
     "La population totale reste par ailleurs le dénominateur de "
     "l'indicateur officiel.",
     T.ENCRE_MUET),
]

ECARTEES = [
    ("Reconstruire les contours des 117 communes",
     "Testé puis **rejeté sur preuve**. Les découpages des deux sources ne "
     "s'emboîtent pas : 65,6 % des points de service tombent dans une unité à "
     "cheval sur plusieurs communes, et un seul polygone couvre à lui seul "
     "six communes de Lomé. Publier ces contours aurait produit des densités "
     "communales fausses, sans qu'aucune alerte ne se déclenche. Les densités "
     "sont donc données à l'échelle préfectorale, où la concordance atteint "
     "98,4 %."),
    ("Utiliser des mesures de débit issues de tests de vitesse",
     "Écarté. Dans ces jeux de données, l'absence de mesure signifie « aucun "
     "test lancé », pas « aucun réseau ». Le biais porte vers les zones "
     "urbaines et vers les usagers **déjà connectés** — l'exact inverse de ce "
     "que ce diagnostic cherche à identifier."),
    ("Lisser les valeurs extrêmes de l'indice",
     "Écarté. Kpendjal compte réellement 2 155 habitants par point de "
     "service. Écrêter ce chiffre aurait effacé le signal le plus fort du jeu "
     "de données. Leur influence est mesurée autrement, par une variante de "
     "calcul insensible aux extrêmes — qui confirme le classement."),
]


def afficher(ctx: dict) -> None:
    st.markdown(T.bandeau(
        "Décision · 07", "Méthode & limites",
        "D'où viennent ces chiffres, jusqu'où peut-on s'y fier, et que ne "
        "disent-ils pas ?"), unsafe_allow_html=True)

    ctrl = D.controles_chaine()
    ok = int(ctrl.Resultat.str.contains("OK").sum()) if len(ctrl) else 0

    k = st.columns(4, gap="small")
    k[0].markdown(T.kpi("Contrôles arithmétiques", f"{ok}", f"/ {len(ctrl)}",
                        "rejoués à chaque exécution de la chaîne",
                        T.STATUT["bon"]), unsafe_allow_html=True)
    k[1].markdown(T.kpi("Population — somme vérifiée", "8 095 498", "",
                        "aux trois niveaux : région, préfecture, commune",
                        T.STATUT["bon"]), unsafe_allow_html=True)
    k[2].markdown(T.kpi("Valeurs estimées ou imputées", "0", "",
                        "toute donnée absente est déclarée absente",
                        T.STATUT["bon"]), unsafe_allow_html=True)
    k[3].markdown(T.kpi("Concordance géographique", "98,4", "%",
                        "des points tombent dans la préfecture déclarée",
                        T.STATUT["bon"]), unsafe_allow_html=True)

    # ------------------------------------------------------------- sources
    st.markdown("")
    st.markdown(T.etiquette("D'où viennent les données", "1.1rem"),
                unsafe_allow_html=True)
    st.dataframe(SOURCES, width="stretch", hide_index=True)

    # ------------------------------------------------------------ confiance
    st.markdown(T.etiquette("Pourquoi s'y fier", "1.4rem"),
                unsafe_allow_html=True)
    g, d = st.columns([1, 1], gap="medium")

    with g:
        st.markdown(
            T.action(
                "<b>Les contrôles ont réellement servi.</b> Deux échecs ont "
                "évité des erreurs graves.<br><br>"
                "① Une jointure sur des noms accentués faisait tomber "
                "<b>neuf préfectures à zéro point Mobile Money</b> — dont "
                "Agoè-Nyivé et ses 882 695 habitants. Le tableau de bord "
                "aurait affiché la deuxième préfecture du pays comme un "
                "désert numérique total.<br><br>"
                "② Une somme régionale à 11 630 489 habitants a révélé un "
                "double comptage du Grand Lomé, corrigé à la source."),
            unsafe_allow_html=True)
        st.markdown("")
        st.markdown(
            T.lecture(
                "Deux constats des données <b>corrigent l'énoncé du défi</b> : "
                "« Télécom » n'est pas un quatrième opérateur mais un doublon "
                "intégral de Moov et Togocom — d'où 90 agences et non 141 ; et "
                "CANAL+ est vide à la source."), unsafe_allow_html=True)

    with d:
        if len(ctrl):
            st.dataframe(ctrl[["Etape", "Controle", "Resultat"]].rename(
                columns={"Etape": "Étape", "Controle": "Contrôle",
                         "Resultat": "Résultat"}),
                width="stretch", hide_index=True, height=396)

    # ------------------------------------------------------------- écartées
    st.markdown(T.etiquette("Ce qui a été testé puis écarté", "1.4rem"),
                unsafe_allow_html=True)
    st.markdown(
        T.lecture(
            "Une méthode n'est solide que si l'on sait ce qu'elle a refusé de "
            "faire. Ces trois pistes ont été mises en œuvre ou évaluées, puis "
            "abandonnées."), unsafe_allow_html=True)
    cols = st.columns(3, gap="small")
    for col, (titre, corps) in zip(cols, ECARTEES):
        col.markdown(
            f'<div class="carte" style="border-top:3px solid {T.GRIS_FOND}">'
            f'<div style="font-size:0.92rem;font-weight:620;color:{T.ENCRE};'
            f'line-height:1.35;margin-bottom:0.55rem">{titre}</div>'
            f'<div style="font-size:0.8rem;color:{T.ENCRE_2};line-height:1.6">'
            f'{corps}</div></div>', unsafe_allow_html=True)

    # -------------------------------------------------------------- limites
    st.markdown(T.etiquette("Ce que ces résultats ne disent pas", "1.4rem"),
                unsafe_allow_html=True)
    for titre, corps, coul in LIMITES:
        with st.expander(titre):
            st.markdown(corps)
