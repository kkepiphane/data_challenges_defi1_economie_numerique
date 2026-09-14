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


# Ecart a l'equipement attendu au-dela duquel un territoire est dit
# « sous-equipe a densite comparable » : 30 % de points en moins que ce que
# sa densite laisse prevoir.
SEUIL_ECART = -0.30


def modele_densite(pref):
    """Equipement ATTENDU compte tenu de la densite, et ecart a cet attendu.

    Regression log-log des points pour 10 000 habitants sur la densite,
    ajustee sur les 39 prefectures — la reference reste nationale quel que
    soit le filtre. Le log tient compte d'un Golfe cent fois plus dense que
    Mo : en echelle lineaire, deux prefectures urbaines piloteraient la droite.

    Ce n'est PAS un modele causal. Il repond a une seule question : la faible
    densite suffit-elle a expliquer un faible equipement ?
    """
    t = pref.dropna(subset=["densite_hab_km2", "points_mm_pour_10k_hab"]).copy()
    t = t[(t.densite_hab_km2 > 0) & (t.points_mm_pour_10k_hab > 0)]
    x, y = np.log10(t.densite_hab_km2), np.log10(t.points_mm_pour_10k_hab)
    pente, origine = np.polyfit(x, y, 1)
    residu = y - (pente * x + origine)
    r2 = 1 - float((residu ** 2).sum() / ((y - y.mean()) ** 2).sum())
    t["attendu_10k"] = 10 ** (pente * x + origine)
    t["ecart"] = t.points_mm_pour_10k_hab / t.attendu_10k - 1
    t["manque_densite"] = np.ceil(
        t.population / 1e4 * (t.attendu_10k - t.points_mm_pour_10k_hab)
    ).clip(lower=0).astype(int)
    # Spearman = Pearson sur les rangs (pas de scipy dans l'application).
    rho = t.densite_hab_km2.rank().corr(t.points_mm_pour_10k_hab.rank())
    return t, pente, origine, r2, rho


def _densite(pref, vue, ctx: dict) -> None:
    modele, pente, origine, r2, rho = modele_densite(pref)
    m = modele[modele.prefecture.isin(vue.prefecture)]
    sous = m[m.ecart <= SEUIL_ECART].sort_values("ecart")
    rural = modele[modele.densite_hab_km2 < 150]
    fort, faible = (rural.loc[rural.points_mm_pour_10k_hab.idxmax()],
                    rural.loc[rural.points_mm_pour_10k_hab.idxmin()])

    st.markdown("")
    st.markdown(T.etiquette("Pourquoi ces écarts ? · ce que la densité "
                            "n'explique pas", "1.2rem"), unsafe_allow_html=True)
    g, d = st.columns([1.45, 1], gap="medium")
    with g:
        with T.bloc("Équipement observé et équipement attendu selon la densité "
                    "· cliquez un point pour ouvrir la fiche"):
            fig = go.Figure()
            xs = np.logspace(np.log10(modele.densite_hab_km2.min() * 0.85),
                             np.log10(modele.densite_hab_km2.max() * 1.15), 60)
            fig.add_trace(go.Scatter(
                x=xs, y=10 ** (pente * np.log10(xs) + origine), mode="lines",
                line=dict(color=T.AXE, width=2, dash="dash"),
                name="Équipement attendu selon la densité", hoverinfo="skip"))
            m = m.assign(sous=m.ecart <= SEUIL_ECART)
            ordre = m.sort_values("sous")          # les points surlignes dessus
            fig.add_trace(go.Scatter(
                x=ordre.densite_hab_km2, y=ordre.points_mm_pour_10k_hab,
                mode="markers+text",
                marker=dict(size=12, color=[T.STATUT["critique"] if s
                                            else T.GRIS_FOND for s in ordre.sous],
                            line=dict(width=2, color=T.SURFACE)),
                text=[p if s else "" for p, s in zip(ordre.prefecture, ordre.sous)],
                textposition="bottom center",
                textfont=dict(size=10, color=T.ENCRE_2),
                name="Préfecture (en rouge : sous-équipée)",
                customdata=np.stack([ordre.region, ordre.attendu_10k,
                                     ordre.ecart, ordre.manque_densite,
                                     ordre.prefecture], axis=-1),
                hovertemplate=("<b>%{customdata[4]}</b> — %{customdata[0]}<br><br>"
                               "Densité : %{x:,.0f} hab./km²<br>"
                               "Observé : %{y:.1f} points / 10 000 hab.<br>"
                               "Attendu : %{customdata[1]:.1f}<br>"
                               "<b>Écart : %{customdata[2]:+.0%}</b><br>"
                               "Points manquants : %{customdata[3]:,.0f}"
                               "<extra></extra>")))
            fig.update_layout(
                height=470, xaxis_type="log", yaxis_type="log",
                xaxis_title="Densité (hab./km², échelle log)",
                yaxis_title="Points Mobile Money pour 10 000 hab. (log)",
                legend=dict(orientation="h", y=-0.2, font=dict(size=10.5)),
                margin=dict(l=4, r=4, t=6, b=36))
            st.plotly_chart(fig, width="stretch", key="nuage_densite",
                            on_select=D.ouvrir_fiche(
                                "nuage_densite", ordre.prefecture.tolist(),
                                True),
                            selection_mode="points",
                            config={"displayModeBar": False})
            st.markdown(T.source(
                "Droite : régression log-log ajustée sur les 39 préfectures. "
                "Un point sous la droite est moins équipé que sa densité ne le "
                "laisse prévoir. Lecture descriptive, non causale."),
                unsafe_allow_html=True)

    with d:
        st.markdown(T.action(
            f"<b>La densité n'explique que {r2:.0%} des écarts d'équipement.</b> "
            f"À moins de 150 hab./km², {fort.prefecture} compte "
            f"{fort.points_mm_pour_10k_hab:.0f} points pour 10 000 habitants, "
            f"{faible.prefecture} {faible.points_mm_pour_10k_hab:.0f}. Le "
            "déficit n'est donc pas la fatalité d'un territoire rural : à "
            "densité égale, d'autres font nettement mieux. C'est ce qui le rend "
            "<b>corrigeable par le déploiement d'agents</b>, sans attendre que "
            "le territoire se densifie."),
            unsafe_allow_html=True)
        pluriel = len(sous) > 1
        manque = f"{int(sous.manque_densite.sum()):,}".replace(",", " ")
        st.markdown(T.conclusion(
            f"{len(sous)} préfecture{'s' if pluriel else ''} du périmètre "
            f"{'ont' if pluriel else 'a'} au moins {-SEUIL_ECART * 100:.0f} % "
            f"de points de moins que {'leur' if pluriel else 'sa'} densité ne "
            f"le laisse prévoir, soit {manque} points manquants."
            if len(sous) else
            "Aucune préfecture du périmètre n'est nettement sous-équipée au "
            "regard de sa densité."), unsafe_allow_html=True)

    # Le detail vient APRES le graphique, replie : il sert a verifier, pas a
    # comprendre.
    with st.expander("Détail : territoires sous-équipés au regard de leur densité"):
        k = st.columns(4, gap="small")
        k[0].markdown(T.kpi("Part des écarts expliquée par la densité",
                            f"{r2:.0%}", "",
                            f"R² log-log · corrélation des rangs {rho:.2f}"
                            .replace(".", ","), T.SERIE_1), unsafe_allow_html=True)
        k[1].markdown(T.kpi("Sous-équipés à densité comparable", f"{len(sous)}",
                            f"/ {len(m)}",
                            f"au moins {-SEUIL_ECART:.0%} sous l'équipement attendu",
                            T.STATUT["critique"]), unsafe_allow_html=True)
        k[2].markdown(T.kpi("Points manquants au regard de la densité",
                            f"{int(sous.manque_densite.sum()):,}".replace(",", " "),
                            "", f"{int(sous.population.sum()):,} habitants concernés"
                            .replace(",", " "), T.SERIE_2), unsafe_allow_html=True)
        k[3].markdown(T.kpi("Écart entre territoires ruraux",
                            f"×{fort.points_mm_pour_10k_hab / faible.points_mm_pour_10k_hab:.0f}",
                            "", f"{fort.prefecture} face à {faible.prefecture}, "
                            "moins de 150 hab./km²", T.SERIE_3),
                      unsafe_allow_html=True)
        st.markdown("")
        with T.bloc("Les plus sous-équipés au regard de leur densité"):
            if sous.empty:
                st.caption("Aucun territoire du périmètre n'est sous-équipé "
                           "au regard de sa densité.")
            else:
                t = sous[["prefecture", "region", "densite_hab_km2",
                          "points_mm_pour_10k_hab", "attendu_10k", "ecart",
                          "manque_densite"]].copy()
                t.columns = ["Préfecture", "Région", "Densité", "Observé /10k",
                             "Attendu /10k", "Écart", "Points manquants"]
                st.dataframe(t.style.format({
                    "Densité": "{:,.0f}", "Observé /10k": "{:.1f}",
                    "Attendu /10k": "{:.1f}", "Écart": "{:+.0%}",
                    "Points manquants": "{:,.0f}"}, thousands=" ", decimal=","),
                    width="stretch", hide_index=True, height=300)
                st.download_button("Télécharger (CSV)", D.csv(t, ctx),
                                   "sous_equipes_densite.csv", "text/csv",
                                   icon=":material/download:", key="dl_densite")
            grand = m.loc[m.manque_densite.idxmax()] if len(m) else None
            # Le constat « le premier besoin n'est pas rural » n'est vrai que si
            # le territoire en tete est effectivement urbain : un filtre sur une
            # region rurale le rendrait faux.
            if (grand is not None and grand.manque_densite > 0
                    and grand.densite_hab_km2 >= 500):
                dens = f"{grand.densite_hab_km2:,.0f}".replace(",", " ")
                vol = f"{int(grand.manque_densite):,}".replace(",", " ")
                st.markdown(T.lecture(
                    f"En volume, le premier besoin n'est pas rural : "
                    f"<b>{grand.prefecture}</b> ({dens} hab./km²) manque de "
                    f"<b>{vol} points</b> au regard de sa densité, et n'est "
                    f"pourtant que <b>{int(grand.rang_DCPI)}ᵉ sur 39</b> dans "
                    "l'indice de priorité, qui raisonne en habitants par point "
                    "et non en volume. Ce besoin périurbain appelle un "
                    "traitement distinct des priorités rurales."),
                    unsafe_allow_html=True)


def afficher(ctx: dict) -> None:
    pref = D.prefectures_operateur(ctx["operateur"])
    vue = pref[pref.prefecture.isin(ctx["prefectures"])].copy()

    st.markdown(T.bandeau(
        "Diagnostic · 03", "Desserte & population",
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

    # Concurrence : lue tous operateurs confondus, sur le perimetre filtre.
    mmo = D.mobile_money_operateurs()
    mmo = mmo[mmo.prefecture.isin(ctx["prefectures"])]
    brut = mmo.drop_duplicates("FID")
    n_tgc = int((brut.operateur == "Togocom").sum())
    n_moov = int((brut.operateur == "Moov").sum())
    _, _, _, r2, _ = modele_densite(pref)

    def _n(v: float) -> str:
        return f"{v:,.0f}".replace(",", " ")

    st.markdown(T.a_retenir([
        f"La moitié la moins desservie de la population ne dispose que de "
        f"<b>{moitie:.0%} des points</b> Mobile Money, au lieu de 50 %."
        .replace("%", " %").replace("  %", " %"),
        f"<b>{len(quadrant)} préfectures</b> sont à la fois plus peuplées que la "
        f"médiane et moins desservies que la moyenne : "
        f"<b>{_n(quadrant.population.sum())} habitants</b>.",
        f"La densité n'explique que <b>{r2 * 100:.0f} %</b> des écarts : le "
        "déficit se corrige en déployant des agents, sans attendre que le "
        "territoire se densifie.",
        f"<b>{_n(n_tgc)} points ne servent que Togocom</b>, contre "
        f"{_n(n_moov)} pour Moov seul : là, l'usager n'a aucune alternative.",
    ]), unsafe_allow_html=True)

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
                        "", f"de {c.loc[c.hab_par_point_mm.idxmin(), 'prefecture']} "
                        f"à {c.loc[c.hab_par_point_mm.idxmax(), 'prefecture']}",
                        T.SERIE_2),
                  unsafe_allow_html=True)

    # ==================================================== quadrant critique
    st.markdown("")
    g, d = st.columns([1.45, 1], gap="medium")

    with g:
        with T.bloc(
                "Population élevée et desserte faible · le quadrant critique"):
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
            st.markdown(T.conclusion(
                f"{len(quadrant)} préfectures (en bleu) cumulent population "
                "élevée et desserte faible : c'est là qu'un investissement "
                "touche le plus d'habitants."), unsafe_allow_html=True)
            st.markdown(T.source(
                "Axe des abscisses logarithmique — sans quoi le Golfe et ses "
                "1,3 million d'habitants écraserait les 38 autres. Traits : "
                "médiane de population et moyenne nationale de desserte."),
                unsafe_allow_html=True)

    with d:
        with T.bloc("Concentration de l'équipement"):
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
            st.markdown(T.conclusion(
                f"La moitié la moins desservie de la population dispose de "
                f"{moitie * 100:.0f} % des points : l'écart à la diagonale "
                "mesure cette inégalité."), unsafe_allow_html=True)
            st.markdown(T.source(
                "Préfectures classées du plus faible au plus fort taux "
                "d'équipement par habitant. Transformation de présentation "
                "appliquée à des valeurs déjà contrôlées."),
                unsafe_allow_html=True)

    # ============================================= ce que la densité explique
    _densite(pref, vue, ctx)

    # ======================================================== opérateurs
    st.markdown("")
    st.markdown(T.etiquette("Concurrence entre opérateurs", "1.2rem"),
                unsafe_allow_html=True)
    libelles ={"Moov, Togocom": "Les deux opérateurs",
                "Togocom": "Togocom seul", "Moov": "Moov seul",
                "Nsp": "Opérateur non renseigné"}
    rep = (brut.operateur.value_counts().rename_axis("modalite")
           .reset_index(name="points"))
    rep["libelle"] = rep.modalite.map(libelles).fillna(rep.modalite)
    couleurs = {"Les deux opérateurs": T.SERIE_1, "Togocom seul": T.SERIE_2,
                "Moov seul": T.SERIE_3, "Opérateur non renseigné": T.GRIS_FOND}

    if ctx["operateur"] != "Tous":
        st.caption(f"Cette comparaison met les deux opérateurs face à face : "
                   f"elle reste affichée en entier malgré le filtre "
                   f"« {ctx['operateur']} ».")
    g2, d2 = st.columns([1.45, 1], gap="medium")
    with g2:
        with T.bloc("Présence des opérateurs sur les points de service"):
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

    n_nsp = int(rep.loc[rep.libelle == "Opérateur non renseigné",
                        "points"].sum())
    with d2:
        st.markdown(T.conclusion(
            f"{_n(n_tgc)} points ne servent que Togocom, contre {_n(n_moov)} "
            f"pour Moov seul — un rapport de "
            f"{n_tgc / max(n_moov, 1):.1f}".replace(".", ",") + " à 1. Ouvrir "
            "la concurrence est un objectif en soi."), unsafe_allow_html=True)
        st.markdown(T.lecture(
            "Là où un seul opérateur est présent, l'usager n'a aucune "
            "alternative en cas de panne, de tarif ou de rupture de "
            "liquidité."), unsafe_allow_html=True)
        st.markdown(T.source(
            f"{_n(n_nsp)} points à opérateur non renseigné forment une "
            "catégorie propre, ni réaffectée ni supprimée. Un point servi par "
            "deux opérateurs n'est pas deux points."), unsafe_allow_html=True)

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
            "Points / 10 000 hab.": "{:,.1f}"}, thousands=" ", decimal=","),
            width="stretch", hide_index=True)
        st.caption("« Présence » compte les points où l'opérateur est "
                   "disponible : un point servi par les deux figure dans les "
                   "deux colonnes.")
