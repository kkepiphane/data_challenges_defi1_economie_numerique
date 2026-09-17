# Accès aux télécommunications et aux services numériques au Togo

Diagnostic territorial et priorisation d'investissement, à partir de données ouvertes.

Question de départ : où faut-il investir en priorité pour réduire les
inégalités d'accès aux télécommunications et aux services numériques au
Togo, et pourquoi ?

---

## Résultat en une page

La référence nationale est de 409 habitants par point Mobile Money. Cette
moyenne cache de grands écarts entre préfectures : le rapport va de 1 à 12,7.

| | Constat mesuré |
|---|---|
| 90 agences recensées après dédoublonnage (28 Moov, 62 Togocom), dont 88 actives | et non 141 comme le laissait croire une première lecture des fichiers : le jeu « Agences – Télécom » est un doublon intégral de Moov ∪ Togocom, et 2 agences Togocom sont déclarées fermées dans la source |
| 2 opérateurs, pas 4 | CANAL+ est vide à la source, et « Télécom » n'est pas un opérateur |
| 13 préfectures sur 39 | sans aucune agence active, soit 20 % de la population |
| 75 communes sur 117 | sans aucune agence active |
| 3 centres de données | tous les trois à Lomé |
| Kpendjal | 2 155 hab. par point Mobile Money, 0 agence, 47 km jusqu'à la plus proche |

Neuf préfectures reviennent dans le top 10 des priorités pour au moins 90 %
des 2 000 pondérations testées : Kpendjal, Mô, Est-Mono, Akébou, Yoto,
Kpendjal-Ouest, Tandjoaré, Wawa, Blitta.

---

## Démarrage

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

Ces quatre bibliothèques suffisent à faire tourner l'application : pas de
compilation, pas d'outil système à installer. Rejouer l'analyse depuis les
données brutes demande davantage, et passe par un autre fichier de
dépendances :

```bash
pip install -r requirements-chaine.txt   # voir la note pdftotext dans le fichier

python src/audit_raw.py          # inventaire, profils, doublons, CRS
python src/extract_rgph5.py      # population INSEED, validée par sommes
python src/build_geo.py          # contours, superficies, densités
python src/build_indicators.py   # déduplication, ratios par habitant
python src/spatial_access.py     # distances (reprojection EPSG:32631)
python src/priority_index.py     # indice DCPI + analyse de sensibilité
python src/zones_blanches.py      # zones à risque de zone blanche (proxy par canton)
python src/build_app_data.py     # paquet léger lu par l'application
```

Chaque script écrit son propre rapport de contrôle dans `reports/`. Au
total, 35 contrôles arithmétiques sont rejoués à chaque exécution.

### Pourquoi deux fichiers de dépendances

| Fichier | Pour quoi | Conséquence |
|---|---|---|
| `requirements.txt` | l'application — streamlit, pandas, numpy, plotly | roues pures, démarrage à froid en quelques secondes |
| `requirements-chaine.txt` | l'analyse — geopandas, shapely, pyproj, scipy, matplotlib, python-pptx | bibliothèques compilées, poste de travail |

L'application ne calcule rien : elle affiche des contours déjà simplifiés et
des points déjà projetés, produits une fois pour toutes par
`src/build_app_data.py`. Lui imposer toute la pile géospatiale aurait
obligé à installer trois bibliothèques compilées pour n'exécuter aucun
calcul géométrique en production, avec les risques d'échec de build que
ça amène.

## Livrables

| Livrable | Fichier |
|---|---|
| Tableau de bord interactif | `reports/tableau_de_bord_togo.zip` — archive autonome, 0,5 Mo |
| Tableau de bord, en local | `streamlit run streamlit_app.py` |
| Support de présentation, 10 diapositives | `reports/Defi1_Togo_Connectivite_numerique.pptx` |
| Aperçu PNG des diapositives | `reports/apercu/diapo_NN.png` |
| Rapports de contrôle, un par étape | `reports/*.md` |
| Datasets analytiques | `data/processed/` |

Aucun chiffre du support n'est saisi à la main : tous sont calculés à partir
de `data/processed/`. Corriger une source en amont met le support à jour
sans retoucher une seule diapositive, page de garde comprise.

L'archive du tableau de bord est testée avant d'être publiée : elle est
extraite hors du projet, dans un répertoire à part, puis les huit pages sont
rejouées avec le harnais de test de Streamlit. Un fichier oublié, un chemin
absolu, un import qui ne fonctionnait que sur ce poste : dans ce cas l'étape
échoue et l'archive n'est pas publiée.

## Déploiement sur Streamlit Community Cloud

Le dépôt est prêt pour ça : point d'entrée `streamlit_app.py` à la racine,
dépendances applicatives isolées, et les dix fichiers de données
versionnés — Streamlit Cloud ne déploie que ce que le dépôt contient.

1. Pousser le dépôt sur GitHub.
2. Sur [share.streamlit.io](https://share.streamlit.io), *New app* → choisir
   le dépôt, la branche `main`, et le fichier `streamlit_app.py`.
3. Déployer. Aucun secret, aucune variable d'environnement, aucun paquet
   système à déclarer.
4. Reporter l'adresse obtenue dans le support de présentation : la page de
   fin renvoie vers le tableau de bord en ligne.

---

## Fiabilité des données

Aucune donnée n'est inventée. Toute valeur affichée provient d'une source
identifiée ou d'un indicateur calculé dont la formule est publiée. Quand une
donnée manque, elle est déclarée manquante, jamais estimée.

Les chiffres ont été vérifiés par l'arithmétique. La population extraite du
PDF de l'INSEED somme exactement à 8 095 498 habitants aux trois niveaux
(5 régions, 39 préfectures, 117 communes), sans écart d'une unité. Les
superficies se conservent à la fusion des contours, et les agrégations
retrouvent bien les effectifs d'origine.

Ces contrôles ont réellement servi à corriger des erreurs. Deux échecs en
particulier : une jointure sur des noms accentués faisait tomber neuf
préfectures à zéro point Mobile Money, dont Agoè-Nyivé et ses 882 695
habitants ; et une somme régionale à 11 630 489 a révélé un double comptage
du Grand Lomé.

Ce qui a été écarté est documenté aussi. Trois pistes ont été essayées puis
abandonnées, preuves conservées : la reconstitution des contours communaux
par fusion de cantons (rejetée, 65,6 % des points tombent dans un canton à
cheval sur plusieurs communes), l'usage de mesures de débit issues de tests
de vitesse (biaisées vers les usagers déjà connectés), et l'écrêtage des
valeurs extrêmes de l'indice.

---

## Sources

| Source | Producteur | Période | Usage |
|---|---|---|---|
| Agences opérateurs, agents Mobile Money, data centers | Géoportail national | Collecte PRISE 2021-2022 | Infrastructures, nomenclature |
| RGPH-5, livret 01 | INSEED | Dénombrement 23 oct. – 16 nov. 2022 | Population |
| Limites administratives COD-AB v02 | OCHA / ITOS | Valide au 07/01/2021 | Contours, superficies |

Les 30 fichiers PRISE ont été livrés en 5 formats. Le CSV fait autorité :
c'est le seul format qui cumule des noms de variables complets et la
précision maximale des coordonnées. Le shapefile a été conservé comme preuve
du CRS — ses six fichiers `.prj` sont strictement identiques et déclarent
EPSG:4326.

---

## Deux unités d'analyse, chacune avec sa propre validité

| Unité | Rôle | Pourquoi |
|---|---|---|
| Préfecture (39) | géographique — polygones, superficie, densité, cartes | concordance spatiale mesurée à 98,4 % |
| Commune (117) | statistique — ratios par habitant, comptages | population validée, mais pas de contours fiables à ce niveau |

Les scores des deux niveaux ne sont pas comparables : la composante
d'éloignement n'y repose pas sur la même mesure.

---

## Limites à connaître avant de citer ces résultats

1. La couverture réseau mobile n'est pas mesurée. Aucune des 19 variables
   des fichiers sources ne décrit la couverture radio. Une zone sans agence
   ni agent Mobile Money n'est pas forcément une zone sans réseau mobile.
2. Les agences CANAL+ sont absentes, l'export était vide à la source.
3. Trois millésimes se croisent : infrastructures 2021-2022, population
   novembre 2022, contours janvier 2021. Tout déploiement postérieur à ces
   dates est invisible dans les données.
4. Les pondérations de l'indice restent un choix, d'où les 2 000
   pondérations alternatives testées et publiées pour vérifier leur
   robustesse.
5. Un score élevé signale un besoin, pas une solution : ni coût, ni
   faisabilité, ni rentabilité n'entrent dans le calcul.

---

## Structure

```
streamlit_app.py          point d'entrée de déploiement (délègue à dashboard/)
requirements.txt          dépendances de l'APPLICATION
requirements-chaine.txt   dépendances de l'ANALYSE

data/raw/          30 fichiers PRISE (6 jeux × 5 formats)
data/external/     RGPH-5 (INSEED), limites COD-AB
data/interim/      extractions intermédiaires
data/processed/    datasets analytiques finaux, dont les 10 fichiers
                   lus par l'application — ceux-là sont versionnés
src/               chaîne de traitement, un script par étape
dashboard/         application Streamlit (lecture seule), 8 pages
reports/           rapports de contrôle, support, aperçus, livrable
```

## Les huit pages du tableau de bord

La navigation suit l'intention du lecteur plutôt que la structure des
données : d'abord établir le diagnostic, ensuite décider. Chaque page
s'ouvre sur un bloc « À retenir » de trois ou quatre messages ; les
graphiques portent une phrase de conclusion, et les tableaux détaillés sont
repliés en dessous.

Un filtre Opérateur (Tous, Moov, Togocom) complète les filtres Région et
Préfecture. Les comptes d'agences suivent une seule définition partout : 90
recensées après dédoublonnage (28 Moov, 62 Togocom), dont 88 actives — les 2
agences Togocom déclarées fermées sont exclues des calculs d'accès.

L'interface est pensée comme un document plutôt que comme une console : fond
crème, titres en romain à empattements (Spectral), filets là où l'on
mettrait d'ordinaire des cadres, et une barre latérale qui fait office de
sommaire. Les nombres, eux, restent en Inter avec chiffres à chasse fixe,
pour qu'une colonne de valeurs s'aligne correctement.

| | Page | Ce qu'on y trouve |
|---|---|---|
| Diagnostic | Vue d'ensemble | le chiffre national, ce qu'il masque, les cinq territoires prioritaires |
| Diagnostic | Infrastructures | agences, agents Mobile Money, centres de données, après déduplication |
| | Desserte & population | ratios par habitant, concentration, écarts entre préfectures |
| | Territoires prioritaires | l'indice DCPI, sa composition, sa robustesse, une fiche par territoire |
| | Couverture & zones blanches | la donnée absente, les sources cherchées, un proxy déclaré et les cantons à investiguer |
| Décider | Arbitrage | réglez vous-même les pondérations, convertissez un objectif de desserte en points à ouvrir, exportez |
| | Plan d'action | quelles interventions les déficits mesurés appellent, et où |
| | Méthode & limites | sources, contrôles, pistes écartées, limites à connaître avant de citer |

La page Arbitrage répond aux deux objections qu'on oppose souvent à un
classement de ce genre. Sur les pondérations : ce sont des choix, alors
autant les régler soi-même. L'indice est une somme pondérée de composantes
déjà normalisées, donc le reclassement est exact et non approché — aux poids
de référence, le score recalculé retombe sur le DCPI publié à la dixième
décimale, et à poids égaux, les dix mêmes territoires restent dans le top
10. Sur l'utilité pratique : un classement seul ne dit pas quoi financer,
donc un simulateur convertit un objectif de desserte en nombre de points à
ouvrir, territoire par territoire, et en population atteinte. Il ne produit
ni coût, ni délai, ni rentabilité, parce qu'aucune source du projet ne
fournit ces grandeurs et que les inventer aurait fragilisé tout le reste.
