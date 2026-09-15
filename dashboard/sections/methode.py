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
     "mesurable avec les données ouvertes disponibles** : il est traité comme "
     "une limite critique et un besoin prioritaire de données. La page "
     "« Couverture & zones blanches » désigne des cantons **à investiguer** à "
     "partir d'un proxy déclaré comme tel : *une zone sans agence ni agent Mobile Money n'est pas "
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
        "Décision · 08", "Méthode & limites",
        "D'où viennent ces chiffres, jusqu'où peut-on s'y fier, et que ne "
        "disent-ils pas ?"), unsafe_allow_html=True)

    ctrl = D.controles_chaine()
    ok, total = D.nombre_controles()
    ag = D.agences_reperes()

    st.markdown(T.a_retenir([
        f"<b>{ok} contrôles arithmétiques sur {total}</b> au vert, rejoués à "
        "chaque exécution de la chaîne d'analyse.",
        "<b>Aucune valeur imputée</b> : la population somme exactement à "
        "8 095 498 habitants aux trois niveaux administratifs.",
        f"<b>{ag['recensees']} agences recensées après dédoublonnage</b> (et "
        f"non 141), dont <b>{ag['actives']} actives</b> : « Télécom » est un "
        "doublon, CANAL+ est vide à la source.",
        "<b>Limite critique</b> : la couverture réseau mobile n'est pas "
        "mesurable avec les données ouvertes disponibles.",
    ]), unsafe_allow_html=True)

    k = st.columns(4, gap="small")
    k[0].markdown(T.kpi("Contrôles arithmétiques", f"{ok}", f"/ {total}",
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
                "Agoè-Nyivé et ses 882 695 habitants.<br><br>"
                "② Une somme régionale à 11 630 489 habitants a révélé un "
                "double comptage du Grand Lomé, corrigé à la source."),
            unsafe_allow_html=True)
    with d:
        st.markdown(T.conclusion(
            f"Les {ag['fermees']} agences d'écart entre recensées et actives "
            "sont déclarées fermées dans la source : "
            f"{D.liste_fr(ag['fermees_detail'])}. Elles figurent dans le "
            "recensement, jamais dans les calculs d'accès."),
            unsafe_allow_html=True)
        st.markdown(T.lecture(
            "« Télécom » n'est pas un quatrième opérateur : ses 51 lignes sont "
            "toutes contenues dans les fichiers Moov et Togocom. Empiler les "
            "fichiers aurait affiché 141 agences au lieu de "
            f"{ag['recensees']}."), unsafe_allow_html=True)

    # Le detail sert a verifier : il vient replie, apres les messages.
    with st.expander(f"Les {total} contrôles, étape par étape"):
        if len(ctrl):
            st.dataframe(ctrl[["Etape", "Controle", "Resultat", "Detail"]].rename(
                columns={"Etape": "Étape", "Controle": "Contrôle",
                         "Resultat": "Résultat", "Detail": "Détail"}),
                width="stretch", hide_index=True, height=420)
    with st.expander("D'où viennent les données — trois sources publiques"):
        st.dataframe(SOURCES, width="stretch", hide_index=True)
    with st.expander("Ce qui a été testé puis écarté — trois pistes"):
        st.markdown(
            T.lecture(
                "Une méthode n'est solide que si l'on sait ce qu'elle a refusé "
                "de faire. Ces trois pistes ont été mises en œuvre ou évaluées, "
                "puis abandonnées."), unsafe_allow_html=True)
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
    # La limite critique reste depliee : c'est la seule qu'un lecteur ne
    # doit pas pouvoir manquer.
    for i, (titre, corps, coul) in enumerate(LIMITES):
        with st.expander(("Limite critique — " if i == 0 else "") + titre,
                         expanded=(i == 0)):
            st.markdown(corps)
