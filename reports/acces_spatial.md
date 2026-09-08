# Analyse spatiale — accessibilite aux infrastructures

Genere par `src/spatial_access.py`. Toutes les distances sont calculees
apres reprojection en **EPSG:32631 (UTM 31N)** ; aucune mesure n'est
faite en degres.

## 1. Cibles

- Agences d'operateur **actives** : **88** (les 2 declarees fermees sont exclues des calculs d'acces)
- Data centers : **3**

## 2. Mesure A — depuis les points representatifs des 373 cantons

Couverture territoriale homogene. Aucune hypothese sur la localisation
des habitants : c'est la geometrie administrative qui est interrogee.

| Statistique | Distance a l'agence active la plus proche |
|---|---|
| Minimum | 0.5 km |
| 1er quartile | 10.6 km |
| **Mediane** | **17.2 km** |
| 3e quartile | 25.4 km |
| 9e decile | 36.9 km |
| Maximum | 61.6 km |

- Cantons a moins de **5 km** d'une agence active : **34 / 373** (9.1%)
- Cantons a moins de **10 km** d'une agence active : **84 / 373** (22.5%)
- Cantons a moins de **20 km** d'une agence active : **227 / 373** (60.9%)

- Distance mediane au data center le plus proche : **235 km** (maximum 564 km)

> Les 3 data centers sont tous a Lome. L'eloignement au data center
> mesure donc surtout la distance a la capitale : il decrit une
> centralisation, il ne mesure pas un acces numerique individuel.

**Les 12 cantons les plus eloignes d'une agence active :**

| Canton | Prefecture | Region | Distance |
|---|---|---|---|
| Mandouri | Kpendjal | Savanes | 62 km |
| Yalla | Akebou | Plateaux | 59 km |
| Kessibo | Wawa | Plateaux | 58 km |
| Gbende | Akebou | Plateaux | 57 km |
| Kamina | Est-Mono | Plateaux | 56 km |
| Djarkpanga | Plaine du Mo | Centrale | 55 km |
| Atchintse | Blitta | Centrale | 55 km |
| Badin | Est-Mono | Plateaux | 55 km |
| Veh | Akebou | Plateaux | 54 km |
| Seregbene | Akebou | Plateaux | 54 km |
| Klabe Efoukpa | Wawa | Plateaux | 52 km |
| Tindjassi | Plaine du Mo | Centrale | 52 km |

## 3. Mesure B — depuis les 19 788 points Mobile Money

**Hypothese explicite** : un agent Mobile Money s'implante la ou il y a
de la clientele. Ces points approximent donc les lieux de vie et
d'activite. *Biais assume* : cette mesure ne peut rien dire des zones
depourvues d'agent — la mesure A couvre ce point aveugle.

- Distance mediane a une agence active : **1.9 km**
- Points a moins de **5 km** d'une agence : **67.2%**
- Points a moins de **10 km** d'une agence : **73.3%**
- Points a moins de **20 km** d'une agence : **86.4%**

## 4. Eloignement par prefecture

| Prefecture | Region | Population | Dist. med. cantons | Dist. med. points MM | % points MM < 10 km |
|---|---|---|---|---|---|
| Kpendjal | Savanes | 88 365 | 47 km | 49 km | 0% |
| Est-Mono | Plateaux | 164 460 | 46 km | 38 km | 0% |
| Mô | Centrale | 52 448 | 45 km | 51 km | 0% |
| Wawa | Plateaux | 101 300 | 44 km | 49 km | 0% |
| Akébou | Plateaux | 73 830 | 43 km | 46 km | 0% |
| Anié | Plateaux | 180 158 | 29 km | 1 km | 74% |
| Blitta | Centrale | 163 272 | 28 km | 9 km | 51% |
| Kpendjal-Ouest | Savanes | 123 330 | 27 km | 27 km | 0% |
| Tandjoaré | Savanes | 138 867 | 26 km | 21 km | 0% |
| Amou | Plateaux | 114 172 | 25 km | 26 km | 0% |
| Binah | Kara | 84 199 | 25 km | 19 km | 0% |
| Tchamba | Centrale | 200 585 | 24 km | 13 km | 39% |
| Moyen-Mono | Plateaux | 90 505 | 23 km | 23 km | 32% |
| Yoto | Maritime | 174 851 | 23 km | 21 km | 0% |
| Oti-Sud | Savanes | 150 376 | 22 km | 15 km | 31% |
| Sotouboua | Centrale | 138 864 | 21 km | 10 km | 49% |
| Kéran | Kara | 128 687 | 21 km | 2 km | 57% |
| Dankpen | Kara | 185 662 | 21 km | 4 km | 54% |
| Oti | Savanes | 124 848 | 20 km | 2 km | 55% |
| Lacs | Maritime | 241 247 | 20 km | 18 km | 30% |
| Ogou | Plateaux | 253 467 | 18 km | 23 km | 19% |
| Vo | Maritime | 224 411 | 17 km | 19 km | 14% |
| Kpélé | Plateaux | 80 939 | 16 km | 2 km | 75% |
| Agou | Plateaux | 85 793 | 16 km | 8 km | 54% |
| Danyi | Plateaux | 40 240 | 16 km | 12 km | 44% |
| Tchaoudjo | Centrale | 240 360 | 15 km | 1 km | 88% |
| Haho | Plateaux | 305 096 | 14 km | 6 km | 56% |
| Tône | Savanes | 388 775 | 14 km | 2 km | 74% |
| Doufelgou | Kara | 84 767 | 14 km | 9 km | 53% |
| Kozah | Kara | 283 738 | 12 km | 2 km | 88% |
| Zio | Maritime | 500 032 | 12 km | 4 km | 78% |
| Assoli | Kara | 66 394 | 11 km | 1 km | 85% |
| Bassar | Kara | 152 065 | 10 km | 1 km | 73% |
| Kloto | Plateaux | 145 986 | 10 km | 2 km | 91% |
| Cinkassé | Savanes | 128 959 | 10 km | 1 km | 90% |
| Avé | Maritime | 111 214 | 9 km | 5 km | 85% |
| Bas-Mono | Maritime | 94 860 | 7 km | 1 km | 96% |
| Agoè-Nyivé | Maritime | 882 695 | 1 km | 1 km | 100% |
| Golfe | Maritime | 1 305 681 | 1 km | 1 km | 100% |

## 5. Controles

| Controle | Resultat | Detail |
|---|---|---|
| Points Mobile Money conserves apres deduplication | ✅ OK | 19788 |
| Accessibilite renseignee pour les 39 prefectures | ✅ OK | A : 39/39 · B : 39/39 |

## 6. Fichiers produits

| Fichier | Contenu |
|---|---|
| `acces_prefecture.csv` | 39 prefectures × indicateurs + accessibilite |
| `acces_canton.csv` | 373 cantons × distances |