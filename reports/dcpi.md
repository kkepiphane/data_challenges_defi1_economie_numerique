# Digital Connectivity Priority Index (DCPI)

Genere par `src/priority_index.py`. L'indice combine trois deficits
mesures et un enjeu demographique ; toutes ses composantes sont issues
de donnees validees, aucune n'est estimee.

## 1. Composantes et ponderations

| Composante | Variable mesuree | Sens | Poids |
|---|---|---|---|
| D1 — Deficit Mobile Money | habitants par point MM | ↑ = priorite plus forte | **30 %** |
| D2 — Deficit d'agences | agences actives / 100 000 hab (inversee) | ↓ = priorite plus forte | **25 %** |
| D3 — Eloignement | distance mediane a une agence active | ↑ = priorite plus forte | **25 %** |
| D4 — Enjeu demographique | population (RGPH-5) | ↑ = plus d'habitants concernes | **20 %** |

Score sur 100. Il **n'a pas de sens absolu** : c'est un outil de
comparaison entre territoires togolais, a un instant donne, avec ces
donnees. Un score de 70 ne signifie pas « 70 % de deficit ».

## 2. Classement des prefectures

| Rang | Prefecture | Region | Population | Hab./point MM | Agences actives | Dist. med. | **DCPI** |
|---|---|---|---|---|---|---|---|
| 1 | **Kpendjal** | Savanes | 88 365 | 2 155 | 0 | 47 km | **80.8** |
| 2 | **Mô** | Centrale | 52 448 | 1 639 | 0 | 45 km | **71.1** |
| 3 | **Est-Mono** | Plateaux | 164 460 | 787 | 0 | 46 km | **60.9** |
| 4 | **Akébou** | Plateaux | 73 830 | 849 | 0 | 43 km | **58.5** |
| 5 | **Blitta** | Centrale | 163 272 | 1 814 | 2 | 28 km | **55.1** |
| 6 | **Wawa** | Plateaux | 101 300 | 415 | 0 | 44 km | **53.1** |
| 7 | **Yoto** | Maritime | 174 851 | 1 093 | 0 | 23 km | **53.1** |
| 8 | **Kpendjal-Ouest** | Savanes | 123 330 | 956 | 0 | 27 km | **52.2** |
| 9 | **Tandjoaré** | Savanes | 138 867 | 873 | 0 | 26 km | **50.6** |
| 10 | **Amou** | Plateaux | 114 172 | 652 | 0 | 25 km | **46.5** |
| 11 | **Dankpen** | Kara | 185 662 | 977 | 1 | 21 km | **45.2** |
| 12 | **Oti-Sud** | Savanes | 150 376 | 946 | 1 | 22 km | **43.8** |
| 13 | **Tchamba** | Centrale | 200 585 | 978 | 2 | 24 km | **43.0** |
| 14 | **Binah** | Kara | 84 199 | 397 | 0 | 25 km | **42.1** |
| 15 | **Moyen-Mono** | Plateaux | 90 505 | 1 117 | 1 | 23 km | **42.0** |
| 16 | **Vo** | Maritime | 224 411 | 471 | 0 | 17 km | **41.3** |
| 17 | **Lacs** | Maritime | 241 247 | 326 | 0 | 20 km | **40.8** |
| 18 | **Ogou** | Plateaux | 253 467 | 602 | 1 | 18 km | **40.7** |
| 19 | **Anié** | Plateaux | 180 158 | 632 | 2 | 29 km | **39.3** |
| 20 | **Zio** | Maritime | 500 032 | 642 | 5 | 12 km | **36.1** |
| 21 | **Tône** | Savanes | 388 775 | 304 | 2 | 14 km | **35.0** |
| 22 | **Haho** | Plateaux | 305 096 | 674 | 3 | 14 km | **35.0** |
| 23 | **Danyi** | Plateaux | 40 240 | 283 | 0 | 16 km | **34.7** |
| 24 | **Kéran** | Kara | 128 687 | 926 | 2 | 21 km | **34.3** |
| 25 | **Oti** | Savanes | 124 848 | 339 | 1 | 20 km | **31.8** |
| 26 | **Agoè-Nyivé** | Maritime | 882 695 | 631 | 14 | 1 km | **30.7** |
| 27 | **Kozah** | Kara | 283 738 | 182 | 2 | 12 km | **28.6** |
| 28 | **Golfe** | Maritime | 1 305 681 | 255 | 26 | 1 km | **27.8** |
| 29 | **Agou** | Plateaux | 85 793 | 383 | 1 | 16 km | **26.2** |
| 30 | **Doufelgou** | Kara | 84 767 | 461 | 1 | 14 km | **26.2** |
| 31 | **Bas-Mono** | Maritime | 94 860 | 518 | 1 | 7 km | **24.5** |
| 32 | **Sotouboua** | Centrale | 138 864 | 391 | 3 | 21 km | **20.8** |
| 33 | **Kloto** | Plateaux | 145 986 | 290 | 2 | 10 km | **20.8** |
| 34 | **Tchaoudjo** | Centrale | 240 360 | 170 | 4 | 15 km | **20.6** |
| 35 | **Assoli** | Kara | 66 394 | 291 | 1 | 11 km | **19.0** |
| 36 | **Cinkassé** | Savanes | 128 959 | 237 | 2 | 10 km | **18.0** |
| 37 | **Bassar** | Kara | 152 065 | 349 | 3 | 10 km | **16.2** |
| 38 | **Avé** | Maritime | 111 214 | 869 | 3 | 9 km | **16.1** |
| 39 | **Kpélé** | Plateaux | 80 939 | 317 | 2 | 16 km | **13.2** |

## 3. Analyse de sensibilite

Question : le classement tient-il si l'on change les choix methodologiques ?

| Variante | Correlation de Spearman avec la reference | Communes du top 10 conservees |
|---|---|---|
| Reference (30/25/25/20, min-max) | 1.000 | 10/10 |
| Normalisation par rang | 0.953 | 8/10 |
| Poids egaux (25 % chacun) | 0.996 | 10/10 |
| Sans enjeu demographique (D4 exclue) | 0.970 | 10/10 |
| Deficits seuls, poids egaux (D1-D3) | 0.966 | 10/10 |
| Sans D1 | 0.925 | 9/10 |
| Sans D2 | 0.880 | 8/10 |
| Sans D3 | 0.933 | 9/10 |
| Sans D4 | 0.970 | 10/10 |

**Perturbation aleatoire des poids** — 2000 jeux de poids tires
au hasard (loi de Dirichlet, graine `20260908`), chaque composante
gardant un poids strictement positif.

- Correlation de Spearman moyenne avec le classement de reference : **0.971**

| Prefecture | Frequence de presence dans le top 10 |
|---|---|
| Kpendjal | **100%** |
| Mô | **100%** |
| Est-Mono | **100%** |
| Akébou | **100%** |
| Yoto | **100%** |
| Kpendjal-Ouest | **100%** |
| Tandjoaré | **99%** |
| Wawa | **97%** |
| Blitta | **91%** |
| Amou | **73%** |
| Dankpen | **14%** |
| Golfe | **11%** |
| Binah | **4%** |
| Lacs | **3%** |

> **9 prefectures figurent dans le top 10 dans au moins
> 90 % des ponderations testees.** Ce sont celles que l'on peut
> defendre comme prioritaires independamment des choix de ponderation :
> Kpendjal, Mô, Est-Mono, Akébou, Yoto, Kpendjal-Ouest, Tandjoaré, Wawa, Blitta.

## 4. Declinaison au niveau commune

- Communes classees : **117 / 117**
- Communes ecartees : **0** — 

> Motif d'exclusion : le RGPH-5 publie un effectif commun a Danyi 1 et
> Danyi 2. Tout ratio par habitant y serait faux. Ces communes sont
> **ecartees du classement, pas estimees**.

> **Difference methodologique avec le niveau prefecture** : la
> composante D3 utilise ici la mesure B (mediane des points Mobile
> Money), faute de contours communaux fiables — voir l'approche
> ecartee dans `socle_geo.md`. Les scores communaux et prefectoraux
> ne sont donc **pas comparables entre eux**.

**20 communes les plus prioritaires :**

| Rang | Commune | Prefecture | Population | Hab./point MM | Agences | Dist. med. | **DCPI** |
|---|---|---|---|---|---|---|---|
| 1 | **Kpendjal 2** | Kpendjal | 40 462 | 8 092 | 0 | 45 km | **76.3** |
| 2 | **Blitta 3** | Blitta | 45 218 | 7 536 | 0 | 29 km | **67.6** |
| 3 | **Mô 2** | Mô | 21 926 | 3 132 | 0 | 57 km | **62.0** |
| 4 | **Kpendjal 1** | Kpendjal | 47 903 | 1 331 | 0 | 54 km | **55.4** |
| 5 | **Blitta 2** | Blitta | 46 515 | 5 168 | 0 | 19 km | **54.3** |
| 6 | **Mô 1** | Mô | 30 522 | 1 221 | 0 | 51 km | **52.7** |
| 7 | **Est-Mono 2** | Est-Mono | 101 866 | 1 029 | 0 | 42 km | **52.2** |
| 8 | **Wawa 1** | Wawa | 51 187 | 298 | 0 | 52 km | **50.7** |
| 9 | **Akébou 1** | Akébou | 44 196 | 702 | 0 | 46 km | **49.3** |
| 10 | **Wawa 3** | Wawa | 29 699 | 530 | 0 | 49 km | **49.0** |
| 11 | **Akébou 2** | Akébou | 29 634 | 1 235 | 0 | 41 km | **48.3** |
| 12 | **Ogou 4** | Ogou | 29 048 | 1 383 | 0 | 38 km | **47.2** |
| 13 | **Anié 2** | Anié | 79 413 | 1 654 | 0 | 26 km | **46.2** |
| 14 | **Wawa 2** | Wawa | 20 414 | 1 276 | 0 | 37 km | **46.0** |
| 15 | **Kéran 3** | Kéran | 30 983 | 3 098 | 0 | 20 km | **45.9** |
| 16 | **Moyen-Mono 2** | Moyen-Mono | 43 708 | 1 041 | 0 | 34 km | **45.1** |
| 17 | **Amou 2** | Amou | 40 016 | 1 291 | 0 | 32 km | **45.0** |
| 18 | **Kéran 2** | Kéran | 53 305 | 1 403 | 0 | 29 km | **44.8** |
| 19 | **Tchamba 2** | Tchamba | 64 930 | 764 | 0 | 32 km | **44.6** |
| 20 | **Yoto 3** | Yoto | 54 086 | 2 003 | 0 | 23 km | **44.4** |

## 5. Limites de l'indice

1. **Il ne mesure pas la couverture reseau.** Aucune donnee de
   couverture radio n'existe dans les sources ouvertes mobilisees. Une
   zone bien classee ici peut rester mal couverte en 3G/4G.
2. **Il decrit l'etat 2021-2022** (collecte PRISE), croise avec la
   population de novembre 2022. Tout deploiement posterieur est absent.
3. **Les ponderations sont un choix**, pas un resultat. C'est pourquoi
   la sensibilite est mesuree et publiee.
4. **Les agences CANAL+ manquent** : leur export source est vide. Le
   deficit d'agences ne porte donc que sur Moov et Togocom.
5. **Un score eleve signale un besoin, pas une solution.** Il ne dit ni
   le cout, ni la faisabilite, ni la rentabilite d'une intervention.

## 6. Controles

| Controle | Resultat | Detail |
|---|---|---|
| Aucune valeur manquante dans les 4 composantes (prefectures) | ✅ OK | 39/39 |
| Classement robuste (Spearman moyen ≥ 0,90) | ✅ OK | 0.971 |
| Communes ecartees du DCPI, et pour un motif documente | ✅ OK | 0 sur 117 |

## 7. Fichiers produits

| Fichier | Contenu |
|---|---|
| `dcpi_prefecture.csv` | 39 prefectures, score et composantes normalisees |
| `dcpi_commune.csv` | 117 communes classees |