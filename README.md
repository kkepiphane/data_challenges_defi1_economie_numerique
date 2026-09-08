# Accès aux télécommunications et aux services numériques au Togo

Diagnostic territorial et priorisation d'investissement, à partir de données ouvertes.

> **Question à laquelle ce travail répond**
> Où faut-il investir en priorité pour réduire les inégalités d'accès aux
> télécommunications et aux services numériques au Togo, et pourquoi ?

---

## Résultat en une page

**Référence nationale : 409 habitants par point Mobile Money.** Cette moyenne
masque un rapport de **1 à 12,7** entre préfectures.

| | Constat mesuré |
|---|---|
| **90 agences** d'opérateur | et non 141 : le jeu « Agences – Télécom » est un doublon intégral de Moov ∪ Togocom |
| **2 opérateurs**, pas 4 | CANAL+ est vide à la source ; « Télécom » n'est pas un opérateur |
| **13 préfectures sur 39** | sans aucune agence active — 20 % de la population |
| **75 communes sur 117** | sans aucune agence active |
| **3 centres de données** | tous les trois à Lomé |
| **Kpendjal** | 2 155 hab./point Mobile Money, 0 agence, 47 km jusqu'à la plus proche |

**Neuf préfectures** restent dans le top 10 des priorités pour au moins 90 % des
2 000 pondérations testées : Kpendjal, Mô, Est‑Mono, Akébou, Yoto,
Kpendjal‑Ouest, Tandjoaré, Wawa, Blitta.

---

## Démarrage

```bash
pip install -r requirements.txt      # voir la note pdftotext dans le fichier
streamlit run dashboard/app.py
```

Pour rejouer toute la chaîne depuis les données brutes :

```bash
python src/audit_raw.py          # inventaire, profils, doublons, CRS
python src/extract_rgph5.py      # population INSEED, validée par sommes
python src/build_geo.py          # contours, superficies, densités
python src/build_indicators.py   # déduplication, ratios par habitant
python src/spatial_access.py     # distances (reprojection EPSG:32631)
python src/priority_index.py     # indice DCPI + analyse de sensibilité
python src/build_deck_figures.py # visuels du support
python src/build_deck.py         # support de présentation, 10 diapositives
```

Chaque script écrit son propre rapport de contrôle dans `reports/`.
**25 contrôles arithmétiques** sont rejoués à chaque exécution.

## Livrables

| Livrable | Fichier |
|---|---|
| Tableau de bord interactif | `streamlit run dashboard/app.py` |
| Support de présentation, 10 diapositives | `reports/Defi1_Togo_Connectivite_numerique.pptx` |
| Rapports de contrôle, un par étape | `reports/*.md` |
| Datasets analytiques | `data/processed/` |

Aucun chiffre du support n'est saisi à la main : tous sont calculés à partir
de `data/processed/`. Corriger une source en amont met le support à jour sans
retoucher une seule diapositive.

---

## Ce que le projet garantit

**Aucune donnée inventée.** Toute valeur affichée provient d'une source
identifiée ou d'un indicateur calculé dont la formule est publiée. Quand une
donnée manque, elle est déclarée manquante — jamais estimée.

**Tout est vérifié par l'arithmétique.** La population extraite du PDF de
l'INSEED somme exactement à **8 095 498 habitants** aux trois niveaux
(5 régions, 39 préfectures, 117 communes), sans écart d'une unité. Les
superficies se conservent à la fusion. Les agrégations retrouvent les effectifs
d'origine.

**Les contrôles ont réellement servi.** Deux échecs ont évité des erreurs
graves : une jointure sur des noms accentués faisait tomber **neuf préfectures
à zéro point Mobile Money** — dont Agoè‑Nyivé et ses 882 695 habitants ; et une
somme régionale à 11 630 489 a révélé un double comptage du Grand Lomé.

**Ce qui a été écarté est documenté.** Trois pistes ont été mises en œuvre ou
évaluées puis abandonnées, preuves conservées : la reconstitution des contours
communaux par fusion de cantons (rejetée — 65,6 % des points tombent dans un
canton à cheval sur plusieurs communes), l'usage de mesures de débit issues de
tests de vitesse (biaisées vers les usagers déjà connectés), et l'écrêtage des
valeurs extrêmes de l'indice.

---

## Sources

| Source | Producteur | Période | Usage |
|---|---|---|---|
| Agences opérateurs, agents Mobile Money, data centers | Géoportail national | Collecte PRISE 2021‑2022 | Infrastructures, nomenclature |
| RGPH‑5, livret 01 | INSEED | Dénombrement 23 oct. – 16 nov. 2022 | Population |
| Limites administratives COD‑AB v02 | OCHA / ITOS | Valide au 07/01/2021 | Contours, superficies |

Les 30 fichiers PRISE ont été livrés en 5 formats. **Le CSV fait autorité** :
seul format cumulant noms de variables complets et précision maximale des
coordonnées. Le shapefile est conservé comme preuve du CRS — ses six fichiers
`.prj` sont strictement identiques et déclarent EPSG:4326.

---

## Deux unités d'analyse, chacune à son niveau de validité prouvé

| Unité | Rôle | Pourquoi |
|---|---|---|
| **Préfecture (39)** | géographique — polygones, superficie, densité, cartes | concordance spatiale mesurée à **98,4 %** |
| **Commune (117)** | statistique — ratios par habitant, comptages | population validée ; pas de contours fiables à ce niveau |

Les scores des deux niveaux **ne sont pas comparables** : la composante
d'éloignement n'y repose pas sur la même mesure.

---

## Limites à connaître avant de citer ces résultats

1. **La couverture réseau mobile n'est pas mesurée.** Aucune des 19 variables
   des fichiers sources ne décrit la couverture radio. *Une zone sans agence ni
   agent Mobile Money n'est pas nécessairement une zone sans réseau mobile.*
2. **Les agences CANAL+ sont absentes** — export vide à la source.
3. **Trois millésimes croisés** : infrastructures 2021‑2022, population
   novembre 2022, contours janvier 2021. Tout déploiement postérieur est invisible.
4. **Les pondérations de l'indice sont un choix** — d'où les 2 000 pondérations
   alternatives testées et publiées.
5. **Un score élevé signale un besoin, pas une solution** : ni coût, ni
   faisabilité, ni rentabilité.

---

## Structure

```
data/raw/          30 fichiers PRISE (6 jeux × 5 formats)
data/external/     RGPH-5 (INSEED), limites COD-AB
data/interim/      extractions intermédiaires
data/processed/    datasets analytiques finaux
src/               chaîne de traitement, un script par étape
dashboard/         application Streamlit (lecture seule)
reports/           un rapport de contrôle par étape
```
