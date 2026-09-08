# Synthèse d'audit et matrice de couverture des objectifs

**Défi 1 — Accès aux télécommunications et aux services numériques au Togo**

Périmètre audité : **30 fichiers** dans `data/raw/` = 6 jeux de données × 5 formats
(CSV, XLSX, KML, GeoJSON, ZIP/shapefile).

Scripts reproductibles : `src/audit_raw.py` → `reports/audit_raw.md`
Provenance des jeux : `reports/audit_sources.md`

---

## A. Les 10 constats qui conditionnent tout le projet

| # | Constat | Preuve | Conséquence |
|---|---|---|---|
| **A1** | **Le jeu « Agences – CANAL+ » est vide** : 0 enregistrement dans les 5 formats. Ce n'est pas une erreur de lecture — le serveur joint sa propre note dans le ZIP : *« The query result is empty… an empty point shapefile has been created to fill the zip file »*. | `audit_raw.md` §3.1 | CANAL+ est nommé dans l'énoncé mais **ne peut pas être cartographié**. À déclarer *donnée non disponible*, jamais comme « absence d'agences sur le terrain ». Preuve opposable au jury. |
| **A2** | **« Agences – Télécom » n'est pas un 4ᵉ opérateur** : ses 51 lignes = 34 Togocom + 17 Moov, avec **0 enregistrement exclusif** face à Moov ∪ Togocom. | `audit_raw.md` §4 | Empiler les 4 fichiers afficherait **141 agences au lieu de 90** : **+57 % d'erreur sur le tout premier KPI**. La déduplication est obligatoire et documentée. |
| **A3** | **L'identifiant `FID` est volatile.** La même agence porte `…_68de` dans le CSV et `…_68fa` dans le XLSX — deux exports du même jeu à 3 secondes d'intervalle. | `audit_raw.md` §2.1 | Le `FID` n'est **ni clé primaire, ni clé de jointure, ni moyen de déduplication**. Il est régénéré par le serveur à chaque export. Le pipeline doit **construire son propre identifiant stable** (hash nom + coordonnées). |
| **A4** | **Le CSV est le seul format faisant autorité.** XLSX et GeoJSON arrondissent les coordonnées à 8 décimales ; le shapefile tronque les noms de colonnes à 10 caractères (`prefecture_nom_bdd` → `prefecture`) et **perd l'identifiant**. | `audit_raw.md` §2 | Travailler à partir des **CSV**. Conserver le shapefile comme **preuve documentaire du CRS**. |
| **A5** | **CRS résolu et prouvé** : les 6 fichiers `.prj` sont **strictement identiques** (même empreinte MD5) et déclarent `EPSG:4326 / WGS 84`. Le CSV et le KML, eux, ne déclarent aucun CRS. | `audit_raw.md` §2.2 | Fixer `EPSG:4326` en entrée. **Tout calcul de distance ou de superficie exige une reprojection métrique préalable** — en degrés il serait faux. |
| **A6** | **Le fichier Mobile Money est le référentiel administratif complet** : à lui seul, 5 régions / 39 préfectures / **117 communes** / 372 cantons — exactement la réunion des 6 jeux. | `audit_raw.md` §5 | Permet de distinguer un **vrai zéro** (subdivision connue, sans infrastructure) d'une **absence de donnée**. Sans cela, aucun déficit ne serait démontrable. **C'est le pivot de tout le diagnostic.** |
| **A7** | **Intégrité hiérarchique validée jusqu'à la commune** : 0 commune à cheval sur 2 préfectures, 0 préfecture sur 2 régions, 0 variante orthographique après normalisation. | `audit_raw.md` §5 | Les jointures Région → Préfecture → Commune se font **sans arbitrage manuel**. Le drill-down du dashboard (critère C3) est fiable jusqu'à ce niveau. |
| **A11** | **Homonymie de cantons** : le canton *Loko* existe en **deux exemplaires distincts** — Savanes/Oti/Oti 2 (8 points MM) et Savanes/Tandjoaré/Tandjoaré 1 (1 point MM). D'où **372 noms de cantons pour 373 cantons réels**. | `audit_raw.md` §5 | **La clé de jointure au niveau canton doit être composite** (région, préfecture, commune, canton). Une jointure sur le seul nom fusionnerait silencieusement deux territoires, sans lever la moindre alerte. Piège invisible en aval. |
| **A8** | **Qualité spatiale sans défaut** : 0 géométrie invalide, 0 point en (0,0), 0 point hors du territoire, **0 doublon de position sur 19 788 points** Mobile Money. | `audit_raw.md` §3 | Aucun nettoyage géométrique lourd. Le budget temps va à l'analyse, pas au décrassage. |
| **A9** | **`operateur` est multivalué** : `Moov, Togocom` 63,9 % · `Togocom` 24,1 % · **`Nsp` 6,8 % (1 348 points)** · `Moov` 5,1 %. | `audit_raw.md` §6 | Un point ≠ un opérateur. Éclatement obligatoire avant toute agrégation par opérateur. Les 1 348 points inconnus forment une **catégorie propre** — jamais réaffectés ni supprimés. |
| **A10** | **Provenance unique et datée** : les 6 jeux portent `source_collecte = « Campagne de collecte PRISE – 2021/2022 »`. | `audit_sources.md` §2 | La date de référence du diagnostic est **2021‑2022**, pas la date de téléchargement (07/09/2026). À afficher explicitement sur le dashboard. |

### Question ouverte documentée — le canton « Loko » (rattachée à A11)

Investigation menée après signalement (reprojection EPSG:32631 avant toute mesure, cf. A5) :

| Fait mesuré | Valeur |
|---|---|
| Points Mobile Money nommés *Loko* | 9 — dont **8** en Savanes/Oti/Oti 2 et **1** en Savanes/Tandjoaré/Tandjoaré 1 |
| Distance du point Tandjoaré au point Oti le plus proche | **2,88 km** |
| Distance du point Tandjoaré au canton le plus proche de sa propre commune (*Pligou*) | **6,49 km** |
| Distance entre les centroïdes des deux groupes | 4,9 km |

Le point rattaché à Tandjoaré est donc plus de deux fois plus proche du groupe d'Oti que du reste de sa commune de rattachement.

**Deux hypothèses subsistent, non départagées :**
1. deux cantons voisins homonymes de part et d'autre d'une limite de préfecture — situation banale pour un toponyme frontalier ;
2. une erreur d'affectation lors de la collecte.

**Aucune conclusion n'est retenue** : la proximité est un indice, pas une preuve — un enregistrement légitime peut se situer près d'une limite administrative. Un test point-dans-polygone sur les contours cantonaux trancherait immédiatement ; ces contours ne sont pas disponibles (cf. §E1).

**Portée du risque** : nulle sur le pipeline. La clé composite (A11) est correcte sous les deux hypothèses. À mentionner dans la section « limites » du rapport final comme exemple de contrôle qualité mené jusqu'au bout, y compris lorsqu'il n'aboutit pas à une certitude.

### Anomalies mineures (traitement au nettoyage, sans impact structurel)

- **2 agences déclarées fermées** (`{Ferme}`) : *Agence Togocom Tabligbo* (Yoto, Maritime) et *Boutique Togocom Awassi Onorio* (Bas‑Mono, Maritime) → à exclure du stock actif, mais à conserver et afficher.
- **7 agences à statut `Nsp`** (activité inconnue) sur 90.
- **`etab_creation_date` non renseignée pour 31 agences sur 90 (34 %)** → toute analyse temporelle du déploiement serait biaisée ; à ne pas produire.
- **Espaces de bord parasites** dans `nom_localite`, `etab_adresse`, `etab_creation_date` → créent de faux doublons de modalité (`'Nsp '` vs `'Nsp'`). C'est cette anomalie qui explique que le taux de dates manquantes soit de 34 % et non 23 % : deux modalités distinctes désignaient la même absence.
- **2 enregistrements distincts nommés *Agence Togocom Sotouboua*** à ~1,2 km l'un de l'autre (localités *Laowe* et *Sotouboua*) → **doublon apparent mais non prouvé** ; à signaler, ne pas fusionner.

---

## B. Ce que contiennent réellement les 30 fichiers

Union de **toutes** les variables, tous jeux et tous formats confondus — **19 au total** :

`FID` · `id` · `geometry` · `geometry_type` · `coordonnees` · `region_nom_bdd` · `prefecture_nom_bdd` · `commune_nom_bdd` · `canton_nom_bdd` · `nom_localite` · `etab_nom` · `etab_adresse` · `etab_jour` · `etab_creation_date` · `activite_statut` · `activite_categorie` · `toilette_type` · `terrain` · `operateur`

| Recherche | Résultat |
|---|---|
| Variable de population / démographie | **AUCUNE** |
| Variable de superficie / surface | **AUCUNE** |
| Variable de couverture réseau (2G/3G/4G, signal, antenne, tour) | **AUCUNE** |
| Géométrie de zone (polygone) | **AUCUNE** — toutes les géométries sont des `Point` |

Ce n'est pas une impression : c'est une recherche exhaustive par motif sur les 19 noms de variables des 30 fichiers.

---

## C. Matrice : OBJECTIF → NÉCESSAIRE → DISPONIBLE → MANQUANT → MÉTHODE

| Obj. | Données nécessaires | Disponible | Manquant | Méthode possible | Verdict |
|---|---|---|---|---|---|
| **1** — Cartographier agences + data centers | Points géolocalisés, opérateur, statut | **Oui** : 90 agences uniques (62 Togocom, 28 Moov) + 3 data centers | Agences CANAL+ (A1) | Déduplication ; cartographie par opérateur ; agrégation aux 4 niveaux administratifs | ✅ **Traitable intégralement** |
| **2** — Mobile Money vs population | Points MM + population | **Partiel** : 19 788 points rattachés aux 117 communes | **Population** | Ratio habitants/point ; écart à la médiane ; concentration (Lorenz/Gini) | ⚠️ **Comptages seuls** — l'« adéquation avec la population » est hors de portée |
| **3** — Infrastructures vs densité démographique | Population + superficie + polygones | **Non** : seuls des libellés texte | **Polygones + population** | Densité hab/km² ; choroplèthes ; quadrant population forte / équipement faible | ❌ **Non traitable** |
| **4** — Couverture réseau, zones blanches | Couverture radio ou sites/antennes | **Non** | **Toute mesure radio** | — | ❌ **Non traitable** |
| **5** — Priorisation | Résultats 1 à 4 | Dépend de ce qui précède | Population, polygones | Indice composite + sensibilité | ⚠️ **Fortement dégradé** |

**Bilan sans données complémentaires : 1 objectif sur 5 pleinement traitable.**

---

## D. Ce qui est possible avec *uniquement* ces 30 fichiers

Il faut être franc : sans population ni polygones, le projet reste **descriptif**. Voici néanmoins ce qui est réellement démontrable, et qui a une valeur analytique :

**Analyses solides et défendables :**
1. **Diagnostic d'infrastructure exact** — 90 agences, 3 data centers, 19 788 points MM, ventilés aux 4 niveaux administratifs, avec déduplication documentée (A2).
2. **Vrais zéros mesurés** — grâce au référentiel complet (A6) : **74 communes sur 117 sans aucune agence**, **12 préfectures sur 39 sans aucune agence** (Akébou, Amou, Binah, Danyi, Est‑Mono, Kpendjal, Kpendjal‑Ouest, Lacs, Mô, Tandjoaré, Vo, Wawa). Ce sont des faits, pas des estimations.
3. **Concentration spatiale** — Maritime concentre 45,4 % des points MM ; l'amplitude entre préfectures va de 32 (Mô) à 5 121 (Golfe), médiane 224.
4. **Accessibilité géométrique** (après reprojection métrique) — distance de chaque point MM à l'agence d'opérateur la plus proche, clustering des points de service, identification des cantons isolés. Calculs rigoureux, réalisables dès maintenant.
5. **Analyse par opérateur** — après éclatement de la variable multivaluée (A9) : où Moov est-il seul, où Togocom est-il seul, où les deux coexistent, où l'opérateur est inconnu.

**Ce qui restera impossible à affirmer :**
- « telle zone est sous-desservie » → sans population, un faible comptage peut refléter une faible démographie, pas un déficit.
- « telle zone est prioritaire » → une priorisation qui ignore le nombre d'habitants concernés classerait en tête des cantons quasi déserts. Ce serait indéfendable devant un jury.
- toute densité (hab/km²), tout ratio par habitant, toute zone blanche.

**Conséquence sur la notation** : le critère C2 (8 points, le plus lourd) exige de passer de *Données → Analyse → Diagnostic → Priorisation → Décision*. Sans population, la chaîne s'arrête à **Diagnostic**.

---

## E. Les deux données manquantes, par ordre d'impact

### E1 — Population et limites administratives *(bloquant pour les objectifs 2, 3 et 5)*

**Pourquoi c'est nécessaire** : sans polygones, pas de superficie, donc pas de densité. Sans population, aucun ratio par habitant. Compter 41 points Mobile Money à Kpendjal ne dit rien tant qu'on ignore combien de personnes y vivent.

**Ce que j'ai identifié lors de l'audit de provenance** (avant ta consigne d'arrêt, consigné dans `reports/audit_sources.md`) : le catalogue open data du portail source contient quatre couches de limites administratives — *Régions*, *Préfectures*, *Communes* et *Cantons* — publiées par le même producteur, issues de la **même campagne PRISE 2021/2022**, avec **la même nomenclature** que nos fichiers. Le schéma de la couche *Cantons*, lu directement dans le catalogue, comporte : `canton_nom`, `commune_id`, `prefecture_id`, `region_id`, **`population` (entier)** et une géométrie `MultiPolygon`.

Cette couche résoudrait simultanément le manque de géométrie **et** le manque démographique, au niveau le plus fin, et s'agrégerait proprement vers commune → préfecture → région.

Les identifiants exacts de ces 4 couches sont consignés dans `reports/audit_sources.md`. **Je ne relance aucun téléchargement et ne produis aucun lien : la décision t'appartient.**

**Contrôle obligatoire si tu obtiens ces fichiers** : l'attribut `population` n'a **pas de millésime déclaré** au catalogue. Avant tout usage, je sommerai les populations cantonales et confronterai le total aux chiffres officiels du recensement national. Tant que ce contrôle n'est pas passé, **aucun indicateur par habitant ne sera produit**.

### E2 — Couverture réseau mobile *(objectif 4)*

**Constat** : aucune des 19 variables des 30 fichiers ne mesure la couverture radio.

**Position méthodologique recommandée** : ne pas prétendre mesurer ce que nous ne mesurons pas. L'objectif 4 sera traité comme un **déficit d'accessibilité aux services numériques** — distance au point de service le plus proche, densité de service — un indicateur **calculé**, nommé sans ambiguïté (« zones de sous‑desserte de service », jamais « zones blanches »), assorti de sa limite écrite noir sur blanc :

> *Une zone sans agence ni agent Mobile Money n'est pas nécessairement une zone sans réseau mobile.*

Assumer cette limite est défendable devant un jury. La maquiller ne l'est pas.

---

## F. État de validation de l'étape 1

| Point de contrôle | Statut |
|---|---|
| Inventaire des 30 fichiers (6 jeux × 5 formats) | ✅ |
| Comparaison inter-formats et choix du format faisant autorité | ✅ (A4) |
| Stabilité de l'identifiant | ✅ — **volatile** (A3) |
| CRS : déclaration, cohérence inter-fichiers, implication métier | ✅ — EPSG:4326 prouvé (A5) |
| Profil de toutes les variables (types, manquants, modalités) | ✅ |
| Contrôles géométriques (validité, emprise, doublons de position) | ✅ (A8) |
| Doublons intra-fichier **et inter-fichiers** | ✅ (A2) |
| Intégrité hiérarchique administrative | ✅ (A7) |
| Recherche exhaustive de variables démographiques / couverture | ✅ — **aucune** (§B) |
| Provenance, producteur et période | ✅ (A10) |
| Matrice objectifs → données → méthode | ✅ (§C) |
| **Décision sur les données complémentaires** | ⛔ **en attente — décision utilisateur** |
