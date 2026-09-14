"""
ZONES A RISQUE DE ZONE BLANCHE — UN PROXY, DECLARE COMME TEL
=============================================================
L'objectif 4 du defi demande d'identifier les zones blanches. AUCUNE mesure de
couverture radio n'existe dans les sources ouvertes (cf. reports/audit_raw.md
§7 et reports/audit_sources.md §4) : les couches « Tours telecoms » et
« Reseau telephonique » figurent au catalogue national, hors open data.

Ce script ne pretend donc PAS cartographier les zones blanches. Il designe des
zones A INVESTIGUER, a partir d'un raisonnement explicite :

    Un agent Mobile Money actif ne peut operer sans reseau mobile : chaque
    transaction passe par le reseau de l'operateur. Un agent est donc un
    TEMOIN INDIRECT de couverture. L'inverse n'est pas vrai : l'absence
    d'agent ne prouve pas l'absence de reseau.

UNITE : le CANTON (373 polygones COD-AB), le maillage le plus fin disponible.

QUATRE COMPOSANTES — plus la valeur est haute, plus le risque est eleve
-----------------------------------------------------------------------
  R1 Eloignement           distance du canton a l'agence active la plus proche
  R2 Rarete des temoins    points Mobile Money pour 100 km² (inversee)
  R3 Presence operateur    nombre d'operateurs identifies parmi les temoins
                           (0, 1 ou 2 ; inverse)
  R4 Faible densite        densite de population de la prefecture (inversee) :
                           un operateur deploie d'abord ou la densite rentabilise
                           l'antenne

Chaque composante est convertie en RANG CENTILE (0-100) sur les 373 cantons :
insensible aux valeurs extremes et aux unites. Poids egaux — aucun n'est
justifiable mieux qu'un autre sans donnee de couverture pour le calibrer.
La robustesse de ce choix est mesuree sur 2 000 ponderations aleatoires.

POURQUOI LA DENSITE PREFECTORALE, ET NON CANTONALE
---------------------------------------------------
Le RGPH-5 publie des populations cantonales, mais le rapprochement par nom avec
les polygones COD-AB n'aboutit que pour 306 cantons sur 373, avec des homonymes
canton/commune. Une densite fausse sans alerte serait pire qu'une densite
grossiere mais juste : la densite retenue est celle, validee, de la prefecture.

SIGNAL COMPLEMENTAIRE (non integre au score)
--------------------------------------------
Grille de 1 km : part de la surface de chaque canton situee a plus de 10 km de
tout agent Mobile Money. C'est la mesure la plus directe du « vide de temoins ».

Sorties :
    data/processed/zones_blanches_canton.csv
    data/processed/cantons.geojson           contours simplifies (application)
    data/processed/vide_temoins.csv          mailles de 2 km sans temoin a 10 km
    reports/zones_blanches.md

Prerequis : spatial_access.py, build_indicators.py, build_app_data.py.
"""

from __future__ import annotations

import io
import json
import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
EXT = ROOT / "data" / "external"
BOUNDARIES = EXT / "tgo_admin_boundaries.geojson.zip"
CRS_GEO, CRS_M = "EPSG:4326", "EPSG:32631"

COMPOSANTES = {
    "r1_eloignement": "Éloignement d'une agence",
    "r2_rarete_temoins": "Rareté des agents Mobile Money",
    "r3_presence_operateur": "Faible présence opérateur",
    "r4_faible_densite": "Faible densité de population",
}
SEUIL_ELEVE = 0.90          # top 10 % des scores
SEUIL_SURVEILLER = 0.75     # 75e-90e centile
RAYON_TEMOIN_KM = 10        # au-dela, aucune maille n'a de temoin proche
PAS_GRILLE_M = 1000
TOLERANCE = 0.002           # ~200 m, comme build_app_data.py
N_TIRAGES = 2000

OUT: list[str] = []
controles: list[tuple[str, bool, str]] = []


def w(line: str = "") -> None:
    OUT.append(line)
    print(line)


def centile(s: pd.Series) -> pd.Series:
    """Rang centile 0-100, ex aequo au rang moyen."""
    return (s.rank(method="average") - 1) / (len(s) - 1) * 100


def main() -> None:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                                  errors="replace")
    rng = np.random.default_rng(20220)

    # ================================================================ sources
    a3 = gpd.read_file(f"zip://{BOUNDARIES}!tgo_admin3.geojson")[
        ["adm3_name", "adm3_pcode", "adm2_pcode", "area_sqkm", "geometry"]]
    acc = pd.read_csv(PROCESSED / "acces_canton.csv")[
        ["adm3_pcode", "dist_agence_km"]]
    reco = pd.read_csv(PROCESSED / "reconciliation_prefectures.csv")[
        ["adm2_pcode", "prefecture"]]
    pref = pd.read_csv(PROCESSED / "acces_prefecture.csv")[
        ["prefecture", "region", "population", "densite_hab_km2"]]
    mm = pd.read_csv(PROCESSED / "points_mobile_money.csv")
    pts = mm.drop_duplicates("FID")

    a3m = a3.to_crs(CRS_M)
    g = gpd.GeoDataFrame(pts[["FID"]],
                         geometry=gpd.points_from_xy(pts.lon, pts.lat),
                         crs=CRS_GEO).to_crs(CRS_M)

    # ============================================= temoins par canton
    j = gpd.sjoin(g, a3m[["adm3_pcode", "geometry"]], predicate="within")
    n_mm = j.groupby("adm3_pcode").size().rename("n_mm")
    ops = (mm.merge(j[["FID", "adm3_pcode"]], on="FID")
           .query("operateur_unitaire in ['Moov', 'Togocom']"))
    par_op = (ops.groupby(["adm3_pcode", "operateur_unitaire"]).size()
              .unstack(fill_value=0).rename(columns={"Moov": "n_moov",
                                                     "Togocom": "n_togocom"}))

    c = (a3m.drop(columns="geometry")
         .merge(acc, on="adm3_pcode", how="left")
         .merge(reco, on="adm2_pcode", how="left")
         .merge(pref, on="prefecture", how="left")
         .merge(n_mm, left_on="adm3_pcode", right_index=True, how="left")
         .merge(par_op, left_on="adm3_pcode", right_index=True, how="left"))
    for col in ("n_mm", "n_moov", "n_togocom"):
        c[col] = c[col].fillna(0).astype(int)
    c["n_operateurs"] = (c.n_moov > 0).astype(int) + (c.n_togocom > 0).astype(int)
    c["mm_100km2"] = c.n_mm / c.area_sqkm * 100

    # ============================================ vide de temoins (grille)
    arbre = cKDTree(np.c_[g.geometry.x, g.geometry.y])
    xmin, ymin, xmax, ymax = a3m.total_bounds
    xs, ys = np.meshgrid(np.arange(xmin, xmax, PAS_GRILLE_M),
                         np.arange(ymin, ymax, PAS_GRILLE_M))
    grille = gpd.GeoDataFrame(geometry=gpd.points_from_xy(xs.ravel(), ys.ravel()),
                              crs=CRS_M)
    grille = gpd.sjoin(grille, a3m[["adm3_pcode", "geometry"]], predicate="within")
    d, _ = arbre.query(np.c_[grille.geometry.x, grille.geometry.y])
    grille["d_km"] = d / 1000
    grille["vide"] = grille.d_km > RAYON_TEMOIN_KM
    vide = grille.groupby("adm3_pcode").agg(
        part_vide_10km=("vide", "mean"), dist_temoin_moy_km=("d_km", "mean"),
        dist_temoin_max_km=("d_km", "max"))
    c = c.merge(vide, left_on="adm3_pcode", right_index=True, how="left")

    # ================================================================ score
    c["r1_eloignement"] = centile(c.dist_agence_km)
    c["r2_rarete_temoins"] = centile(-c.mm_100km2)
    c["r3_presence_operateur"] = centile(-c.n_operateurs)
    c["r4_faible_densite"] = centile(-np.log10(c.densite_hab_km2))
    X = c[list(COMPOSANTES)].to_numpy()
    c["score_risque"] = X.mean(axis=1)
    c["rang_risque"] = c.score_risque.rank(ascending=False, method="min").astype(int)

    s_eleve = c.score_risque.quantile(SEUIL_ELEVE)
    s_surv = c.score_risque.quantile(SEUIL_SURVEILLER)
    c["classe"] = np.select(
        [(c.score_risque >= s_eleve) | (c.n_mm == 0),
         c.score_risque >= s_surv], ["Élevé", "À surveiller"], "Faible")
    c["sans_temoin"] = c.n_mm == 0

    # ========================================================== sensibilite
    n_top = int(round(len(c) * (1 - SEUIL_ELEVE)))
    ref_top = set(c.nlargest(n_top, "score_risque").adm3_pcode)
    poids = rng.dirichlet(np.ones(4), N_TIRAGES)
    presence = np.zeros(len(c))
    rhos = []
    for p in poids:
        s = X @ p
        presence[np.argsort(-s)[:n_top]] += 1
        rhos.append(spearmanr(s, c.score_risque).statistic)
    c["frequence_top"] = presence / N_TIRAGES
    variantes = []
    for i, (col, lib) in enumerate(COMPOSANTES.items()):
        s = np.delete(X, i, axis=1).mean(axis=1)
        top = set(c.adm3_pcode.iloc[np.argsort(-s)[:n_top]])
        variantes.append({"variante": f"Sans « {lib} »",
                          "spearman": spearmanr(s, c.score_risque).statistic,
                          "top_conserve": len(top & ref_top)})

    # ============================================================ sorties
    garder = ["adm3_pcode", "adm3_name", "prefecture", "region", "area_sqkm",
              "population", "densite_hab_km2", "dist_agence_km", "n_mm",
              "n_moov", "n_togocom", "n_operateurs", "mm_100km2",
              "part_vide_10km", "dist_temoin_moy_km", "dist_temoin_max_km",
              *COMPOSANTES, "score_risque", "rang_risque", "classe",
              "sans_temoin", "frequence_top"]
    sortie = (c[garder].rename(columns={"adm3_name": "canton",
                                        "population": "population_prefecture",
                                        "densite_hab_km2": "densite_prefecture"})
              .sort_values("rang_risque"))
    sortie.to_csv(PROCESSED / "zones_blanches_canton.csv", index=False)
    pd.DataFrame(variantes).to_csv(PROCESSED / "zones_blanches_variantes.csv",
                                   index=False)

    geo = a3[["adm3_pcode", "adm3_name", "geometry"]].rename(
        columns={"adm3_name": "canton"}).copy()
    pts_int = geo.geometry.representative_point()
    geo["centre_lon"], geo["centre_lat"] = pts_int.x.round(5), pts_int.y.round(5)
    geo["geometry"] = geo.geometry.simplify(TOLERANCE, preserve_topology=True)
    gj = json.loads(geo.to_json())
    # 5 decimales ~ 1 m : au-dela, le fichier grossit sans rien montrer
    for f in gj["features"]:
        f["geometry"] = json.loads(json.dumps(f["geometry"]),
                                   parse_float=lambda v: round(float(v), 5))
    (PROCESSED / "cantons.geojson").write_text(
        json.dumps(gj, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8")

    # Mailles de 2 km : un point sur quatre de la grille de 1 km suffit a
    # l'affichage national et divise le fichier par quatre.
    g2 = grille[grille.vide].copy()
    g2 = g2[(np.round((g2.geometry.x - xmin) / PAS_GRILLE_M) % 2 == 0)
            & (np.round((g2.geometry.y - ymin) / PAS_GRILLE_M) % 2 == 0)]
    g2 = g2.to_crs(CRS_GEO)
    pd.DataFrame({"lon": g2.geometry.x.round(4), "lat": g2.geometry.y.round(4),
                  "dist_km": g2.d_km.round(1)}).to_csv(
        PROCESSED / "vide_temoins.csv", index=False)

    # ========================================================== controles
    joints = int(j.FID.nunique())
    controles.append(("373 cantons, un score chacun",
                      len(c) == 373 and c.score_risque.notna().all(),
                      f"{len(c)} cantons, {int(c.score_risque.isna().sum())} score manquant"))
    controles.append(("Agents rattaches a un canton >= 99,5 %",
                      joints / len(pts) >= 0.995,
                      f"{joints} / {len(pts)} ({joints / len(pts):.2%})"))
    controles.append(("Somme des agents par canton = agents rattaches",
                      int(c.n_mm.sum()) == joints, f"{int(c.n_mm.sum())}"))
    controles.append(("Chaque canton rattache a une prefecture validee",
                      c.prefecture.notna().all() and c.densite_hab_km2.notna().all(),
                      f"{c.prefecture.nunique()} prefectures"))
    surf = len(grille) * PAS_GRILLE_M ** 2 / 1e6
    controles.append(("Grille de 1 km : surface couverte a 1 % pres",
                      abs(surf / c.area_sqkm.sum() - 1) < 0.01,
                      f"{surf:,.0f} km² pour {c.area_sqkm.sum():,.0f} km²"
                      .replace(",", " ")))
    # Controle de coherence, pas de verite : un canton sans aucun agent doit
    # ressortir haut, sinon les composantes se neutralisent entre elles.
    med_sans = float(centile(c.score_risque)[c.sans_temoin].median())
    controles.append(("Cantons sans agent : score median au-dela du 75e centile",
                      med_sans >= 75, f"centile median {med_sans:.0f}"))
    controles.append(("Contours cantonaux : 373 entites non vides",
                      len(gj["features"]) == 373 and
                      all(f["geometry"] for f in gj["features"]),
                      f"{(PROCESSED / 'cantons.geojson').stat().st_size / 1024:.0f} Ko"))

    # ============================================================ rapport
    w("# Zones a risque de zone blanche — proxy par canton")
    w()
    w("Genere par `src/zones_blanches.py`. **Ceci n'est pas une carte de")
    w("couverture reseau** : aucune mesure radio n'est disponible en open data.")
    w("C'est une liste de zones a investiguer en priorite.")
    w()
    w("## 1. Ce qui manque, et ce qui a ete cherche")
    w()
    w("| Source | Statut |")
    w("|---|---|")
    w("| 30 fichiers du defi (6 jeux x 5 formats) | aucune variable de couverture (audit_raw.md §7) |")
    w("| Catalogue du geoportail national — « Tours telecoms », Moov, Togocom | **existe, hors open data** (audit_sources.md §4) |")
    w("| Catalogue — reseau telephonique, fibre optique | **existe, hors open data** |")
    w("| Mesures de debit participatives | evaluees puis ecartees : biais vers les zones deja connectees |")
    w()
    w("## 2. Resultats")
    w()
    n_el = int((c.classe == "Élevé").sum())
    w(f"- Cantons a risque **eleve** : **{n_el}** "
      f"(top 10 % du score, ou aucun agent Mobile Money)")
    w(f"- dont cantons **sans aucun agent Mobile Money** : **{int(c.sans_temoin.sum())}**")
    w(f"- Cantons a surveiller : {int((c.classe == 'À surveiller').sum())}")
    w(f"- Cantons ou un seul operateur est identifie : {int((c.n_operateurs == 1).sum())}")
    w(f"- Part du territoire a plus de {RAYON_TEMOIN_KM} km de tout agent : "
      f"**{grille.vide.mean():.1%}**")
    w()
    w("| Rang | Canton | Prefecture | Agents | Operateurs | Agence (km) | Vide >10 km | Score |")
    w("|---|---|---|---|---|---|---|---|")
    for _, r in sortie.head(20).iterrows():
        w(f"| {r.rang_risque} | {r.canton} | {r.prefecture} | {r.n_mm} | "
          f"{r.n_operateurs} | {r.dist_agence_km:.0f} | {r.part_vide_10km:.0%} | "
          f"{r.score_risque:.1f} |")
    w()
    w("## 3. Robustesse")
    w()
    w(f"- Correlation de Spearman moyenne sur {N_TIRAGES} ponderations "
      f"aleatoires : **{np.mean(rhos):.3f}** (minimum {np.min(rhos):.3f})")
    stables = int((c.frequence_top >= 0.9).sum())
    w(f"- Cantons dans le top {n_top} pour au moins 90 % des ponderations : "
      f"**{stables}**")
    w()
    w("| Variante | Spearman | Top conserve |")
    w("|---|---|---|")
    for v in variantes:
        w(f"| {v['variante']} | {v['spearman']:.3f} | {v['top_conserve']}/{n_top} |")
    w()
    w("## 4. Controles")
    w()
    w("| Controle | Resultat | Detail |")
    w("|---|---|---|")
    for nom, ok, detail in controles:
        w(f"| {nom} | {'OK' if ok else 'ECHEC'} | {detail} |")
    w()
    w("## 5. Limites")
    w()
    w("1. **Un agent est un temoin de couverture ; son absence n'est pas une")
    w("   preuve d'absence de reseau.** Un canton peu peuple peut etre couvert")
    w("   sans qu'aucun commerce n'y exerce le Mobile Money.")
    w("2. Les donnees datent de 2021-2022 : toute antenne posterieure est invisible.")
    w("3. Parcs et reserves peu habites ressortent mecaniquement : a verifier")
    w("   avant toute conclusion.")
    w("4. La densite est prefectorale : un canton peuple dans une prefecture")
    w("   peu dense est surestime en risque, et inversement.")

    (ROOT / "reports" / "zones_blanches.md").write_text("\n".join(OUT) + "\n",
                                                       encoding="utf-8")
    if not all(ok for _, ok, _ in controles):
        sys.exit(1)


if __name__ == "__main__":
    main()
