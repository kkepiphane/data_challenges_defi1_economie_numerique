"""
PAGE DE GARDE ET PAGE DE FIN DU SUPPORT
========================================
Une couverture de rapport public a un seul travail : faire qu'un decideur qui
n'ouvrira peut-etre que cette page reparte avec la these et un ordre de
grandeur. Elle n'annonce pas un sujet — elle annonce un resultat.

CE QUI EST TENU ICI
-------------------
1. UN TITRE QUI AFFIRME.  « Diagnostic de la connectivite » nomme un dossier.
   « Connecter le Togo la ou le manque est prouve » engage une these, et le
   reste du support la demontre.

2. TROIS CHIFFRES, PAS DIX.  Trois reperes tiennent dans une memoire courte :
   la moyenne, l'ecart qu'elle cache, le nombre de territoires a zero agence.
   Un quatrieme ferait perdre les trois premiers.

3. UNE HIERARCHIE QUI SE LIT SANS EFFORT.  Quatre niveaux seulement — sur-titre,
   titre, these, chiffres — separes par des ECARTS, pas par des traits. Chaque
   filet present ici a une fonction : le tricolore signe l'institution, l'or
   ferme le titre, le filet clair ouvre la bande de chiffres.

4. UN INTERLETTRAGE REEL.  Les capitales sans interlettrage se lisent mal en
   petit corps. PowerPoint sait le faire, python-pptx ne l'expose pas : on
   ecrit l'attribut `spc` directement dans le XML du run.

LA POLICE — UN ARBITRAGE, PAS UN GOUT
--------------------------------------
python-pptx ne sait PAS incorporer une police dans le fichier. Toute police
absente du poste qui ouvre le fichier est remplacee par Calibri, et la mise en
page saute. Un support remis a un jury doit donc s'en tenir a une police
reellement installee partout — sous Windows, c'est Segoe UI.

Le tableau de bord, lui, charge Inter depuis le web : meme squelette humaniste,
memes proportions, memes graisses. Les deux livrables se ressemblent sans que
le support parie sur une installation.
"""

from __future__ import annotations

from pathlib import Path

from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt

ROOT = Path(__file__).resolve().parents[1]
ARMOIRIES_SVG = ROOT / "dashboard" / "assets" / "armoiries.svg"
ARMOIRIES_PNG = ROOT / "reports" / "figures" / "armoiries.png"

L, H = Inches(13.333), Inches(7.5)

# --- palette de la couverture ------------------------------------------------
# Le vert est volontairement PLUS SOMBRE que le vert d'interface (#156C52) :
# sur un aplat pleine page, un vert de navigation devient criard et le texte
# blanc y perd en contraste. #0D3A2C porte un rapport de 12,9:1 avec le blanc.
FOND = RGBColor(0x0D, 0x3A, 0x2C)
BLANC = RGBColor(0xFF, 0xFF, 0xFF)
TEXTE_CLAIR = RGBColor(0xCB, 0xDE, 0xD6)      # corps sur fond sombre — 9,4:1
TEXTE_MUET = RGBColor(0x8E, 0xB6, 0xA6)       # etiquettes — 5,6:1
TEXTE_TENU = RGBColor(0x6D, 0x9A, 0x89)       # mention de source — 3,6:1
OR = RGBColor(0xFF, 0xCE, 0x15)
ROUGE = RGBColor(0xD2, 0x1B, 0x33)
VERT_INSTITUTION = RGBColor(0x15, 0x6C, 0x52)
VERT_FILET = RGBColor(0x1B, 0x5E, 0x49)       # filets sur fond vert

SANS = "Segoe UI"
MARGE = Inches(0.95)


# =============================================================================
# PRIMITIVES
# =============================================================================
def _spc(run, points: float) -> None:
    """Interlettrage. `spc` s'exprime en centiemes de point, comme `sz`."""
    run.font._rPr.set("spc", str(int(round(points * 100))))


def texte(slide, x, y, w, h, contenu, taille, couleur, gras=False,
          interligne=1.2, interlettrage=0.0, aligne=PP_ALIGN.LEFT,
          police=SANS):
    tb = slide.shapes.add_textbox(x, y, w, h)
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    for i, ligne in enumerate(contenu.split("\n")):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = aligne
        p.line_spacing = interligne
        r = p.add_run()
        r.text = ligne
        r.font.size = Pt(taille)
        r.font.bold = gras
        r.font.color.rgb = couleur
        r.font.name = police
        if interlettrage:
            _spc(r, interlettrage)
    return tb


def filet(slide, x, y, w, h, couleur):
    f = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, x, y, w, h)
    f.shadow.inherit = False
    f.fill.solid()
    f.fill.fore_color.rgb = couleur
    f.line.fill.background()
    return f


def bande_tricolore(slide, y=0, epaisseur=Inches(0.06)):
    """Signature institutionnelle, reprise a l'identique sur chaque page."""
    filet(slide, 0, y, L * 0.62, epaisseur, VERT_INSTITUTION)
    filet(slide, L * 0.62, y, L * 0.19, epaisseur, OR)
    filet(slide, L * 0.81, y, L * 0.19, epaisseur, ROUGE)


# =============================================================================
# ARMOIRIES
# =============================================================================
# Le SVG du depot dessine le listel VIDE : la devise n'y est pas un trace.
# Elle est donc composee ici, a la place exacte qu'elle occupe sur les armoiries
# officielles — deux mots sur l'arc, un mot dans le cartouche central.
#
# Geometrie MESUREE sur le rendu, pas estimee : l'arc du listel a ete ajuste
# par les moindres carres sur les pixels de son trace (residu inferieur a 1 px),
# ce qui donne un centre a (450, 472) et un rayon median de 330 px pour une
# image de 900 px de large. Toutes les valeurs ci-dessous sont exprimees dans
# ce repere, puis mises a l'echelle.
DEVISE = ("TRAVAIL", "LIBERTÉ", "PATRIE")
_ARC_CENTRE = (450.0, 472.0)      # centre du cercle du listel
_ARC_RAYON = 330.0                # rayon median de la bande
_ARC_ANGLES = (-38.0, 38.0)       # angle, en degres, du milieu de chaque mot
_CARTOUCHE = (450.0, 151.0)       # centre du cartouche central
_CORPS = 30.0                     # corps de la devise
_REFERENCE = 900.0                # largeur pour laquelle ces valeurs valent


def _police(taille: int):
    from PIL import ImageFont
    for chemin in (r"C:\Windows\Fonts\segoeuib.ttf",
                   r"C:\Windows\Fonts\arialbd.ttf",
                   "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"):
        if Path(chemin).exists():
            return ImageFont.truetype(chemin, taille)
    return None


def _mot_sur_arc(image, mot, angle_milieu, centre, rayon, police):
    """Pose un mot le long d'un arc, lettre a lettre.

    Chaque lettre est rendue seule, tournee de sa propre tangente, puis collee.
    Faire tourner le mot entier d'un seul bloc le ferait decoller du listel des
    la troisieme lettre.
    """
    import math

    from PIL import Image as _Im
    from PIL import ImageDraw as _Dr

    mesure = _Dr.Draw(_Im.new("RGB", (1, 1)))
    largeurs = [mesure.textlength(c, font=police) for c in mot]
    # Un leger interlettrage : sur un arc, les lettres se resserrent a la base.
    ecart = police.size * 0.09
    total = sum(largeurs) + ecart * (len(mot) - 1)

    angle = math.radians(angle_milieu) - (total / rayon) / 2
    for lettre, largeur in zip(mot, largeurs):
        angle += (largeur / 2) / rayon
        vignette = _Im.new("RGBA", (int(largeur) + 8, police.size + 10),
                           (0, 0, 0, 0))
        _Dr.Draw(vignette).text((4, 2), lettre, font=police,
                                fill=(17, 17, 17, 255))
        tournee = vignette.rotate(-math.degrees(angle), expand=True,
                                  resample=_Im.BICUBIC)
        x = centre[0] + rayon * math.sin(angle)
        y = centre[1] - rayon * math.cos(angle)
        image.paste(tournee, (int(x - tournee.width / 2),
                              int(y - tournee.height / 2)), tournee)
        angle += (largeur / 2 + ecart) / rayon


def _graver_devise(image) -> None:
    """Compose « TRAVAIL LIBERTÉ PATRIE » sur le listel."""
    from PIL import ImageDraw

    e = image.width / _REFERENCE                       # facteur d'echelle
    police = _police(int(round(_CORPS * e)))
    if police is None:
        return
    centre = (_ARC_CENTRE[0] * e, _ARC_CENTRE[1] * e)
    for mot, angle in zip((DEVISE[0], DEVISE[2]), _ARC_ANGLES):
        _mot_sur_arc(image, mot, angle, centre, _ARC_RAYON * e, police)
    ImageDraw.Draw(image).text((_CARTOUCHE[0] * e, _CARTOUCHE[1] * e),
                               DEVISE[1], font=police, fill=(17, 17, 17),
                               anchor="mm")


def armoiries_png(fond: RGBColor = FOND, largeur_px: int = 900):
    """Rasterise les armoiries UNE FOIS, sur la couleur de fond exacte.

    Pas de canal alpha : le fond de la page est un aplat uni, donc peindre le
    dessin directement sur cette couleur donne un bord parfaitement net, la ou
    un PNG transparent redimensionne par PowerPoint laisse un lisere clair.
    """
    if ARMOIRIES_PNG.exists():
        return ARMOIRIES_PNG
    try:
        from reportlab.graphics import renderPM
        from svglib.svglib import svg2rlg
    except ImportError:
        return None                   # le support se construit sans emblème
    dessin = svg2rlg(str(ARMOIRIES_SVG))
    if dessin is None:
        return None
    facteur = largeur_px / dessin.width
    dessin.width *= facteur
    dessin.height *= facteur
    dessin.scale(facteur, facteur)
    ARMOIRIES_PNG.parent.mkdir(parents=True, exist_ok=True)

    from io import BytesIO

    from PIL import Image
    tampon = BytesIO()
    renderPM.drawToFile(dessin, tampon, fmt="PNG",
                        bg=(fond[0] << 16) | (fond[1] << 8) | fond[2])
    image = Image.open(tampon).convert("RGB")
    _graver_devise(image)
    image.save(ARMOIRIES_PNG)
    return ARMOIRIES_PNG


# =============================================================================
# PAGE DE GARDE
# =============================================================================
def page_de_garde(prs, titre, these, reperes, auteur, qualite, sources,
                  surtitre="DÉFI 1 · ÉCONOMIE NUMÉRIQUE · RÉPUBLIQUE TOGOLAISE"):
    """`reperes` : trois triplets (etiquette, valeur, precision). `qualite` :
    ligne sous le nom de l'auteur (role/fonction) — vide pour l'omettre,
    comme sur la version relue par l'auteur (page de garde epuree, le nom
    seul)."""
    s = prs.slides.add_slide(prs.slide_layouts[6])
    filet(s, 0, 0, L, H, FOND)
    bande_tricolore(s)

    colonne = Inches(8.3)                      # largeur de la colonne de texte

    # --- sur-titre ----------------------------------------------------------
    texte(s, MARGE, Inches(1.02), colonne, Inches(0.22), surtitre,
          9.5, TEXTE_MUET, gras=True, interlettrage=1.9)

    # --- titre : la these, en deux lignes, interligne serre -----------------
    texte(s, MARGE, Inches(1.52), colonne, Inches(1.9), titre,
          43, BLANC, gras=True, interligne=1.02, interlettrage=-0.5)

    # --- filet d'or : ferme le titre et ouvre le corps ----------------------
    filet(s, MARGE, Inches(3.42), Inches(0.92), Inches(0.045), OR)

    # --- these developpee ---------------------------------------------------
    texte(s, MARGE, Inches(3.78), Inches(7.9), Inches(1.1), these,
          14, TEXTE_CLAIR, interligne=1.52)

    # --- bande de trois reperes ---------------------------------------------
    y_bande = Inches(5.02)
    filet(s, MARGE, y_bande, Inches(8.95), Pt(0.75), VERT_FILET)
    pas = Inches(3.12)
    for i, (etiquette, valeur, precision) in enumerate(reperes):
        x = MARGE + pas * i
        texte(s, x, y_bande + Inches(0.26), pas - Inches(0.28), Inches(0.24),
              etiquette.upper(), 8.5, TEXTE_MUET, gras=True, interlettrage=1.3)
        texte(s, x, y_bande + Inches(0.55), pas - Inches(0.28), Inches(0.5),
              valeur, 27, BLANC, gras=True, interlettrage=-0.4)
        texte(s, x, y_bande + Inches(1.07), pas - Inches(0.28), Inches(0.24),
              precision, 9, TEXTE_TENU, interligne=1.3)

    # --- signature ----------------------------------------------------------
    y_sig = Inches(6.50)
    texte(s, MARGE, y_sig, Inches(6.2), Inches(0.3), auteur, 14.5, BLANC,
          gras=True)
    if qualite:
        texte(s, MARGE, y_sig + Inches(0.27), Inches(6.2), Inches(0.22),
              qualite.upper(), 8.5, TEXTE_MUET, gras=True, interlettrage=1.3)
    filet(s, MARGE, Inches(7.09), Inches(8.95), Pt(0.75), VERT_FILET)
    texte(s, MARGE, Inches(7.19), Inches(11.45), Inches(0.22),
          sources, 8, TEXTE_TENU, interligne=1.4)

    # --- armoiries ----------------------------------------------------------
    png = armoiries_png()
    if png:
        haut = Inches(3.55)
        s.shapes.add_picture(str(png), L - MARGE - Inches(2.47),
                             (H - haut) / 2 + Inches(0.18), height=haut)
    return s


# =============================================================================
# PAGE DE FIN
# =============================================================================
def page_de_fin(prs, titre, lignes, url, auteur, mention):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    filet(s, 0, 0, L, H, FOND)
    bande_tricolore(s)

    texte(s, MARGE, Inches(1.55), Inches(8.6), Inches(0.22),
          "POUR ALLER PLUS LOIN", 9.5, TEXTE_MUET, gras=True,
          interlettrage=1.9)
    texte(s, MARGE, Inches(2.02), Inches(8.6), Inches(1.0), titre,
          36, BLANC, gras=True, interligne=1.06, interlettrage=-0.4)
    filet(s, MARGE, Inches(3.26), Inches(0.92), Inches(0.045), OR)

    y = Inches(3.68)
    for etiquette, valeur in lignes:
        texte(s, MARGE, y, Inches(2.85), Inches(0.24), etiquette.upper(),
              8.5, TEXTE_MUET, gras=True, interlettrage=1.3)
        texte(s, MARGE + Inches(3.0), y - Inches(0.04), Inches(6.1),
              Inches(0.3), valeur, 12.5, TEXTE_CLAIR, interligne=1.35)
        y += Inches(0.62)

    filet(s, MARGE, Inches(5.72), Inches(9.35), Pt(0.75), VERT_FILET)
    texte(s, MARGE, Inches(5.98), Inches(9.0), Inches(0.3), url, 15, OR,
          gras=True)
    texte(s, MARGE, Inches(6.46), Inches(6.2), Inches(0.3), auteur, 13.5,
          BLANC, gras=True)
    texte(s, MARGE, Inches(6.78), Inches(11.4), Inches(0.22), mention, 8,
          TEXTE_TENU, interligne=1.4)

    png = armoiries_png()
    if png:
        haut = Inches(3.2)
        s.shapes.add_picture(str(png), L - MARGE - Inches(2.23),
                             (H - haut) / 2 + Inches(0.2), height=haut)
    return s
