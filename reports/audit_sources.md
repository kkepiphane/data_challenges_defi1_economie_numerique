# AUDIT DE PROVENANCE DES SOURCES

Genere par `src/audit_sources.py` en interrogeant l'API publique du
geoportail national togolais. Aucune information n'est deduite du nom
des fichiers ni des URL : tout est lu dans le catalogue officiel.

## 1. Volumetrie du catalogue

- Couches **open data** : 177
- Couches presentes au catalogue mais **hors open data** : 277
- Indicateurs open data : 239
- Date de creation de la configuration open data : 2023-03-14

## 2. Identification des 6 jeux fournis dans l'enonce

| Reference enonce | Nom officiel de la couche | Description officielle | Source de collecte |
|---|---|---|---|
| URL 1 | Agents mobile money | Liste des agents mobile money (points de recharge de crédit, de transfert d'argent, de paiement des factures...) | Campagne de collecte PRISE - 2021/2022 |
| URL 2 | Datacenter - Établissements | Centres de données | Campagne de collecte PRISE - 2021/2022 |
| URL 3 | Agences - CANAL+ | Agences de l'opérateur CANAL+ | Campagne de collecte PRISE - 2021/2022 |
| URL 4 | Agences - Togocom | Agences de l'opérateur Togocom | Campagne de collecte PRISE - 2021/2022 |
| URL 5 | Agences - Moov | Agences de l'opérateur Moov | Campagne de collecte PRISE - 2021/2022 |
| URL 6 | Agences - Télécom | Agences des opérateurs télécoms | Campagne de collecte PRISE - 2021/2022 |

> **Constat de provenance** : les 6 jeux proviennent tous de la meme
> campagne de collecte. La date de reference du diagnostic est donc
> celle de cette campagne, et non la date de telechargement des fichiers.

## 3. Couches complementaires necessaires — disponibilite reelle

| Couche | UUID | Statut | Page de telechargement |
|---|---|---|---|
| Limites administratives - Régions | `f8d02e38-1d4b-42d2-99cb-c1918316a153` | **OPEN DATA** | https://geodata.gouv.tg/donnees/f8d02e38-1d4b-42d2-99cb-c1918316a153 |
| Limites administratives - Préféctures | `1fd2b7a3-329c-40f3-813f-7d3397d30ded` | **OPEN DATA** | https://geodata.gouv.tg/donnees/1fd2b7a3-329c-40f3-813f-7d3397d30ded |
| Limites administratives - Communes | `0d32e7d7-9ae2-4451-9df5-20e4bf9fa771` | **OPEN DATA** | https://geodata.gouv.tg/donnees/0d32e7d7-9ae2-4451-9df5-20e4bf9fa771 |
| Limites administratives - Cantons | `fd32bf4a-86e8-43ef-8201-fdcc41f2140e` | **OPEN DATA** | https://geodata.gouv.tg/donnees/fd32bf4a-86e8-43ef-8201-fdcc41f2140e |

### Schema exact de ces couches (lu via `get_couche_metadata`)

- **Limites administratives - Régions** — `typeName=regions` : `geometry` (MultiPolygon), `nom_region` (string)
- **Limites administratives - Préféctures** — `typeName=prefectures` : `nom_prefecture` (string), `region_id` (string), `geometry` (MultiPolygon)
- **Limites administratives - Communes** — `typeName=communes` : `nom_commune` (string), `prefecture_id` (string), `region_id` (string), `geometry` (MultiPolygon)
- **Limites administratives - Cantons** — `typeName=cantons` : `canton_nom` (string), `commune_id` (string), `prefecture_id` (string), `region_id` (string), `population` (int), `geometry` (MultiPolygon)

> **Point decisif** : la couche *Cantons* porte un attribut `population`
> de type entier. C'est la seule source de population de la meme famille
> que nos 6 fichiers (meme producteur, meme nomenclature administrative).
> Sa periode de reference devra etre verifiee apres telechargement en
> confrontant la somme nationale aux totaux publies par l'INSEED.

## 4. Couches pertinentes existantes mais NON accessibles en open data

Recherche par mots-cles sur l'ensemble du catalogue.

| Couche | Statut |
|---|---|
| Tourisme - Restaurants, bars, boites de nuit | open data |
| Tourisme - Hôtels | open data |
| Agents mobile money | open data |
| Patrimoine - Établissements touristiques | open data |
| Tourisme - Chambres d'hotel | **HORS open data — inaccessible** |
| Agents mobile money - Moov | **HORS open data — inaccessible** |
| Agents mobile money - Togocom | **HORS open data — inaccessible** |
| Tours télécom - Bâtiments | **HORS open data — inaccessible** |
| Tours télécom - Bâtiments - Moov | **HORS open data — inaccessible** |
| Tours télécom - Bâtiments - Togocom | **HORS open data — inaccessible** |
| Tours télécoms | **HORS open data — inaccessible** |
| Tours télécoms - Moov | **HORS open data — inaccessible** |
| Tours télécoms - Togocom | **HORS open data — inaccessible** |
| Réseau téléphonique aérien - Lignes | **HORS open data — inaccessible** |
| Réseau téléphonique enterré - Lignes - Cuivre et ADSL | **HORS open data — inaccessible** |
| Réseau téléphonique enterré - Lignes - Togocom | **HORS open data — inaccessible** |
| Réseau téléphonique enterré - Lignes - Moov | **HORS open data — inaccessible** |
| Réseau téléphonique enterré - Lignes - Port | **HORS open data — inaccessible** |
| Réseau téléphonique enterré - Lignes - Fibre optique | **HORS open data — inaccessible** |
| Réseau téléphonique aérien - Poteaux | **HORS open data — inaccessible** |
| Réseau téléphonique enterré - Bornes et points de raccordements | **HORS open data — inaccessible** |
| Réseau téléphonique enterré - Bornes et points de raccordements - Togocom | **HORS open data — inaccessible** |
| Réseau téléphonique enterré - Bornes et points de raccordements - Moov | **HORS open data — inaccessible** |

> **Consequence directe sur l'objectif 4** (couverture reseau / zones
> blanches) : les couches `Tours telecoms` et `Reseau telephonique` 
> existent au catalogue national mais ne sont pas ouvertes. Aucune
> mesure de couverture radio n'est donc disponible dans le perimetre
> open data du portail.

## 5. Verification du plafonnement de l'endpoint `get_couche_glimpse`

| Couche | Entites renvoyees | Valeurs d'attributs |
|---|---|---|
| Limites administratives - Régions | 5 | toutes masquees (`N/A`) |
| Limites administratives - Préféctures | 10 | toutes masquees (`N/A`) |
| Limites administratives - Communes | 10 | toutes masquees (`N/A`) |
| Limites administratives - Cantons | 10 | toutes masquees (`N/A`) |

> `get_couche_glimpse` est un **apercu de structure**, plafonne et
> anonymise. Il ne peut pas servir de substitut au telechargement :
> il documente le schema, pas les donnees.
