"""
Charte graphique du tableau de bord.

DEUX SYSTEMES DE COULEUR, VOLONTAIREMENT DISJOINTS
---------------------------------------------------
1. L'INTERFACE (chrome) porte l'identite institutionnelle : vert #156c52,
   repris des armoiries de la Republique togolaise. Il n'apparait JAMAIS dans
   un graphique — ainsi un aplat de navigation ne peut pas etre confondu avec
   une serie de donnees.

2. LES DONNEES utilisent la palette validee du projet. Trois emplacements
   categoriels (bleu, orange, aqua) verifies par le validateur en mode
   all-pairs : bande de luminosite OK, plancher de chroma OK, separation
   daltonisme minimale dE 9.2, plancher vision normale 24.0. L'aqua etant
   sous 3:1 de contraste sur fond clair, chaque graphique porte des
   etiquettes directes et une vue tableau.

Regles tenues partout : sequentiel = une teinte claire -> foncee ; la couleur
suit l'entite et jamais son rang ; emphase (une couleur + gris) des que le
sujet est « ce territoire se detache » ; jamais deux axes y.
"""

from __future__ import annotations

import base64
from pathlib import Path

import plotly.graph_objects as go
import plotly.io as pio

# =============================================================================
# IDENTITE INSTITUTIONNELLE (interface uniquement)
# =============================================================================
VERT = "#156c52"          # vert des armoiries — accent de navigation
VERT_CLAIR = "#e8f2ee"
VERT_SOMBRE = "#0f4d3b"
OR = "#ffce15"            # or des armoiries — liseres fins uniquement
ROUGE = "#d21b33"

# =============================================================================
# PALETTE DE DONNEES (validee)
# =============================================================================
SERIE_1 = "#2a78d6"       # bleu
SERIE_2 = "#eb6834"       # orange
SERIE_3 = "#1baf7a"       # aqua
CATEGORIEL = [SERIE_1, SERIE_2, SERIE_3]

SEQUENTIEL = ["#cde2fb", "#b7d3f6", "#9ec5f4", "#86b6ef", "#6da7ec",
              "#5598e7", "#3987e5", "#2a78d6", "#256abf", "#1c5cab",
              "#184f95", "#104281", "#0d366b"]

STATUT = {"bon": "#0ca30c", "attention": "#fab219",
          "serieux": "#ec835a", "critique": "#d03b3b"}

# =============================================================================
# SURFACES ET ENCRE
# =============================================================================
SURFACE = "#ffffff"
PLAN = "#f7f7f5"
BORDURE = "#e6e5e0"
ENCRE = "#12120f"
ENCRE_2 = "#55544f"
ENCRE_MUET = "#8b8a84"
GRILLE = "#eeede8"
AXE = "#d5d4ce"
GRIS_FOND = "#d9d8d2"

# =============================================================================
# TYPOGRAPHIE
# =============================================================================
# INTER pour tout ce qui se lit, IBM PLEX MONO pour tout ce qui s'etiquette.
#
# Pourquoi pas la police systeme ? Parce qu'un tableau de bord de decision
# affiche surtout des NOMBRES, et que les chiffres doivent s'aligner en colonne
# d'une ligne a l'autre. Inter possede des chiffres a chasse fixe (`tnum`) que
# les polices systeme n'exposent pas de facon fiable : sans eux, « 1 621 720 »
# et « 8 095 498 » n'ont pas la meme largeur, et une colonne de valeurs se met
# a danser. Inter offre aussi un `1` a empattement et un `l` a queue (`cv05`,
# `cv08`) : un l et un 1 ne se confondent plus dans un identifiant.
#
# IBM Plex Mono est dessine pour s'accorder a une grotesque humaniste. Il porte
# les sur-titres, les etiquettes et les mentions de source — tout ce qui doit
# etre lu comme une METADONNEE et non comme un propos.
#
# Chaque famille garde une pile de repli complete : si les fontes Google ne
# repondent pas, la mise en page tient sur les polices du systeme.
POLICES_WEB = ("https://fonts.googleapis.com/css2?"
               "family=Inter:wght@400;500;600;700&"
               "family=IBM+Plex+Mono:wght@400;500;600&display=swap")

SANS = "'Inter', system-ui, -apple-system, \"Segoe UI\", Roboto, sans-serif"
MONO = ("'IBM Plex Mono', ui-monospace, \"SF Mono\", \"Cascadia Mono\", "
        "Menlo, Consolas, monospace")

# Chiffres a chasse fixe + `1` et `l` differencies. Applique partout ou une
# valeur est censee s'aligner sur celle du dessus.
CHIFFRES = "font-feature-settings: 'tnum' 1, 'cv05' 1, 'cv08' 1; font-variant-numeric: tabular-nums;"

ASSETS = Path(__file__).resolve().parent / "assets"


def armoiries_data_uri() -> str:
    svg = (ASSETS / "armoiries.svg").read_bytes()
    return "data:image/svg+xml;base64," + base64.b64encode(svg).decode()


# =============================================================================
# TEMPLATE PLOTLY
# =============================================================================
def enregistrer_template() -> str:
    t = go.layout.Template()
    t.layout = go.Layout(
        font=dict(family=SANS, size=12.5, color=ENCRE_2),
        title=dict(font=dict(size=14, color=ENCRE), x=0, xanchor="left"),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        colorway=CATEGORIEL,
        margin=dict(l=6, r=6, t=28, b=6),
        xaxis=dict(gridcolor=GRILLE, linecolor=AXE, zerolinecolor=AXE,
                   tickfont=dict(color=ENCRE_MUET, size=11),
                   title_font=dict(color=ENCRE_MUET, size=11), showgrid=False),
        yaxis=dict(gridcolor=GRILLE, linecolor=AXE, zerolinecolor=AXE,
                   tickfont=dict(color=ENCRE_MUET, size=11),
                   title_font=dict(color=ENCRE_MUET, size=11), gridwidth=1),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0,
                    font=dict(color=ENCRE_2, size=11), title_text=""),
        hoverlabel=dict(font=dict(family=SANS, size=12), bgcolor=SURFACE,
                        bordercolor=AXE),
    )
    pio.templates["togo"] = t
    pio.templates.default = "togo"
    return "togo"


# =============================================================================
# CSS
# =============================================================================
CSS = f"""
<style>
  @import url('{POLICES_WEB}');

  html, body, .stApp, [class*="st-"] {{ font-family: {SANS}; }}
  .stApp {{ background: {PLAN}; -webkit-font-smoothing: antialiased;
            -moz-osx-font-smoothing: grayscale; }}
  .block-container {{ padding: 0 2.2rem 3rem 2.2rem; max-width: 1680px; }}
  header[data-testid="stHeader"] {{ background: transparent; height: 0; }}
  #MainMenu, footer {{ visibility: hidden; }}

  h1, h2, h3, h4 {{ font-family: {SANS}; color: {ENCRE};
                    letter-spacing: -0.018em; margin: 0; }}

  /* ---------- bandeau d'en-tete ---------- */
  .bandeau {{
      border-top: 3px solid {VERT};
      background: {SURFACE};
      border-bottom: 1px solid {BORDURE};
      margin: 0 -2.2rem 1.4rem -2.2rem;
      padding: 1.4rem 2.2rem 1.5rem 2.2rem;
      display: flex; align-items: flex-start; justify-content: space-between;
      gap: 2rem;
  }}
  .eyebrow {{
      font-family: {MONO}; font-size: 0.66rem; letter-spacing: 0.16em;
      text-transform: uppercase; color: {ENCRE_MUET}; margin-bottom: 0.45rem;
  }}
  .bandeau h1 {{ font-size: 1.95rem; font-weight: 660; line-height: 1.08;
                 letter-spacing: -0.024em; }}
  .bandeau .sous {{
      font-size: 0.92rem; color: {ENCRE_2}; margin-top: 0.5rem;
      max-width: 62ch; line-height: 1.5;
  }}
  .inst {{ text-align: right; display: flex; align-items: center; gap: 1rem; }}
  .inst-txt {{ font-family: {MONO}; font-size: 0.68rem; line-height: 1.7;
               color: {ENCRE_2}; letter-spacing: 0.03em; white-space: nowrap; }}
  .inst-txt .b {{ color: {ENCRE}; font-weight: 600; }}
  .inst img {{ height: 62px; width: auto; }}

  /* ---------- cartes ---------- */
  .carte {{
      background: {SURFACE}; border: 1px solid {BORDURE}; border-radius: 12px;
      padding: 1.05rem 1.25rem 1.15rem 1.25rem; height: 100%;
  }}
  .carte-t {{
      font-family: {MONO}; font-size: 0.66rem; letter-spacing: 0.13em;
      text-transform: uppercase; color: {ENCRE_MUET}; margin-bottom: 0.7rem;
  }}

  /* ---------- indicateurs ---------- */
  .kpi {{
      background: {SURFACE}; border: 1px solid {BORDURE}; border-radius: 12px;
      padding: 0.95rem 1.15rem 1rem 1.15rem; height: 100%;
  }}
  .kpi .lib {{
      font-family: {MONO}; font-size: 0.62rem; letter-spacing: 0.12em;
      text-transform: uppercase; color: {ENCRE_MUET}; line-height: 1.5;
      min-height: 2.1em; display: block;
  }}
  .kpi .val {{ font-size: 2.15rem; font-weight: 680; color: {ENCRE};
               line-height: 1.05; margin-top: 0.25rem;
               letter-spacing: -0.022em; {CHIFFRES} }}
  .kpi .unite {{ font-size: 0.92rem; font-weight: 500; color: {ENCRE_2};
                 margin-left: 0.28rem; }}
  .kpi .note {{ font-size: 0.74rem; color: {ENCRE_2}; margin-top: 0.55rem;
                display: flex; align-items: center; gap: 0.4rem;
                line-height: 1.45; }}
  .pastille {{ width: 7px; height: 7px; border-radius: 50%;
               display: inline-block; flex: 0 0 7px; }}

  /* ---------- chiffre hero ---------- */
  .hero-val {{ font-size: 4.1rem; font-weight: 700; color: {ENCRE};
               line-height: 0.98; letter-spacing: -0.038em; {CHIFFRES} }}
  .hero-un {{ font-size: 1.15rem; font-weight: 500; color: {ENCRE_2};
              margin-left: 0.45rem; }}
  .hero-txt {{ font-size: 0.95rem; color: {ENCRE_2}; line-height: 1.62;
               margin-top: 0.85rem; max-width: 46ch; }}
  .hero-txt b {{ color: {ENCRE}; font-weight: 620; }}

  /* ---------- question et lecture ---------- */
  .question {{ font-size: 1rem; font-weight: 620; color: {ENCRE};
               margin: 0 0 0.1rem 0; }}
  .lecture {{
      font-size: 0.86rem; color: {ENCRE_2}; line-height: 1.6;
      border-left: 2px solid {VERT}; padding-left: 0.85rem;
      margin: 0.7rem 0 0.3rem 0;
  }}
  .lecture b {{ color: {ENCRE}; }}
  .source {{ font-family: {MONO}; font-size: 0.66rem; color: {ENCRE_MUET};
             letter-spacing: 0.04em; margin-top: 0.5rem; line-height: 1.6; }}

  /* ---------- bandeau d'action ---------- */
  .action {{
      background: {VERT_CLAIR}; border-left: 3px solid {VERT};
      border-radius: 0 8px 8px 0; padding: 0.85rem 1.1rem;
      font-size: 0.88rem; color: {ENCRE}; line-height: 1.6;
  }}
  .action b {{ color: {VERT_SOMBRE}; }}

  /* ---------- rangee de priorite ---------- */
  .prio {{
      background: {SURFACE}; border: 1px solid {BORDURE};
      border-left: 3px solid {VERT}; border-radius: 0 10px 10px 0;
      padding: 0.85rem 1.1rem; margin-bottom: 0.55rem;
      display: flex; align-items: center; gap: 1.1rem;
  }}
  .prio .rang {{ font-family: {MONO}; font-size: 1.3rem; font-weight: 600;
                 color: {VERT}; min-width: 2.1rem; {CHIFFRES} }}
  .prio .nom {{ font-size: 1rem; font-weight: 620; color: {ENCRE};
                min-width: 9.5rem; }}
  .prio .det {{ font-size: 0.8rem; color: {ENCRE_2}; line-height: 1.5; }}
  .prio .det b {{ color: {ENCRE}; }}

  /* ---------- barre laterale ---------- */
  section[data-testid="stSidebar"] {{
      background: {SURFACE}; border-right: 1px solid {BORDURE};
  }}
  section[data-testid="stSidebar"] > div {{ padding-top: 1.1rem; }}
  .sb-titre {{ font-size: 1.02rem; font-weight: 660; color: {ENCRE};
               line-height: 1.25; }}
  .sb-sous {{ font-family: {MONO}; font-size: 0.62rem; letter-spacing: 0.14em;
              text-transform: uppercase; color: {ENCRE_MUET};
              margin-top: 0.2rem; }}
  .sb-groupe {{ font-family: {MONO}; font-size: 0.6rem; letter-spacing: 0.15em;
                text-transform: uppercase; color: {ENCRE_MUET};
                margin: 1.1rem 0 0.3rem 0; }}
  .sb-pied {{ font-family: {MONO}; font-size: 0.6rem; color: {ENCRE_MUET};
              line-height: 1.9; letter-spacing: 0.03em;
              border-top: 1px solid {BORDURE}; padding-top: 0.8rem;
              margin-top: 0.9rem; }}

  section[data-testid="stSidebar"] div[role="radiogroup"] > label {{
      padding: 0.36rem 0.55rem; border-radius: 7px; border-left: 2px solid transparent;
  }}
  section[data-testid="stSidebar"] div[role="radiogroup"] > label:hover {{
      background: {PLAN};
  }}
  section[data-testid="stSidebar"] div[role="radiogroup"] input:checked + div {{
      color: {VERT_SOMBRE} !important; font-weight: 620;
  }}

  /* ---------- divers ---------- */
  div[data-testid="stDataFrame"] {{ {CHIFFRES} }}
  div[data-testid="stMetricValue"] {{ {CHIFFRES} }}
  div[data-testid="stExpander"] {{ border: 1px solid {BORDURE};
                                   border-radius: 10px; background: {SURFACE}; }}
  .stTabs [data-baseweb="tab-list"] {{ gap: 1.4rem; border-bottom: 1px solid {BORDURE}; }}
  .stTabs [data-baseweb="tab"] {{ font-size: 0.88rem; padding: 0.45rem 0; }}
  .stTabs [aria-selected="true"] {{ color: {VERT_SOMBRE} !important; }}
  hr {{ border-color: {BORDURE}; }}
</style>
"""


# =============================================================================
# FRAGMENTS
# =============================================================================
def bandeau(eyebrow: str, titre: str, question: str) -> str:
    return f"""
    <div class="bandeau">
      <div>
        <div class="eyebrow">{eyebrow}</div>
        <h1>{titre}</h1>
        <div class="sous">{question}</div>
      </div>
      <div class="inst">
        <div class="inst-txt">
          <span class="b">République togolaise</span><br>
          Défi Économie numérique<br>
          Données ouvertes · 2021-2022
        </div>
        <img src="{armoiries_data_uri()}" alt="Armoiries du Togo">
      </div>
    </div>
    """


def kpi(libelle: str, valeur: str, unite: str = "", note: str = "",
        couleur: str = VERT) -> str:
    u = f'<span class="unite">{unite}</span>' if unite else ""
    n = (f'<div class="note"><span class="pastille" '
         f'style="background:{couleur}"></span><span>{note}</span></div>'
         if note else "")
    return (f'<div class="kpi"><span class="lib">{libelle}</span>'
            f'<div class="val">{valeur}{u}</div>{n}</div>')


def carte_ouvre(titre: str) -> str:
    return f'<div class="carte"><div class="carte-t">{titre}</div>'


def question(texte: str) -> str:
    return f'<div class="question">{texte}</div>'


def lecture(texte: str) -> str:
    return f'<div class="lecture">{texte}</div>'


def source(texte: str) -> str:
    return f'<div class="source">{texte}</div>'


def action(texte: str) -> str:
    return f'<div class="action">{texte}</div>'


def ligne_priorite(rang: int, nom: str, detail: str) -> str:
    return (f'<div class="prio"><div class="rang">{rang:02d}</div>'
            f'<div class="nom">{nom}</div><div class="det">{detail}</div></div>')
