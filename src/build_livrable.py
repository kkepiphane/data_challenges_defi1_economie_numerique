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

# Les dix fichiers lus par l'application. La liste est EXPLICITE : embarquer
# `data/processed/*` entrainerait les 5 Mo de la table WKT d'origine, que
# l'application n'ouvre jamais.
DONNEES = [
    "acces_canton.csv", "acces_prefecture.csv", "dcpi_commune.csv",
    "dcpi_prefecture.csv", "dcpi_sensibilite.csv", "dcpi_variantes.csv",
    "etablissements_pts.csv", "indicateurs_commune.csv",
    "points_mobile_money.csv", "prefectures.geojson",
]

PAGES = ["Vue d'ensemble", "Infrastructures", "Desserte & population",
         "Territoires prioritaires", "Arbitrage", "Plan d'action",
         "Méthode & limites"]

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
| `dashboard/` | l'application : 7 pages, cartes, fiches de territoire |
| `data/processed/` | les 10 fichiers lus par l'application |
| `reports/` | un rapport de contrôle par étape de la chaîne d'analyse |

## Les sept pages

| Page | Ce qu'on y trouve |
|---|---|
| **Vue d'ensemble** | le chiffre national, ce qu'il masque, les cinq territoires prioritaires |
| **Infrastructures** | agences, agents Mobile Money, centres de données — après déduplication |
| **Desserte & population** | ratios par habitant, concentration, écarts entre préfectures |
| **Territoires prioritaires** | l'indice DCPI, sa composition, sa robustesse, une fiche par territoire |
| **Arbitrage** | réglez vous-même les pondérations, puis convertissez un objectif de desserte en nombre de points à ouvrir |
| **Plan d'action** | quelles interventions les déficits mesurés appellent, et sur quels territoires |
| **Méthode & limites** | sources, contrôles arithmétiques, pistes écartées, limites à connaître avant de citer les résultats |

## Ce que l'outil ne fait pas

Il ne produit **ni coût, ni délai, ni rentabilité** : ces grandeurs ne figurent
dans aucune source du projet. Un score élevé signale un besoin mesuré — pas une
solution, et pas un budget.

Il ne mesure **pas la couverture réseau mobile** : aucune des 19 variables des
fichiers sources ne la décrit. Une zone sans agence n'est pas nécessairement
une zone sans réseau.

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

    controles = []
    for page in PAGES:
        at = AppTest.from_file(str(dossier / "streamlit_app.py"),
                               default_timeout=240)
        at.session_state["page"] = page
        at.run()
        motif = ("; ".join(e.message for e in at.exception)[:120]
                 if at.exception else
                 f"{len(at.markdown)} blocs, {len(at.dataframe)} tables")
        controles.append((f"Page « {page} »", not at.exception, motif))
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
        controles.append(("Les 10 fichiers de données sont présents",
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
