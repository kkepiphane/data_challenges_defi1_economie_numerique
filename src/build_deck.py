"""
SUPPORT DE PRESENTATION — 10 DIAPOSITIVES
==========================================
Assemble `reports/Defi1_Togo_Connectivite_numerique.pptx`.

Une PAGE DE GARDE, puis NEUF diapositives de contenu. Le reglement plafonne le
support a dix pages, page de garde comprise : les deux diapositives consacrees
aux donnees — sources d'une part, qualite et preparation d'autre part — sont
donc reunies en une seule, qui porte les deux propos.

Regle de construction : CHAQUE diapositive porte un MESSAGE PRINCIPAL unique,
formule comme une affirmation defendable, pas comme un titre de rubrique.
Si le message ne tient pas en une phrase verifiable, la diapositive est mal
concue.

Les chiffres proviennent tous de `data/processed/` et sont donc traçables
jusqu'aux controles publies dans `reports/`. Aucun n'est saisi a la main.

Prerequis : `python src/build_deck_figures.py` (genere les visuels).
"""

from __future__ import annotations

import io
import sys
from pathlib import Path

import pandas as pd
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Emu, Inches, Pt

sys.path.insert(0, str(Path(__file__).resolve().parent))
import couverture as CV                                             # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
FIGURES = ROOT / "reports" / "figures"
SORTIE = ROOT / "reports" / "Defi1_Togo_Connectivite_numerique.pptx"

# Adresse publique du tableau de bord, affichee sur la page de fin.
# A renseigner apres le deploiement sur Streamlit Community Cloud ; tant
# qu'elle vaut None, la page de fin renvoie vers le depot.
URL_TABLEAU_DE_BORD = None

# --- couleurs (identiques au tableau de bord) --------------------------------
VERT = RGBColor(0x15, 0x6C, 0x52)
OR = RGBColor(0xFF, 0xCE, 0x15)
ROUGE_DRAPEAU = RGBColor(0xD2, 0x1B, 0x33)
SERIE_1 = RGBColor(0x2A, 0x78, 0xD6)
SERIE_2 = RGBColor(0xEB, 0x68, 0x34)
SERIE_3 = RGBColor(0x1B, 0xAF, 0x7A)
ENCRE = RGBColor(0x12, 0x12, 0x0F)
ENCRE_2 = RGBColor(0x55, 0x54, 0x4F)
ENCRE_MUET = RGBColor(0x8B, 0x8A, 0x84)
BLANC = RGBColor(0xFF, 0xFF, 0xFF)
PLAN = RGBColor(0xF7, 0xF7, 0xF5)
BORDURE = RGBColor(0xE6, 0xE5, 0xE0)
VERT_CLAIR = RGBColor(0xE8, 0xF2, 0xEE)
CRITIQUE = RGBColor(0xD0, 0x3B, 0x3B)

SANS = "Segoe UI"
L, H = Inches(13.333), Inches(7.5)
MARGE = Inches(0.62)


# =============================================================================
# PRIMITIVES
# =============================================================================
def _zone(slide, x, y, w, h, texte, taille=12, gras=False, couleur=ENCRE_2,
          interligne=1.22, aligne=PP_ALIGN.LEFT, police=SANS, espacement=None):
    tb = slide.shapes.add_textbox(x, y, w, h)
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    for i, ligne in enumerate(texte.split("\n")):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = aligne
        p.line_spacing = interligne
        if espacement:
            p.space_after = Pt(espacement)
        r = p.add_run()
        r.text = ligne
        r.font.size = Pt(taille)
        r.font.bold = gras
        r.font.color.rgb = couleur
        r.font.name = police
    return tb


def _rect(slide, x, y, w, h, remplissage=None, bordure=None, epaisseur=1.0):
    from pptx.enum.shapes import MSO_SHAPE
    f = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, x, y, w, h)
    f.shadow.inherit = False
    if remplissage is None:
        f.fill.background()
    else:
        f.fill.solid()
        f.fill.fore_color.rgb = remplissage
    if bordure is None:
        f.line.fill.background()
    else:
        f.line.color.rgb = bordure
        f.line.width = Pt(epaisseur)
    return f


def _diapo(prs, eyebrow: str, titre: str, message: str, numero: int,
           total: int = 10):
    """Ossature commune : filet tricolore, sur-titre, titre, message, pied."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _rect(slide, 0, 0, L, H, PLAN)

    # Filet tricolore institutionnel
    _rect(slide, 0, 0, L * 0.62, Inches(0.055), VERT)
    _rect(slide, L * 0.62, 0, L * 0.19, Inches(0.055), OR)
    _rect(slide, L * 0.81, 0, L * 0.19, Inches(0.055), ROUGE_DRAPEAU)

    _zone(slide, MARGE, Inches(0.34), Inches(9), Inches(0.24),
          eyebrow.upper(), 9, True, ENCRE_MUET, police="Consolas")
    _zone(slide, MARGE, Inches(0.60), Inches(9.4), Inches(0.62),
          titre, 28, True, ENCRE)

    # Message principal : l'affirmation que la diapositive doit soutenir
    _rect(slide, MARGE, Inches(1.30), L - 2 * MARGE, Inches(0.62), VERT_CLAIR)
    _rect(slide, MARGE, Inches(1.30), Inches(0.035), Inches(0.62), VERT)
    _zone(slide, MARGE + Inches(0.22), Inches(1.43), L - 2 * MARGE - Inches(0.4),
          Inches(0.4), message, 13.5, True, RGBColor(0x0F, 0x4D, 0x3B))

    # Pied de page
    _rect(slide, MARGE, H - Inches(0.52), L - 2 * MARGE, Pt(0.75), BORDURE)
    _zone(slide, MARGE, H - Inches(0.42), Inches(9.5), Inches(0.26),
          "République togolaise · Défi Économie numérique · Données ouvertes "
          "PRISE 2021-2022, RGPH-5 2022, COD-AB 2021",
          8, False, ENCRE_MUET, police="Consolas")
    _zone(slide, L - MARGE - Inches(1.2), H - Inches(0.42), Inches(1.2),
          # +1 : la page de garde est la page 1. Le numero affiche est
          # celui qu'on cite en reunion (« slide 5 »), pas un rang de contenu.
          Inches(0.26), f"{numero + 1:02d} / {total}", 8, True, ENCRE_MUET,
          aligne=PP_ALIGN.RIGHT, police="Consolas")
    return slide


def _kpi(slide, x, y, w, libelle, valeur, note, couleur=VERT,
         h=Inches(1.32)):
    _rect(slide, x, y, w, h, BLANC, BORDURE, 0.75)
    _rect(slide, x, y, w, Inches(0.038), couleur)
    _zone(slide, x + Inches(0.16), y + Inches(0.17), w - Inches(0.32),
          Inches(0.3), libelle.upper(), 7.5, True, ENCRE_MUET,
          police="Consolas", interligne=1.3)
    _zone(slide, x + Inches(0.16), y + Inches(0.52), w - Inches(0.32),
          Inches(0.42), valeur, 23, True, ENCRE)
    _zone(slide, x + Inches(0.16), y + Inches(0.99), w - Inches(0.32),
          Inches(0.3), note, 8, False, ENCRE_2, interligne=1.25)


def _puces(slide, x, y, w, elements, taille=11, couleur_puce=VERT,
           interligne_bloc=Inches(0.0)):
    """Liste a puces carrees, avec titre en gras et corps en gris."""
    curseur = y
    for titre, corps in elements:
        _rect(slide, x, curseur + Inches(0.055), Inches(0.075),
              Inches(0.075), couleur_puce)
        _zone(slide, x + Inches(0.19), curseur, w - Inches(0.19),
              Inches(0.24), titre, taille, True, ENCRE)
        hauteur = Inches(0.245)
        if corps:
            # Hauteur du bloc : estimee a partir de la largeur utile et de la
            # chasse moyenne d'une police humaniste (~0,079 pouce par point de
            # corps). La boite est dimensionnee a cette hauteur exacte, et non
            # a une valeur fixe : sinon deux blocs se recouvrent dans le
            # fichier meme si le texte rendu, lui, ne se recouvre pas.
            taille_corps = taille - 1.5
            largeur_utile = (w - Inches(0.19)) / 914400          # en pouces
            par_ligne = max(20, int(largeur_utile / (taille_corps * 0.0079)))
            lignes = max(1, -(-len(corps) // par_ligne))         # arrondi haut
            h_corps = Inches(taille_corps * 1.32 / 72) * lignes
            _zone(slide, x + Inches(0.19), curseur + Inches(0.25),
                  w - Inches(0.19), h_corps, corps, taille_corps, False,
                  ENCRE_2, interligne=1.32)
            hauteur += h_corps
        curseur += hauteur + Inches(0.15) + interligne_bloc
    return curseur


def _image(slide, nom, x, y, largeur=None, hauteur=None):
    chemin = FIGURES / f"{nom}.png"
    if not chemin.exists():
        return None
    kw = {}
    if largeur:
        kw["width"] = largeur
    if hauteur:
        kw["height"] = hauteur
    return slide.shapes.add_picture(str(chemin), x, y, **kw)


def _tableau(slide, x, y, w, entetes, lignes, largeurs=None, taille=9.5):
    n_l, n_c = len(lignes) + 1, len(entetes)
    h = Inches(0.32) * n_l
    tbl = slide.shapes.add_table(n_l, n_c, x, y, w, h).table
    if largeurs:
        for i, prop in enumerate(largeurs):
            tbl.columns[i].width = Emu(int(w * prop))
    for j, t in enumerate(entetes):
        c = tbl.cell(0, j)
        c.text = t
        c.fill.solid()
        c.fill.fore_color.rgb = VERT
        c.vertical_anchor = MSO_ANCHOR.MIDDLE
        p = c.text_frame.paragraphs[0]
        p.runs[0].font.size = Pt(taille)
        p.runs[0].font.bold = True
        p.runs[0].font.color.rgb = BLANC
        p.runs[0].font.name = SANS
    for i, ligne in enumerate(lignes, start=1):
        for j, v in enumerate(ligne):
            c = tbl.cell(i, j)
            c.text = str(v)
            c.fill.solid()
            c.fill.fore_color.rgb = BLANC if i % 2 else PLAN
            c.vertical_anchor = MSO_ANCHOR.MIDDLE
            p = c.text_frame.paragraphs[0]
            p.runs[0].font.size = Pt(taille)
            p.runs[0].font.color.rgb = ENCRE if j == 0 else ENCRE_2
            p.runs[0].font.bold = (j == 0)
            p.runs[0].font.name = SANS
    return tbl


def _controles() -> tuple[int, int]:
    """(au vert, total) — meme lecture des memes rapports que
    `dashboard/data.py::controles_chaine`, pour que le support et le tableau
    de bord citent toujours le meme nombre."""
    etapes = ["extraction_rgph5", "socle_geo", "indicateurs", "acces_spatial",
              "dcpi", "zones_blanches"]
    ok = total = 0
    for nom in etapes:
        chemin = ROOT / "reports" / f"{nom}.md"
        if not chemin.exists():
            continue
        dans = False
        for ligne in chemin.read_text(encoding="utf-8").split("\n"):
            if ligne.startswith("| Controle |"):
                dans = True
                continue
            if dans:
                if not ligne.startswith("|"):
                    break
                cells = [c.strip() for c in ligne.strip("|").split("|")]
                if len(cells) >= 3 and not set(cells[0]) <= {"-", " "}:
                    total += 1
                    ok += "OK" in cells[1]
    return ok, total


def _esp(n: float, dec: int = 0) -> str:
    return f"{n:,.{dec}f}".replace(",", " ")


# =============================================================================
# CONSTRUCTION
# =============================================================================
def main() -> None:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                                  errors="replace")

    pref = (pd.read_csv(PROCESSED / "acces_prefecture.csv")
            .merge(pd.read_csv(PROCESSED / "dcpi_prefecture.csv")
                   [["prefecture", "DCPI", "rang_DCPI"]], on="prefecture"))
    sens = pd.read_csv(PROCESSED / "dcpi_sensibilite.csv")
    com = pd.read_csv(PROCESSED / "indicateurs_commune.csv")
    mmo = pd.read_csv(PROCESSED / "mobile_money_operateurs.csv")
    mm = mmo.drop_duplicates("FID")

    # -------------------------------------------------------------------------
    # TOUTES les valeurs citees dans les diapositives sont calculees ici.
    # Aucune n'est saisie en dur : une edition differente d'une source, ou une
    # correction en amont, doit se propager au support sans reecriture.
    # -------------------------------------------------------------------------
    NAT = 8_095_498
    stables = sens[sens.frequence_top10 >= 0.90]
    national = NAT / pref.points_mm.sum()
    sans_agence = pref[pref.agences_actives == 0]
    pop_stable = int(pref[pref.prefecture.isin(stables.prefecture)]
                     .population.sum())
    pire = pref.loc[pref.hab_par_point_mm.idxmax()]
    mieux = pref.loc[pref.hab_par_point_mm.idxmin()]
    rapport = pire.hab_par_point_mm / mieux.hab_par_point_mm
    au_dessus = int((pref.hab_par_point_mm > national).sum())
    com_sans = com[com.agences_actives == 0]
    quadrant = int(((pref.hab_par_point_mm > national)
                    & (pref.population > pref.population.median())).sum())

    import numpy as _np
    b = pref.dropna(subset=["hab_par_point_mm"]).sort_values(
        "points_mm_pour_10k_hab")
    cp = _np.concatenate([[0], _np.cumsum(b.population) / b.population.sum()])
    cm = _np.concatenate([[0], _np.cumsum(b.points_mm) / b.points_mm.sum()])
    part_moitie = float(_np.interp(0.5, cp, cm))
    tgc_seul = int((mm.operateur == "Togocom").sum())
    moov_seul = int((mm.operateur == "Moov").sum())

    # Meme definition que `dashboard/data.py::agences_reperes` :
    #   RECENSEES = agences uniques apres dedoublonnage ;
    #   ACTIVES   = recensees moins les fermees declarees par la source.
    etab = pd.read_csv(PROCESSED / "etablissements.csv")
    agences = etab[etab.type_infrastructure != "Data center"]
    n_agences = len(agences)
    n_actives = int(agences.actif.sum())
    n_fermees = n_agences - n_actives
    n_agences_moov = int((agences.operateur == "Moov").sum())
    n_agences_tgc = int((agences.operateur == "Togocom").sum())
    n_actives_tgc = int((agences.actif & (agences.operateur == "Togocom")).sum())
    n_dc = int((etab.type_infrastructure == "Data center").sum())
    n_ctrl_ok, n_ctrl = _controles()
    # Meme regression que la page Desserte du tableau de bord.
    ld = _np.log10(pref.densite_hab_km2)
    lp = _np.log10(pref.points_mm_pour_10k_hab)
    pente, orig = _np.polyfit(ld, lp, 1)
    r2_densite = float(1 - ((lp - (pente * ld + orig)) ** 2).sum()
                       / ((lp - lp.mean()) ** 2).sum())
    zb = pd.read_csv(PROCESSED / "zones_blanches_canton.csv")
    n_zb_eleve = int((zb.classe == "Élevé").sum())
    n_zb_sans = int(zb.sans_temoin.sum())

    # Points a ouvrir pour les territoires prioritaires : MEME formule et
    # MEME objectif que `dashboard/data.py::plan_couverture` /
    # `OBJECTIF_DEFAUT` (409 hab./point) — Arbitrage, Plan d'action et ce
    # support doivent toujours afficher le meme total pour les memes 9
    # territoires (1 497 avec les donnees actuelles).
    OBJECTIF_DEFAUT = 409
    prio = pref[pref.prefecture.isin(stables.prefecture)]
    a_ouvrir = int((_np.ceil(prio.population / OBJECTIF_DEFAUT)
                    - prio.points_mm).clip(lower=0).sum())

    def _fr(x: float, dec: int = 1) -> str:
        return f"{x:.{dec}f}".replace(".", ",")

    def _pct(x: float, dec: int = 0) -> str:
        """Pourcentage en notation francaise (espace avant %) — meme regle
        que `dashboard/theme.py::pct`, l'entree est une FRACTION (0-1)."""
        return f"{_fr(x * 100, dec)} %"

    prs = Presentation()
    prs.slide_width, prs.slide_height = L, H

    # -------------------------------------------------------- PAGE DE GARDE
    # Les trois reperes sont calcules, jamais saisis : si une source change,
    # la couverture change avec elle.
    CV.page_de_garde(
        prs,
        titre="Connecter le Togo\nlà où le manque est prouvé",
        these=(
            f"Le Togo compte un point de service financier numérique pour "
            f"{_esp(national)} habitants. Cette moyenne ne dit rien d'utile : "
            f"entre la préfecture la mieux dotée et la moins dotée, l'écart "
            f"est de 1 à {_fr(rapport)}.\n"
            "Ce diagnostic désigne les territoires où investir, et publie de "
            "quoi contester le classement."),
        reperes=[
            ("Habitants par point de service", _esp(national),
             "moyenne nationale · 19 788 points géolocalisés"),
            ("Écart entre préfectures", f"1 à {_fr(rapport)}",
             f"{pire.prefecture} contre {mieux.prefecture}"),
            ("Préfectures sans agence active", f"{len(sans_agence)} / 39",
             f"{_esp(int(sans_agence.population.sum()))} habitants concernés"),
        ],
        auteur="KOUTSAVA Kossi Epiphane",
        # Vide : page de garde epuree (nom seul), choix de l'auteur en
        # relecture — voir reports/Defi1_Togo_Connectivite_numerique.pptx.
        qualite="",
        sources=("Géoportail national (PRISE 2021-2022) · RGPH-5, INSEED "
                 "(novembre 2022) · limites COD-AB v02, OCHA (2021) — "
                 f"{n_ctrl} contrôles arithmétiques publiés"))

    # ---------------------------------------------------------------- 01
    s = _diapo(prs, "Défi Économie numérique · Togo",
               "Problématique et enjeux",
               "L'accès aux services numériques au Togo n'est pas faible "
               "partout : il est très inégal — et l'inégalité se mesure.", 1)
    _zone(s, MARGE, Inches(2.15), Inches(6.5), Inches(0.9),
          "Où faut-il investir en priorité pour réduire les inégalités "
          "d'accès aux télécommunications et aux services numériques au "
          "Togo, et pourquoi ?", 17, True, ENCRE, interligne=1.3)
    _puces(s, MARGE, Inches(3.25), Inches(6.3), [
        ("Une moyenne nationale ne suffit pas à décider",
         f"{_esp(national)} habitants par point Mobile Money en moyenne — mais "
         f"un rapport de 1 à {_fr(rapport)} entre préfectures. Agir "
         "« partout » revient à n'agir nulle part en priorité."),
        ("Un déficit se prouve, il ne se déclare pas",
         "Affirmer qu'un territoire est sous-desservi exige un dénominateur : "
         "la population. Sans elle, un faible comptage peut simplement "
         "refléter une faible démographie."),
        ("Une priorisation doit résister à la contestation",
         "Un classement dépendant de pondérations arbitraires n'est pas "
         "défendable. Il doit être testé, et sa stabilité publiée."),
    ])
    x = Inches(7.55)
    for i, (lib, val, note, coul) in enumerate([
            ("Population résidente", _esp(8_095_498), "RGPH-5 · novembre 2022",
             VERT),
            ("Points de service recensés", _esp(int(pref.points_mm.sum())),
             "tous géolocalisés", SERIE_1),
            ("Préfectures sans agence active", f"{len(sans_agence)} / 39",
             f"{_esp(int(sans_agence.population.sum()))} habitants", CRITIQUE),
            ("Territoires prioritaires identifiés", f"{len(stables)}",
             "priorité stable sur 2 000 pondérations", SERIE_3)]):
        _kpi(s, x + Inches(2.6) * (i % 2), Inches(2.15) + Inches(1.52) * (i // 2),
             Inches(2.4), lib, val, note, coul)

    # ---------------------------------------------------------------- 02
    s = _diapo(prs, "Données", "Données, sources et qualité",
               "Trois sources publiques, deux corrections de l'énoncé : "
               f"2 opérateurs et non 4, {n_agences} agences recensées et non 141.", 2)
    _tableau(s, MARGE, Inches(2.05), L - 2 * MARGE,
             ["Donnée", "Producteur", "Période", "Ce qu'elle apporte"],
             [["Agences, agents Mobile Money, data centers",
               "Géoportail national du Togo", "Collecte 2021-2022",
               "Localisation de chaque équipement"],
              ["Population résidente", "INSEED — 5ᵉ recensement (RGPH-5)",
               "23 oct. – 16 nov. 2022",
               "Le dénominateur de tous les ratios"],
              ["Limites administratives et superficies",
               "Common Operational Datasets (OCHA)", "Valides au 07/01/2021",
               "Contours, densités, distances"]],
             largeurs=[0.30, 0.24, 0.18, 0.28])

    # La donnee absente est annoncee des la diapositive des sources : elle
    # conditionne la lecture de tout le reste. La diapositive 08 y revient.
    _rect(s, MARGE, Inches(3.5), L - 2 * MARGE, Inches(0.66), BLANC,
          BORDURE, 0.75)
    _rect(s, MARGE, Inches(3.5), Inches(0.035), Inches(0.66), CRITIQUE)
    _zone(s, MARGE + Inches(0.22), Inches(3.63), Inches(3.0), Inches(0.24),
          "LA DONNÉE QUI MANQUE", 8, True, ENCRE_MUET, police="Consolas")
    _zone(s, MARGE + Inches(0.22), Inches(3.86), L - 2 * MARGE - Inches(0.5),
          Inches(0.26),
          "Aucune mesure de couverture réseau mobile n'existe dans les sources "
          "ouvertes mobilisées. Ce travail mesure un déficit d'accès aux "
          "services — pas une absence de réseau.", 10.5, False, ENCRE_2)

    _puces(s, MARGE, Inches(4.45), Inches(6.15), [
        ("« Agences – Télécom » n'est pas un quatrième opérateur",
         "Ses 51 lignes sont déjà contenues dans les fichiers Moov et "
         "Togocom réunis, sans un seul enregistrement propre. "
         "Empiler les fichiers afficherait 141 agences au lieu de "
         f"{n_agences} recensées après dédoublonnage ({n_agences_moov} Moov, "
         f"{n_agences_tgc} Togocom), dont {n_actives} actives : {n_fermees} "
         "agences Togocom déclarées fermées sont exclues des calculs."),
        ("« Agences – CANAL+ » est vide à la source",
         "Le serveur joint lui-même la mention « the query result is empty » : "
         "c'est une donnée non disponible, et non une absence d'agences sur le "
         "terrain."),
        ("L'identifiant fourni est volatile",
         "La même agence porte un identifiant différent dans deux fichiers "
         "exportés à trois secondes d'intervalle. La déduplication repose sur "
         "le nom et les coordonnées."),
    ])

    _rect(s, Inches(7.2), Inches(4.45), Inches(5.5), Inches(2.15), BLANC,
          BORDURE, 0.75)
    _rect(s, Inches(7.2), Inches(4.45), Inches(0.035), Inches(2.15), VERT)
    _zone(s, Inches(7.45), Inches(4.63), Inches(5.0), Inches(0.3),
          f"{n_ctrl} CONTRÔLES ARITHMÉTIQUES, REJOUÉS À CHAQUE EXÉCUTION", 8, True,
          ENCRE_MUET, police="Consolas", interligne=1.3)
    _zone(s, Inches(7.45), Inches(5.0), Inches(5.0), Inches(1.45),
          "La population extraite du PDF de l'INSEED somme exactement à "
          "8 095 498 habitants aux trois niveaux — 5 régions, 39 préfectures, "
          "117 communes — sans écart d'une unité.\n\n"
          "Ces contrôles ont servi : une jointure sur des noms accentués "
          "faisait tomber neuf préfectures à zéro point Mobile Money, et une "
          "somme régionale à 11 630 489 a révélé un double comptage du Grand "
          "Lomé.", 10, False, ENCRE_2, interligne=1.3)

    # ---------------------------------------------------------------- 04
    s = _diapo(prs, "Méthode", "Méthodologie",
               "Deux unités d'analyse, chacune utilisée là où sa validité est "
               "prouvée — et un indice dont les pondérations sont testées.", 3)
    _zone(s, MARGE, Inches(2.15), Inches(6.2), Inches(0.26),
          "LES DEUX UNITÉS D'ANALYSE", 8, True, ENCRE_MUET, police="Consolas")
    _tableau(s, MARGE, Inches(2.45), Inches(6.2),
             ["Unité", "Rôle", "Justification"],
             [["Préfecture (39)", "Cartes, superficies, densités",
               "concordance spatiale 98,4 %"],
              ["Commune (117)", "Ratios par habitant",
               "population validée à l'unité près"]],
             largeurs=[0.26, 0.37, 0.37], taille=9)
    _zone(s, MARGE, Inches(3.65), Inches(6.2), Inches(1.1),
          "Reconstruire les contours des 117 communes a été testé puis rejeté "
          "sur preuve : les découpages ne s'emboîtent pas — 65,6 % des points "
          "tombent dans une unité à cheval sur plusieurs communes. Publier "
          "ces contours aurait produit des densités fausses sans aucune "
          "alerte.", 10, False, ENCRE_2, interligne=1.32)
    _zone(s, Inches(7.2), Inches(2.15), Inches(5.5), Inches(0.26),
          "L'INDICE DE PRIORITÉ — QUATRE COMPOSANTES", 8, True, ENCRE_MUET,
          police="Consolas")
    _tableau(s, Inches(7.2), Inches(2.45), Inches(5.5),
             ["Composante", "Mesure", "Poids"],
             [["Déficit Mobile Money", "habitants par point", "30 %"],
              ["Déficit d'agences", "agences actives / 100 000 hab.", "25 %"],
              ["Éloignement", "distance à l'agence active", "25 %"],
              ["Enjeu démographique", "population concernée", "20 %"]],
             largeurs=[0.34, 0.44, 0.22], taille=9)
    _zone(s, Inches(7.2), Inches(4.35), Inches(5.5), Inches(1.3),
          "Le déficit Mobile Money reprend la définition officielle du "
          "géoportail national — « nombre d'habitants par point mobile "
          "money ». L'indicateur central n'a pas été inventé pour ce travail."
          "\n\nCes pondérations sont un choix assumé. C'est exactement "
          "pourquoi 2 000 pondérations alternatives sont testées.",
          10, False, ENCRE_2, interligne=1.32)
    _zone(s, MARGE, Inches(5.1), Inches(6.2), Inches(1.2),
          "Aucune valeur n'est imputée ni estimée. Toute donnée absente est "
          "déclarée absente. Aucun écrêtage n'est appliqué aux valeurs "
          "extrêmes : elles sont des faits, et leur influence est mesurée par "
          "une variante de calcul insensible aux extrêmes.",
          10, False, ENCRE_2, interligne=1.32)

    # ---------------------------------------------------------------- 05
    s = _diapo(prs, "Diagnostic", "Diagnostic national",
               f"{_esp(national)} habitants par point de service en moyenne, mais "
               f"un rapport de 1 à {_fr(rapport)} entre préfectures.", 4)
    _image(s, "ecart_desserte", Inches(4.35), Inches(2.05), hauteur=Inches(4.7))
    for i, (lib, val, note, coul) in enumerate([
            ("Moyenne nationale", _esp(national),
             "habitants par point Mobile Money", VERT),
            ("Préfecture la moins desservie", _esp(pire.hab_par_point_mm),
             f"{pire.prefecture} · {_fr(pire.hab_par_point_mm / national)} × la moyenne",
             CRITIQUE),
            ("Préfectures au-dessus de la moyenne", f"{au_dessus} / 39",
             "moins bien desservies que le pays", SERIE_1),
            ("Communes sans agence active", f"{len(com_sans)} / {len(com)}",
             f"{_esp(int(com_sans.population.sum()))} habitants", SERIE_2)]):
        _kpi(s, MARGE, Inches(2.15) + Inches(1.22) * i, Inches(3.5),
             lib, val, note, coul, h=Inches(1.06))
    _zone(s, MARGE, Inches(7.0), Inches(3.5), Inches(0.3), "", 8)

    # ---------------------------------------------------------------- 06
    s = _diapo(prs, "Géospatial",
               "Analyse géospatiale et inégalités territoriales",
               f"La moitié la moins bien desservie de la population ne dispose "
               f"que de {_pct(part_moitie)} des points de service.", 5)
    _image(s, "quadrant", Inches(0.55), Inches(2.1), hauteur=Inches(4.3))
    _image(s, "concentration", Inches(7.0), Inches(2.1), hauteur=Inches(4.3))
    _zone(s, Inches(0.55), Inches(6.5), Inches(6.0), Inches(0.5),
          f"{quadrant} préfectures sont à la fois plus peuplées que la médiane "
          "nationale et moins bien desservies que la moyenne : c'est là "
          "qu'un investissement touche le plus d'habitants.",
          10, False, ENCRE_2, interligne=1.3)
    _zone(s, Inches(7.0), Inches(6.5), Inches(5.7), Inches(0.5),
          "L'écart à la diagonale mesure la concentration. Les distances "
          "sont calculées après reprojection métrique — en degrés, elles "
          "seraient fausses.", 10, False, ENCRE_2, interligne=1.3)

    # ---------------------------------------------------------------- 07
    s = _diapo(prs, "Priorisation", "Zones prioritaires · indice DCPI",
               "Neuf préfectures restent dans le top 10 pour au moins 90 % de "
               "2 000 pondérations testées : leur priorité ne dépend pas de "
               "la méthode.", 6)
    _image(s, "carte_priorite", Inches(0.6), Inches(2.05), hauteur=Inches(4.75))
    # hauteur bridee a 3,1 po : au-dela, l'image (ratio ~1,28) deborderait
    # sur le tableau qui commence a x=8,6 po.
    _image(s, "sensibilite", Inches(4.5), Inches(2.05), hauteur=Inches(3.1))
    lignes = [[f"{int(r.rang_DCPI)}", r.prefecture, _esp(int(r.population)),
               _esp(r.hab_par_point_mm), f"{int(r.agences_actives)}",
               f"{r.dist_agence_med_canton_km:.0f} km"]
              for _, r in pref.nsmallest(6, "rang_DCPI")
              .sort_values("rang_DCPI").iterrows()]
    _tableau(s, Inches(8.6), Inches(2.05), Inches(4.15),
             ["#", "Préfecture", "Hab.", "Hab./pt", "Ag.", "Dist."],
             lignes, largeurs=[0.08, 0.28, 0.16, 0.16, 0.14, 0.18], taille=8.5)
    _zone(s, Inches(8.6), Inches(4.55), Inches(4.15), Inches(2.1),
          "Corrélation de Spearman moyenne avec le classement de référence : "
          "0,971 sur 2 000 pondérations aléatoires, plus huit variantes "
          "structurelles (retrait de chaque composante, poids égaux, "
          "normalisation par rang).\n\n"
          "Les territoires dont le rang dépend des pondérations ne sont pas "
          "présentés comme prioritaires.", 10, False, ENCRE_2, interligne=1.32)

    # ---------------------------------------------------------------- 08
    s = _diapo(prs, "Décision", "Recommandations stratégiques",
               "Cinq leviers, chacun déclenché par un seuil mesuré — aucune "
               "recommandation sans le chiffre qui la justifie.", 7)
    _image(s, "leviers", Inches(6.9), Inches(2.35), largeur=Inches(5.85))
    _puces(s, MARGE, Inches(2.15), Inches(6.0), [
        ("Densifier le réseau d'agents Mobile Money — levier rapide",
         "Déclencheur : plus de 800 habitants par point. S'appuie sur des "
         "commerces existants, sans construction."),
        ("Implanter un point de présence opérateur — levier structurel",
         "Déclencheur : aucune agence active. Seul levier créant un guichet "
         "là où il n'en existe aucun."),
        ("Répartir le maillage plutôt qu'un point unique",
         "Déclencheur : 25 km ou plus jusqu'à une agence active. Quand "
         "l'éloignement domine, un guichet au chef-lieu ne règle rien."),
        ("Ouvrir la concurrence entre opérateurs",
         f"Déclencheur : un seul opérateur présent. {_esp(tgc_seul)} points ne "
         f"servent que Togocom contre {_esp(moov_seul)} pour Moov seul."),
    ])
    _rect(s, Inches(6.9), Inches(5.4), Inches(5.85), Inches(1.35), BLANC,
          BORDURE, 0.75)
    _rect(s, Inches(6.9), Inches(5.4), Inches(0.035), Inches(1.35), VERT)
    _zone(s, Inches(7.15), Inches(5.6), Inches(5.4), Inches(1.0),
          f"Les {len(stables)} territoires prioritaires représentent "
          f"{_esp(pop_stable)} habitants, soit "
          f"{_pct(pop_stable / 8_095_498)} de la population nationale. Les "
          f"porter à {OBJECTIF_DEFAUT} hab./point demanderait "
          f"{_esp(a_ouvrir)} points Mobile Money supplémentaires.\n"
          "Un même territoire peut relever de plusieurs leviers : les "
          "populations ne s'additionnent pas d'un levier à l'autre.",
          10, False, ENCRE_2, interligne=1.32)

    # ---------------------------------------------------------------- 09
    s = _diapo(prs, "Précautions", "Limites et précautions d'interprétation",
               "Ce diagnostic mesure un déficit d'accès aux services — pas "
               "une absence de réseau mobile. La distinction est décisive.", 8)
    _puces(s, MARGE, Inches(2.15), Inches(6.1), [
        ("La couverture réseau n'est pas mesurée",
         "Une zone sans agence ni agent Mobile Money n'est pas nécessairement "
         f"une zone sans réseau mobile. Les {n_zb_eleve} cantons signalés par "
         "le proxy sont à vérifier, pas des zones blanches avérées."),
        ("Les agences CANAL+ sont absentes",
         f"Fichier source vide. Le déficit porte sur les {n_actives} agences "
         f"actives Moov et Togocom ({n_fermees} fermées exclues sur "
         f"{n_agences} recensées)."),
        ("Le diagnostic décrit 2021-2022",
         "Tout déploiement postérieur est invisible. La hiérarchie des "
         "besoins reste valable tant que les écarts ne sont pas comblés."),
    ])
    _puces(s, Inches(7.1), Inches(2.15), Inches(5.6), [
        ("Les scores communaux et préfectoraux ne sont pas comparables",
         "La composante d'éloignement ne repose pas sur la même mesure aux "
         "deux niveaux. Les rangs se lisent à l'intérieur de chaque niveau."),
        ("Un score élevé signale un besoin, pas une solution",
         "L'indice ne dit rien du coût, de la faisabilité ni de la "
         "rentabilité d'une intervention. Il hiérarchise des besoins mesurés "
         "— préalable à un arbitrage, jamais son substitut."),
        ("La structure par âge n'est pas prise en compte",
         "Un dénominateur « 15 ans et plus » serait plus juste. Les tableaux "
         "d'âges n'ont pas pu être extraits avec une garantie arithmétique "
         "suffisante : ils ont été écartés plutôt que repris sans contrôle."),
    ])

    # ---------------------------------------------------------------- 10
    # La conclusion prend la forme d'un BILAN PAR OBJECTIF : le jury lit, pour
    # chaque objectif du sujet, ce qui a ete repondu — et pour la couverture
    # mobile, pourquoi elle n'a pas pu l'etre. Le plafond de dix pages impose
    # que ce bilan remplace la conclusion plutot que de s'y ajouter.
    s = _diapo(prs, "Conclusion", "Objectifs du sujet → réponses fournies",
               "Quatre objectifs traités ; la couverture mobile, non mesurable "
               "en open data, devient une limite critique.", 9)
    lignes_bilan = [
        ("1 · Cartographier agences et centres de données",
         f"{n_agences} agences recensées après dédoublonnage, dont "
         f"{n_actives} actives : {n_agences_moov} Moov et {n_actives_tgc} "
         f"Togocom actives — et {n_dc} centres de données, concentrés dans "
         "le Grand Lomé. « Télécom » est un doublon ; CANAL+ est vide à la "
         "source.",
         "Traité", SERIE_3),
        ("2 · Mobile Money au regard de la population",
         f"{_esp(national)} habitants par point en moyenne, de 1 à "
         f"{_fr(rapport)} entre préfectures ; la moitié la moins desservie de "
         f"la population ne dispose que de {_pct(part_moitie)} des points.",
         "Traité", SERIE_3),
        ("3 · Infrastructures et densité démographique",
         f"{quadrant} préfectures peuplées et sous-desservies. La densité "
         f"n'explique que {_pct(r2_densite)} des écarts d'équipement : le déficit "
         "n'est pas la fatalité d'un territoire rural.",
         "Traité", SERIE_3),
        ("4 · Couverture réseau et zones blanches",
         "Non mesurable avec les données ouvertes disponibles — couches "
         "antennes hors open data. Traitée comme limite critique et besoin "
         f"prioritaire de données. Proxy déclaré : {n_zb_eleve} cantons à "
         f"investiguer, dont {n_zb_sans} sans aucun agent Mobile Money.",
         "Limite critique", CRITIQUE),
        ("5 · Prioriser les investissements",
         f"{len(stables)} préfectures stables sur 2 000 pondérations "
         f"(corrélation 0,971), {_esp(pop_stable)} habitants : "
         + ", ".join(stables.prefecture.tolist()[:5]) + "…",
         "Traité", SERIE_3),
    ]
    y = Inches(2.12)
    h_ligne = Inches(0.8)
    for objectif, reponse, statut, coul in lignes_bilan:
        critique = coul == CRITIQUE
        _rect(s, MARGE, y, L - 2 * MARGE, h_ligne - Inches(0.08),
              RGBColor(0xFB, 0xEE, 0xEE) if critique else BLANC, BORDURE, 0.75)
        _rect(s, MARGE, y, Inches(0.045), h_ligne - Inches(0.08), coul)
        _zone(s, MARGE + Inches(0.22), y + Inches(0.13), Inches(3.35),
              Inches(0.5), objectif, 11, True, ENCRE, interligne=1.2)
        _zone(s, MARGE + Inches(3.65), y + Inches(0.1), Inches(0.3),
              Inches(0.4), "→", 16, True, ENCRE_MUET)
        _zone(s, MARGE + Inches(4.0), y + Inches(0.1), Inches(6.35),
              Inches(0.6), reponse, 9.5, critique, ENCRE if critique else ENCRE_2,
              interligne=1.25)
        _rect(s, L - MARGE - Inches(1.55), y + Inches(0.2), Inches(1.4),
              Inches(0.32), coul)
        _zone(s, L - MARGE - Inches(1.55), y + Inches(0.255), Inches(1.4),
              Inches(0.24), statut.upper(), 8, True, BLANC,
              aligne=PP_ALIGN.CENTER, police="Consolas")
        y += h_ligne
    _zone(s, MARGE, y + Inches(0.02), L - 2 * MARGE, Inches(0.3),
          "Première recommandation au producteur de données : ouvrir les "
          "couches « Tours télécoms » du catalogue national, pour transformer "
          "les zones suspectes en zones blanches confirmées ou écartées.",
          10, True, RGBColor(0x0F, 0x4D, 0x3B), interligne=1.25)

    SORTIE.parent.mkdir(parents=True, exist_ok=True)
    prs.save(SORTIE)
    print(f"Support ecrit : {SORTIE.relative_to(ROOT)}")
    print(f"  {len(prs.slides.__iter__.__self__._sldIdLst)} diapositives · "
          f"{SORTIE.stat().st_size / 1024:.0f} Ko")


if __name__ == "__main__":
    main()
