# Dataset analytique et indicateurs

Genere par `src/build_indicators.py`. Chaque transformation est
controlee ; aucune valeur n'est imputee.

## 1. Etablissements — deduplication

| Fichier source | Lignes |
|---|---|
| Agences – Moov | 28 |
| Agences – Togocom | 62 |
| Agences – Telecom | 51 |
| Agences – CANAL+ | 0 |
| **Somme brute** | **141** |

- Etablissements uniques apres deduplication : **90**
- Lignes eliminees : **51** (57% de surestimation evitee)

**L'operateur reel est lu dans `activite_categorie`, pas deduit du nom du fichier :**

| Operateur | Etablissements | dont actifs |
|---|---|---|
| Moov | 28 | 28 |
| Togocom | 62 | 60 |
| **Total** | **90** | **88** |

Etablissements declares fermes, conserves et signales :

- *Agence Togocom Tabligbo* — Yoto (Maritime)
- *Boutique Togocom Awassi Onorio* — Bas-Mono (Maritime)

- Data centers : **3**, tous en Golfe (Maritime)
- **Table `etablissements` : 93 lignes** (90 agences + 3 data centers)

## 2. Mobile Money — variable `operateur` multivaluee

- Points recenses : **19788**

| Modalite brute | Points | Part |
|---|---|---|
| `Moov, Togocom` | 12649 | 63.9% |
| `Togocom` | 4773 | 24.1% |
| `Nsp` | 1348 | 6.8% |
| `Moov` | 1018 | 5.1% |

**Apres eclatement — presence par operateur** (un point servi par deux operateurs compte dans les deux lignes) :

| Operateur | Points ou il est present | Part des points |
|---|---|---|
| Togocom | 17422 | 88.0% |
| Moov | 13667 | 69.1% |
| Non renseigne | 1348 | 6.8% |

> **Lecture** : 4 773 points ne servent que Togocom contre 1 018 pour Moov seul
> — un desequilibre de couverture a analyser, pas un artefact de saisie.

## 3. Indicateur central — habitants par point Mobile Money

Definition reprise de l'indicateur officiel du geoportail national
(« Nombre d'habitants par point mobile money », mode de calcul `popRatio`).
Un ratio **eleve** signale une desserte **faible**.

**Reference nationale : 409 habitants par point.**

| Prefecture | Region | Population | Points MM | Hab./point | Ecart au national |
|---|---|---|---|---|---|
| Kpendjal | Savanes | 88 365 | 41 | 2 155 | ×5.27 |
| Blitta | Centrale | 163 272 | 90 | 1 814 | ×4.43 |
| Mô | Centrale | 52 448 | 32 | 1 639 | ×4.01 |
| Moyen-Mono | Plateaux | 90 505 | 81 | 1 117 | ×2.73 |
| Yoto | Maritime | 174 851 | 160 | 1 093 | ×2.67 |
| Tchamba | Centrale | 200 585 | 205 | 978 | ×2.39 |
| Dankpen | Kara | 185 662 | 190 | 977 | ×2.39 |
| Kpendjal-Ouest | Savanes | 123 330 | 129 | 956 | ×2.34 |
| Oti-Sud | Savanes | 150 376 | 159 | 946 | ×2.31 |
| Kéran | Kara | 128 687 | 139 | 926 | ×2.26 |
| Tandjoaré | Savanes | 138 867 | 159 | 873 | ×2.13 |
| Avé | Maritime | 111 214 | 128 | 869 | ×2.12 |
| Akébou | Plateaux | 73 830 | 87 | 849 | ×2.07 |
| Est-Mono | Plateaux | 164 460 | 209 | 787 | ×1.92 |
| Haho | Plateaux | 305 096 | 453 | 674 | ×1.65 |
| Amou | Plateaux | 114 172 | 175 | 652 | ×1.59 |
| Zio | Maritime | 500 032 | 779 | 642 | ×1.57 |
| Anié | Plateaux | 180 158 | 285 | 632 | ×1.55 |
| Agoè-Nyivé | Maritime | 882 695 | 1398 | 631 | ×1.54 |
| Ogou | Plateaux | 253 467 | 421 | 602 | ×1.47 |
| Bas-Mono | Maritime | 94 860 | 183 | 518 | ×1.27 |
| Vo | Maritime | 224 411 | 476 | 471 | ×1.15 |
| Doufelgou | Kara | 84 767 | 184 | 461 | ×1.13 |
| Wawa | Plateaux | 101 300 | 244 | 415 | ×1.01 |
| Binah | Kara | 84 199 | 212 | 397 | ×0.97 |
| Sotouboua | Centrale | 138 864 | 355 | 391 | ×0.96 |
| Agou | Plateaux | 85 793 | 224 | 383 | ×0.94 |
| Bassar | Kara | 152 065 | 436 | 349 | ×0.85 |
| Oti | Savanes | 124 848 | 368 | 339 | ×0.83 |
| Lacs | Maritime | 241 247 | 741 | 326 | ×0.80 |
| Kpélé | Plateaux | 80 939 | 255 | 317 | ×0.78 |
| Tône | Savanes | 388 775 | 1280 | 304 | ×0.74 |
| Assoli | Kara | 66 394 | 228 | 291 | ×0.71 |
| Kloto | Plateaux | 145 986 | 503 | 290 | ×0.71 |
| Danyi | Plateaux | 40 240 | 142 | 283 | ×0.69 |
| Golfe | Maritime | 1 305 681 | 5121 | 255 | ×0.62 |
| Cinkassé | Savanes | 128 959 | 543 | 237 | ×0.58 |
| Kozah | Kara | 283 738 | 1562 | 182 | ×0.44 |
| Tchaoudjo | Centrale | 240 360 | 1411 | 170 | ×0.42 |

## 4. Deserts d'agences

- Prefectures sans aucune agence active : **13 / 39**  soit **1 621 720 habitants** (20.0% du pays)

| Prefecture | Region | Population | Points MM | Hab./point |
|---|---|---|---|---|
| Lacs | Maritime | 241 247 | 741 | 326 |
| Vo | Maritime | 224 411 | 476 | 471 |
| Yoto | Maritime | 174 851 | 160 | 1 093 |
| Est-Mono | Plateaux | 164 460 | 209 | 787 |
| Tandjoaré | Savanes | 138 867 | 159 | 873 |
| Kpendjal-Ouest | Savanes | 123 330 | 129 | 956 |
| Amou | Plateaux | 114 172 | 175 | 652 |
| Wawa | Plateaux | 101 300 | 244 | 415 |
| Kpendjal | Savanes | 88 365 | 41 | 2 155 |
| Binah | Kara | 84 199 | 212 | 397 |
| Akébou | Plateaux | 73 830 | 87 | 849 |
| Mô | Centrale | 52 448 | 32 | 1 639 |
| Danyi | Plateaux | 40 240 | 142 | 283 |

- Communes sans aucune agence active : **75 / 117**  soit **3 371 081 habitants**

## 5. Controles

| Controle | Resultat | Detail |
|---|---|---|
| Deduplication des agences : 141 lignes -> 90 etablissements | ✅ OK | 141 -> 90 |
| Eclatement operateur : aucun point perdu | ✅ OK | 19788 points distincts / 19788 |
| Somme des points MM agreges par prefecture = total | ✅ OK | 19788 / 19788 |
| Somme des points MM agreges par commune = total | ✅ OK | 19788 / 19788 |
| Somme des agences agregees = etablissements uniques | ✅ OK | 90 / 90 |
| Communes a population partagee : marquees et privees de ratio | ✅ OK | 0 commune(s) — aucune dans cette edition du livret |

## 6. Fichiers produits

| Fichier | Contenu |
|---|---|
| `etablissements.csv` | 93 points dedupliques, identifiant stable |
| `mobile_money_operateurs.csv` | 32437 lignes point × operateur |
| `indicateurs_prefecture.csv` | 39 prefectures × indicateurs |
| `indicateurs_commune.csv` | 117 communes × indicateurs |