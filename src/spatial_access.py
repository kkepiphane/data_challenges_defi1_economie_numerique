"""
ANALYSE SPATIALE — ACCESSIBILITE AUX INFRASTRUCTURES
=====================================================
Mesure l'eloignement physique aux infrastructures telecoms, en complement
des ratios par habitant.

REPROJECTION OBLIGATOIRE
------------------------
Les sources sont en EPSG:4326 (degres). Toute distance calculee en degres
serait fausse : un degre de longitude vaut ~110 km a l'equateur mais varie
avec la latitude. Tout est donc reprojete en **EPSG:32631 (UTM 31N)**,
CRS metrique couvrant le Togo (lon 0-6 E).

DEUX MESURES COMPLEMENTAIRES, AUX HYPOTHESES DIFFERENTES
---------------------------------------------------------
A. Depuis les CANTONS (373 points representatifs COD-AB `center_lat/lon`)
   -> couvre le territoire de facon homogene, y compris les zones sans
      aucun service. Ne suppose rien sur la localisation des habitants.

B. Depuis les POINTS MOBILE MONEY (19 788)
   -> approxime les lieux d'activite economique. HYPOTHESE EXPLICITE :
      un agent Mobile Money s'installe la ou il y a de la clientele, donc
      de la population. Biais assume : cette mesure ignore par
      construction les zones depourvues d'agent.

Les deux sont rapportees. A sert a l'indice de priorite (couverture
territoriale complete), B sert au diagnostic de la desserte effective.

CIBLES
------
  - agences d'operateur ACTIVES (88 sur 90 : 2 declarees fermees)
  - data centers (3, tous a Lome)

Sorties : data/processed/acces_prefecture.csv
          data/processed/acces_canton.csv
          reports/acces_spatial.md
"""

from __future__ import annotations

import io
import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely import wkt
from shapely.geometry import Point

ROOT = Path(__file__).resolve().parents[1]
EXT = ROOT / "data" / "external"
PROCESSED = ROOT / "data" / "processed"
REPORTS = ROOT / "reports"

BOUNDARIES = EXT / "tgo_admin_boundaries.geojson.zip"
CRS_GEO = "EPSG:4326"
CRS_M = "EPSG:32631"
SEUILS_KM = (5, 10, 20)

OUT: list[str] = []
controles: list[tuple[str, bool, str]] = []


def w(line: str = "") -> None:
    OUT.append(line)
    print(line)


def plus_proche(source: gpd.GeoDataFrame, cible: gpd.GeoDataFrame) -> np.ndarray:
    """Distance en km de chaque point source a la cible la plus proche."""
    if len(cible) == 0:
        return np.full(len(source), np.nan)
    jointure = gpd.sjoin_nearest(source[["geometry"]], cible[["geometry"]],
                                 how="left", distance_col="_d")
    # sjoin_nearest peut renvoyer plusieurs ex aequo : on garde le minimum
    return jointure.groupby(jointure.index)._d.min().reindex(source.index).values / 1000


def main() -> None:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    REPORTS.mkdir(parents=True, exist_ok=True)

    w("# Analyse spatiale — accessibilite aux infrastructures")
    w()
    w("Genere par `src/spatial_access.py`. Toutes les distances sont calculees")
    w("apres reprojection en **EPSG:32631 (UTM 31N)** ; aucune mesure n'est")
    w("faite en degres.")
    w()

    # =========================================================================
    # 1. CIBLES
    # =========================================================================
    etab = pd.read_csv(PROCESSED / "etablissements.csv")
    etab["geometry"] = etab.geometry.map(wkt.loads)
    etab = gpd.GeoDataFrame(etab, geometry="geometry", crs=CRS_GEO).to_crs(CRS_M)

    agences = etab[(etab.type_infrastructure == "Agence operateur") & etab.actif]
    datacenters = etab[etab.type_infrastructure == "Data center"]

    w("## 1. Cibles")
    w()
    w(f"- Agences d'operateur **actives** : **{len(agences)}** "
      f"(les 2 declarees fermees sont exclues des calculs d'acces)")
    w(f"- Data centers : **{len(datacenters)}**")
    w()

    # =========================================================================
    # 2. MESURE A — DEPUIS LES CANTONS
    # =========================================================================
    a3 = gpd.read_file(f"zip://{BOUNDARIES}!tgo_admin3.geojson")[
        ["adm3_name", "adm3_pcode", "adm2_name", "adm1_name", "area_sqkm",
         "center_lat", "center_lon"]]
    cantons = gpd.GeoDataFrame(
        a3, geometry=[Point(lon, lat) for lon, lat in
                      zip(a3.center_lon, a3.center_lat)], crs=CRS_GEO).to_crs(CRS_M)

    cantons["dist_agence_km"] = plus_proche(cantons, agences)
    cantons["dist_datacenter_km"] = plus_proche(cantons, datacenters)

    w("## 2. Mesure A — depuis les points representatifs des 373 cantons")
    w()
    w("Couverture territoriale homogene. Aucune hypothese sur la localisation")
    w("des habitants : c'est la geometrie administrative qui est interrogee.")
    w()
    d = cantons.dist_agence_km
    w("| Statistique | Distance a l'agence active la plus proche |")
    w("|---|---|")
    w(f"| Minimum | {d.min():.1f} km |")
    w(f"| 1er quartile | {d.quantile(.25):.1f} km |")
    w(f"| **Mediane** | **{d.median():.1f} km** |")
    w(f"| 3e quartile | {d.quantile(.75):.1f} km |")
    w(f"| 9e decile | {d.quantile(.90):.1f} km |")
    w(f"| Maximum | {d.max():.1f} km |")
    w()
    for s in SEUILS_KM:
        part = (d <= s).mean()
        w(f"- Cantons a moins de **{s} km** d'une agence active : "
          f"**{int((d <= s).sum())} / {len(d)}** ({part:.1%})")
    w()
    w(f"- Distance mediane au data center le plus proche : "
      f"**{cantons.dist_datacenter_km.median():.0f} km** "
      f"(maximum {cantons.dist_datacenter_km.max():.0f} km)")
    w()
    w("> Les 3 data centers sont tous a Lome. L'eloignement au data center")
    w("> mesure donc surtout la distance a la capitale : il decrit une")
    w("> centralisation, il ne mesure pas un acces numerique individuel.")
    w()

    top = cantons.nlargest(12, "dist_agence_km")
    w("**Les 12 cantons les plus eloignes d'une agence active :**")
    w()
    w("| Canton | Prefecture | Region | Distance |")
    w("|---|---|---|---|")
    for _, r in top.iterrows():
        w(f"| {r.adm3_name} | {r.adm2_name} | {r.adm1_name} | "
          f"{r.dist_agence_km:.0f} km |")
    w()

    # =========================================================================
    # 3. MESURE B — DEPUIS LES POINTS MOBILE MONEY
    # =========================================================================
    mmo = pd.read_csv(PROCESSED / "mobile_money_operateurs.csv")
    mm = mmo.drop_duplicates("FID").copy()
    mm["geometry"] = mm.geometry.map(wkt.loads)
    mm = gpd.GeoDataFrame(mm, geometry="geometry", crs=CRS_GEO).to_crs(CRS_M)
    mm["dist_agence_km"] = plus_proche(mm, agences)

    controles.append(("Points Mobile Money conserves apres deduplication",
                      len(mm) == 19788, f"{len(mm)}"))

    w("## 3. Mesure B — depuis les 19 788 points Mobile Money")
    w()
    w("**Hypothese explicite** : un agent Mobile Money s'implante la ou il y a")
    w("de la clientele. Ces points approximent donc les lieux de vie et")
    w("d'activite. *Biais assume* : cette mesure ne peut rien dire des zones")
    w("depourvues d'agent — la mesure A couvre ce point aveugle.")
    w()
    dm = mm.dist_agence_km
    w(f"- Distance mediane a une agence active : **{dm.median():.1f} km**")
    for s in SEUILS_KM:
        w(f"- Points a moins de **{s} km** d'une agence : **{(dm <= s).mean():.1%}**")
    w()

    # =========================================================================
    # 4. AGREGATION PAR PREFECTURE
    # =========================================================================
    ind = pd.read_csv(PROCESSED / "indicateurs_prefecture.csv")

    # Mesure A agregee : mediane des cantons, ponderee par leur superficie
    def med_ponderee(valeurs: pd.Series, poids: pd.Series) -> float:
        o = np.argsort(valeurs.values)
        v, p = valeurs.values[o], poids.values[o]
        c = np.cumsum(p) / p.sum()
        return float(v[np.searchsorted(c, 0.5)])

    agg_a = (cantons.groupby("adm2_name")
             .apply(lambda g: pd.Series({
                 "dist_agence_med_canton_km": med_ponderee(
                     g.dist_agence_km, g.area_sqkm),
                 "dist_agence_max_canton_km": g.dist_agence_km.max(),
                 "dist_datacenter_med_km": g.dist_datacenter_km.median(),
             }), include_groups=False).reset_index())

    # Rattachement a la graphie PRISE via la table de reconciliation unique
    # produite par `build_geo.py` — aucune correspondance n'est redefinie ici.
    recon = pd.read_csv(PROCESSED / "reconciliation_prefectures.csv")
    agg_a["prefecture"] = agg_a.adm2_name.map(
        dict(zip(recon.adm2_name, recon.prefecture)))
    agg_a = (agg_a.dropna(subset=["prefecture"])
             .groupby("prefecture", as_index=False)
             .agg(dist_agence_med_canton_km=("dist_agence_med_canton_km", "min"),
                  dist_agence_max_canton_km=("dist_agence_max_canton_km", "max"),
                  dist_datacenter_med_km=("dist_datacenter_med_km", "median")))

    agg_b = (mm.groupby("prefecture")
             .agg(dist_agence_med_mm_km=("dist_agence_km", "median"),
                  dist_agence_p90_mm_km=("dist_agence_km",
                                         lambda s: s.quantile(.90)))
             .reset_index())
    for s in SEUILS_KM:
        agg_b[f"part_mm_moins_{s}km"] = (
            mm.groupby("prefecture").dist_agence_km
            .apply(lambda x, s=s: (x <= s).mean()).values)

    acces = ind.merge(agg_a, on="prefecture", how="left").merge(
        agg_b, on="prefecture", how="left")

    controles.append(("Accessibilite renseignee pour les 39 prefectures",
                      acces.dist_agence_med_canton_km.notna().all()
                      and acces.dist_agence_med_mm_km.notna().all(),
                      f"A : {int(acces.dist_agence_med_canton_km.notna().sum())}/39 · "
                      f"B : {int(acces.dist_agence_med_mm_km.notna().sum())}/39"))

    acces.to_csv(PROCESSED / "acces_prefecture.csv", index=False, encoding="utf-8")
    cantons.drop(columns="geometry").to_csv(
        PROCESSED / "acces_canton.csv", index=False, encoding="utf-8")

    w("## 4. Eloignement par prefecture")
    w()
    w("| Prefecture | Region | Population | Dist. med. cantons | Dist. med. points MM | % points MM < 10 km |")
    w("|---|---|---|---|---|---|")
    for _, r in acces.sort_values("dist_agence_med_canton_km",
                                  ascending=False).iterrows():
        w(f"| {r.prefecture} | {r.region} | {int(r.population):,} | "
          f"{r.dist_agence_med_canton_km:.0f} km | {r.dist_agence_med_mm_km:.0f} km | "
          f"{r.part_mm_moins_10km:.0%} |".replace(",", " "))
    w()

    # =========================================================================
    w("## 5. Controles")
    w()
    w("| Controle | Resultat | Detail |")
    w("|---|---|---|")
    for nom, ok, detail in controles:
        w(f"| {nom} | {'✅ OK' if ok else '❌ ECHEC'} | {detail} |")
    w()
    w("## 6. Fichiers produits")
    w()
    w("| Fichier | Contenu |")
    w("|---|---|")
    w(f"| `acces_prefecture.csv` | 39 prefectures × indicateurs + accessibilite |")
    w(f"| `acces_canton.csv` | {len(cantons)} cantons × distances |")

    (REPORTS / "acces_spatial.md").write_text("\n".join(OUT), encoding="utf-8")


if __name__ == "__main__":
    main()
