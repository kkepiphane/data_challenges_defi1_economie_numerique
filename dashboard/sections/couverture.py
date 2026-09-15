"""
COUVERTURE RESEAU & ZONES BLANCHES
==================================
La page d'une donnee ABSENTE. Elle ne la maquille pas ; elle en tire le parti
honnete, dans cet ordre :

    1. ce qui manque, et ou on l'a cherche ;
    2. le proxy retenu, et pourquoi il vaut quelque chose ;
    3. la carte des cantons a investiguer ;
    4. ce qu'il faut publier pour remplacer le proxy par une mesure.

Tout est lu dans `data/processed/zones_blanches_canton.csv`, produit et
controle par `src/zones_blanches.py`.
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import cartes
import data as D
import theme as T

CLASSES = {                                     # ordre = ordre de la legende
    "Élevé": T.STATUT["critique"],
    "À surveiller": T.STATUT["attention"],
    "Faible": "#e4ded1",
}

COMPOSANTES = [
    ("r1_eloignement", "Éloignement d'une agence", T.SERIE_1),
    ("r2_rarete_temoins", "Rareté des agents Mobile Money", T.SERIE_2),
    ("r3_presence_operateur", "Faible présence opérateur", T.SERIE_3),
    ("r4_faible_densite", "Faible densité de population", T.ENCRE_MUET),
]

SOURCES = pd.DataFrame([
    {"Source interrogée": "Les 30 fichiers du défi (6 jeux × 5 formats)",
     "Ce qu'on y cherchait": "Signal, technologie 2G/3G/4G, antenne",
     "Résultat": "Aucune variable — vérifié sur les 19 colonnes"},
    {"Source interrogée": "Géoportail national — couches « Tours télécoms » "
                          "(toutes, Moov, Togocom)",
     "Ce qu'on y cherchait": "Position des antennes",
     "Résultat": "Existent au catalogue, HORS open data"},
    {"Source interrogée": "Géoportail national — « Réseau téléphonique » "
                          "(fibre, cuivre, raccordements)",
     "Ce qu'on y cherchait": "Réseau de collecte",
     "Résultat": "Existent au catalogue, HORS open data"},
    {"Source interrogée": "Mesures de débit participatives",
     "Ce qu'on y cherchait": "Qualité de service observée",
     "Résultat": "Écartées : l'absence de mesure veut dire « aucun test », "
                 "biais vers les zones déjà connectées"},
])

A_PUBLIER = [
    ("Sites d'antennes par opérateur",
     "Position, technologie (2G/3G/4G), date de mise en service. Les couches "
     "existent déjà au catalogue national : il s'agit de les ouvrir, pas de "
     "les produire."),
    ("Cartes de couverture déclarées",
     "Emprise de couverture par technologie et par opérateur, au format "
     "géographique — la donnée qui permet de dire « zone blanche » sans proxy."),
    ("Mesures de contrôle du régulateur",
     "Relevés terrain du taux de réussite d'appel et de connexion data, "
     "localisés : ils valident ou corrigent les cartes déclarées."),
]


def _centile(s: pd.Series) -> pd.Series:
    """Rang centile 0-100, ex aequo au rang moyen — comme la chaine."""
    return (s.rank(method="average") - 1) / (len(s) - 1) * 100


@st.cache_data(show_spinner=False)
def par_operateur(operateur: str) -> pd.DataFrame:
    """Score de risque recalcule sur les SEULS temoins d'un operateur.

    La couverture est propre a chaque reseau : un canton couvert par Togocom
    peut etre une zone blanche pour un abonne Moov. Pour un operateur :
      - eloignement : distance du canton a SES agences ;
      - rarete : SES agents au km² ;
      - presence operateur : SANS OBJET (un seul operateur par definition) ;
      - densite : inchangee.
    Les rangs centiles portent toujours sur les 373 cantons, avant tout filtre
    territorial, et les regles de classe sont celles de la chaine.
    """
    t = D.zones_blanches()
    if operateur == "Tous":
        return t
    t = t.copy()
    s = operateur.lower()
    t["n_mm"] = t[f"n_{s}"]
    t["dist_agence_km"] = t[f"dist_agence_{s}_km"]
    t["part_vide_10km"] = t[f"part_vide_10km_{s}"]
    t["mm_100km2"] = t.n_mm / t.area_sqkm * 100
    t["r1_eloignement"] = _centile(t.dist_agence_km)
    t["r2_rarete_temoins"] = _centile(-t.mm_100km2)
    t["r3_presence_operateur"] = float("nan")
    t["score_risque"] = t[["r1_eloignement", "r2_rarete_temoins",
                           "r4_faible_densite"]].mean(axis=1)
    t["rang_risque"] = t.score_risque.rank(ascending=False,
                                           method="min").astype(int)
    eleve, surveiller = t.score_risque.quantile([0.90, 0.75])
    t["sans_temoin"] = t.n_mm == 0
    t["classe"] = "Faible"
    t.loc[t.score_risque >= surveiller, "classe"] = "À surveiller"
    t.loc[(t.score_risque >= eleve) | t.sans_temoin, "classe"] = "Élevé"
    t["frequence_top"] = float("nan")      # sensibilite non recalculee ici
    return t.sort_values("rang_risque")


def _carte(zb: pd.DataFrame, geo: dict, pref_vue: pd.DataFrame,
           mode: str, vide: pd.DataFrame | None) -> go.Figure:
    fig = go.Figure()
    if mode == "classe":
        # Une trace par classe : legende lisible, et couleur NOMINALE — un
        # niveau de risque est une categorie, pas une intensite continue.
        for classe, couleur in CLASSES.items():
            t = zb[zb.classe == classe]
            if t.empty:
                continue
            fig.add_trace(go.Choroplethmap(
                geojson=geo, locations=t.adm3_pcode,
                featureidkey="properties.adm3_pcode", z=[1] * len(t),
                colorscale=[[0, couleur], [1, couleur]], showscale=False,
                marker=dict(line=dict(color="#ffffff", width=0.6),
                            opacity=0.9),
                name=f"{classe} ({len(t)})", showlegend=True,
                customdata=t[["canton", "prefecture", "n_mm", "n_operateurs",
                              "dist_agence_km", "score_risque",
                              "adm3_pcode"]].values,
                hovertemplate=_survol()))
    else:
        fig.add_trace(go.Choroplethmap(
            geojson=geo, locations=zb.adm3_pcode,
            featureidkey="properties.adm3_pcode", z=zb.score_risque,
            colorscale=[[i / (len(T.SEQUENTIEL) - 1), c]
                        for i, c in enumerate(T.SEQUENTIEL)],
            zmin=0, zmax=100,
            marker=dict(line=dict(color="#ffffff", width=0.6), opacity=0.9),
            colorbar=dict(title=dict(text="Score de risque", side="right",
                                     font=dict(size=11)),
                          thickness=11, len=0.6, x=0.985, xanchor="right"),
            customdata=zb[["canton", "prefecture", "n_mm", "n_operateurs",
                           "dist_agence_km", "score_risque",
                           "adm3_pcode"]].values,
            hovertemplate=_survol()))

    # Limites prefectorales par-dessus : on lit le canton DANS sa prefecture.
    lon, lat = cartes.contours(D.geojson_prefectures(), "prefecture",
                               set(pref_vue.prefecture))
    fig.add_trace(go.Scattermap(lon=lon, lat=lat, mode="lines",
                                line=dict(color="rgba(18,18,15,0.6)", width=1.4),
                                hoverinfo="skip", showlegend=False))
    if vide is not None and len(vide):
        fig.add_trace(go.Scattermap(
            lon=vide.lon, lat=vide.lat, mode="markers",
            marker=dict(size=4, color="#12120f", opacity=0.55),
            name=f"À plus de 10 km de tout agent", hoverinfo="skip"))
    fig.update_layout(
        map=dict(style=cartes.STYLE_FOND, center=cartes.CENTRE, zoom=cartes.ZOOM),
        height=640, margin=dict(l=0, r=0, t=0, b=0),
        legend=dict(orientation="v", yanchor="top", y=0.98, x=0.012,
                    bgcolor="rgba(255,255,255,0.92)", bordercolor=T.BORDURE,
                    borderwidth=1, font=dict(size=11.5, color=T.ENCRE_2)))
    return fig


def _survol() -> str:
    return ("<b>%{customdata[0]}</b> — %{customdata[1]}<br><br>"
            "Agents Mobile Money : %{customdata[2]}<br>"
            "Opérateurs identifiés : %{customdata[3]} / 2<br>"
            "Agence la plus proche : %{customdata[4]:.0f} km<br>"
            "<b>Score de risque : %{customdata[5]:.1f} / 100</b>"
            "<extra></extra>")


def _choisir_canton() -> None:
    """Rappel du clic sur la carte : memorise le canton designe."""
    etat = st.session_state.get("carte_zb") or {}
    for p in (etat.get("selection") or {}).get("points") or []:
        donnees = p.get("customdata")
        code = (donnees[-1] if isinstance(donnees, list) and donnees
                else p.get("location"))
        if code:
            st.session_state["canton_zb"] = code
            return


def afficher(ctx: dict) -> None:
    op = ctx["operateur"]
    zb_all = par_operateur(op)
    zb = zb_all[zb_all.prefecture.isin(ctx["prefectures"])]
    avec_op = "" if op == "Tous" else f" · {op}"
    pref = D.prefectures()
    pref_vue = pref[pref.prefecture.isin(ctx["prefectures"])]
    geo = D.geojson_cantons()

    st.markdown(T.bandeau(
        "Diagnostic · 05", "Couverture réseau & zones blanches",
        "La couverture mobile n'est pas mesurable avec les données ouvertes. "
        "Où faut-il donc aller vérifier en priorité, et quelle donnée publier "
        "pour ne plus avoir à deviner ?"), unsafe_allow_html=True)

    eleve = zb[zb.classe == "Élevé"]
    sans = zb[zb.sans_temoin]
    surface_vide = (zb.part_vide_10km * zb.area_sqkm).sum() / max(zb.area_sqkm.sum(), 1)
    variantes = D.zones_blanches_variantes()
    par_pref = eleve.groupby("prefecture").size().sort_values(ascending=False)
    robustes = set(pd.read_csv(D.PROCESSED / "dcpi_sensibilite.csv")
                   .query("frequence_top10 >= 0.9").prefecture)
    communs = [p for p in par_pref.index[:5] if p in robustes]
    tete = par_pref.index[0] if len(par_pref) else None

    def _n(v: float) -> str:
        return T.fr(v, 0)

    # Trois messages exactement : les autres constats (qui concentre le
    # risque, la recommandation) ont leur propre section plus bas — les
    # repeter ici ferait double emploi.
    messages = [
        "La couverture mobile <b>n'est pas mesurable</b> avec les données "
        "ouvertes disponibles.",
        f"Le proxy identifie <b>{len(eleve)} cantons à vérifier</b>{avec_op}, "
        f"dont <b>{len(sans)} sans aucun agent Mobile Money</b>.",
    ]
    if communs:
        messages.append(f"<b>{D.liste_fr(communs)}</b> "
                        f"{'figure' if len(communs) == 1 else 'figurent'} "
                        "aussi parmi les priorités robustes.")
    else:
        messages.append("Aucun des cantons à risque élevé n'appartient à une "
                        "préfecture prioritaire robuste de l'indice DCPI.")
    st.markdown(T.a_retenir(messages), unsafe_allow_html=True)

    k = st.columns(4, gap="small")
    k[0].markdown(T.kpi(f"Cantons à risque élevé{avec_op}", f"{len(eleve)}",
                        f"/ {len(zb)}",
                        "top 10 % du score national, ou aucun agent",
                        T.STATUT["critique"]), unsafe_allow_html=True)
    k[1].markdown(T.kpi(f"Cantons sans aucun agent Mobile Money{avec_op}",
                        f"{len(sans)}", "",
                        f"{_n(sans.area_sqkm.sum())} km² sans témoin de couverture",
                        T.STATUT["critique"]), unsafe_allow_html=True)
    k[2].markdown(T.kpi(f"Surface à plus de 10 km de tout agent{avec_op}",
                        T.fr(surface_vide * 100, 1), "%",
                        "grille de 1 km, distance au témoin le plus proche",
                        T.STATUT["attention"]), unsafe_allow_html=True)
    if op == "Tous":
        k[3].markdown(T.kpi("Stabilité du classement",
                            T.fr(variantes.spearman.min(), 2),
                            "", "corrélation minimale, retrait de chaque "
                            "composante", T.STATUT["bon"]),
                      unsafe_allow_html=True)
    else:
        # Ce que la lecture par operateur apporte : des cantons qui ne
        # ressortent pas quand les deux reseaux sont confondus.
        tous = D.zones_blanches()
        deja = set(tous[tous.classe == "Élevé"].adm3_pcode)
        propres = eleve[~eleve.adm3_pcode.isin(deja)]
        k[3].markdown(T.kpi(f"À risque pour {op} seulement",
                            f"{len(propres)}", "",
                            "cantons absents de la lecture tous opérateurs",
                            T.SERIE_1), unsafe_allow_html=True)

    # ===================================================== 1. LA CARTE
    st.markdown(T.etiquette("1 · Zones à risque de zone blanche", "1.4rem"),
                unsafe_allow_html=True)
    g, d = st.columns([2.2, 1], gap="medium")
    with d:
        with T.bloc("Ce que la carte affiche"):
            mode = st.radio("Lecture", ["Niveau de risque", "Score continu"],
                            horizontal=True, label_visibility="collapsed")
            montrer_vide = st.toggle("Mailles à plus de 10 km d'un agent",
                                     value=True)
        if tete is not None:
            n_tete = int(par_pref.iloc[0])
            total_tete = int((zb.prefecture == tete).sum())
            convergence = (" Deux lectures indépendantes — ce proxy et l'indice "
                           "de priorité — désignent les mêmes territoires."
                           if communs else "")
            st.markdown(T.conclusion(
                f"{tete} concentre {n_tete} des {len(eleve)} cantons à risque "
                f"élevé ({n_tete} sur {total_tete} de ses cantons)."
                + convergence), unsafe_allow_html=True)
        st.markdown(T.source(
            "Quatre composantes à poids égaux, en rang centile sur les 373 "
            "cantons : distance à l'agence active la plus proche, agents Mobile "
            "Money au km², nombre d'opérateurs identifiés, densité de la "
            "préfecture." if op == "Tous"
            else f"Score recalculé pour {op} : distance à ses agences actives, "
            "densité de ses agents, densité de population. La composante "
            "« présence opérateur » est sans objet pour un seul réseau."),
            unsafe_allow_html=True)

    with g:
        with T.bloc(f"Zones à risque de zone blanche{avec_op} · par canton · "
                    "cliquez un canton pour son détail"):
            vide = None
            if montrer_vide:
                vide = D.vide_temoins()
                col_d = "dist_km" if op == "Tous" else f"dist_{op.lower()}_km"
                vide = vide[vide[col_d] > 10]
                # Filtre spatial grossier sur l'emprise des prefectures vues :
                # suffisant pour l'affichage, sans bibliotheque geometrique.
                if ctx["filtre_actif"]:
                    lon, lat = cartes.contours(D.geojson_prefectures(),
                                               "prefecture", set(pref_vue.prefecture))
                    lon = [v for v in lon if v is not None]
                    lat = [v for v in lat if v is not None]
                    vide = vide[vide.lon.between(min(lon), max(lon))
                                & vide.lat.between(min(lat), max(lat))]
            st.plotly_chart(
                _carte(zb, geo, pref_vue,
                       "classe" if mode == "Niveau de risque" else "score", vide),
                width="stretch", key="carte_zb", on_select=_choisir_canton,
                selection_mode="points", config={"displayModeBar": False})
            st.markdown(T.source(
                "Contours COD-AB (373 cantons) · agents Mobile Money PRISE "
                "2021-2022 · trait sombre : limites préfectorales. Proxy "
                "d'investigation, pas mesure de couverture."),
                unsafe_allow_html=True)

    # ======================================== 2. POURQUOI UN PROXY
    st.markdown(T.etiquette("2 · Pourquoi un proxy, et ce qu'il ne dit pas",
                            "1.4rem"), unsafe_allow_html=True)
    st.markdown(T.lecture(
        "<b>Absence d'agent ≠ absence de réseau.</b> Le résultat est une "
        "liste de zones à investiguer, jamais une carte de couverture."),
        unsafe_allow_html=True)
    with st.expander("Détail : sources cherchées, proxy retenu, ses limites "
                     "(454 couches du catalogue national interrogées)"):
        cartes_statut = [
            ("Donnée indisponible", T.STATUT["critique"],
             "<b>Aucune mesure de couverture radio</b> — ni signal, ni "
             "technologie, ni position d'antenne — dans les sources "
             "ouvertes."),
            ("Sources cherchées", T.STATUT["attention"],
             "Les 30 fichiers du défi, puis les <b>454 couches</b> du "
             "catalogue national. Les couches antennes existent, <b>hors "
             "open data</b>."),
            ("Proxy utilisé", T.SERIE_1,
             "La présence d'un agent Mobile Money constitue un <b>témoin "
             "minimal de connectivité exploitable</b>, mais ne mesure ni la "
             "qualité ni la continuité du réseau."),
            ("Ce que le proxy ne dit pas", T.ENCRE_MUET,
             "<b>Absence d'agent ≠ absence de réseau.</b> Le résultat est "
             "une liste de zones à investiguer."),
        ]
        cols = st.columns(4, gap="small")
        for col, (titre, coul, corps) in zip(cols, cartes_statut):
            col.markdown(
                f'<div class="carte" style="border-top:3px solid {coul};'
                f'min-height:8rem"><div class="carte-t">{titre}</div>'
                f'<div style="font-size:0.84rem;color:{T.ENCRE_2};'
                f'line-height:1.55">{corps}</div></div>',
                unsafe_allow_html=True)
        st.markdown("")
        st.markdown('<div class="carte-t">Sources interrogées, en détail'
                    '</div>', unsafe_allow_html=True)
        st.dataframe(SOURCES, width="stretch", hide_index=True)

    # ================================================ 3. LE DETAIL
    st.markdown(T.etiquette("3 · Zones suspectes à investiguer", "1.4rem"),
                unsafe_allow_html=True)
    g2, d2 = st.columns([1, 1.2], gap="medium")
    with g2:
        options = zb.sort_values("rang_risque")
        libelles = dict(zip(options.adm3_pcode,
                            options.canton + " — " + options.prefecture))
        if st.session_state.get("canton_zb") not in libelles:
            st.session_state["canton_zb"] = options.adm3_pcode.iloc[0]
        code = st.selectbox("Canton", list(libelles), key="canton_zb",
                            format_func=libelles.get,
                            label_visibility="collapsed")
        r = zb[zb.adm3_pcode == code].iloc[0]
        with T.bloc(f"{r.canton} · rang {int(r.rang_risque)} sur 373"):
            fig = go.Figure()
            actives = [(c, l, k) for c, l, k in COMPOSANTES if pd.notna(r[c])]
            for col, lib, coul in actives:
                part = r[col] / len(actives)
                fig.add_trace(go.Bar(
                    x=[part], y=["Score"], orientation="h", name=lib,
                    marker=dict(color=coul, line=dict(width=2, color=T.SURFACE)),
                    text=[f"{part:.0f}"], textposition="inside",
                    insidetextanchor="middle",
                    textfont=dict(size=11, color=T.SURFACE),
                    hovertemplate=f"<b>{lib}</b><br>centile {r[col]:.0f}"
                                  "<extra></extra>"))
            fig.update_layout(barmode="stack", height=150,
                              xaxis=dict(range=[0, 100]),
                              margin=dict(l=4, r=4, t=4, b=4),
                              legend=dict(orientation="h", y=-0.5,
                                          font=dict(size=10)))
            st.plotly_chart(fig, width="stretch",
                            config={"displayModeBar": False})
            pluriel = "s" if r.n_mm > 1 else ""
            st.markdown(T.conclusion(
                f"Risque {r.classe.lower()} : {int(r.n_mm)} agent{pluriel} "
                f"Mobile Money sur {_n(r.area_sqkm)} km², agence active la plus "
                f"proche à {r.dist_agence_km:.0f} km."), unsafe_allow_html=True)
            n_op = int(r.n_operateurs)
            st.markdown(T.source(
                f"{n_op} opérateur{'s' if n_op != 1 else ''} identifié"
                f"{'s' if n_op != 1 else ''} · {T.pct(r.part_vide_10km)} de "
                "la surface à plus de 10 km de tout agent · préfecture à "
                f"{_n(r.densite_prefecture)} hab./km²."), unsafe_allow_html=True)

    with d2:
        st.markdown(T.lecture(
            f"<b>{len(eleve)} cantons</b> sont à risque élevé dans le "
            "périmètre. Choisissez-en un à gauche, ou cliquez-le sur la carte, "
            "pour voir de quoi son score est fait."), unsafe_allow_html=True)
        with st.expander(f"Les {len(eleve)} cantons à risque élevé "
                         "(tableau et export CSV)"):
            t = eleve.sort_values("rang_risque")[
                ["rang_risque", "canton", "prefecture", "n_mm", "n_operateurs",
                 "dist_agence_km", "part_vide_10km", "frequence_top",
                 "score_risque"]].copy()
            t.columns = ["Rang", "Canton", "Préfecture", "Agents MM",
                         "Opérateurs", "Agence active (km)", "Surface > 10 km",
                         "Stabilité", "Score"]
            if op != "Tous":
                t = t.drop(columns="Stabilité").rename(columns={
                    "Agents MM": f"Agents {op}",
                    "Agence active (km)": f"Agence active {op} (km)",
                    "Opérateurs": "Opérateurs (tous)"})
            formats = {"Agence active (km)": "{:.0f}",
                       f"Agence active {op} (km)": "{:.0f}",
                       "Surface > 10 km": "{:.0%}", "Stabilité": "{:.0%}",
                       "Score": "{:.1f}"}
            st.dataframe(t.style.format({
                c: f for c, f in formats.items() if c in t.columns},
                thousands=" ", decimal=","),
                width="stretch", hide_index=True, height=400)
            st.download_button("Télécharger les zones à investiguer (CSV)",
                               D.csv(eleve.drop(columns=[c for c, *_ in COMPOSANTES]),
                                     ctx),
                               "zones_a_investiguer.csv", "text/csv",
                               icon=":material/download:", key="dl_zb")
            if op == "Tous":
                st.markdown(T.source(
                    "« Stabilité » : part des 2 000 pondérations aléatoires "
                    "pour lesquelles le canton reste dans le top 10 % "
                    "national."), unsafe_allow_html=True)

    # ============================================= 4. RECOMMANDATION
    st.markdown(T.etiquette("4 · Ce qu'il faut publier pour remplacer ce proxy",
                            "1.4rem"), unsafe_allow_html=True)
    st.markdown(T.action(
        "<b>Recommandation prioritaire au producteur de données et au "
        "régulateur : ouvrir les couches d'antennes et de couverture.</b> "
        f"Elles transformeraient ces {len(eleve)} zones suspectes en zones "
        "blanches confirmées ou écartées."), unsafe_allow_html=True)
    with st.expander("Quelles couches publier, et que faire en attendant"):
        cols = st.columns(3, gap="small")
        for col, (titre, corps) in zip(cols, A_PUBLIER):
            col.markdown(
                f'<div class="carte" style="border-top:3px solid {T.VERT}">'
                f'<div style="font-size:0.92rem;font-weight:620;color:{T.ENCRE};'
                f'line-height:1.35;margin-bottom:0.5rem">{titre}</div>'
                f'<div style="font-size:0.8rem;color:{T.ENCRE_2};line-height:1.6">'
                f'{corps}</div></div>', unsafe_allow_html=True)
        st.markdown(T.lecture(
            "<b>En attendant :</b> une vérification de terrain ciblée — relevé "
            "de signal par opérateur au chef-lieu de chaque canton à risque "
            "élevé — coûte peu, et suffit à confirmer ou écarter chaque zone "
            "de la liste."), unsafe_allow_html=True)
