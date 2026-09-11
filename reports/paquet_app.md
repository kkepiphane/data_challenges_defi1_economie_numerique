# Paquet de donnees du tableau de bord

Genere par `src/build_app_data.py`. L'application lit ces trois
fichiers et n'a besoin d'aucune bibliotheque geospatiale.

| Controle | Resultat | Detail |
|---|---|---|
| 39 prefectures conservees | OK | 39 entites |
| Aucune geometrie vide apres simplification | OK | preserve_topology=True |
| Point interieur present sur chaque entite | OK | representative_point |
| Table Mobile Money : aucune ligne perdue | OK | 32437 lignes |
| Points uniques conserves | OK | 19788 points distincts |
| Etablissements : aucune ligne perdue | OK | 93 etablissements |
| Paquet applicatif sous 8 Mo | OK | 4.4 Mo |
