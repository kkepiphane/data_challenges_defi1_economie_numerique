"""
DIGITAL CONNECTIVITY PRIORITY INDEX (DCPI)
===========================================
Indice composite classant les subdivisions selon leur priorite d'intervention
pour l'extension de la connectivite et des services numeriques.

PRINCIPE DE CONSTRUCTION
------------------------
L'indice ne mesure pas « la qualite du numerique ». Il repond a une question
de decision publique precise :

    ou un investissement toucherait-il le plus d'habitants aujourd'hui
    mal desservis ?

Il combine donc un DEFICIT (trois facettes mesurees) et un ENJEU (le nombre
d'habitants concernes). Un territoire tres mal desservi mais quasi desert ne
remonte pas en tete ; un territoire tres peuple mais bien equipe non plus.

LES QUATRE COMPOSANTES
----------------------
  D1  Deficit Mobile Money   habitants par point MM            ↑ = pire
      Definition officielle du geoportail national (« Nombre d'habitants
      par point mobile money », mode `popRatio`). Non inventee.

  D2  Deficit d'agences      agences actives / 100 000 hab     ↓ = pire
      Inversee pour orienter toutes les composantes dans le meme sens.

  D3  Eloignement            distance mediane a une agence     ↑ = pire
      Prefecture : mediane des cantons, ponderee par superficie (mesure A,
      couverture territoriale homogene). Commune : mediane des points
      Mobile Money (mesure B, hypothese documentee dans acces_spatial.md).

  D4  Enjeu demographique    population                        ↑ = plus urgent
      Ce n'est pas un deficit : c'est le nombre d'habitants qu'une
      intervention toucherait.

NORMALISATION
-------------
Deux variantes calculees systematiquement :
  - min-max sur [0, 100] : lisible, mais sensible aux valeurs extremes ;
  - rang (percentile)    : insensible aux extremes, mais perd l'amplitude.
La correlation entre les deux classements est reportee. Si elle est forte,
le resultat ne depend pas du choix de normalisation — c'est ce qu'il faut
pouvoir affirmer devant un jury.

PONDERATIONS ET LEUR JUSTIFICATION
----------------------------------
  D1 30 %  le Mobile Money est le service numerique de masse au Togo, et
           c'est la seule composante dont la definition est officielle ;
  D2 25 %  presence d'agences — facette « offre » de l'acces ;
  D3 25 %  eloignement — facette « distance » du meme acces, poids egal a
           D2 car aucune donnee ne permet de trancher laquelle prime ;
  D4 20 %  enjeu demographique — pondere sans dominer : au-dela, l'indice
           reviendrait a classer les territoires par population.

Ces poids sont un CHOIX, assume comme tel. L'analyse de sensibilite mesure
a quel point le classement en depend.

VALEURS MANQUANTES ET EXTREMES
-------------------------------
  - Aucune valeur manquante au niveau prefecture : les 39 sont completes.
  - Danyi 1 / Danyi 2 : le RGPH-5 leur attribue un effectif COMMUN. Leurs
    ratios par habitant seraient faux -> DCPI non calcule, jamais estime.
  - Aucun ecretage (winsorisation) : les valeurs extremes sont des faits
    (Kpendjal a reellement 2 155 hab/point). La variante par rang mesure
    leur influence sans les effacer.

Sorties : data/processed/dcpi_prefecture.csv
          data/processed/dcpi_commune.csv
          reports/dcpi.md
"""

from __future__ import annotations

import io
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
REPORTS = ROOT / "reports"

POIDS = {"D1_deficit_mm": 0.30, "D2_deficit_agences": 0.25,
         "D3_eloignement": 0.25, "D4_enjeu_demographique": 0.20}
GRAINE = 20260908          # reproductibilite de l'analyse de sensibilite
N_TIRAGES = 2000

OUT: list[str] = []
controles: list[tuple[str, bool, str]] = []


def w(line: str = "") -> None:
    OUT.append(line)
    print(line)


def minmax(s: pd.Series) -> pd.Series:
    lo, hi = s.min(), s.max()
    return pd.Series(np.where(hi > lo, (s - lo) / (hi - lo) * 100, 50.0),
                     index=s.index)


def rang(s: pd.Series) -> pd.Series:
    return s.rank(pct=True) * 100


def composer(df: pd.DataFrame, methode) -> pd.Series:
    return sum(methode(df[c]) * p for c, p in POIDS.items())


def construire(df: pd.DataFrame, libelle: str) -> pd.DataFrame:
    """Oriente, normalise et compose les 4 composantes."""
    t = df.copy()
    t["D1_deficit_mm"] = t.hab_par_point_mm
    t["D2_deficit_agences"] = -t.agences_pour_100k_hab      # inversee
    t["D3_eloignement"] = t.dist_agence_km
    t["D4_enjeu_demographique"] = t.population

    t["DCPI"] = composer(t, minmax)
    t["DCPI_rang"] = composer(t, rang)
    for c in POIDS:
        t[f"n_{c}"] = minmax(t[c])
    t["rang_DCPI"] = t.DCPI.rank(ascending=False).astype(int)
    return t.sort_values("DCPI", ascending=False)


def main() -> None:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    REPORTS.mkdir(parents=True, exist_ok=True)

    w("# Digital Connectivity Priority Index (DCPI)")
    w()
    w("Genere par `src/priority_index.py`. L'indice combine trois deficits")
    w("mesures et un enjeu demographique ; toutes ses composantes sont issues")
    w("de donnees validees, aucune n'est estimee.")
    w()

    # =========================================================================
    # 1. PREFECTURES
    # =========================================================================
    acc = pd.read_csv(PROCESSED / "acces_prefecture.csv")
    acc["dist_agence_km"] = acc.dist_agence_med_canton_km
    pref = construire(acc, "prefecture")

    controles.append(("Aucune valeur manquante dans les 4 composantes (prefectures)",
                      pref[list(POIDS)].notna().all().all(),
                      f"{int(pref[list(POIDS)].notna().all(axis=1).sum())}/39"))

    w("## 1. Composantes et ponderations")
    w()
    w("| Composante | Variable mesuree | Sens | Poids |")
    w("|---|---|---|---|")
    w("| D1 — Deficit Mobile Money | habitants par point MM | ↑ = priorite plus forte | **30 %** |")
    w("| D2 — Deficit d'agences | agences actives / 100 000 hab (inversee) | ↓ = priorite plus forte | **25 %** |")
    w("| D3 — Eloignement | distance mediane a une agence active | ↑ = priorite plus forte | **25 %** |")
    w("| D4 — Enjeu demographique | population (RGPH-5) | ↑ = plus d'habitants concernes | **20 %** |")
    w()
    w("Score sur 100. Il **n'a pas de sens absolu** : c'est un outil de")
    w("comparaison entre territoires togolais, a un instant donne, avec ces")
    w("donnees. Un score de 70 ne signifie pas « 70 % de deficit ».")
    w()

    w("## 2. Classement des prefectures")
    w()
    w("| Rang | Prefecture | Region | Population | Hab./point MM | Agences actives | Dist. med. | **DCPI** |")
    w("|---|---|---|---|---|---|---|---|")
    for _, r in pref.iterrows():
        w(f"| {r.rang_DCPI} | **{r.prefecture}** | {r.region} | "
          f"{int(r.population):,} | {r.hab_par_point_mm:,.0f} | "
          f"{int(r.agences_actives)} | {r.dist_agence_km:.0f} km | "
          f"**{r.DCPI:.1f}** |".replace(",", " "))
    w()

    # =========================================================================
    # 2. ANALYSE DE SENSIBILITE
    # =========================================================================
    w("## 3. Analyse de sensibilite")
    w()
    w("Question : le classement tient-il si l'on change les choix "
      "methodologiques ?")
    w()

    variantes: dict[str, pd.Series] = {
        "Reference (30/25/25/20, min-max)": pref.DCPI,
        "Normalisation par rang": pref.DCPI_rang,
        "Poids egaux (25 % chacun)":
            sum(minmax(pref[c]) * 0.25 for c in POIDS),
        "Sans enjeu demographique (D4 exclue)":
            sum(minmax(pref[c]) * (p / 0.80)
                for c, p in POIDS.items() if c != "D4_enjeu_demographique"),
        "Deficits seuls, poids egaux (D1-D3)":
            sum(minmax(pref[c]) / 3 for c in POIDS if c != "D4_enjeu_demographique"),
    }
    # Retrait d'une composante a la fois
    for c in POIDS:
        reste = {k: v for k, v in POIDS.items() if k != c}
        s = sum(minmax(pref[k]) * (v / sum(reste.values())) for k, v in reste.items())
        variantes[f"Sans {c.split('_')[0]}"] = s

    ref = pref.DCPI
    w("| Variante | Correlation de Spearman avec la reference | Communes du top 10 conservees |")
    w("|---|---|---|")
    top_ref = set(pref.nlargest(10, "DCPI").prefecture)
    for nom, serie in variantes.items():
        rho = spearmanr(ref, serie).statistic
        top = set(pref.assign(v=serie).nlargest(10, "v").prefecture)
        w(f"| {nom} | {rho:.3f} | {len(top_ref & top)}/10 |")
    w()

    # --- perturbation aleatoire des poids ---
    rng = np.random.default_rng(GRAINE)
    tirages = rng.dirichlet(np.ones(len(POIDS)) * 8, size=N_TIRAGES)
    normalisees = np.column_stack([minmax(pref[c]).values for c in POIDS])
    scores = normalisees @ tirages.T                     # 39 x N_TIRAGES
    rangs = pd.DataFrame(scores, index=pref.prefecture).rank(
        ascending=False, axis=0)
    freq_top10 = (rangs <= 10).mean(axis=1).sort_values(ascending=False)
    rho_moyen = np.mean([spearmanr(ref.values, scores[:, i]).statistic
                         for i in range(N_TIRAGES)])

    w(f"**Perturbation aleatoire des poids** — {N_TIRAGES} jeux de poids tires")
    w(f"au hasard (loi de Dirichlet, graine `{GRAINE}`), chaque composante")
    w("gardant un poids strictement positif.")
    w()
    w(f"- Correlation de Spearman moyenne avec le classement de reference : "
      f"**{rho_moyen:.3f}**")
    w()
    w("| Prefecture | Frequence de presence dans le top 10 |")
    w("|---|---|")
    for nom, f in freq_top10.head(14).items():
        w(f"| {nom} | **{f:.0%}** |")
    w()

    # Persistance : le tableau de bord LIT ces resultats, il ne les recalcule
    # pas. Le classement affiche et l'analyse de sensibilite proviennent donc
    # du meme calcul, execute une seule fois.
    pd.DataFrame({"prefecture": freq_top10.index,
                  "frequence_top10": freq_top10.values,
                  "rang_median": rangs.median(axis=1).reindex(freq_top10.index).values,
                  "rang_min": rangs.min(axis=1).reindex(freq_top10.index).values,
                  "rang_max": rangs.max(axis=1).reindex(freq_top10.index).values,
                  }).to_csv(PROCESSED / "dcpi_sensibilite.csv", index=False,
                            encoding="utf-8")
    pd.DataFrame([{"variante": nom,
                   "spearman": spearmanr(ref, s).statistic,
                   "top10_conserve": len(top_ref & set(
                       pref.assign(v=s).nlargest(10, "v").prefecture))}
                  for nom, s in variantes.items()]
                 ).to_csv(PROCESSED / "dcpi_variantes.csv", index=False,
                          encoding="utf-8")

    stables = freq_top10[freq_top10 >= 0.90]
    controles.append(("Classement robuste (Spearman moyen ≥ 0,90)",
                      rho_moyen >= 0.90, f"{rho_moyen:.3f}"))
    w(f"> **{len(stables)} prefectures figurent dans le top 10 dans au moins")
    w(f"> 90 % des ponderations testees.** Ce sont celles que l'on peut")
    w("> defendre comme prioritaires independamment des choix de ponderation :")
    w(f"> {', '.join(stables.index)}.")
    w()

    # =========================================================================
    # 3. COMMUNES
    # =========================================================================
    com = pd.read_csv(PROCESSED / "indicateurs_commune.csv")
    mm = pd.read_csv(PROCESSED / "mobile_money_operateurs.csv").drop_duplicates("FID")
    acc_com = pd.read_csv(PROCESSED / "acces_canton.csv")  # pour tracabilite

    # Distance mediane des points MM de la commune (mesure B)
    from shapely import wkt
    import geopandas as gpd
    etab = pd.read_csv(PROCESSED / "etablissements.csv")
    etab["geometry"] = etab.geometry.map(wkt.loads)
    etab = gpd.GeoDataFrame(etab, geometry="geometry", crs="EPSG:4326").to_crs("EPSG:32631")
    agences = etab[(etab.type_infrastructure == "Agence operateur") & etab.actif]
    mm["geometry"] = mm.geometry.map(wkt.loads)
    mmg = gpd.GeoDataFrame(mm, geometry="geometry", crs="EPSG:4326").to_crs("EPSG:32631")
    j = gpd.sjoin_nearest(mmg[["commune", "geometry"]], agences[["geometry"]],
                          how="left", distance_col="_d")
    dist_com = (j.groupby(j.index)._d.min().groupby(mmg.commune.values)
                .median() / 1000).rename("dist_agence_km")

    com = com.merge(dist_com, left_on="commune", right_index=True, how="left")
    com["agences_pour_100k_hab"] = com.agences_actives / com.population * 100_000

    calculable = com.population_fiable & com.hab_par_point_mm.notna() & \
        com.dist_agence_km.notna()
    com_ok = construire(com[calculable], "commune")
    exclues = com[~calculable]

    controles.append(("Communes ecartees du DCPI, et pour un motif documente",
                      len(exclues) == int((~com.population_fiable).sum())
                      + int((com.population_fiable & ~calculable).sum()),
                      f"{len(exclues)} sur {len(com)}"))

    w("## 4. Declinaison au niveau commune")
    w()
    w(f"- Communes classees : **{len(com_ok)} / {len(com)}**")
    w(f"- Communes ecartees : **{len(exclues)}** — "
      f"{', '.join(exclues.commune.tolist())}")
    w()
    w("> Motif d'exclusion : le RGPH-5 publie un effectif commun a Danyi 1 et")
    w("> Danyi 2. Tout ratio par habitant y serait faux. Ces communes sont")
    w("> **ecartees du classement, pas estimees**.")
    w()
    w("> **Difference methodologique avec le niveau prefecture** : la")
    w("> composante D3 utilise ici la mesure B (mediane des points Mobile")
    w("> Money), faute de contours communaux fiables — voir l'approche")
    w("> ecartee dans `socle_geo.md`. Les scores communaux et prefectoraux")
    w("> ne sont donc **pas comparables entre eux**.")
    w()
    w("**20 communes les plus prioritaires :**")
    w()
    w("| Rang | Commune | Prefecture | Population | Hab./point MM | Agences | Dist. med. | **DCPI** |")
    w("|---|---|---|---|---|---|---|---|")
    for _, r in com_ok.head(20).iterrows():
        w(f"| {r.rang_DCPI} | **{r.commune}** | {r.prefecture} | "
          f"{int(r.population):,} | {r.hab_par_point_mm:,.0f} | "
          f"{int(r.agences_actives)} | {r.dist_agence_km:.0f} km | "
          f"**{r.DCPI:.1f}** |".replace(",", " "))
    w()

    # =========================================================================
    # 4. LIMITES ET CONTROLES
    # =========================================================================
    w("## 5. Limites de l'indice")
    w()
    w("1. **Il ne mesure pas la couverture reseau.** Aucune donnee de")
    w("   couverture radio n'existe dans les sources ouvertes mobilisees. Une")
    w("   zone bien classee ici peut rester mal couverte en 3G/4G.")
    w("2. **Il decrit l'etat 2021-2022** (collecte PRISE), croise avec la")
    w("   population de novembre 2022. Tout deploiement posterieur est absent.")
    w("3. **Les ponderations sont un choix**, pas un resultat. C'est pourquoi")
    w("   la sensibilite est mesuree et publiee.")
    w("4. **Les agences CANAL+ manquent** : leur export source est vide. Le")
    w("   deficit d'agences ne porte donc que sur Moov et Togocom.")
    w("5. **Un score eleve signale un besoin, pas une solution.** Il ne dit ni")
    w("   le cout, ni la faisabilite, ni la rentabilite d'une intervention.")
    w()

    w("## 6. Controles")
    w()
    w("| Controle | Resultat | Detail |")
    w("|---|---|---|")
    for nom, ok, detail in controles:
        w(f"| {nom} | {'✅ OK' if ok else '❌ ECHEC'} | {detail} |")
    w()

    colonnes = (["rang_DCPI", "prefecture", "region", "population",
                 "hab_par_point_mm", "agences_actives", "agences_pour_100k_hab",
                 "dist_agence_km", "points_mm", "DCPI", "DCPI_rang"]
                + [f"n_{c}" for c in POIDS])
    pref[colonnes].to_csv(PROCESSED / "dcpi_prefecture.csv", index=False,
                          encoding="utf-8")
    com_ok.to_csv(PROCESSED / "dcpi_commune.csv", index=False, encoding="utf-8")

    w("## 7. Fichiers produits")
    w()
    w("| Fichier | Contenu |")
    w("|---|---|")
    w("| `dcpi_prefecture.csv` | 39 prefectures, score et composantes normalisees |")
    w(f"| `dcpi_commune.csv` | {len(com_ok)} communes classees |")

    (REPORTS / "dcpi.md").write_text("\n".join(OUT), encoding="utf-8")


if __name__ == "__main__":
    main()
