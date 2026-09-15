"""
Charte graphique du tableau de bord.

REGISTRE : LE RAPPORT IMPRIME, PAS LE TABLEAU DE BORD LOGICIEL
---------------------------------------------------------------
Le parti pris est editorial. Un fond de papier creme, une serif de labeur pour
les titres, des FILETS la ou l'on met d'ordinaire des cadres, et une barre
laterale composee comme le SOMMAIRE du document. L'ecran doit evoquer une piece
que l'on remet a un ministre, pas une console de supervision.

Ce choix n'est pas decoratif : il change ce que le lecteur croit avoir sous les
yeux. Un encadre gris a coins arrondis annonce un logiciel — donc quelque chose
qui se manipule et se parametre. Un filet et une serif annoncent un texte qui
engage son auteur. Ce projet defend des conclusions ; il devait en avoir l'air.

TROIS SYSTEMES DE COULEUR, VOLONTAIREMENT DISJOINTS
----------------------------------------------------
1. LE PAPIER porte l'interface : creme, encre chaude, filets sable. Aucune de
   ces valeurs n'apparait dans un graphique.

2. L'IDENTITE se limite au filet tricolore et aux armoiries. Le vert profond
   #0d3a2c ne sert qu'a marquer la page courante et les filets de titre — c'est
   exactement le vert de la couverture du support, ce qui relie les deux
   livrables sans repeter leur mise en page.

3. LES DONNEES gardent la palette validee du projet : trois emplacements
   categoriels (bleu, orange, aqua) verifies en mode all-pairs — bande de
   luminosite OK, plancher de chroma OK, separation daltonisme minimale
   dE 9.2, plancher vision normale 24.0. L'aqua etant sous 3:1 de contraste
   sur fond clair, chaque graphique porte des etiquettes directes et une vue
   tableau.

Regles tenues partout : sequentiel = une teinte claire -> foncee ; la couleur
suit l'entite et jamais son rang ; emphase (une couleur + gris) des que le
sujet est « ce territoire se detache » ; jamais deux axes y.
"""

from __future__ import annotations

import base64
import itertools
from contextlib import contextmanager
from pathlib import Path

import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st

# =============================================================================
# FORMATAGE DES NOMBRES — notation francaise, PARTOUT
# =============================================================================
# Python formate "12.7" et "20%" par defaut : virgule et espace anglo-saxons.
# Deux fonctions, appelees partout ou un nombre est ecrit dans un texte, pour
# qu'aucune page ne mette a nu le formatage par defaut de Python.
def fr(x: float, dec: int = 1) -> str:
    """Nombre en notation francaise : virgule decimale, espace pour les
    milliers. `fr(1234.5, 1)` -> "1 234,5" ; `fr(409, 0)` -> "409". Espace
    ASCII ordinaire — pas une espace insecable — pour rester coherent avec le
    reste du code (`.replace(",", " ")`, deja partout ailleurs)."""
    entier, _, decimales = f"{x:,.{dec}f}".partition(".")
    entier = entier.replace(",", " ")
    return entier if dec == 0 else f"{entier},{decimales}"


def pct(x: float, dec: int = 0) -> str:
    """Pourcentage en notation francaise : espace avant le signe %.
    `pct(0.271, 0)` -> "27 %" ; l'entree est une FRACTION (0-1)."""
    return f"{fr(x * 100, dec)} %"


def ordinal(n: int) -> str:
    """Ordinal francais : « 1er » pour 1, « 2ᵉ », « 3ᵉ »... au-dela (« ᵉ » en
    exposant, deja l'usage du reste du tableau de bord). Le francais n'a pas
    la meme forme pour le premier rang que pour les suivants — « 1ᵉ » seul
    n'existe pas."""
    return "1er" if n == 1 else f"{n}ᵉ"


# =============================================================================
# PAPIER ET ENCRE
# =============================================================================
# Le fond n'est pas blanc mais CREME. Un blanc pur sur un ecran lumineux fatigue
# a la lecture longue, et surtout il lit « application ». Le creme lit « page ».
PAPIER = "#faf7f2"
SURFACE = "#ffffff"          # reserve aux tableaux, qui sont des surfaces
ENCRE = "#1a1a17"
ENCRE_2 = "#57534a"          # gris CHAUD : un gris neutre jurerait sur le creme
ENCRE_MUET = "#8a8579"
FILET = "#e2dccf"            # filets et bordures
FILET_FORT = "#c9c0ad"

# Conserves sous leurs anciens noms : les pages les citent.
PLAN = PAPIER
BORDURE = FILET
GRILLE = "#ece6da"
AXE = "#cdc5b4"
GRIS_FOND = "#d6cfc0"

# =============================================================================
# IDENTITE INSTITUTIONNELLE (interface uniquement)
# =============================================================================
VERT = "#0d3a2c"             # vert profond — page courante, filets de titre
VERT_CLAIR = "#edf1ee"
VERT_SOMBRE = "#082720"
OR = "#c8a020"               # or des armoiries — liseres fins uniquement
ROUGE = "#a3202f"

# =============================================================================
# PALETTE DE DONNEES (validee — inchangee)
# =============================================================================
SERIE_1 = "#2a78d6"          # bleu
SERIE_2 = "#eb6834"          # orange
SERIE_3 = "#1baf7a"          # aqua
CATEGORIEL = [SERIE_1, SERIE_2, SERIE_3]

SEQUENTIEL = ["#cde2fb", "#b7d3f6", "#9ec5f4", "#86b6ef", "#6da7ec",
              "#5598e7", "#3987e5", "#2a78d6", "#256abf", "#1c5cab",
              "#184f95", "#104281", "#0d366b"]

STATUT = {"bon": "#0c7a3e", "attention": "#b8860b",
          "serieux": "#c2622f", "critique": "#a3202f"}

# =============================================================================
# TYPOGRAPHIE
# =============================================================================
# SPECTRAL pour ce qui affirme, INTER pour ce qui se mesure.
#
# Spectral est une serif dessinee pour l'ecran, a l'oeil ouvert et aux
# empattements francs : elle tient a 34 px comme a 13. Elle porte les titres,
# les intitules de section et — en italique — les mentions de source. L'italique
# d'une serif dit « note de bas de page » sans avoir besoin de capitales
# chassees ni d'une fonte a chasse fixe.
#
# Inter porte tout ce qui est CHIFFRE. Un tableau de bord de decision aligne des
# nombres en colonne : ils doivent avoir la meme largeur d'une ligne a l'autre.
# Inter expose `tnum` (chiffres a chasse fixe), que les polices systeme
# n'offrent pas de facon fiable — sans quoi « 1 621 720 » et « 8 095 498 » ne
# s'alignent pas. `cv05` et `cv08` donnent en prime un `1` a empattement et un
# `l` a queue, qui cessent de se confondre.
#
# Aucune fonte a chasse fixe : elle signale du CODE, pas une donnee publique.
#
# Chaque famille garde une pile de repli complete : si les fontes Google ne
# repondent pas, la mise en page tient sur les polices du systeme.
POLICES_WEB = ("https://fonts.googleapis.com/css2?"
               "family=Inter:wght@400;500;600;700&"
               "family=Spectral:ital,wght@0,400;0,500;0,600;1,400&"
               "display=swap")

SANS = "'Inter', system-ui, -apple-system, \"Segoe UI\", Roboto, sans-serif"
SERIF = "'Spectral', 'Iowan Old Style', Georgia, 'Times New Roman', serif"

# Chiffres a chasse fixe + `1` et `l` differencies. Applique partout ou une
# valeur est censee s'aligner sur celle du dessus.
CHIFFRES = ("font-feature-settings: 'tnum' 1, 'cv05' 1, 'cv08' 1;"
            " font-variant-numeric: tabular-nums;")

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

  html, body, .stApp {{ font-family: {SANS}; }}

  /* Les icones de Streamlit sont des LIGATURES d'une fonte symbole : leur
     imposer une police de texte afficherait leur nom en clair
     (« keyboard_double_arrow_left » au lieu de la fleche). La regle ci-dessus
     ne cible que la racine ; celle-ci restaure explicitement la fonte symbole,
     au cas ou une regle plus large viendrait un jour la recouvrir. */
  span[data-testid="stIconMaterial"], .material-icons,
  [class*="material-symbols"], [data-testid$="Icon"] {{
      font-family: "Material Symbols Rounded", "Material Icons" !important;
  }}

  .stApp {{ background: {PAPIER}; -webkit-font-smoothing: antialiased;
            -moz-osx-font-smoothing: grayscale; }}
  .block-container {{ padding: 0 3rem 4rem 3rem; max-width: 1560px; }}
  header[data-testid="stHeader"] {{ background: transparent; height: 0; }}
  /* « Deploy » et le menu de Streamlit sont l'outillage de l'auteur, sans objet
     pour qui consulte le diagnostic — mais on ne peut PAS masquer la barre
     d'outils entiere : le bouton qui REOUVRE la barre laterale y loge aussi.
     La masquer emportait ce bouton, et un sommaire referme devenait
     irrecuperable. On ne retire donc que ce qui doit l'etre. */
  [data-testid="stAppDeployButton"], [data-testid="stMainMenu"],
  [data-testid="stDecoration"], #MainMenu, footer {{
      display: none !important; visibility: hidden;
  }}
  /* Et Streamlit ne revele le bouton de reouverture qu'au survol du bord
     gauche. Sur un outil remis a un tiers, une commande qui n'existe que si
     l'on devine ou passer la souris n'existe pas : elle est rendue visible en
     permanence. */
  [data-testid="stExpandSidebarButton"] {{
      visibility: visible !important; opacity: 1 !important;
      width: auto !important; height: auto !important;
  }}
  [data-testid="stExpandSidebarButton"] button,
  [data-testid="stSidebarCollapseButton"] button {{
      visibility: visible !important; color: {ENCRE_2} !important;
      background: transparent !important; box-shadow: none !important;
  }}
  [data-testid="stExpandSidebarButton"] button:hover,
  [data-testid="stSidebarCollapseButton"] button:hover {{
      color: {VERT} !important;
  }}

  /* Barre laterale : meme papier que la page, separee par un simple filet.
     Un aplat blanc en ferait un panneau d'application ; un filet en fait une
     marge de document. */
  section[data-testid="stSidebar"] {{
      background: {PAPIER}; border-right: 1px solid {FILET};
  }}
  section[data-testid="stSidebar"] > div {{ padding: 1.5rem 1.1rem 1.5rem 1.4rem; }}

  h1, h2, h3, h4 {{ font-family: {SERIF}; color: {ENCRE}; margin: 0;
                    font-weight: 600; letter-spacing: -0.004em; }}

  /* =====================================================================
     EN-TETE GLOBAL — filet tricolore, marque, armoiries
     ===================================================================== */
  .tricolore {{
      display: flex; height: 3px; margin: 0 -3rem;
  }}
  .tricolore i {{ display: block; height: 100%; }}
  .tricolore .v {{ flex: 62; background: {VERT}; }}
  .tricolore .o {{ flex: 19; background: {OR}; }}
  .tricolore .r {{ flex: 19; background: {ROUGE}; }}

  .marque {{
      display: flex; align-items: center; justify-content: space-between;
      gap: 2rem; padding: 0.95rem 0 0.85rem 0;
  }}
  .marque .id {{ font-size: 0.72rem; letter-spacing: 0.13em;
                 text-transform: uppercase; color: {ENCRE_2};
                 font-weight: 600; line-height: 1.7; }}
  .marque .id b {{ color: {ENCRE}; font-weight: 700; }}
  .marque .id em {{ font-family: {SERIF}; font-style: italic;
                    font-size: 0.82rem; letter-spacing: 0; text-transform: none;
                    color: {ENCRE_MUET}; font-weight: 400; }}
  .marque img {{ height: 54px; width: auto; }}

  /* =====================================================================
     TITRE DE PAGE
     ===================================================================== */
  .bandeau {{ padding: 1.5rem 0 1.7rem 0; border-top: 1px solid {FILET};
              margin-bottom: 0.6rem; }}
  .eyebrow {{
      font-size: 0.7rem; letter-spacing: 0.14em; text-transform: uppercase;
      color: {ENCRE_MUET}; font-weight: 600; margin-bottom: 0.7rem;
  }}
  .bandeau h1 {{ font-family: {SERIF}; font-size: 2.6rem; font-weight: 600;
                 line-height: 1.06; letter-spacing: -0.012em;
                 max-width: 22ch; }}
  .bandeau .sous {{
      font-family: {SERIF}; font-size: 1.06rem; color: {ENCRE_2};
      margin-top: 0.9rem; max-width: 68ch; line-height: 1.62;
  }}

  /* =====================================================================
     BLOCS — un filet, pas un cadre
     ===================================================================== */
  div[class*="st-key-bloc"] {{
      background: transparent; border: none; border-top: 2px solid {ENCRE};
      border-radius: 0; padding: 0.85rem 0 1.3rem 0; height: 100%;
  }}
  div[class*="st-key-bloc"] div[class*="st-key-bloc"] {{
      border-top: 1px solid {FILET}; padding-bottom: 0.4rem;
  }}
  .carte-t {{
      font-family: {SERIF}; font-size: 1.02rem; font-weight: 600;
      color: {ENCRE}; margin-bottom: 0.9rem; line-height: 1.35;
      letter-spacing: -0.004em;
  }}
  .carte {{
      border-top: 2px solid {ENCRE}; padding: 0.85rem 0 1.1rem 0;
      height: 100%;
  }}

  /* =====================================================================
     INDICATEURS — le chiffre porte, le filet cadre
     ===================================================================== */
  .kpi {{ border-top: 1px solid {FILET_FORT}; padding: 0.7rem 1.1rem 0.2rem 0;
          height: 100%; }}
  .kpi .lib {{
      font-size: 0.665rem; letter-spacing: 0.11em; text-transform: uppercase;
      color: {ENCRE_MUET}; font-weight: 600; line-height: 1.5;
      min-height: 2.2em; display: block;
  }}
  .kpi .val {{ font-size: 2.2rem; font-weight: 650; color: {ENCRE};
               line-height: 1.08; margin-top: 0.3rem;
               letter-spacing: -0.028em; {CHIFFRES} }}
  .kpi .unite {{ font-size: 0.9rem; font-weight: 500; color: {ENCRE_MUET};
                 margin-left: 0.3rem; letter-spacing: 0; }}
  .kpi .note {{ font-family: {SERIF}; font-style: italic; font-size: 0.8rem;
                color: {ENCRE_2}; margin-top: 0.5rem; display: flex;
                align-items: baseline; gap: 0.45rem; line-height: 1.5; }}
  .pastille {{ width: 6px; height: 6px; border-radius: 50%;
               display: inline-block; flex: 0 0 6px;
               transform: translateY(-2px); }}

  /* =====================================================================
     CHIFFRE HERO — en serif : c'est une affirmation, pas une mesure
     ===================================================================== */
  .hero-val {{ font-family: {SERIF}; font-size: 5rem; font-weight: 600;
               color: {ENCRE}; line-height: 0.95; letter-spacing: -0.03em; }}
  .hero-un {{ font-family: {SANS}; font-size: 1rem; font-weight: 500;
              color: {ENCRE_MUET}; margin-left: 0.6rem;
              letter-spacing: 0.02em; }}
  .hero-txt {{ font-size: 0.95rem; color: {ENCRE_2}; line-height: 1.68;
               margin-top: 1.1rem; max-width: 48ch;
               border-top: 1px solid {FILET}; padding-top: 1rem; }}
  .hero-txt b {{ color: {ENCRE}; font-weight: 600; }}

  /* =====================================================================
     TEXTES COURANTS
     ===================================================================== */
  .question {{ font-family: {SERIF}; font-size: 1.06rem; font-weight: 600;
               color: {ENCRE}; margin: 0 0 0.2rem 0; }}
  .lecture {{
      font-family: {SERIF}; font-size: 0.95rem; color: {ENCRE_2};
      line-height: 1.66; border-left: 2px solid {FILET_FORT};
      padding-left: 1rem; margin: 0.8rem 0 0.3rem 0;
  }}
  .lecture b {{ color: {ENCRE}; font-weight: 600; }}
  .source {{ font-family: {SERIF}; font-style: italic; font-size: 0.83rem;
             color: {ENCRE_MUET}; margin-top: 0.6rem; line-height: 1.6; }}

  /* Bandeau d'action : le seul aplat de toute l'interface, et c'est voulu —
     il ne sert qu'a ce qu'il faut retenir. */
  .action {{
      background: {VERT_CLAIR}; border-left: 3px solid {VERT};
      padding: 0.95rem 1.2rem; font-size: 0.93rem; color: {ENCRE};
      line-height: 1.65;
  }}
  .action b {{ color: {VERT_SOMBRE}; font-weight: 650; }}

  /* A RETENIR — les trois ou quatre messages d'une page, lisibles sans
     defiler. Filet d'encre et numeros : un sommaire de conclusions, pas un
     second bandeau d'action. */
  .retenir {{
      border-top: 2px solid {ENCRE}; border-bottom: 1px solid {FILET};
      padding: 0.75rem 0 0.9rem 0; margin: 0.2rem 0 0.4rem 0;
  }}
  .retenir .titre {{
      font-size: 0.665rem; letter-spacing: 0.11em; text-transform: uppercase;
      color: {ENCRE_MUET}; font-weight: 600; margin-bottom: 0.55rem;
  }}
  .retenir ol {{
      display: grid; grid-template-columns: repeat(auto-fit, minmax(15rem, 1fr));
      gap: 0.4rem 1.6rem; margin: 0; padding: 0; list-style: none;
      counter-reset: msg;
  }}
  .retenir li {{
      counter-increment: msg; font-family: {SERIF}; font-size: 0.97rem;
      color: {ENCRE}; line-height: 1.5; padding-left: 1.7rem; position: relative;
  }}
  .retenir li::before {{
      content: counter(msg); position: absolute; left: 0; top: 0.1rem;
      font-family: {SANS}; font-size: 0.72rem; font-weight: 650;
      color: {VERT}; border: 1.5px solid {VERT}; border-radius: 50%;
      width: 1.2rem; height: 1.2rem; display: flex; align-items: center;
      justify-content: center; {CHIFFRES}
  }}
  .retenir li b {{ font-weight: 650; }}

  /* Conclusion sous un graphique : ce que le lecteur doit en tirer. */
  .conclusion {{
      font-family: {SERIF}; font-size: 0.95rem; font-weight: 600;
      color: {ENCRE}; line-height: 1.5; margin: 0.35rem 0 0.2rem 0;
  }}
  .conclusion::before {{ content: "→ "; color: {VERT}; }}

  /* Rangee de priorite */
  .prio {{
      border-bottom: 1px solid {FILET}; padding: 0.85rem 0.2rem;
      display: flex; align-items: baseline; gap: 1.2rem;
  }}
  .prio .rang {{ font-size: 1.15rem; font-weight: 650; color: {ENCRE_MUET};
                 min-width: 2.2rem; {CHIFFRES} }}
  .prio .nom {{ font-family: {SERIF}; font-size: 1.06rem; font-weight: 600;
                color: {ENCRE}; min-width: 10rem; }}
  .prio .det {{ font-size: 0.83rem; color: {ENCRE_2}; line-height: 1.55; }}
  .prio .det b {{ color: {ENCRE}; font-weight: 600; }}

  /* Sur-titre de section */
  /* Le retrait a gauche vaut celui du texte des entrees (filet de 2 px +
     0,7 rem de marge interieure) : intertitres et intitules partagent ainsi
     une seule et meme verticale. */
  .sb-groupe {{
      font-size: 0.68rem; letter-spacing: 0.14em; text-transform: uppercase;
      color: {ENCRE_MUET}; font-weight: 600;
      padding: 0 0 0.3rem calc(0.7rem + 2px); margin: 0;
  }}

  /* =====================================================================
     NAVIGATION LATERALE — un sommaire, pas un menu
     =====================================================================
     Les entrees sont composees en SERIF, comme les titres de page : la barre
     laterale devient le sommaire du document, et non la barre d'outils d'un
     logiciel. Aucun aplat, aucune bordure : seul un filet vert marque la page
     ouverte, exactement comme un signet dans une marge. */
  .sb-marque {{
      font-size: 0.68rem; letter-spacing: 0.13em; text-transform: uppercase;
      color: {ENCRE_MUET}; font-weight: 600; line-height: 1.8;
      padding: 0 0.2rem 1rem 0.2rem; border-bottom: 1px solid {FILET};
  }}
  .sb-marque b {{ color: {ENCRE}; font-weight: 700; }}
  .sb-marque em {{ font-family: {SERIF}; font-style: italic; font-size: 0.8rem;
                   letter-spacing: 0; text-transform: none; font-weight: 400; }}

  /* Streamlit espace ses elements d'un `gap` d'environ 1 rem. Sur un sommaire,
     cet air transforme sept entrees en une liste qui se parcourt au lieu de se
     voir d'un coup : le rythme est resserre, et seuls les intertitres
     reintroduisent de l'air. */
  /* Intertitre aligne a gauche, sur la meme verticale que les ICONES des
     entrees : filet de marge (2 px) plus la marge interieure du bouton. Le
     sommaire n'a ainsi qu'un seul bord gauche, du haut jusqu'aux filtres. */
  section[data-testid="stSidebar"] .sb-groupe {{
      padding: 0 0 0.35rem calc(0.7rem + 2px); text-align: left;
  }}

  section[data-testid="stSidebar"] div[data-testid="stVerticalBlock"] {{
      gap: 0.1rem;
  }}
  section[data-testid="stSidebar"] div[class*="st-key-navgrp"] {{
      padding-top: 0.5rem;
  }}
  /* La marque deborde de son conteneur de 16 px — meme cause que les
     intertitres, mesuree : 56,1 px de contenu pour 40,1 px de conteneur. Le
     premier groupe doit donc s'ecarter, sinon son intertitre passe sous le
     filet de la marque. */
  section[data-testid="stSidebar"] div[class*="st-key-navgrp0"] {{
      margin-top: 1.2rem;
  }}
  /* Le conteneur d'un fragment HTML brut ne prend PAS la hauteur de son
     contenu (mesure : 4,94 px pour une etiquette qui en occupe 20,9), et
     aucune propriete `height` ne corrige cela. L'ecart est donc pose sur
     l'element NATIF qui suit, dont le dimensionnement, lui, est juste. */
  section[data-testid="stSidebar"] div[class*="st-key-navgrp"]
      div[data-testid="stElementContainer"]:nth-child(2) {{
      margin-top: 1.15rem;
  }}

  section[data-testid="stSidebar"] div[data-testid="stButton"] > button {{
      width: 100%; padding: 0.4rem 0.7rem;
      justify-content: flex-start !important; text-align: left !important;
      border: none; border-left: 2px solid transparent; border-radius: 0;
      background: transparent; color: {ENCRE_2}; box-shadow: none;
      min-height: 0; transition: color 0.12s ease, border-color 0.12s ease;
  }}
  /* Le libelle est centre par un conteneur INTERNE, pas par le bouton : regler
     `justify-content` sur le bouton seul reste sans effet. Le bouton devient
     donc une RANGEE explicite — icone, puis intitule qui occupe le reste.
     `!important` est ici justifie et non commode : les classes d'emotion que
     Streamlit engendre portent une specificite qu'aucun selecteur stable ne
     peut depasser, et leur nom change a chaque version. */
  section[data-testid="stSidebar"] div[data-testid="stButton"] > button {{
      display: flex !important; align-items: center !important;
      justify-content: flex-start !important;
  }}
  /* Streamlit empile DEUX conteneurs flex CENTRES entre le bouton et son
     contenu (mesure dans le navigateur). L'alignement doit etre impose aux
     deux : sur le bouton seul, le couple icone + intitule reste centre, et les
     intitules cessent de s'aligner d'une ligne a l'autre. */
  section[data-testid="stSidebar"] div[data-testid="stButton"] > button > div,
  section[data-testid="stSidebar"] div[data-testid="stButton"] > button > div > span {{
      flex: 1 1 auto !important; width: 100% !important; min-width: 0;
      justify-content: flex-start !important; align-items: center !important;
      text-align: left !important;
  }}
  section[data-testid="stSidebar"] div[data-testid="stButton"] > button > div > span {{
      gap: 0.62rem;
  }}
  /* L'icone reste en retrait : elle accompagne l'intitule, elle ne le
     concurrence pas. Elle ne prend la couleur d'accent que sur la page
     ouverte, ou elle redouble le filet de marge. */
  section[data-testid="stSidebar"] div[data-testid="stButton"] > button
      [data-testid="stIconMaterial"] {{
      /* Largeur FIXE : c'est elle qui garantit que les intitules demarrent
         tous sur la meme verticale, quel que soit le dessin de l'icone. */
      flex: 0 0 auto !important; font-size: 1.05rem !important;
      width: 1.15rem !important; text-align: center !important;
      color: {FILET_FORT} !important; transition: color 0.12s ease;
  }}
  section[data-testid="stSidebar"] div[data-testid="stButton"] > button:hover
      [data-testid="stIconMaterial"] {{ color: {ENCRE_MUET} !important; }}
  section[data-testid="stSidebar"] button[kind="primary"] [data-testid="stIconMaterial"],
  section[data-testid="stSidebar"] button[data-testid="stBaseButton-primary"]
      [data-testid="stIconMaterial"] {{ color: {VERT} !important; }}
  section[data-testid="stSidebar"] div[data-testid="stButton"] > button p {{
      font-family: {SERIF}; font-size: 0.97rem; font-weight: 400;
      line-height: 1.45; letter-spacing: -0.004em;
  }}
  section[data-testid="stSidebar"] div[data-testid="stButton"] > button:hover {{
      color: {ENCRE}; border-left-color: {FILET_FORT};
  }}
  section[data-testid="stSidebar"] button[kind="primary"],
  section[data-testid="stSidebar"] button[data-testid="stBaseButton-primary"] {{
      background: transparent !important; color: {VERT} !important;
      border-left: 2px solid {VERT} !important;
  }}
  section[data-testid="stSidebar"] button[kind="primary"]:hover,
  section[data-testid="stSidebar"] button[data-testid="stBaseButton-primary"]:hover {{
      background: transparent !important; color: {VERT} !important;
  }}
  section[data-testid="stSidebar"] button[kind="primary"] p,
  section[data-testid="stSidebar"] button[data-testid="stBaseButton-primary"] p {{
      font-weight: 600;
  }}

  /* ---------- filtres ----------
     Les champs de Streamlit arrivent en boites blanches a coins arrondis :
     seuls elements de toute l'interface a ressembler a un formulaire de
     logiciel. Ils sont ramenes a un simple filet souligne, comme un champ
     a remplir sur un imprime. */
  /* La boite visible est le premier enfant du ComboBox. `react-aria-ComboBox`
     est un nom SEMANTIQUE, pas une empreinte d'emotion : il ne change pas a
     chaque version de Streamlit, contrairement aux classes voisines. */
  section[data-testid="stSidebar"] .react-aria-ComboBox > div {{
      background: transparent !important; border: none !important;
      border-bottom: 1px solid {FILET_FORT} !important;
      border-radius: 0 !important; box-shadow: none !important;
  }}
  section[data-testid="stSidebar"] .react-aria-ComboBox:focus-within > div {{
      border-bottom-color: {VERT} !important;
  }}
  section[data-testid="stSidebar"] [data-testid="stMultiSelect"] input {{
      font-family: {SERIF}; font-size: 0.93rem;
  }}

  /* « Select all » — la seule chaine anglaise de toute l'interface. Streamlit
     l'ecrit en dur dans son paquet JavaScript et n'expose aucun reglage pour
     la retirer ; elle est donc masquee par le CSS, sur la cle stable que
     porte l'option. La liste est virtualisee et positionne ses lignes en
     absolu : masquer l'option laisserait un vide de 40 px en tete, d'ou la
     remontee compensatoire.
     LES DEUX REGLES DEPENDENT DU MEME MARQUEUR : si une version future de
     Streamlit le renomme, aucune des deux ne s'applique et l'on retrouve le
     comportement d'origine — jamais une liste decalee. */
  [role="listbox"] div[role="presentation"]:has(> [data-key="__select_all__"]) {{
      display: none !important;
  }}
  [role="listbox"]:has([data-key="__select_all__"]) > div[role="presentation"] {{
      margin-top: -40px;
  }}

  /* =====================================================================
     DIVERS
     ===================================================================== */
  div[data-testid="stDataFrame"] {{ {CHIFFRES} }}
  div[data-testid="stExpander"] {{ border: none;
      border-top: 1px solid {FILET}; border-radius: 0;
      background: transparent; }}
  div[data-testid="stExpander"] summary p {{ font-family: {SERIF};
      font-size: 0.96rem; font-weight: 500; }}
  .stTabs [data-baseweb="tab-list"] {{ gap: 1.6rem;
      border-bottom: 1px solid {FILET}; }}
  .stTabs [data-baseweb="tab"] {{ font-family: {SERIF}; font-size: 0.96rem;
      padding: 0.5rem 0; }}
  .stTabs [aria-selected="true"] {{ color: {VERT} !important; }}
  hr {{ border-color: {FILET}; }}

  /* Pied de page */
  .pied {{ font-family: {SERIF}; font-style: italic; font-size: 0.8rem;
           color: {ENCRE_MUET}; line-height: 1.8; border-top: 1px solid {FILET};
           padding-top: 1rem; margin-top: 2.5rem; }}
</style>
"""


# =============================================================================
# BLOCS
# =============================================================================
# POURQUOI UN GESTIONNAIRE DE CONTEXTE, ET PAS UN <div> OUVERT EN MARKDOWN
# ------------------------------------------------------------------------
# Emettre `<div class="carte">` dans un `st.markdown` puis `</div>` dans un
# autre NE FONCTIONNE PAS : chaque appel produit son propre conteneur, et le
# navigateur referme le div des la fin du premier. Le graphique ou le tableau
# qui suit se retrouve A COTE du bloc, jamais dedans — a l'ecran, un titre
# surmonte un vide, et son contenu flotte en dessous.
#
# `st.container(key=...)` resout le probleme a la source : Streamlit pose la
# classe `st-key-<cle>` sur un conteneur REEL, et tout ce qui est ecrit dans le
# bloc `with` y est place.
#
# La cle est un numero d'ordre, remis a zero avant chaque rendu de page. Elle
# doit etre DETERMINISTE : une cle qui changerait d'un rendu a l'autre ferait
# remonter tout l'arbre React, et les graphiques clignoteraient a chaque
# mouvement d'un curseur.
_compteur_blocs = itertools.count()


def reinitialiser_blocs() -> None:
    """A appeler une fois par rendu, avant d'afficher la page."""
    global _compteur_blocs
    _compteur_blocs = itertools.count()


@contextmanager
def bloc(titre: str | None = None):
    """Section titree, qui contient reellement ce qu'on y ecrit."""
    with st.container(key=f"bloc{next(_compteur_blocs)}"):
        if titre:
            st.markdown(f'<div class="carte-t">{titre}</div>',
                        unsafe_allow_html=True)
        yield


# =============================================================================
# FRAGMENTS
# =============================================================================
# Chaque fragment porte la classe `bloc-html`. Elle ne sert qu'a une chose :
# donner au CSS une prise sur les fragments, sans dependre des noms de classes
# que Streamlit engendre et renomme a chaque version.
MARQUEUR = "bloc-html"


def etiquette(texte: str, marge: str = "", classe: str = "sb-groupe") -> str:
    """Sur-titre de section. `marge` ajoute de l'air au-dessus."""
    style = f' style="margin-top:{marge}"' if marge else ""
    return f'<div class="{MARQUEUR} {classe}"{style}>{texte}</div>'


def entete(mention: str = "Données ouvertes · PRISE 2021-2022 · RGPH-5 2022") -> str:
    """Filet tricolore, identite de l'emetteur, armoiries. Une fois par rendu."""
    return f"""
    <div class="tricolore"><i class="v"></i><i class="o"></i><i class="r"></i></div>
    <div class="{MARQUEUR} marque">
      <div class="id">
        <b>République togolaise</b> · Défi Économie numérique<br>
        <em>{mention}</em>
      </div>
      <img src="{armoiries_data_uri()}" alt="Armoiries de la République togolaise">
    </div>
    """


def marque_laterale() -> str:
    """Identite en tete de la barre laterale, avant le sommaire."""
    return (f'<div class="{MARQUEUR} sb-marque">'
            f'<b>République togolaise</b><br>Défi Économie numérique</div>')


def bandeau(eyebrow: str, titre: str, question: str) -> str:
    """Titre de page : sur-titre, titre, question a laquelle la page repond."""
    return f"""
    <div class="{MARQUEUR} bandeau">
      <div class="eyebrow">{eyebrow}</div>
      <h1>{titre}</h1>
      <div class="sous">{question}</div>
    </div>
    """


def kpi(libelle: str, valeur: str, unite: str = "", note: str = "",
        couleur: str = VERT) -> str:
    u = f'<span class="unite">{unite}</span>' if unite else ""
    n = (f'<div class="note"><span class="pastille" '
         f'style="background:{couleur}"></span><span>{note}</span></div>'
         if note else "")
    return (f'<div class="{MARQUEUR} kpi"><span class="lib">{libelle}</span>'
            f'<div class="val">{valeur}{u}</div>{n}</div>')


def question(texte: str) -> str:
    return f'<div class="{MARQUEUR} question">{texte}</div>'


def lecture(texte: str) -> str:
    return f'<div class="{MARQUEUR} lecture">{texte}</div>'


def source(texte: str) -> str:
    return f'<div class="{MARQUEUR} source">{texte}</div>'


def action(texte: str) -> str:
    return f'<div class="{MARQUEUR} action">{texte}</div>'


def a_retenir(messages: list[str]) -> str:
    """Les messages essentiels d'une page, en tete, avant tout graphique."""
    items = "".join(f"<li>{m}</li>" for m in messages)
    return (f'<div class="{MARQUEUR} retenir"><div class="titre">À retenir</div>'
            f'<ol>{items}</ol></div>')


def conclusion(texte: str) -> str:
    """Phrase de conclusion, visible sous un graphique."""
    return f'<div class="{MARQUEUR} conclusion">{texte}</div>'


def pied(texte: str) -> str:
    return f'<div class="{MARQUEUR} pied">{texte}</div>'


def ligne_priorite(rang: int, nom: str, detail: str) -> str:
    return (f'<div class="{MARQUEUR} prio"><div class="rang">{rang:02d}</div>'
            f'<div class="nom">{nom}</div><div class="det">{detail}</div></div>')
