"""
LIVRABLE — TABLEAU DE BORD INTERACTIF (.zip)
=============================================
Assemble `reports/tableau_de_bord_togo.zip` : l'application, ses donnees, ses
rapports de controle et sa notice, dans une archive qui demarre sur un poste
neuf en deux commandes.

CE QUI ENTRE DANS L'ARCHIVE — ET CE QUI N'Y ENTRE PAS
------------------------------------------------------
Entrent : l'application, les DIX fichiers qu'elle lit, les rapports de controle
(la page Methode les affiche), la notice et les dependances.

N'entrent pas : les 34 Mo de donnees brutes et les 25 Mo de sources externes.
Un evaluateur qui ouvre une archive veut lancer l'outil, pas heberger un
entrepot. La chaine complete reste accessible par le depot.

L'ARCHIVE EST VERIFIEE, PAS SEULEMENT ECRITE
---------------------------------------------
Zipper des fichiers ne prouve rien. Alors cette etape va plus loin : elle
extrait l'archive dans un repertoire temporaire, AILLEURS que dans le projet,
et y execute les sept pages du tableau de bord avec le harnais de test de
Streamlit. Si une page leve une exception — un fichier oublie, un chemin
absolu, un import qui ne tient que sur ce poste — l'etape echoue et l'archive
n'est pas publiee.

C'est la difference entre « j'ai fait un zip » et « ce zip fonctionne ».

Usage :
    python src/build_livrable.py            assemble et verifie
    python src/build_livrable.py --rapide   assemble sans executer les pages
"""

from __future__ import annotations

import io
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "reports" / "tableau_de_bord_togo.zip"
RACINE_ARCHIVE = "tableau_de_bord_togo"

# Les quatorze fichiers lus par l'application. La liste est EXPLICITE : embarquer
# `data/processed/*` entrainerait les 5 Mo de la table WKT d'origine, que
# l'application n'ouvre jamais.
DONNEES = [
    "acces_canton.csv", "acces_prefecture.csv", "dcpi_commune.csv",
    "dcpi_prefecture.csv", "dcpi_sensibilite.csv", "dcpi_variantes.csv",
    "etablissements_pts.csv", "indicateurs_commune.csv",
    "points_mobile_money.csv", "prefectures.geojson",
    "zones_blanches_canton.csv", "zones_blanches_variantes.csv",
    "cantons.geojson", "vide_temoins.csv",
]

# Les sept pages, lues telles que l'application les nomme. La liste n'est pas
# recopiee a la main : un controle qui code en dur ce qu'il verifie cesse de le
# verifier des qu'on renomme une page.
def _pages(dossier: Path) -> list[str]:
    import sys as _sys
    _sys.path.insert(0, str(dossier / "dashboard"))
    import app as _app
    return list(_app.PAGES)

NOTICE = """# Tableau de bord — Accès aux télécommunications et aux services numériques au Togo

Diagnostic territorial et priorisation d'investissement, à partir de données ouvertes.

## Démarrer

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

L'application s'ouvre sur `http://localhost:8501`. Quatre bibliothèques
suffisent : ni compilation, ni outil système, ni base de données.

## Ce que contient l'archive

| Dossier | Contenu |
|---|---|
| `dashboard/` | l'application : 8 pages, cartes, fiches de territoire |
| `data/processed/` | les 14 fichiers lus par l'application |
| `reports/` | un rapport de contrôle par étape de la chaîne d'analyse |

## Les huit pages

| Page | Ce qu'on y trouve |
|---|---|
| **Vue d'ensemble** | le chiffre national, ce qu'il masque, les cinq territoires prioritaires |
| **Infrastructures** | agences, agents Mobile Money, centres de données — après déduplication |
| **Desserte & population** | ratios par habitant, concentration, écarts entre préfectures |
| **Territoires prioritaires** | l'indice DCPI, sa composition, sa robustesse, une fiche par territoire |
| **Couverture & zones blanches** | la donnée de couverture absente, les sources cherchées, un proxy déclaré comme tel et la carte des cantons à investiguer |
| **Arbitrage** | réglez vous-même les pondérations, puis convertissez un objectif de desserte en nombre de points à ouvrir |
| **Plan d'action** | quelles interventions les déficits mesurés appellent, et sur quels territoires |
| **Méthode & limites** | sources, contrôles arithmétiques, pistes écartées, limites à connaître avant de citer les résultats |

## Ce que l'outil ne fait pas

Il ne produit **ni coût, ni délai, ni rentabilité** : ces grandeurs ne figurent
dans aucune source du projet. Un score élevé signale un besoin mesuré — pas une
solution, et pas un budget.

Il ne mesure **pas la couverture réseau mobile** : aucune des 19 variables des
fichiers sources ne la décrit. La page « Couverture & zones blanches » désigne
des cantons à investiguer à partir d'un proxy déclaré — une zone sans agent
Mobile Money n'est pas nécessairement une zone sans réseau.

## Sources

| Source | Producteur | Période |
|---|---|---|
| Agences opérateurs, agents Mobile Money, centres de données | Géoportail national | collecte PRISE 2021-2022 |
| RGPH-5, livret 01 | INSEED | dénombrement oct.-nov. 2022 |
| Limites administratives COD-AB v02 | OCHA / ITOS | valide au 07/01/2021 |

Aucune valeur affichée n'est imputée. La population extraite somme exactement à
8 095 498 habitants aux trois niveaux administratifs, sans écart d'une unité.

---

KOUTSAVA Kossi Epiphane — Défi Économie numérique, République togolaise
"""


def _contenu() -> list[tuple[Path, str]]:
    """(source sur le disque, chemin dans l'archive)."""
    elements: list[tuple[Path, str]] = []

    for chemin in sorted((ROOT / "dashboard").rglob("*")):
        if chemin.is_file() and "__pycache__" not in chemin.parts:
            elements.append((chemin, str(chemin.relative_to(ROOT)).replace("\\", "/")))

    for nom in DONNEES:
        elements.append((ROOT / "data" / "processed" / nom,
                         f"data/processed/{nom}"))

    for chemin in sorted((ROOT / "reports").glob("*.md")):
        elements.append((chemin, f"reports/{chemin.name}"))

    elements.append((ROOT / "streamlit_app.py", "streamlit_app.py"))
    elements.append((ROOT / "requirements.txt", "requirements.txt"))
    elements.append((ROOT / ".streamlit" / "config.toml", ".streamlit/config.toml"))
    return elements


def _verifier(dossier: Path) -> list[tuple[str, bool, str]]:
    """Execute les sept pages depuis l'archive extraite."""
    from streamlit.testing.v1 import AppTest

    entree = str(dossier / "streamlit_app.py")
    controles = []
    for page in _pages(dossier):
        at = AppTest.from_file(entree, default_timeout=240)
        at.session_state["page"] = page
        at.run()
        motif = ("; ".join(e.message for e in at.exception)[:120]
                 if at.exception else
                 f"{len(at.markdown)} blocs, {len(at.dataframe)} tables")
        controles.append((f"Page « {page} »", not at.exception, motif))

    # NON-REGRESSION — la feuille de style doit etre reemise a CHAQUE execution.
    # Streamlit rejoue le script d'entree a chaque interaction, mais Python ne
    # reimporte pas un module deja charge : du CSS emis au niveau module de
    # `dashboard/app.py` disparait des le premier clic, et la page s'affiche
    # nue. Le defaut ne leve aucune exception — seul ce controle le voit.
    def _css(at) -> bool:
        return any("<style>" in m.value for m in at.markdown)

    at = AppTest.from_file(entree, default_timeout=240)
    at.run()
    rendus = [_css(at)]
    for _ in range(3):
        at.run()
        rendus.append(_css(at))
    controles.append(("Feuille de style réémise à chaque rendu",
                      all(rendus), f"4 rendus successifs : {rendus}"))

    # Et sous une vraie navigation, qui declenche un rerun par `st.rerun()`.
    at = AppTest.from_file(entree, default_timeout=240)
    at.run()
    cible = next((b for b in at.sidebar.button if b.label == "Arbitrage"), None)
    if cible is not None:
        cible.click().run()
    controles.append(("Feuille de style conservée après navigation",
                      cible is not None and _css(at) and not at.exception,
                      "clic sur « Arbitrage » dans la navigation"))

    # NON-REGRESSION — les icones de Streamlit sont des LIGATURES d'une fonte
    # symbole. Un selecteur large du genre [class*="st-"] qui imposerait une
    # police de texte les ferait s'afficher en clair : « keyboard_double_
    # arrow_left » a la place d'une fleche, sur toutes les pages. Le defaut est
    # purement visuel, donc invisible a l'execution — d'ou ce controle.
    style = next((m.value for m in at.markdown if "<style>" in m.value), "")
    pieges = [s for s in ('[class*="st-"]', '[class^="st-"]', '[class~="st-"]')
              if s in style]
    controles.append(("Aucun sélecteur large n'écrase la fonte des icônes",
                      not pieges,
                      "; ".join(pieges) if pieges
                      else "fonte symbole préservée"))

    # NON-REGRESSION — « Select all », seule chaine anglaise de l'interface.
    # Streamlit l'ecrit en dur dans son paquet JavaScript et n'expose aucun
    # reglage : elle est masquee par le CSS, sur la cle `__select_all__` que
    # porte l'option. Ce controle verifie les DEUX moitiés de l'hypothese —
    # la regle existe, et la cle sur laquelle elle s'appuie existe encore dans
    # la version de Streamlit installee. Si Streamlit la renomme, le masquage
    # cesse silencieusement d'operer : seul ce controle le verrait.
    regle = "__select_all__" in style
    try:
        import streamlit as _st
        statique = (Path(_st.__file__).parent / "static" / "static" / "js")
        cle = any("__select_all__" in f.read_text(encoding="utf-8",
                                                  errors="ignore")
                  for f in statique.glob("Multiselect*.js"))
    except Exception:
        cle = False
    controles.append(
        ("« Select all » masqué dans les filtres", regle and cle,
         "règle CSS présente et clé `__select_all__` confirmée dans Streamlit"
         if regle and cle else
         f"règle CSS : {regle} · clé présente dans Streamlit : {cle}"))

    # NON-REGRESSION — le bouton qui reouvre la barre laterale loge DANS la
    # barre d'outils de Streamlit, aux cotes de « Deploy ». Masquer la barre
    # d'outils entiere pour faire disparaitre « Deploy » emporte ce bouton :
    # une fois le sommaire referme, il devient irrecuperable.
    masque_tout = ('[data-testid="stToolbar"]' in style
                   and "stExpandSidebarButton" not in style)
    controles.append(
        ("Le sommaire refermé reste réouvrable", not masque_tout,
         "la barre d'outils entière est masquée" if masque_tout
         else "« Deploy » masqué seul, bouton de réouverture conservé"))

    # Et les depart rapides de la page Arbitrage, qui ecrivaient dans l'etat
    # d'un widget deja instancie — Streamlit leve alors une exception.
    at = AppTest.from_file(entree, default_timeout=240)
    at.session_state["page"] = "Arbitrage"
    at.run()
    # Les libelles sont LUS dans la page, jamais recopies ici : un controle qui
    # code en dur ce qu'il verifie cesse de le verifier des qu'on renomme.
    import sys as _sys
    _sys.path.insert(0, str(dossier / "dashboard"))
    from sections import arbitrage as _Arb
    presets, echecs = 0, []
    for label in _Arb.PRESETS:
        essai = AppTest.from_file(entree, default_timeout=240)
        essai.session_state["page"] = "Arbitrage"
        essai.run()
        bouton = next((b for b in essai.button if b.label == label), None)
        if bouton is None:
            echecs.append(f"{label} : bouton absent")
            continue
        bouton.click().run()
        presets += 1
        if essai.exception:
            echecs.append(f"{label} : {essai.exception[0].message[:60]}")
    controles.append(("Départs rapides de pondération sans exception",
                      not echecs and presets == len(_Arb.PRESETS),
                      "; ".join(echecs) if echecs
                      else f"{presets} préréglages appliqués"))

    # NON-REGRESSION — invariant de la repondération.
    # Aux poids de référence, le score reponderé DOIT retomber sur le DCPI
    # publié, et la corrélation des rangs valoir exactement 1. Un appariement
    # par position plutôt que par nom de territoire donnait ici -0,154 : un
    # chiffre faux, affiché sans erreur, à côté d'un « 10 sur 10 » correct.
    try:
        import data as _D
        from sections import arbitrage as _A
        pref = _D.prefectures()
        cles = [c for c, *_ in _A.COMPOSANTES]
        poids = dict(zip(cles, _A.PRESETS["Référence"][0]))
        classe = _A._reponderer(pref, poids)
        ecart = float((classe.DCPI_perso - classe.DCPI).abs().max())
        app = pref[["prefecture", "rang_DCPI"]].merge(
            classe[["prefecture", "rang_perso"]], on="prefecture")
        rho = float(app.rang_DCPI.corr(app.rang_perso, method="spearman"))
        controles.append(
            ("Repondération de référence = DCPI publié",
             ecart < 1e-9 and abs(rho - 1.0) < 1e-9,
             f"écart max {ecart:.2e} · corrélation des rangs {rho:.4f}"))
    except Exception as e:                      # pragma: no cover
        controles.append(("Repondération de référence = DCPI publié", False,
                          f"{type(e).__name__}: {e}"[:120]))
    return controles


def main() -> None:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                                  errors="replace")
    rapide = "--rapide" in sys.argv

    elements = _contenu()
    manquants = [d for s, d in elements if not s.exists()]
    if manquants:
        sys.exit("Fichiers absents : " + ", ".join(manquants) +
                 "\nLancer d'abord la chaîne (voir README.md).")

    ARCHIVE.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(ARCHIVE, "w", zipfile.ZIP_DEFLATED,
                         compresslevel=9) as z:
        for source, destination in elements:
            z.write(source, f"{RACINE_ARCHIVE}/{destination}")
        z.writestr(f"{RACINE_ARCHIVE}/README.md", NOTICE)

    controles: list[tuple[str, bool, str]] = []
    with zipfile.ZipFile(ARCHIVE) as z:
        noms = z.namelist()
        corrompu = z.testzip()
        controles.append(("Archive lisible et sans entrée corrompue",
                          corrompu is None, corrompu or "intégrité vérifiée"))
        controles.append((f"Les {len(DONNEES)} fichiers de données sont présents",
                          all(f"{RACINE_ARCHIVE}/data/processed/{n}" in noms
                              for n in DONNEES), f"{len(DONNEES)} fichiers"))
        controles.append(("Notice et dépendances embarquées",
                          f"{RACINE_ARCHIVE}/README.md" in noms
                          and f"{RACINE_ARCHIVE}/requirements.txt" in noms,
                          "README.md + requirements.txt"))
        controles.append(("Aucun cache Python dans l'archive",
                          not any("__pycache__" in n for n in noms),
                          f"{len(noms)} entrées"))

    poids = ARCHIVE.stat().st_size / 1024 ** 2
    controles.append(("Archive sous 10 Mo", poids < 10, f"{poids:.1f} Mo"))

    if not rapide:
        temporaire = Path(tempfile.mkdtemp(prefix="livrable_togo_"))
        try:
            with zipfile.ZipFile(ARCHIVE) as z:
                z.extractall(temporaire)
            print(f"Archive extraite hors du projet : {temporaire}")
            print("Exécution des sept pages...\n")
            controles += _verifier(temporaire / RACINE_ARCHIVE)
        finally:
            shutil.rmtree(temporaire, ignore_errors=True)

    lignes = ["# Livrable — tableau de bord interactif", "",
              "Genere par `src/build_livrable.py`.", "",
              f"Archive : `reports/{ARCHIVE.name}` — {poids:.1f} Mo, "
              f"{len(elements) + 1} fichiers.", "",
              "L'archive est EXTRAITE hors du projet puis EXECUTEE : les sept",
              "pages tournent depuis son seul contenu avant qu'elle soit",
              "declaree valide.", "",
              "| Controle | Resultat | Detail |", "|---|---|---|"]
    for nom, ok, detail in controles:
        lignes.append(f"| {nom} | {'OK' if ok else 'ECHEC'} | {detail} |")
    (ROOT / "reports" / "livrable.md").write_text("\n".join(lignes) + "\n",
                                                  encoding="utf-8")

    for nom, ok, detail in controles:
        print(f"[{'OK ' if ok else 'ECHEC'}] {nom} — {detail}")
    if not all(ok for _, ok, _ in controles):
        sys.exit(1)
    print(f"\nLivrable : reports/{ARCHIVE.name} — {poids:.1f} Mo, "
          f"{len(elements) + 1} fichiers.")


if __name__ == "__main__":
    main()
