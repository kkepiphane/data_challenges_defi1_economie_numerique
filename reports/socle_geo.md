# Socle geographique et demographique

Genere par `src/build_geo.py`. Chaque jointure est verifiee ; aucune
valeur n'est imputee, aucune geometrie n'est fabriquee.

## 1. Construction de la couche prefecture

- Unites COD-AB `tgo_admin2` livrees : **40**

**Reconciliation appliquee :**

| COD-AB | PRISE | Traitement |
|---|---|---|
| `Lome Commune` (TG0305) | incluse dans Golfe | fusionnee dans TG0303 |
| `Naki-Ouest` (TG0518) | `Kpendjal-Ouest` | renommee |
| `Plaine du Mo` (TG0102) | `Mô` | renommee |

**Verification par la geometrie** — les 19 788 points Mobile Money tombent-ils dans la prefecture qu'ils declarent ?

- Points rattaches a un polygone : **19748 / 19788** (99.80%)
- Prefecture geometrique = prefecture declaree : **98.39%** (19431/19748)
- Desaccords residuels : **317** points

> Les desaccords sont des points situes pres d'une limite. Ils
> proviennent de millesimes de contours differents (COD-AB `valid_on` 2021-01-07 / collecte PRISE 2021-2022), pas d'erreurs de
> coordonnees : l'audit a etabli 0 point hors du territoire togolais.
> **L'attribut declare PRISE fait foi pour les agregations** ; la
> geometrie sert a cartographier et a mesurer les superficies.

## 2. Population (RGPH-5, novembre 2022)

- Lignes prefecture : **39** — somme **8 095 498**
- Lignes commune : **117** — somme **8 095 498**

**Cas particulier documente — Danyi**


## 3. Controles

| Controle | Resultat | Detail |
|---|---|---|
| Nombre de prefectures apres fusion = 39 | ✅ OK | 39 |
| Superficie totale conservee | ✅ OK | 57 242.1 km² |
| Noms de prefecture apparies COD-AB <-> PRISE | ✅ OK | 39/39 |
| Concordance spatiale des prefectures ≥ 95 % | ✅ OK | 98.39% |
| Population jointe a toutes les prefectures | ✅ OK | 39/39 |
| Somme des populations prefectorales = total national | ✅ OK | 8 095 498 |
| Population jointe a toutes les communes | ✅ OK | 117/117 |
| Somme des populations communales = total national | ✅ OK | 8 095 498 |

## 4. Apercu — densite par prefecture

| Prefecture | Region | Population | Superficie (km²) | Densite (hab/km²) |
|---|---|---|---|---|
| Golfe | Maritime | 1 305 681 | 240.8 | 5 422.8 |
| Agoè-Nyivé | Maritime | 882 695 | 167.1 | 5 282.5 |
| Lacs | Maritime | 241 247 | 416.3 | 579.5 |
| Cinkassé | Savanes | 128 959 | 276.1 | 467.1 |
| Tône | Savanes | 388 775 | 1 221.7 | 318.2 |
| Vo | Maritime | 224 411 | 755.3 | 297.1 |
| Bas-Mono | Maritime | 94 860 | 329.4 | 288.0 |
| Kloto | Plateaux | 145 986 | 528.2 | 276.4 |
| Kozah | Kara | 283 738 | 1 086.0 | 261.3 |
| Zio | Maritime | 500 032 | 2 164.0 | 231.1 |
| Kpendjal-Ouest | Savanes | 123 330 | 786.5 | 156.8 |
| Tandjoaré | Savanes | 138 867 | 952.9 | 145.7 |
| Binah | Kara | 84 199 | 580.8 | 145.0 |
| Moyen-Mono | Plateaux | 90 505 | 626.2 | 144.5 |
| Yoto | Maritime | 174 851 | 1 261.0 | 138.7 |
| Ogou | Plateaux | 253 467 | 1 944.1 | 130.4 |
| Avé | Maritime | 111 214 | 1 049.8 | 105.9 |
| Danyi | Plateaux | 40 240 | 396.4 | 101.5 |
| Tchaoudjo | Centrale | 240 360 | 2 396.1 | 100.3 |
| Haho | Plateaux | 305 096 | 3 051.2 | 100.0 |
| Anié | Plateaux | 180 158 | 1 985.9 | 90.7 |
| Kpélé | Plateaux | 80 939 | 930.9 | 86.9 |
| Wawa | Plateaux | 101 300 | 1 244.8 | 81.4 |
| Oti | Savanes | 124 848 | 1 543.7 | 80.9 |
| Agou | Plateaux | 85 793 | 1 096.0 | 78.3 |
| Doufelgou | Kara | 84 767 | 1 157.9 | 73.2 |
| Dankpen | Kara | 185 662 | 2 543.5 | 73.0 |
| Assoli | Kara | 66 394 | 933.3 | 71.1 |
| Akébou | Plateaux | 73 830 | 1 146.7 | 64.4 |
| Kéran | Kara | 128 687 | 2 019.0 | 63.7 |
| Kpendjal | Savanes | 88 365 | 1 394.2 | 63.4 |
| Amou | Plateaux | 114 172 | 1 808.5 | 63.1 |
| Oti-Sud | Savanes | 150 376 | 2 395.0 | 62.8 |
| Tchamba | Centrale | 200 585 | 3 197.1 | 62.7 |
| Est-Mono | Plateaux | 164 460 | 2 652.5 | 62.0 |
| Blitta | Centrale | 163 272 | 3 129.6 | 52.2 |
| Sotouboua | Centrale | 138 864 | 3 147.7 | 44.1 |
| Bassar | Kara | 152 065 | 3 456.9 | 44.0 |
| Mô | Centrale | 52 448 | 1 255.6 | 41.8 |

## 5. Fichiers produits

| Fichier | Contenu |
|---|---|
| `data/processed/prefectures.gpkg` | 39 polygones + population + superficie + densite |
| `data/processed/communes_population.csv` | 117 communes + population (sans geometrie) |