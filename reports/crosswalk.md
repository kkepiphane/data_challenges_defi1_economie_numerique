# Table de correspondance canton (COD-AB) → commune (PRISE)

Genere par `src/build_crosswalk.py`. Le rattachement est etabli par la
geometrie, pas par les noms : aucune correspondance n'est supposee.

## 1. Sources

- Polygones de canton (COD-AB `tgo_admin3`) : **373** entites, CRS `EPSG:4326`
- Points Mobile Money (PRISE) : **19788** points, CRS `EPSG:4326`
- Communes distinctes declarees dans les points : **117**

## 2. Jointure spatiale point-dans-polygone

- Points rattaches a un canton : **19748 / 19788** (99.80%)
- Points hors de tout polygone : **40** — ecartes du vote, jamais reaffectes
- Points tombant dans deux polygones : **0** (0 attendu si la couche est topologiquement propre)

**Repartition des points non rattaches, par prefecture declaree :**

| Prefecture | Points |
|---|---|
| Cinkassé | 38 |
| Tône | 2 |

> Ces points se situent en limite de territoire (littoral, frontieres).
> L'ecart provient de millesimes de contours differents, pas d'une
> erreur de coordonnees : l'audit a montre 0 point hors du Togo.

## 3. Vote majoritaire

| Situation | Cantons |
|---|---|
| Rattaches avec confiance ≥ 80 % | 321 |
| Rattaches avec confiance < 80 % (vote partage) | 30 |
| **Sans aucun point — vote impossible** | **22** |
| **Total** | **373** |

**Cantons sans aucun agent Mobile Money :**

| Canton | P-code | Prefecture COD-AB | Superficie (km²) |
|---|---|---|---|
| Game | `TG040106` | Amou | 340.8 |
| Tintchro | `TG010117` | Blitta | 285.9 |
| Langabou | `TG010110` | Blitta | 225.6 |
| Koffiti | `TG010109` | Blitta | 182.8 |
| Koutougou | `TG020605` | Keran | 179.7 |
| Yegue | `TG010121` | Blitta | 166.5 |
| Doufouli | `TG010107` | Blitta | 144.8 |
| Katchenke | `TG010108` | Blitta | 115.4 |
| Mamproug | `TG051509` | Tandjoare | 99.3 |
| Diguengue | `TG010105` | Blitta | 97.9 |
| Kpalave | `TG041005` | Akebou | 95.1 |
| Pagala Village | `TG010113` | Blitta | 94.2 |
| Massedena | `TG020509` | Doufelgou | 89.5 |
| Tchifama | `TG010116` | Blitta | 66.1 |
| Pouda | `TG020511` | Doufelgou | 41.1 |
| Boulogou | `TG051504` | Tandjoare | 39.5 |
| Avedje | `TG040103` | Amou | 39.1 |
| Dikpeleou | `TG010106` | Blitta | 27.2 |
| Pitikita | `TG020307` | Binah | 19.2 |
| Okpahoe | `TG040110` | Amou | 15.2 |
| Sangou | `TG051513` | Tandjoare | 8.9 |
| Gnoaga | `TG051704` | Cinkasse | 5.9 |

> **Information en soi** : ces cantons n'ont aucun point Mobile Money.
> C'est un resultat analytique (zone sans service recense), pas une
> lacune de donnees. Ils ne peuvent pas etre rattaches par vote et
> sont traites separement ci-dessous.

**Cantons au vote partage (confiance < 80 %) :**

| Canton | Commune majoritaire | Confiance | Points |
|---|---|---|---|
| Lome Commune | Golfe 1 | 36% | 3099 |
| Borgou | Oti 2 | 42% | 12 |
| Landa-Pozenda/Kpinzinde | Kozah 1 | 54% | 26 |
| Gape Kpodji | Zio 4 | 54% | 13 |
| Namoundjoga | Tône 4 | 58% | 36 |
| Amoutive | Golfe 1 | 59% | 86 |
| Kpessi | Est-Mono 3 | 60% | 10 |
| Kaboli | Tchamba 3 | 63% | 67 |
| Bolou Kpeta | Zio 2 | 67% | 27 |
| Danyi Kpeto-Evita | Danyi 2 | 67% | 9 |
| Zanguera | Agoè-Nyivé 5 | 67% | 111 |
| Bidjenga | Tône 1 | 67% | 6 |
| Legbassito | Agoè-Nyivé 2 | 69% | 36 |
| Alibi | Tchaoudjo 1 | 70% | 10 |
| Dalave | Zio 1 | 70% | 77 |
| Elavagnon/Atigba | Danyi 1 | 71% | 99 |
| Mission-Tove | Zio 2 | 72% | 57 |
| Kamina | Est-Mono 2 | 72% | 25 |
| Ahlon | Danyi 2 | 73% | 11 |
| Agoenyive | Agoè-Nyivé 1 | 74% | 586 |
| Landa | Kozah 1 | 74% | 39 |
| Pligou | Tandjoaré 1 | 75% | 4 |
| Aklakou | Lacs 2 | 76% | 33 |
| Danyi-Kakpa | Danyi 1 | 76% | 29 |
| Klabe Efoukpa | Wawa 3 | 76% | 42 |
| Kantindi | Tône 4 | 77% | 56 |
| Manga | Bassar 3 | 77% | 13 |
| Atalote | Kéran 2 | 78% | 9 |
| Datcha | Ogou 2 | 78% | 9 |
| Badja | Avé 2 | 78% | 9 |

## 4. Couverture des communes

- Communes declarees dans les donnees PRISE : **117**
- Communes atteintes par au moins un canton : **112**
- **Communes sans aucun canton rattache : 5** → ['Golfe 2', 'Golfe 3', 'Golfe 4', 'Kozah 3', 'Kpendjal 2']

## 5. Fusion des cantons en communes

- Cantons fusionnes : **351**
- Polygones communaux obtenus : **112**

| Controle de superficie | km² |
|---|---|
| Somme des cantons COD-AB (attribut `area_sqkm`) | 57 242.1 |
| Somme des cantons rattaches | 54 862.2 |
| Somme des communes apres fusion (attribut cumule) | 54 862.2 |
| Somme des communes apres fusion (geometrie recalculee  EPSG:32631) | 54 887.6 |

> Ecart entre attribut cumule et cantons d'origine : **0.0000 km²**. La fusion ne cree ni ne detruit de surface.

## 6. Fichiers produits

| Fichier | Contenu |
|---|---|
| `data/interim/crosswalk_canton_commune.csv` | 373 cantons, commune de rattachement et confiance |
| `data/processed/communes.gpkg` | 112 polygones communaux + superficie |

> La population n'est pas encore jointe : elle fait l'objet de l'etape
> suivante, avec son propre controle (somme = 8 095 498).