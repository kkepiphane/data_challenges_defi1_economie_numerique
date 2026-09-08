# AUDIT DES DONNEES BRUTES — Defi 1 (Economie numerique, Togo)

Genere par `src/audit_raw.py`. Toute valeur est **lue** dans les fichiers ;
aucune n'est estimee, imputee ni completee.

## 1. Inventaire : 6 jeux x 5 formats

| Jeu de donnees | CSV | XLSX | KML | GeoJSON | ZIP (shapefile) |
|---|---|---|---|---|---|
| `canal_plus` | 192.0 o | 15.4 Ko | 1.2 Ko | 147.0 o | 1.5 Ko |
| `moov` | 8.5 Ko | 36.5 Ko | 41.5 Ko | 17.0 Ko | 3.6 Ko |
| `togocom` | 19.0 Ko | 61.7 Ko | 90.9 Ko | 37.9 Ko | 6.2 Ko |
| `telecom` | 15.5 Ko | 53.5 Ko | 74.8 Ko | 31.1 Ko | 5.2 Ko |
| `mobile_money` | 2.9 Mo | 7.8 Mo | 15.5 Mo | 6.4 Mo | 602.8 Ko |
| `datacenter` | 1.2 Ko | 18.3 Ko | 5.7 Ko | 2.1 Ko | 1.8 Ko |

**30 fichiers** presents pour 6 jeux de donnees.

## 2. Quel format fait autorite ?

Question auditee : les 5 formats portent-ils la meme information ?
Comparaison sur un jeu non vide (`moov`), meme entite.

| Format | Enregistrements | Colonnes | Identifiant | Precision des coordonnees |
|---|---|---|---|---|
| CSV | 28 | 14 (noms complets) | `FID` | `POINT (0.9770733333333333 8.560676666666666)` |
| XLSX | 28 | 15 (noms complets) | `id` | `[0.97707333,8.56067667]` — **arrondi** |
| KML | — | schema `SimpleField` (noms complets) | aucun | `0.9770733333333333,8.560676666666666` |
| GeoJSON | 28 | noms complets | `id` (feature) | `[0.97707333, 8.56067667]` — **arrondi** |
| Shapefile | 28 | 13 — **noms tronques a 10 car.** | **aucun** | `0.9770733333333333 8.560676666666666` |

- Noms de colonnes du shapefile : `region_nom`, `prefecture`, `commune_no`, `canton_nom`, `nom_locali`, `etab_nom`, `etab_adres`, `etab_jour`, `etab_creat`, `activite_s`, `activite_c`, `toilette_t`, `geometry`
- Noms de colonnes du CSV : `FID`, `region_nom_bdd`, `prefecture_nom_bdd`, `commune_nom_bdd`, `canton_nom_bdd`, `nom_localite`, `etab_nom`, `etab_adresse`, `etab_jour`, `etab_creation_date`, `activite_statut`, `activite_categorie`, `toilette_type`, `geometry`

### 2.1 L'identifiant `FID` est-il stable ?

- Meme entite (Agence Moov, coordonnees `0.97707333,8.56067667`) :
  - identifiant dans le **CSV**  : `_mview_agences_etablissements_agences.fid--4db96f1c_1a07ca73f53_68de`
  - identifiant dans le **XLSX** : `_mview_agences_etablissements_agences.fid--4db96f1c_1a07ca73f53_68fa`

> **Verdict : l'identifiant est VOLATILE.** Les deux fichiers decrivent le meme jeu, exporte a quelques secondes d'intervalle, et pourtant les identifiants different. Le `FID` est regenere par le serveur a chaque export : il n'est ni une cle primaire, ni une cle de jointure, ni un moyen de deduplication entre fichiers. Le pipeline devra construire son propre identifiant stable.

### 2.2 Systeme de coordonnees (CRS)

- Fichiers `.prj` presents dans **6/6** shapefiles.
- Definitions distinctes : **1** → toutes identiques
- CRS declare, lu par GeoPandas : **EPSG:4326**
- Encodage declare des attributs (`.cst`) : **ISO-8859-1** (alors que CSV et GeoJSON sont en UTF-8)

> Le CSV et le KML ne declarent aucun CRS. Le shapefile, lui, l'affirme :
> **EPSG:4326 / WGS 84, degres decimaux**, de facon identique sur tous les
> jeux. C'est cette declaration qui fait foi. Consequence directe : tout
> calcul de distance ou de superficie exigera une **reprojection prealable**
> vers un CRS metrique — en degres, ces calculs seraient faux.

### 2.3 Format retenu pour la suite du projet

**Le CSV**, seul format cumulant : noms de variables complets, precision
maximale des coordonnees, et presence de tous les enregistrements. Le
shapefile est conserve comme **preuve documentaire du CRS**. Le XLSX et le
GeoJSON sont ecartes (coordonnees arrondies a 8 decimales).

## 3. Audit detaille de chaque jeu (a partir des CSV)

### 3.1 `canal_plus`

- Enregistrements : **0** (CSV) / 0 (GeoJSON) / `totalFeatures` declare : 0
- Horodatage d'export : 2026-09-07T16:22:18.700Z
- Variables (14) : `FID`, `region_nom_bdd`, `prefecture_nom_bdd`, `commune_nom_bdd`, `canton_nom_bdd`, `nom_localite`, `etab_nom`, `etab_adresse`, `etab_jour`, `etab_creation_date`, `activite_statut`, `activite_categorie`, `toilette_type`, `geometry`

> **JEU VIDE — 0 enregistrement.** Ce n'est pas une erreur de lecture :
> le serveur joint lui-meme une note dans le shapefile livre :
>
> « The query result is empty, and the geometric type of the features is unknwon:an empty point shapefile has been created to fill the zip file »
>
> A declarer comme **donnee non disponible**. Il serait faux d'en
> conclure une absence d'agences sur le terrain.

### 3.2 `moov`

- Enregistrements : **28** (CSV) / 28 (GeoJSON) / `totalFeatures` declare : 28
- Horodatage d'export : 2026-09-07T16:21:38.749Z
- Variables (14) : `FID`, `region_nom_bdd`, `prefecture_nom_bdd`, `commune_nom_bdd`, `canton_nom_bdd`, `nom_localite`, `etab_nom`, `etab_adresse`, `etab_jour`, `etab_creation_date`, `activite_statut`, `activite_categorie`, `toilette_type`, `geometry`

| Variable | Renseignees | NaN | `Nsp`/`Néant` | Distinctes | Modalites (exemples) |
|---|---|---|---|---|---|
| `FID` | 28 | 0 | 0 | 28 | _mview_agences_etablissements_agences. ; _mview_agences_etablissements_agences. ; _mview_agences_etablissements_agences. |
| `region_nom_bdd` | 28 | 0 | 0 | 5 | Centrale ; Maritime ; Kara |
| `prefecture_nom_bdd` | 28 | 0 | 0 | 15 | Sotouboua ; Tchaoudjo ; Blitta |
| `commune_nom_bdd` | 28 | 0 | 0 | 22 | Sotouboua 1 ; Tchaoudjo 1 ; Blitta 1 |
| `canton_nom_bdd` | 28 | 0 | 0 | 23 | Sotouboua ; Sokodè (Komah) ; Blitta-Village |
| `nom_localite` | 28 | 0 | 0 | 28 | Sotouboua ; Kossobio ; Blitta Sous L'antenne  |
| `etab_nom` | 28 | 0 | 0 | 28 | Agence Moov Sotouboua ; Agence Moov Sokode ; Agence Moov Blitta Sous L'Antenne  |
| `etab_adresse` | 28 | 0 | 0 | 28 | Agence Moov Sotouboua, Sotouboua ; Agence Moov Sokode, Kossobio, 400BP701 ; Agence Moov Blitta Sous L'Antenne , Bl |
| `etab_jour` | 28 | 0 | 0 | 6 | {Lundi,Mardi,Mercredi,jeudi,Vendredi,S ; {Lundi,Mardi,Mercredi,jeudi,Vendredi} ; {Lundi,Mardi,Mercredi,Vendredi,jeudi,S |
| `etab_creation_date` | 17 | 0 | 11 | 11 | 2011 ; 2018 ; 2017 |
| `activite_statut` | 26 | 0 | 2 | 2 | {Utilise} |
| `activite_categorie` | 28 | 0 | 0 | 1 | Agence Moov |
| `toilette_type` | 22 | 0 | 6 | 6 | {WCs,Latrines a eau} ; {WCs,Douches} ; {Latrines a eau} |
| `geometry` | 28 | 0 | 0 | 28 | POINT (lon lat) |

**Controle geometrique :** emprise lon [0.02077 ; 1.33799], lat [6.13049 ; 11.09723] · invalides : 0 · vides : 0 · hors Togo : 0 · en (0,0) : 0 · positions dupliquees : 0

**Doublons :** `FID` dupliques : 0 · lignes identiques hors `FID` : 0

**Espaces de bord parasites :** `nom_localite` (6), `etab_nom` (2), `etab_adresse` (8), `etab_creation_date` (2) → produit de faux doublons de modalites (ex. `'Nsp '` vs `'Nsp'`).

### 3.3 `togocom`

- Enregistrements : **62** (CSV) / 62 (GeoJSON) / `totalFeatures` declare : 62
- Horodatage d'export : 2026-09-07T16:21:59.113Z
- Variables (14) : `FID`, `region_nom_bdd`, `prefecture_nom_bdd`, `commune_nom_bdd`, `canton_nom_bdd`, `nom_localite`, `etab_nom`, `etab_adresse`, `etab_jour`, `etab_creation_date`, `activite_statut`, `activite_categorie`, `toilette_type`, `geometry`

| Variable | Renseignees | NaN | `Nsp`/`Néant` | Distinctes | Modalites (exemples) |
|---|---|---|---|---|---|
| `FID` | 62 | 0 | 0 | 62 | _mview_agences_etablissements_agences. ; _mview_agences_etablissements_agences. ; _mview_agences_etablissements_agences. |
| `region_nom_bdd` | 62 | 0 | 0 | 5 | Centrale ; Maritime ; Kara |
| `prefecture_nom_bdd` | 62 | 0 | 0 | 27 | Sotouboua ; Golfe ; Tchaoudjo |
| `commune_nom_bdd` | 62 | 0 | 0 | 42 | Sotouboua 1 ; Golfe 4 ; Tchaoudjo 1 |
| `canton_nom_bdd` | 62 | 0 | 0 | 44 | Sotouboua ; Amoutivé ; Sokodè (Komah) |
| `nom_localite` | 62 | 0 | 0 | 61 | Laowe ; Assivito ; Zongo |
| `etab_nom` | 62 | 0 | 0 | 61 | Agence Togocom Sotouboua ; Agence Togocom Assivito ; Boutique Togocom Tchakala |
| `etab_adresse` | 62 | 0 | 0 | 62 | Agence Togocom Sotouboua, Laowe ; Agence Togocom Assivito, Assivito ; Boutique Togocom Tchakala, Zongo, BP24 |
| `etab_jour` | 59 | 0 | 3 | 15 | {Lundi,Mardi,Mercredi,jeudi,Vendredi,S ; {Lundi,Mardi,Mercredi,jeudi,Vendredi,S ; {Mardi,Lundi,Mercredi,jeudi,Vendredi,S |
| `etab_creation_date` | 42 | 0 | 20 | 19 | 2022 ; 2014 ; 2007 |
| `activite_statut` | 57 | 0 | 5 | 3 | {Utilise} ; {Ferme} |
| `activite_categorie` | 62 | 0 | 0 | 1 | Agence Togocom |
| `toilette_type` | 45 | 0 | 17 | 11 | {Douches} ; {WCs,Douches} ; {WCs,Latrines a eau} |
| `geometry` | 62 | 0 | 0 | 62 | POINT (lon lat) |

**Controle geometrique :** emprise lon [0.03966 ; 1.62870], lat [6.12942 ; 11.08793] · invalides : 0 · vides : 0 · hors Togo : 0 · en (0,0) : 0 · positions dupliquees : 0

**Doublons :** `FID` dupliques : 0 · lignes identiques hors `FID` : 0

**Espaces de bord parasites :** `nom_localite` (11), `etab_nom` (1), `etab_adresse` (11), `etab_creation_date` (8) → produit de faux doublons de modalites (ex. `'Nsp '` vs `'Nsp'`).

### 3.4 `telecom`

- Enregistrements : **51** (CSV) / 51 (GeoJSON) / `totalFeatures` declare : 51
- Horodatage d'export : 2026-09-07T16:21:12.783Z
- Variables (14) : `FID`, `region_nom_bdd`, `prefecture_nom_bdd`, `commune_nom_bdd`, `canton_nom_bdd`, `nom_localite`, `etab_nom`, `etab_adresse`, `etab_jour`, `etab_creation_date`, `activite_statut`, `activite_categorie`, `toilette_type`, `geometry`

| Variable | Renseignees | NaN | `Nsp`/`Néant` | Distinctes | Modalites (exemples) |
|---|---|---|---|---|---|
| `FID` | 51 | 0 | 0 | 51 | _mview_agences_etablissements_agences. ; _mview_agences_etablissements_agences. ; _mview_agences_etablissements_agences. |
| `region_nom_bdd` | 51 | 0 | 0 | 1 | Maritime |
| `prefecture_nom_bdd` | 51 | 0 | 0 | 6 | Golfe ; Agoè-Nyivé ; Zio |
| `commune_nom_bdd` | 51 | 0 | 0 | 18 | Golfe 4 ; Golfe 6 ; Agoè-Nyivé 1 |
| `canton_nom_bdd` | 51 | 0 | 0 | 21 | Amoutivé ; Baguida ; Agoè-Nyivé |
| `nom_localite` | 51 | 0 | 0 | 47 | Assivito ; Baguida ; Agoe |
| `etab_nom` | 51 | 0 | 0 | 51 | Agence Togocom Assivito ; Agence Togocom Baguida ; Moov Store Agoe |
| `etab_adresse` | 51 | 0 | 0 | 51 | Agence Togocom Assivito, Assivito ; Agence Togocom Baguida, Baguida ; Moov Store Agoe, Agoe |
| `etab_jour` | 49 | 0 | 2 | 12 | {Lundi,Mardi,Mercredi,jeudi,Vendredi,S ; {Mardi,Lundi,Mercredi,jeudi,Vendredi,S ; {Lundi,Mardi,Mercredi,jeudi,Vendredi,S |
| `etab_creation_date` | 29 | 0 | 22 | 13 | 2022 ; 2001 ; 2018 |
| `activite_statut` | 45 | 0 | 6 | 3 | {Utilise} ; {Ferme} |
| `activite_categorie` | 51 | 0 | 0 | 2 | Agence Togocom ; Agence Moov |
| `toilette_type` | 36 | 0 | 15 | 6 | {WCs} ; {Latrines a eau} ; {WCs,Douches} |
| `geometry` | 51 | 0 | 0 | 51 | POINT (lon lat) |

**Controle geometrique :** emprise lon [0.91429 ; 1.62870], lat [6.12942 ; 6.67508] · invalides : 0 · vides : 0 · hors Togo : 0 · en (0,0) : 0 · positions dupliquees : 0

**Doublons :** `FID` dupliques : 0 · lignes identiques hors `FID` : 0

**Espaces de bord parasites :** `nom_localite` (8), `etab_nom` (2), `etab_adresse` (8), `etab_creation_date` (9) → produit de faux doublons de modalites (ex. `'Nsp '` vs `'Nsp'`).

### 3.5 `mobile_money`

- Enregistrements : **19788** (CSV) / 19788 (GeoJSON) / `totalFeatures` declare : 19788
- Horodatage d'export : 2026-09-07T16:23:50.567Z
- Variables (7) : `FID`, `region_nom_bdd`, `prefecture_nom_bdd`, `commune_nom_bdd`, `canton_nom_bdd`, `operateur`, `geometry`

| Variable | Renseignees | NaN | `Nsp`/`Néant` | Distinctes | Modalites (exemples) |
|---|---|---|---|---|---|
| `FID` | 19788 | 0 | 0 | 19788 | _mview_tel_agents_mobile_money.fid--4d ; _mview_tel_agents_mobile_money.fid--4d ; _mview_tel_agents_mobile_money.fid--4d |
| `region_nom_bdd` | 19788 | 0 | 0 | 5 | Savanes ; Maritime ; Plateaux |
| `prefecture_nom_bdd` | 19788 | 0 | 0 | 39 | Tône ; Kpendjal-Ouest ; Golfe |
| `commune_nom_bdd` | 19788 | 0 | 0 | 117 | Tône 4 ; Kpendjal-Ouest 1 ; Tône 1 |
| `canton_nom_bdd` | 19788 | 0 | 0 | 372 | Sanfatoute ; Naki-Est ; Dapaong |
| `operateur` | 18440 | 0 | 1348 | 4 | Moov, Togocom ; Togocom ; Moov |
| `geometry` | 19788 | 0 | 0 | 19788 | POINT (lon lat) |

**Controle geometrique :** emprise lon [-0.10360 ; 1.80408], lat [6.11345 ; 11.12449] · invalides : 0 · vides : 0 · hors Togo : 0 · en (0,0) : 0 · positions dupliquees : 0

**Doublons :** `FID` dupliques : 0 · lignes identiques hors `FID` : 0

### 3.6 `datacenter`

- Enregistrements : **3** (CSV) / 3 (GeoJSON) / `totalFeatures` declare : 3
- Horodatage d'export : 2026-09-07T16:22:37.432Z
- Variables (14) : `FID`, `region_nom_bdd`, `prefecture_nom_bdd`, `commune_nom_bdd`, `canton_nom_bdd`, `nom_localite`, `etab_nom`, `etab_adresse`, `etab_jour`, `etab_creation_date`, `terrain`, `activite_statut`, `toilette_type`, `geometry`

| Variable | Renseignees | NaN | `Nsp`/`Néant` | Distinctes | Modalites (exemples) |
|---|---|---|---|---|---|
| `FID` | 3 | 0 | 0 | 3 | _mview_datacenter_etablissements_datac ; _mview_datacenter_etablissements_datac ; _mview_datacenter_etablissements_datac |
| `region_nom_bdd` | 3 | 0 | 0 | 1 | Maritime |
| `prefecture_nom_bdd` | 3 | 0 | 0 | 1 | Golfe |
| `commune_nom_bdd` | 3 | 0 | 0 | 3 | Golfe 3 ; Golfe 4 ; Golfe 5 |
| `canton_nom_bdd` | 3 | 0 | 0 | 3 | Bè-Ouest ; Amoutivé ; Aflao-Gakli |
| `nom_localite` | 3 | 0 | 0 | 3 | GTA ; Nyekonakpoe ; Avenou |
| `etab_nom` | 3 | 0 | 0 | 3 | Lomé Data Center (LDC) ; E-Gouv NOC ; Cloud & Racks - Café Informatique |
| `etab_adresse` | 3 | 0 | 0 | 3 | Lome Data Center (LDC), GTA ; E-Gouv NOC, Nyekonakpoe ; Cloud & Racks - Cafe Informatique, Ave |
| `etab_jour` | 3 | 0 | 0 | 2 | {Lundi,Mardi,Mercredi,jeudi,Vendredi,S ; {Lundi,Mardi,Mercredi,jeudi,Vendredi} |
| `etab_creation_date` | 3 | 0 | 0 | 3 | 2022 ; 2016 ; 2021 |
| `terrain` | 3 | 0 | 0 | 2 | Domaine public de l Etat ou des collec ; Prive - entreprise |
| `activite_statut` | 3 | 0 | 0 | 1 | {Construit et Utilise} |
| `toilette_type` | 3 | 0 | 0 | 1 | {WCs} |
| `geometry` | 3 | 0 | 0 | 3 | POINT (lon lat) |

**Controle geometrique :** emprise lon [1.19163 ; 1.21152], lat [6.12870 ; 6.19249] · invalides : 0 · vides : 0 · hors Togo : 0 · en (0,0) : 0 · positions dupliquees : 0

**Doublons :** `FID` dupliques : 0 · lignes identiques hors `FID` : 0

## 4. Recouvrement entre les jeux « Agences »

Question auditee : les 4 exports « Agences » sont-ils disjoints ?
La deduplication ne peut PAS s'appuyer sur le `FID` (§2.1). Cle retenue :
**nom de l'etablissement + coordonnees arrondies a 1e-6°** (~0,1 m).

| Jeu | Lignes | `activite_categorie` |
|---|---|---|
| `moov` | 28 | {'Agence Moov': 28} |
| `togocom` | 62 | {'Agence Togocom': 62} |
| `telecom` | 51 | {'Agence Togocom': 34, 'Agence Moov': 17} |
| `canal_plus` | 0 | — (vide) |

| Paire de jeux | Etablissements en commun |
|---|---|
| `moov` ∩ `togocom` | 0 |
| `moov` ∩ `telecom` | 17 |
| `togocom` ∩ `telecom` | 34 |

- Somme brute des lignes des 4 fichiers : **141**
- Etablissements reellement uniques : **90**
- Enregistrements exclusifs a `telecom` : **0**

> **`Agences - Telecom` n'est pas un operateur supplementaire** : c'est un
> agregat deja contenu dans `moov` ∪ `togocom`. Empiler les 4 fichiers
> afficherait **141 agences au lieu de 90**, soit une
> surestimation de **57%** des le premier KPI.

**Statut d'activite des 90 agences uniques :**

| Statut | Effectif |
|---|---|
| `{Utilise}` | 81 |
| `Nsp` | 7 |
| `{Ferme}` | 2 |

Agences declarees fermees (a exclure du stock actif, mais a conserver) :

- *Agence Togocom Tabligbo* — Yoto (Maritime)
- *Boutique Togocom Awassi Onorio* — Bas-Mono (Maritime)

**Date de creation** non renseignee pour **31 agences sur 90** (34%) → toute analyse temporelle du deploiement serait biaisee.

## 5. Referentiel administratif reellement present

| Jeu | Regions | Prefectures | Communes | Cantons |
|---|---|---|---|---|
| `canal_plus` | — | — | — | — |
| `moov` | 5 | 15 | 22 | 23 |
| `togocom` | 5 | 27 | 42 | 44 |
| `telecom` | 1 | 6 | 18 | 21 |
| `mobile_money` | 5 | 39 | 117 | 372 |
| `datacenter` | 1 | 1 | 3 | 3 |
| **UNION** | **5** | **39** | **117** | **372** |

> **Le jeu `mobile_money` couvre a lui seul l'integralite du referentiel**
> administratif observable. Il fournit donc la liste exhaustive des
> subdivisions, ce qui permet de distinguer un **vrai zero** (subdivision
> connue, sans infrastructure) d'une **absence de donnee**. C'est la
> condition sans laquelle aucun deficit ne serait demontrable.

**Regions observees :** Centrale, Kara, Maritime, Plateaux, Savanes

**Integrite hierarchique :**

- Communes rattachees a plusieurs prefectures : **0**
- Prefectures rattachees a plusieurs regions : **0**
- **Cantons rattaches a plusieurs communes : 1**

> ⚠ **Homonymie de cantons detectee.** Les cantons suivants portent le
> meme nom tout en appartenant a des communes differentes :
>
> - **Loko** → Savanes / Oti / Oti 2 · Savanes / Tandjoaré / Tandjoaré 1
>

- Noms de cantons distincts : **372**
- Quadruplets (region, prefecture, commune, canton) distincts : **373**

> **La cle de jointure au niveau canton doit etre COMPOSITE.** Joindre
> sur le seul `canton_nom_bdd` fusionnerait des territoires distincts
> sans declencher la moindre alerte. Toute jointure cantonale utilisera
> le quadruplet complet.

- Cantons par commune : min **1**, mediane **3**, max **10** (Agou 1)
- Communes ayant plusieurs graphies (casse/accents) : **0**

> Les jointures Region → Prefecture → Commune se feront **sans arbitrage**
> manuel. La navigation drill-down du dashboard est donc realisable de
> facon fiable (critere C3).

**Subdivisions depourvues d'agence d'operateur** (vrais zeros, mesurables grace au referentiel complet) :

- Communes sans aucune agence : **74 / 117**
- Prefectures sans aucune agence : **12 / 39** → Akébou, Amou, Binah, Danyi, Est-Mono, Kpendjal, Kpendjal-Ouest, Lacs, Mô, Tandjoaré, Vo, Wawa

## 6. Mobile Money — profil specifique

- Enregistrements : **19788**

| Modalite brute de `operateur` | Effectif | Part |
|---|---|---|
| `Moov, Togocom` | 12649 | 63.9% |
| `Togocom` | 4773 | 24.1% |
| `Nsp` | 1348 | 6.8% |
| `Moov` | 1018 | 5.1% |

> Variable **multivaluee** : un point Mobile Money n'est pas un operateur.
> Toute agregation par operateur exige un eclatement prealable, et les
> **1348 points a operateur inconnu** doivent former une categorie propre —
> jamais etre reaffectes ni supprimes silencieusement.

- Positions uniques : **19788** pour 19788 enregistrements → 0 doublon(s) de position.

**Repartition par region (comptage brut — non interpretable sans population) :**

| Region | Points MM | Part |
|---|---|---|
| Maritime | 8986 | 45.4% |
| Plateaux | 3079 | 15.6% |
| Kara | 2951 | 14.9% |
| Savanes | 2679 | 13.5% |
| Centrale | 2093 | 10.6% |

- Amplitude entre prefectures : de **32** (Mô) a **5121** (Golfe) points, mediane **224**.

> Ces comptages **ne prouvent aucun deficit**. Une prefecture peu peuplee
> avec peu de points peut etre correctement desservie. La conversion en
> indicateur de desserte exige la population, absente de ces fichiers (§7).

## 7. Couverture des 5 objectifs du challenge

| # | Objectif | Donnee necessaire | Presente ? |
|---|---|---|---|
| 1 | Cartographier agences + data centers | Points geolocalises par operateur | **OUI** — 90 agences uniques + 3 data centers |
| 1 | idem — CANAL+ | Agences CANAL+ | **NON** — export vide (§3.1) |
| 2 | Mobile Money vs population | Points Mobile Money | **OUI** — 19788 points |
| 2 | idem | Population par subdivision | **NON** — absente des 6 jeux |
| 3 | Infrastructures vs densite | Population + superficie | **NON** |
| 3 | idem | Limites administratives (polygones) | **NON** — seuls des libelles texte |
| 4 | Couverture reseau / zones blanches | Couverture radio ou sites/antennes | **NON** — aucune couche de ce type dans les 6 jeux |
| 5 | Priorisation | Depend des lignes ci-dessus | Partiel |

> **Aucun des 30 fichiers livres ne contient de variable demographique, de
> superficie, de geometrie de zone, ni de mesure de couverture reseau.**
> Verifie colonne par colonne sur les 6 jeux (§3).
