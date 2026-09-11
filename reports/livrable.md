# Livrable — tableau de bord interactif

Genere par `src/build_livrable.py`.

Archive : `reports/tableau_de_bord_togo.zip` — 0.5 Mo, 38 fichiers.

L'archive est EXTRAITE hors du projet puis EXECUTEE : les sept
pages tournent depuis son seul contenu avant qu'elle soit
declaree valide.

| Controle | Resultat | Detail |
|---|---|---|
| Archive lisible et sans entrée corrompue | OK | intégrité vérifiée |
| Les 10 fichiers de données sont présents | OK | 10 fichiers |
| Notice et dépendances embarquées | OK | README.md + requirements.txt |
| Aucun cache Python dans l'archive | OK | 38 entrées |
| Archive sous 10 Mo | OK | 0.5 Mo |
| Page « Vue d'ensemble » | OK | 26 blocs, 0 tables |
| Page « Infrastructures » | OK | 30 blocs, 1 tables |
| Page « Desserte & population » | OK | 22 blocs, 1 tables |
| Page « Territoires prioritaires » | OK | 32 blocs, 2 tables |
| Page « Arbitrage » | OK | 31 blocs, 2 tables |
| Page « Plan d'action » | OK | 36 blocs, 1 tables |
| Page « Méthode & limites » | OK | 30 blocs, 2 tables |
| Feuille de style réémise à chaque rendu | OK | 4 rendus successifs : [True, True, True, True] |
| Feuille de style conservée après navigation | OK | clic sur « Arbitrage » dans la navigation |
| Aucun sélecteur large n'écrase la fonte des icônes | OK | fonte symbole préservée |
| « Select all » masqué dans les filtres | OK | règle CSS présente et clé `__select_all__` confirmée dans Streamlit |
| Le sommaire refermé reste réouvrable | OK | « Deploy » masqué seul, bouton de réouverture conservé |
| Départs rapides de pondération sans exception | OK | 4 préréglages appliqués |
| Repondération de référence = DCPI publié | OK | écart max 7.11e-15 · corrélation des rangs 1.0000 |
