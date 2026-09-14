# Zones a risque de zone blanche — proxy par canton

Genere par `src/zones_blanches.py`. **Ceci n'est pas une carte de
couverture reseau** : aucune mesure radio n'est disponible en open data.
C'est une liste de zones a investiguer en priorite.

## 1. Ce qui manque, et ce qui a ete cherche

| Source | Statut |
|---|---|
| 30 fichiers du defi (6 jeux x 5 formats) | aucune variable de couverture (audit_raw.md §7) |
| Catalogue du geoportail national — « Tours telecoms », Moov, Togocom | **existe, hors open data** (audit_sources.md §4) |
| Catalogue — reseau telephonique, fibre optique | **existe, hors open data** |
| Mesures de debit participatives | evaluees puis ecartees : biais vers les zones deja connectees |

## 2. Resultats

- Cantons a risque **eleve** : **41** (top 10 % du score, ou aucun agent Mobile Money)
- dont cantons **sans aucun agent Mobile Money** : **22**
- Cantons a surveiller : 54
- Cantons ou un seul operateur est identifie : 8
- Part du territoire a plus de 10 km de tout agent : **8.0%**

| Rang | Canton | Prefecture | Agents | Operateurs | Agence (km) | Vide >10 km | Score |
|---|---|---|---|---|---|---|---|
| 1 | Diguengue | Blitta | 0 | 0 | 51 | 30% | 95.3 |
| 2 | Dikpeleou | Blitta | 0 | 0 | 47 | 100% | 95.0 |
| 3 | Tintchro | Blitta | 0 | 0 | 42 | 44% | 94.3 |
| 4 | Atchintse | Blitta | 1 | 1 | 55 | 4% | 93.9 |
| 5 | Yegue | Blitta | 0 | 0 | 39 | 90% | 93.8 |
| 6 | Katchenke | Blitta | 0 | 0 | 36 | 65% | 93.3 |
| 7 | Koffiti | Blitta | 0 | 0 | 29 | 3% | 91.4 |
| 8 | Langabou | Blitta | 0 | 0 | 28 | 39% | 91.1 |
| 9 | Tchifama | Blitta | 0 | 0 | 28 | 0% | 90.9 |
| 10 | Kpalave | Akébou | 0 | 0 | 40 | 0% | 89.6 |
| 11 | Nali | Oti-Sud | 3 | 1 | 34 | 2% | 88.6 |
| 12 | Pagala Village | Blitta | 0 | 0 | 21 | 0% | 87.5 |
| 13 | Okpahoe | Amou | 0 | 0 | 25 | 0% | 87.2 |
| 14 | Koutougou | Kéran | 0 | 0 | 21 | 62% | 83.1 |
| 15 | Tindjassi | Mô | 5 | 2 | 52 | 36% | 83.0 |
| 16 | Tabinde | Sotouboua | 2 | 0 | 17 | 0% | 83.0 |
| 17 | Kri-Kri | Tchamba | 2 | 1 | 21 | 0% | 82.8 |
| 18 | Kagnigbara | Mô | 2 | 2 | 42 | 4% | 82.7 |
| 19 | Boulohou | Mô | 3 | 2 | 37 | 7% | 82.0 |
| 20 | Pouda | Doufelgou | 0 | 0 | 23 | 38% | 81.7 |

## 3. Robustesse

- Correlation de Spearman moyenne sur 2000 ponderations aleatoires : **0.942** (minimum 0.752)
- Cantons dans le top 37 pour au moins 90 % des ponderations : **15**

| Variante | Spearman | Top conserve |
|---|---|---|
| Sans « Éloignement d'une agence » | 0.937 | 31/37 |
| Sans « Rareté des agents Mobile Money » | 0.958 | 30/37 |
| Sans « Faible présence opérateur » | 0.992 | 26/37 |
| Sans « Faible densité de population » | 0.941 | 30/37 |

## 4. Controles

| Controle | Resultat | Detail |
|---|---|---|
| 373 cantons, un score chacun | OK | 373 cantons, 0 score manquant |
| Agents rattaches a un canton >= 99,5 % | OK | 19748 / 19788 (99.80%) |
| Somme des agents par canton = agents rattaches | OK | 19748 |
| Chaque canton rattache a une prefecture validee | OK | 39 prefectures |
| Grille de 1 km : surface couverte a 1 % pres | OK | 57 261 km² pour 57 242 km² |
| Cantons sans agent : score median au-dela du 75e centile | OK | centile median 97 |
| Contours cantonaux : 373 entites non vides | OK | 242 Ko |

## 5. Limites

1. **Un agent est un temoin de couverture ; son absence n'est pas une
   preuve d'absence de reseau.** Un canton peu peuple peut etre couvert
   sans qu'aucun commerce n'y exerce le Mobile Money.
2. Les donnees datent de 2021-2022 : toute antenne posterieure est invisible.
3. Parcs et reserves peu habites ressortent mecaniquement : a verifier
   avant toute conclusion.
4. La densite est prefectorale : un canton peuple dans une prefecture
   peu dense est surestime en risque, et inversement.
