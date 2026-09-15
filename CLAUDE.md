# Défi 1 — Économie numérique (Togo) : état du projet

Ce fichier existe pour qu'une reprise en main — nouvelle conversation, autre
agent IA, ou simplement vous dans six mois — n'ait pas besoin de relire tout
l'historique de conversation pour savoir où ça en est. Il est mis à jour à
chaque session de travail importante.

## Ce que c'est

Diagnostic territorial de l'accès aux télécommunications et aux services
numériques au Togo, à partir de données ouvertes (PRISE 2021-2022, RGPH-5
INSEED, contours COD-AB/OCHA). Réalisé pour un défi noté par un jury (voir
`reports/00_synthese_audit_et_matrice.md` pour le détail méthodologique).

**Trois livrables** :
1. Tableau de bord Streamlit interactif — `streamlit run streamlit_app.py`,
   déployé sur Streamlit Community Cloud.
2. Support de présentation PowerPoint, 10 diapositives —
   `reports/Defi1_Togo_Connectivite_numerique.pptx`.
3. Archive autonome du tableau de bord — `reports/tableau_de_bord_togo.zip`.

## ⚠️ État Git — À VÉRIFIER EN PREMIER

**Au 15 septembre 2026**, le dépôt local est sur la branche `version2`, pas
`main`. `main` (local et `origin/main`) est resté au commit `6b78873`
(« Arbitrage : Spearman calculé sans scipy ») — **6 commits en retard** sur
`version2`. Concrètement : le site Streamlit Cloud en production ne contient
**ni la page Couverture & zones blanches, ni le filtre Opérateur, ni les
corrections d'harmonisation des chiffres** décrites plus bas.

L'utilisateur a dit vouloir pousser lui-même (`git push origin version2`,
puis fusion dans `main`). **Ne poussez pas sans qu'on vous le demande** —
vérifiez d'abord `git branch -vv` et `git log --oneline main..version2` pour
voir si la situation a changé depuis.

## Architecture — le principe qui structure tout

L'application **ne calcule rien**. Elle lit des fichiers déjà produits et
contrôlés par une chaîne de scripts, jamais les données brutes :

```
src/ (chaîne, poste de travail)          dashboard/ (application, Streamlit Cloud)
  audit_raw → extract_rgph5 → build_geo    lit UNIQUEMENT data/processed/*.csv
  → build_indicators → spatial_access      + prefectures.geojson, cantons.geojson
  → priority_index → zones_blanches
  → build_app_data → build_deck*
```

**Deux fichiers de dépendances, volontairement séparés** :
- `requirements.txt` (app) : streamlit, pandas, `numpy==2.3.5`, plotly — roues
  pures, aucune compilation. **`numpy==2.2.6` n'a pas de roue pour Python
  3.14** (celui de Streamlit Cloud au moment du dernier déploiement) : ne
  jamais redescendre sous `numpy==2.3.2` sans revérifier.
- `requirements-chaine.txt` (analyse) : geopandas, shapely, pyproj, scipy,
  matplotlib, python-pptx — poste de travail uniquement.
- `dashboard/sections/arbitrage.py` calcule un Spearman **sans scipy**
  (Pearson sur les rangs, mathématiquement identique) — scipy n'est pas dans
  `requirements.txt`, l'importer ferait planter le déploiement.

## Les 8 pages du tableau de bord

Diagnostic (établir les faits) puis Décider (en tirer des conséquences) :
Vue d'ensemble, Infrastructures, Desserte & population, Territoires
prioritaires, **Couverture & zones blanches**, Arbitrage, Plan d'action,
Méthode & limites.

**Couverture & zones blanches** (`dashboard/sections/couverture.py`,
`src/zones_blanches.py`) existe parce qu'**aucune mesure de couverture radio
n'existe dans les données ouvertes**. Plutôt que d'ignorer l'objectif, la
page construit un **proxy explicite** (un agent Mobile Money actif témoigne
d'un réseau) et le déclare comme tel — jamais présenté comme une vraie carte
de couverture. 373 cantons, score de risque à 4 composantes, 2 000
pondérations testées pour la robustesse.

**Trois filtres**, dans la barre latérale : Région, Préfecture, **Opérateur**
(Tous / Moov / Togocom). Le filtre Opérateur recalcule les indicateurs
d'offre (agences, points Mobile Money, distances) mais **ne s'applique pas**
aux pages construites sur l'indice DCPI (Territoires prioritaires, Arbitrage,
Plan d'action), calculé tous opérateurs confondus — un bandeau le dit
explicitement plutôt que de l'ignorer en silence.

## Une seule source pour chaque chiffre qui compte

Trois familles de nombres apparaissaient avec des valeurs différentes selon
la page avant d'être corrigées — **toujours passer par ces fonctions**,
jamais recalculer à la main dans une page :

| Chiffre | Fonction | Valeur actuelle |
|---|---|---|
| Agences | `dashboard/data.py::agences_reperes()` / `libelle_agences()` | 90 recensées après dédoublonnage, dont 88 actives : 28 Moov et 60 Togocom actives (2 agences Togocom déclarées fermées dans la source) |
| Contrôles arithmétiques | `dashboard/data.py::nombre_controles()` | 35 / 35 (lit tous les `reports/*.md`) |
| Points à ouvrir | `dashboard/data.py::plan_couverture(df, objectif=OBJECTIF_DEFAUT)`, `OBJECTIF_DEFAUT = 409` | 1497 pour les 9 territoires prioritaires robustes, à l'objectif par défaut |

`src/build_deck.py` (PowerPoint) recalcule ces mêmes chiffres indépendamment
via des fonctions miroir (`_controles()`, etc.) — **volontaire** (pas
d'import direct du module Streamlit) mais `src/build_livrable.py` vérifie à
chaque génération du livrable que les deux versions concordent
(3 contrôles de cohérence croisée en fin de rapport).

**Formatage des nombres en français** : `dashboard/theme.py::fr(x, dec)`,
`pct(x, dec)`, `ordinal(n)` — à utiliser partout qu'un nombre entre dans un
texte affiché. Python formate nativement en anglais (`12.7`, `20%`) ; ces
trois fonctions produisent `12,7`, `20 %`, `1er`/`2ᵉ`. Équivalents locaux
côté PowerPoint dans `build_deck.py` (`_fr`, `_pct`, `_esp`) et
`build_deck_figures.py` (les graphiques matplotlib avaient le même défaut).

## ⚠️ Le PowerPoint est parfois retouché à la main

L'utilisateur ouvre et modifie parfois `reports/Defi1_Togo_Connectivite_numerique.pptx`
directement dans PowerPoint (exemple vécu : suppression de la ligne
« Analyse de données · Défi Économie numérique » sous son nom en page de
garde). **Ne jamais relancer `python src/build_deck.py` sans vérifier
d'abord** si le fichier committé diffère du fichier sur disque
(`git status`, puis comparer le texte des diapositives via python-pptx) —
une régénération écrase silencieusement toute retouche manuelle. Si une
correction est nécessaire : mettre à jour le générateur (pour que la
*prochaine* génération soit correcte) **et** patcher le fichier existant en
place avec python-pptx (modifier le run de texte concerné, pas régénérer).

## Vérification avant de considérer un changement fini

`python src/build_livrable.py` rejoue l'app dans un dossier temporaire hors
du projet et vérifie ~24 points (8 pages sans exception, cohérence des
nombres, non-régression de l'indice DCPI...). Pour les changements de texte/
formatage, un balayage automatisé via `streamlit.testing.v1.AppTest` sur les
72 combinaisons page × filtre région/préfecture × opérateur, en cherchant les
motifs `\d%` (pourcentage non espacé) et `\d\.\d` (décimale au point
anglais) dans le texte rendu, a servi à traquer les dernières occurrences.

## Notation du défi (jury)

Dernière note connue (avant les améliorations C2/C3 de cette session) :
**15,5/20** — C1 (ergonomie) 3,5/4, C2 (analyse) 6/8, C3 (interactivité) 3/4,
C4 (rapport) 3/4. Le jury n'a pas laissé de commentaires écrits connus ; les
pistes d'amélioration retenues (page Couverture, filtres croisés, export
CSV, densité vs équipement, rapport PDF pour C4 — toujours pas fait) sont
dans l'historique de conversation, pas dans ce fichier.
