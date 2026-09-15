"""
FIGURES DU SUPPORT DE PRESENTATION
===================================
Genere les visuels du PowerPoint en PNG haute definition.

Les figures suivent les MEMES regles que le tableau de bord :
  - rampe sequentielle a une seule teinte pour les magnitudes ;
  - emphase (une couleur + gris) quand le sujet est « ces territoires-la
    se detachent », jamais un degrade par valeur qui doublerait l'encodage ;
  - marques fines, grille en filet, etiquettes directes selectives ;
  - palette categorielle validee (3 emplacements maximum).

Matplotlib est utilise plutot que Plotly : l'export d'images Plotly exige
kaleido, absent de l'environnement. Aucune installation n'est requise.

Sortie : reports/figures/*.png
"""

from __future__ import annotations

import io
import sys
from pathlib import Path

import geopandas as gpd
import matplotlib as mpl
import matplotlib.patheffects
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.lines import Line2D

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
FIGURES = ROOT / "reports" / "figures"

# --- palette (identique au tableau de bord) ----------------------------------
VERT = "#156c52"
SERIE_1, SERIE_2, SERIE_3 = "#2a78d6", "#eb6834", "#1baf7a"
SEQUENTIEL = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#2a78d6",
              "#256abf", "#1c5cab", "#184f95", "#0d366b"]
ENCRE, ENCRE_2, ENCRE_MUET = "#12120f", "#55544f", "#8b8a84"
GRILLE, GRIS_FOND, SURFACE = "#eeede8", "#d9d8d2", "#ffffff"
CRITIQUE = "#d03b3b"

CMAP = LinearSegmentedColormap.from_list("togo_bleu", SEQUENTIEL)

mpl.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 10,
    "axes.edgecolor": "#d5d4ce",
    "axes.labelcolor": ENCRE_2,
    "axes.titlecolor": ENCRE,
    "text.color": ENCRE_2,
    "xtick.color": ENCRE_MUET,
    "ytick.color": ENCRE_MUET,
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "figure.facecolor": SURFACE,
    "axes.facecolor": SURFACE,
    "savefig.facecolor": SURFACE,
    "axes.spines.top": False,
    "axes.spines.right": False,
})

TOP_STABLES = ["Kpendjal", "Mô", "Est-Mono", "Akébou", "Yoto",
               "Kpendjal-Ouest", "Tandjoaré", "Wawa", "Blitta"]


def _espace(n: float, dec: int = 0) -> str:
    return f"{n:,.{dec}f}".replace(",", " ")


def _sauver(fig, nom: str) -> Path:
    FIGURES.mkdir(parents=True, exist_ok=True)
    chemin = FIGURES / f"{nom}.png"
    fig.savefig(chemin, dpi=200, bbox_inches="tight", pad_inches=0.12)
    plt.close(fig)
    return chemin


# =============================================================================
def carte_priorite(pref: pd.DataFrame, geo: gpd.GeoDataFrame) -> Path:
    """Choroplethe du DCPI : liseres blancs, limites regionales, etiquettes."""
    g = geo.merge(pref[["prefecture", "DCPI", "rang_DCPI"]], on="prefecture")
    fig, ax = plt.subplots(figsize=(6.6, 8.4))

    g.plot(column="DCPI", cmap=CMAP, ax=ax, edgecolor="white", linewidth=1.1)
    # Limites regionales : second niveau de lecture
    g.dissolve(by="region").boundary.plot(ax=ax, color="#12120f",
                                          linewidth=1.5, alpha=0.55)

    # --- Etiquettes lisibles ------------------------------------------------
    # Trois problemes traites : le texte sombre disparait sur les aplats
    # fonces, les libelles se chevauchent dans le nord et autour de Lome, et
    # un nom deborde des petits polygones.
    norme = plt.Normalize(g.DCPI.min(), g.DCPI.max())
    aire_min = g.geometry.area.quantile(0.22)
    poses: list[tuple[float, float, float, float]] = []

    for _, r in g.sort_values("DCPI", ascending=False).iterrows():
        p = r.geometry.representative_point()
        prioritaire = r.prefecture in TOP_STABLES

        # Un petit polygone non prioritaire n'est pas etiquete : mieux vaut
        # une carte lisible qu'une carte exhaustive et illisible.
        if not prioritaire and r.geometry.area < aire_min:
            continue
        # Anti-chevauchement par RECTANGLES, et non par distance entre ancres :
        # « Kpendjal-Ouest » deborde loin de son point d'ancrage alors que
        # celui-ci n'est pas proche de son voisin. Seule la largeur reelle du
        # libelle permet de detecter le recouvrement.
        taille = 8.0 if prioritaire else 6.4
        demi_l = len(r.prefecture) * taille * 0.0021      # degres de longitude
        demi_h = taille * 0.0068                          # degres de latitude
        px, py = p.x, p.y

        def _chevauche(a: float, b: float) -> bool:
            return any(abs(a - x) < (demi_l + dl) and abs(b - y) < (demi_h + dh)
                       for x, y, dl, dh in poses)

        if _chevauche(px, py):
            # Un libelle secondaire est supprime ; un libelle PRIORITAIRE ne
            # l'est jamais — son absence serait une perte d'information.
            if not prioritaire:
                continue
            for decalage in (0.16, -0.16, 0.30, -0.30, 0.44, -0.44):
                if not _chevauche(px, py + decalage):
                    py += decalage
                    break
        poses.append((px, py, demi_l, demi_h))
        p = type("P", (), {"x": px, "y": py})()

        # Contraste : texte blanc sur aplat fonce, sombre sur aplat clair
        fonce = norme(r.DCPI) > 0.58
        couleur = "#ffffff" if fonce else ENCRE
        halo = "#12120f" if fonce else "#ffffff"

        ax.annotate(
            r.prefecture, (p.x, p.y), ha="center", va="center",
            fontsize=taille,
            fontweight="bold" if prioritaire else "normal",
            color=couleur,
            path_effects=[mpl.patheffects.withStroke(linewidth=2.4,
                                                     foreground=halo,
                                                     alpha=0.55)])

    sm = plt.cm.ScalarMappable(cmap=CMAP,
                               norm=plt.Normalize(g.DCPI.min(), g.DCPI.max()))
    cb = fig.colorbar(sm, ax=ax, fraction=0.031, pad=0.01, aspect=26)
    cb.set_label("Score de priorité DCPI", fontsize=9, color=ENCRE_2)
    cb.outline.set_visible(False)
    cb.ax.tick_params(labelsize=8, color=ENCRE_MUET)

    ax.set_axis_off()
    return _sauver(fig, "carte_priorite")


# =============================================================================
def ecart_desserte(pref: pd.DataFrame, national: float) -> Path:
    """Barres en emphase : au-dessus / en dessous de la moyenne nationale."""
    c = pref.dropna(subset=["hab_par_point_mm"]).sort_values("hab_par_point_mm")
    couleurs = [SERIE_1 if v > national else GRIS_FOND for v in c.hab_par_point_mm]

    fig, ax = plt.subplots(figsize=(11.2, 6.6))
    ax.barh(c.prefecture, c.hab_par_point_mm, color=couleurs, height=0.72)
    ax.axvline(national, color=CRITIQUE, linewidth=1.8)
    ax.text(national * 1.03, len(c) - 0.4,
            f"moyenne nationale  {_espace(national)}",
            color=CRITIQUE, fontsize=9, va="center")

    for y, (v, coul) in enumerate(zip(c.hab_par_point_mm, couleurs)):
        if coul == SERIE_1:
            ax.text(v * 1.02, y, _espace(v), va="center", fontsize=8,
                    color=ENCRE_2)

    ax.set_xlabel("Habitants par point Mobile Money  ·  plus haut = moins bien desservi",
                  fontsize=9.5)
    ax.xaxis.grid(True, color=GRILLE, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.tick_params(axis="y", labelsize=8.4, length=0)
    ax.set_xlim(0, c.hab_par_point_mm.max() * 1.14)
    ax.spines["left"].set_visible(False)
    return _sauver(fig, "ecart_desserte")


# =============================================================================
def concentration(pref: pd.DataFrame) -> Path:
    """Courbe de concentration de l'equipement."""
    b = pref.dropna(subset=["hab_par_point_mm"]).sort_values(
        "points_mm_pour_10k_hab")
    cp = np.concatenate([[0], np.cumsum(b.population) / b.population.sum()])
    cm = np.concatenate([[0], np.cumsum(b.points_mm) / b.points_mm.sum()])
    moitie = np.interp(0.5, cp, cm)

    fig, ax = plt.subplots(figsize=(6.4, 5.6))
    ax.plot([0, 1], [0, 1], color="#d5d4ce", linewidth=1.6,
            label="Répartition proportionnelle")
    ax.plot(cp, cm, color=SERIE_1, linewidth=2.4, label="Répartition observée")
    ax.fill_between(cp, cm, cp, color=SERIE_1, alpha=0.10)

    ax.plot([0.5, 0.5], [0, moitie], color=CRITIQUE, linewidth=1.2, ls=":")
    ax.plot([0, 0.5], [moitie, moitie], color=CRITIQUE, linewidth=1.2, ls=":")
    ax.annotate(f"la moitié la moins bien desservie\nde la population n'a que "
                f"{moitie * 100:.0f} % des points",
                xy=(0.5, moitie), xytext=(0.54, moitie - 0.20),
                fontsize=9, color=CRITIQUE,
                arrowprops=dict(arrowstyle="-", color=CRITIQUE, lw=1))

    ax.set_xlabel("Part cumulée de la population", fontsize=9.5)
    ax.set_ylabel("Part cumulée des points Mobile Money", fontsize=9.5)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.xaxis.set_major_formatter(mpl.ticker.PercentFormatter(1.0, decimals=0, symbol=" %"))
    ax.yaxis.set_major_formatter(mpl.ticker.PercentFormatter(1.0, decimals=0, symbol=" %"))
    ax.grid(True, color=GRILLE, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.legend(frameon=False, fontsize=9, loc="upper left")
    return _sauver(fig, "concentration")


# =============================================================================
def sensibilite(sens: pd.DataFrame) -> Path:
    """Frequence de presence dans le top 10 sur 2 000 ponderations."""
    s = sens.head(13).sort_values("frequence_top10")
    couleurs = [SERIE_1 if f >= 0.90 else GRIS_FOND for f in s.frequence_top10]

    fig, ax = plt.subplots(figsize=(6.6, 5.6))
    ax.barh(s.prefecture, s.frequence_top10, color=couleurs, height=0.72)
    ax.axvline(0.90, color=CRITIQUE, linewidth=1.6)
    for y, f in enumerate(s.frequence_top10):
        ax.text(f + 0.015, y, f"{f * 100:.0f} %", va="center", fontsize=8.6,
                color=ENCRE_2)

    ax.set_xlabel("Présence dans le top 10 des priorités", fontsize=9.5)
    ax.set_xlim(0, 1.13)
    ax.xaxis.set_major_formatter(mpl.ticker.PercentFormatter(1.0, decimals=0, symbol=" %"))
    ax.xaxis.grid(True, color=GRILLE, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.tick_params(axis="y", labelsize=9, length=0)
    ax.spines["left"].set_visible(False)
    return _sauver(fig, "sensibilite")


# =============================================================================
def quadrant(pref: pd.DataFrame, national: float) -> Path:
    """Population elevee x desserte faible."""
    c = pref.dropna(subset=["hab_par_point_mm"]).copy()
    med = pref.population.median()
    c["crit"] = (c.hab_par_point_mm > national) & (c.population > med)

    fig, ax = plt.subplots(figsize=(7.4, 5.8))
    for etat, coul, lib in ((False, GRIS_FOND, "Autres préfectures"),
                            (True, SERIE_1, "Population et déficit élevés")):
        s = c[c.crit == etat]
        ax.scatter(s.population, s.hab_par_point_mm, s=68, c=coul,
                   edgecolors="white", linewidths=1.6, label=lib, zorder=3)
    for _, r in c[c.crit].iterrows():
        ax.annotate(r.prefecture, (r.population, r.hab_par_point_mm),
                    xytext=(0, 9), textcoords="offset points",
                    ha="center", fontsize=8.2, color=ENCRE)

    ax.axhline(national, color="#d5d4ce", linewidth=1.1)
    ax.axvline(med, color="#d5d4ce", linewidth=1.1)
    ax.set_xscale("log")
    ax.set_xlabel("Population  ·  échelle logarithmique", fontsize=9.5)
    ax.set_ylabel("Habitants par point Mobile Money", fontsize=9.5)
    ax.grid(True, color=GRILLE, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.legend(frameon=False, fontsize=9, loc="upper left")
    ax.xaxis.set_major_formatter(
        mpl.ticker.FuncFormatter(lambda v, _: _espace(v)))
    return _sauver(fig, "quadrant")


# =============================================================================
def leviers(pref: pd.DataFrame, stables: set) -> Path:
    """Population atteinte par levier d'intervention."""
    regles = [
        ("Densifier le réseau d'agents", lambda r: r.hab_par_point_mm > 800, SERIE_1),
        ("Implanter une agence", lambda r: r.agences_actives == 0, SERIE_2),
        ("Répartir le maillage", lambda r: r.dist_agence_med_canton_km >= 25, SERIE_3),
        ("Ouvrir la concurrence",
         lambda r: (r.mm_moov == 0) or (r.mm_togocom == 0), "#fab219"),
        ("Fiabiliser le recensement",
         lambda r: r.points_mm > 0 and r.mm_operateur_inconnu / r.points_mm > .15,
         ENCRE_MUET),
    ]
    p = pref[pref.prefecture.isin(stables)]
    lignes = [(nom, int(p[p.apply(cond, axis=1)].population.sum()),
               int(p.apply(cond, axis=1).sum()), coul)
              for nom, cond, coul in regles]
    lignes = [x for x in lignes if x[1] > 0]
    lignes.sort(key=lambda x: x[1])

    fig, ax = plt.subplots(figsize=(8.6, 4.4))
    noms = [x[0] for x in lignes]
    vals = [x[1] for x in lignes]
    ax.barh(noms, vals, color=[x[3] for x in lignes], height=0.66)
    for y, (v, n) in enumerate(zip(vals, [x[2] for x in lignes])):
        ax.text(v * 1.015, y, f"{_espace(v)} hab.  ·  {n} préfectures",
                va="center", fontsize=8.8, color=ENCRE_2)

    ax.set_xlabel("Habitants concernés dans les territoires prioritaires",
                  fontsize=9.5)
    ax.set_xlim(0, max(vals) * 1.42)
    ax.xaxis.grid(True, color=GRILLE, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.tick_params(axis="y", labelsize=9.4, length=0)
    ax.xaxis.set_major_formatter(
        mpl.ticker.FuncFormatter(lambda v, _: _espace(v)))
    ax.spines["left"].set_visible(False)
    return _sauver(fig, "leviers")


# =============================================================================
def main() -> None:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                                  errors="replace")
    pref = (pd.read_csv(PROCESSED / "acces_prefecture.csv")
            .merge(pd.read_csv(PROCESSED / "dcpi_prefecture.csv")
                   [["prefecture", "DCPI", "rang_DCPI"]], on="prefecture"))
    geo = gpd.read_file(PROCESSED / "prefectures.gpkg")
    sens = pd.read_csv(PROCESSED / "dcpi_sensibilite.csv")
    stables = set(sens[sens.frequence_top10 >= 0.90].prefecture)
    national = 8_095_498 / pref.points_mm.sum()

    produites = [
        carte_priorite(pref, geo),
        ecart_desserte(pref, national),
        concentration(pref),
        sensibilite(sens),
        quadrant(pref, national),
        leviers(pref, stables),
    ]
    print(f"{len(produites)} figures ecrites dans reports/figures/")
    for p in produites:
        print(f"  {p.name:24s} {p.stat().st_size / 1024:7.1f} Ko")


if __name__ == "__main__":
    main()
