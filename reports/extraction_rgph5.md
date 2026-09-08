# Extraction de la population — RGPH-5 (INSEED, novembre 2022)

Genere par `src/extract_rgph5.py`. Aucun chiffre n'est saisi a la main ni
estime : tout provient du PDF officiel de l'INSEED, et rien n'est retenu
sans controle arithmetique.

- Pages du PDF : **103**
- Total national de reference (publie par l'INSEED) : **8 095 498** habitants

## 1. Volumetrie extraite

| Niveau | Pages | Lignes |
|---|---|---|
| regions | 23–23 | 8 |
| prefectures | 25–25 | 23 |
| communes | 26–32 | 162 |
| quartiers | 36–44 | 114 |
| cantons | 48–94 | 476 |
| villes | 95–96 | 39 |

### Pages exclues faute d'appariement (8)

- page 24 (prefectures) : 24 libelles pour 23 valeurs — page EXCLUE
- page 37 (quartiers) : 31 libelles pour 32 valeurs — page EXCLUE
- page 38 (quartiers) : 31 libelles pour 32 valeurs — page EXCLUE
- page 41 (quartiers) : 31 libelles pour 32 valeurs — page EXCLUE
- page 43 (quartiers) : 31 libelles pour 32 valeurs — page EXCLUE
- page 59 (cantons) : 16 libelles pour 15 valeurs — page EXCLUE
- page 90 (cantons) : 11 libelles pour 10 valeurs — page EXCLUE
- page 99 (villes) : 12 libelles pour 8 valeurs — page EXCLUE

## 2. Controles arithmetiques

**Unites regionales du RGPH-5 :**

| Unite | Population |
|---|---|
| MARITIME (GRAND LOME INCLUS) | 3 534 991 |
| PLATEAUX | 1 635 946 |
| CENTRALE | 795 529 |
| KARA | 985 512 |
| SAVANES | 1 143 520 |
| **TOTAL** | **8 095 498** |

Sous-unites detaillees par le livret, **exclues du total** pour
eviter un double comptage :

- `- DAGL` : 2 188 376 habitants
- `- MARITIME SANS GRAND LOME` : 1 346 615 habitants

| Controle | Resultat | Detail |
|---|---|---|
| Somme des 5 regions = total national | ✅ OK | 8 095 498 (5 regions) |
| Somme des communes = total national | ✅ OK | 8 095 498 (117 unites) |
| Somme des prefectures = total national | ✅ OK | 8 095 498 (39 unites) |
| Aucune commune comptee deux fois | ✅ OK | 0 doublon(s) |
| Emboitement communes : enfants sommant a leur parent | ✅ OK | 39 conformes, 0 en echec |
| Emboitement cantons : enfants sommant a leur parent | ✅ OK | 97 conformes, 0 en echec |

## 3. Fichiers produits

| Fichier | Lignes |
|---|---|
| `data/interim/rgph5_regions.csv` | 8 |
| `data/interim/rgph5_prefectures.csv` | 23 |
| `data/interim/rgph5_communes.csv` | 162 |
| `data/interim/rgph5_quartiers.csv` | 114 |
| `data/interim/rgph5_cantons.csv` | 476 |
| `data/interim/rgph5_villes.csv` | 39 |

> Fichiers **intermediaires** : libelles bruts du PDF, sans rapprochement
> avec la nomenclature PRISE ni avec les P-codes COD-AB. Ce rapprochement
> fait l'objet d'une etape distincte et tracee.