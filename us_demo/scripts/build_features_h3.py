"""
Build zone_features.parquet using H3 resolution-8 hexagons.

Covers all benchmark constraint types:
  - cnt_*            POI counts per category
  - dist_to_*_m      Distance to nearest POI of category
  - spend_*          Aggregate spending metrics (2023)
  - cnt_bus_stops    Transit: bus stop count from OSM
  - cnt_subway_entrances  Transit: subway from OSM
  - cnt_parking      Parking lot count
  - parking_capacity Largest lot capacity (sq m / 30)
  - population       Census block group population
"""

import math
import sys
from pathlib import Path

import h3
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Polygon, Point

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.category_map import (
    CATEGORY_MAP, DISTANCE_CATEGORIES, SPEND_YEAR,
    cnt_col, dist_col,
    spend_total_col, spend_transactions_col, spend_customers_col,
    spend_median_txn_col, spend_median_customer_col, spend_pct_change_col,
    cnt_bus_stops_col, cnt_subway_col,
    cnt_parking_col, parking_capacity_col, population_col,
)

POI_PARQUET     = ROOT / "icml" / "preloaded_data" / "poi_spend_df.parquet"
PARKING_CSV     = ROOT / "data" / "safegraph_dataset" / "Massachusetts_Parking.csv"
OSM_PBF         = ROOT / "data" / "safegraph_dataset" / "Transportation" / "planet_-71.123,42.2434_-70.8728,42.3814.osm.pbf"
POP_DIR         = ROOT / "data" / "safegraph_dataset" / "Population" / "Massachusetts"
OUT_DIR         = Path(__file__).resolve().parents[1] / "output"
OUT_FEATURES    = OUT_DIR / "zone_features.parquet"
OUT_GEOJSON     = OUT_DIR / "zones.geojson"
H3_RES          = 8

# Boston bounding box for filtering
BOSTON_BBOX = {"min_lat": 42.2, "max_lat": 42.45, "min_lng": -71.2, "max_lng": -70.85}


def haversine_vectorized(lat1, lng1, lats2, lngs2):
    R = 6_371_000
    phi1, phi2 = math.radians(lat1), np.radians(lats2)
    dphi = np.radians(lats2 - lat1)
    dlam = np.radians(lngs2 - lng1)
    a = np.sin(dphi / 2)**2 + math.cos(phi1) * np.cos(phi2) * np.sin(dlam / 2)**2
    return R * 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))


def in_boston(lat, lng):
    b = BOSTON_BBOX
    return b["min_lat"] <= lat <= b["max_lat"] and b["min_lng"] <= lng <= b["max_lng"]


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # ── 1. Load POIs and assign H3 cells ──────────────────────────────────
    print("Loading POIs ...")
    poi = pd.read_parquet(POI_PARQUET)
    poi = poi.dropna(subset=["LATITUDE", "LONGITUDE"])
    # Keep only Boston area
    poi = poi[poi.apply(lambda r: in_boston(r.LATITUDE, r.LONGITUDE), axis=1)]
    print(f"  {len(poi):,} Boston POIs")

    poi["zone_id"] = poi.apply(
        lambda r: h3.geo_to_h3(r.LATITUDE, r.LONGITUDE, H3_RES), axis=1
    )
    occupied = sorted(poi["zone_id"].unique())
    print(f"  {len(occupied)} H3 cells")

    # ── 2. Zone centroids ─────────────────────────────────────────────────
    centroids = [{"zone_id": c, "center_lat": h3.h3_to_geo(c)[0], "center_lng": h3.h3_to_geo(c)[1]}
                 for c in occupied]
    features = pd.DataFrame(centroids)

    # ── 3. POI count columns ──────────────────────────────────────────────
    print("Building count columns ...")
    for alias, safegraph_cat in CATEGORY_MAP.items():
        subset = poi[poi["TOP_CATEGORY"] == safegraph_cat]
        counts = subset.groupby("zone_id").size().rename(cnt_col(alias))
        features = features.merge(counts, on="zone_id", how="left")
        features[cnt_col(alias)] = features[cnt_col(alias)].fillna(0).astype(int)
        if features[cnt_col(alias)].sum() > 0:
            print(f"  {cnt_col(alias)}: {features[cnt_col(alias)].sum()} total")
        else:
            print(f"  {cnt_col(alias)}: (no data in Boston for '{safegraph_cat}')")

    # ── 4. Distance columns ───────────────────────────────────────────────
    print("Building distance columns ...")
    for alias in DISTANCE_CATEGORIES:
        safegraph_cat = CATEGORY_MAP[alias]
        subset = poi[poi["TOP_CATEGORY"] == safegraph_cat].dropna(subset=["LATITUDE", "LONGITUDE"])
        col = dist_col(alias)
        if subset.empty:
            features[col] = float("inf")
            print(f"  {col}: no POIs, filling inf")
            continue
        poi_lats, poi_lngs = subset["LATITUDE"].values, subset["LONGITUDE"].values
        dists = [float(haversine_vectorized(r.center_lat, r.center_lng, poi_lats, poi_lngs).min())
                 for _, r in features.iterrows()]
        features[col] = dists
        print(f"  {col}: min={min(dists):.0f}m max={max(dists):.0f}m")

    # ── 5. Spending columns (2023) ─────────────────────────────────────────
    print(f"Building spending columns (year={SPEND_YEAR}) ...")
    yr = SPEND_YEAR
    spend_cols_raw = {
        spend_total_col():          f"RAW_TOTAL_SPEND_{yr}",
        spend_transactions_col():   f"RAW_NUM_TRANSACTIONS_{yr}",
        spend_customers_col():      f"RAW_NUM_CUSTOMERS_{yr}",
        spend_median_txn_col():     f"MEDIAN_SPEND_PER_TRANSACTION_{yr}",
        spend_median_customer_col(): f"MEDIAN_SPEND_PER_CUSTOMER_{yr}",
        spend_pct_change_col():     f"SPEND_PCT_CHANGE_VS_PREV_YEAR_{yr}",
    }
    # sum for totals, mean for medians and pct_change
    agg_fn = {
        spend_total_col():          "sum",
        spend_transactions_col():   "sum",
        spend_customers_col():      "sum",
        spend_median_txn_col():     "mean",
        spend_median_customer_col(): "mean",
        spend_pct_change_col():     "mean",
    }
    spend_df = poi[["zone_id"] + [c for c in spend_cols_raw.values() if c in poi.columns]].copy()
    for feat_col, raw_col in spend_cols_raw.items():
        if raw_col not in poi.columns:
            features[feat_col] = 0.0
            continue
        fn = agg_fn[feat_col]
        agg = spend_df.groupby("zone_id")[raw_col].agg(fn).rename(feat_col)
        features = features.merge(agg, on="zone_id", how="left")
        features[feat_col] = features[feat_col].fillna(0.0)
        nonzero = (features[feat_col] > 0).sum()
        print(f"  {feat_col}: {nonzero} zones with data, max={features[feat_col].max():.0f}")

    # ── 6. Parking ────────────────────────────────────────────────────────
    print("Building parking columns ...")
    try:
        park = pd.read_csv(PARKING_CSV, usecols=["LATITUDE", "LONGITUDE", "WKT_AREA_SQ_METERS"])
        park = park.dropna(subset=["LATITUDE", "LONGITUDE"])
        park = park[park.apply(lambda r: in_boston(r.LATITUDE, r.LONGITUDE), axis=1)]
        park["zone_id"] = park.apply(
            lambda r: h3.geo_to_h3(r.LATITUDE, r.LONGITUDE, H3_RES), axis=1
        )
        # count
        cnt = park.groupby("zone_id").size().rename(cnt_parking_col())
        features = features.merge(cnt, on="zone_id", how="left")
        features[cnt_parking_col()] = features[cnt_parking_col()].fillna(0).astype(int)
        # largest lot capacity (area / 30 sq m per space)
        cap = park.groupby("zone_id")["WKT_AREA_SQ_METERS"].max().rename("_max_area")
        features = features.merge(cap, on="zone_id", how="left")
        features[parking_capacity_col()] = (features["_max_area"].fillna(0) / 30).astype(int)
        features.drop(columns=["_max_area"], inplace=True)
        print(f"  {cnt_parking_col()}: {features[cnt_parking_col()].sum()} lots, "
              f"max capacity={features[parking_capacity_col()].max()}")
    except Exception as e:
        print(f"  Parking failed: {e} — filling zeros")
        features[cnt_parking_col()] = 0
        features[parking_capacity_col()] = 0

    # ── 7. Transit from OSM ────────────────────────────────────────────────
    print("Building transit columns ...")
    try:
        import pyrosm
        osm = pyrosm.OSM(str(OSM_PBF))

        def extract_pois_by_tag(osm_obj, tag_key, tag_values):
            rows = []
            try:
                pois = osm_obj.get_pois(custom_filter={tag_key: tag_values})
                if pois is not None and len(pois) > 0:
                    for _, row in pois.iterrows():
                        geom = row.geometry
                        if geom is None:
                            continue
                        if geom.geom_type == "Point":
                            lat, lng = geom.y, geom.x
                        else:
                            lat, lng = geom.centroid.y, geom.centroid.x
                        if in_boston(lat, lng):
                            rows.append({"lat": lat, "lng": lng})
            except Exception as ex:
                print(f"    OSM extract warning: {ex}")
            return pd.DataFrame(rows)

        bus_df = extract_pois_by_tag(osm, "highway", ["bus_stop"])
        if not bus_df.empty:
            bus_df["zone_id"] = bus_df.apply(
                lambda r: h3.geo_to_h3(r.lat, r.lng, H3_RES), axis=1
            )
            bc = bus_df.groupby("zone_id").size().rename(cnt_bus_stops_col())
            features = features.merge(bc, on="zone_id", how="left")
        features[cnt_bus_stops_col()] = features.get(cnt_bus_stops_col(), pd.Series(0, index=features.index)).fillna(0).astype(int)
        print(f"  {cnt_bus_stops_col()}: {features[cnt_bus_stops_col()].sum()} stops across zones")

        sub_df = extract_pois_by_tag(osm, "railway", ["subway_entrance"])
        if not sub_df.empty:
            sub_df["zone_id"] = sub_df.apply(
                lambda r: h3.geo_to_h3(r.lat, r.lng, H3_RES), axis=1
            )
            sc = sub_df.groupby("zone_id").size().rename(cnt_subway_col())
            features = features.merge(sc, on="zone_id", how="left")
        features[cnt_subway_col()] = features.get(cnt_subway_col(), pd.Series(0, index=features.index)).fillna(0).astype(int)
        print(f"  {cnt_subway_col()}: {features[cnt_subway_col()].sum()} entrances across zones")

    except Exception as e:
        print(f"  Transit failed: {e} — filling zeros")
        features[cnt_bus_stops_col()] = 0
        features[cnt_subway_col()] = 0

    # ── 8. Population ─────────────────────────────────────────────────────
    print("Building population column ...")
    try:
        import zipfile, os
        shp_dir = POP_DIR / "shp"
        if not shp_dir.exists():
            zip_path = POP_DIR / "tl_2024_25_bg.zip"
            with zipfile.ZipFile(zip_path, "r") as z:
                z.extractall(shp_dir)

        shp_files = list(shp_dir.glob("*.shp"))
        bg = gpd.read_file(shp_files[0]).to_crs("EPSG:4326")

        pop_csv = POP_DIR / "Massachusetts.csv"
        # ACS format: row 0 = header, row 1 = description, rows 2+ = data
        pop_df = pd.read_csv(pop_csv, skiprows=[1], usecols=["GEO_ID", "B01003_001E"])
        pop_df.columns = ["GEO_ID", "population"]
        pop_df = pop_df[pop_df["GEO_ID"].str.startswith("1500000US")]  # block group rows only
        pop_df["population"] = pd.to_numeric(pop_df["population"], errors="coerce").fillna(0).astype(int)
        pop_df["GEOID"] = pop_df["GEO_ID"].str.replace("1500000US", "", regex=False)
        bg = bg.merge(pop_df[["GEOID", "population"]], on="GEOID", how="left")
        bg["population"] = bg["population"].fillna(0).astype(int)

        # Build H3 zone polygons
        zone_polys = []
        for cell in occupied:
            boundary = h3.h3_to_geo_boundary(cell, geo_json=True)
            zone_polys.append({"zone_id": cell, "geometry": Polygon(boundary)})
        zone_gdf = gpd.GeoDataFrame(zone_polys, crs="EPSG:4326")

        joined = gpd.sjoin(bg[["geometry", "population"]], zone_gdf, how="inner", predicate="intersects")
        pop_per_zone = joined.groupby("zone_id")["population"].sum().reset_index()
        features = features.merge(pop_per_zone, on="zone_id", how="left")
        features[population_col()] = features["population"].fillna(0).astype(int)
        if "population" in features.columns and population_col() != "population":
            features.drop(columns=["population"], inplace=True)
        print(f"  {population_col()}: max={features[population_col()].max():,}, "
              f"nonzero={( features[population_col()] > 0).sum()} zones")

    except Exception as e:
        print(f"  Population failed: {e} — filling zeros")
        features[population_col()] = 0

    # ── 9. Save features ──────────────────────────────────────────────────
    print(f"\nFinal shape: {features.shape}")
    print(f"Columns: {list(features.columns)}")
    features.to_parquet(OUT_FEATURES, index=False)
    print(f"Saved → {OUT_FEATURES}")

    # ── 10. GeoJSON ───────────────────────────────────────────────────────
    print("Building zones.geojson ...")
    polys = [{"zone_id": c, "geometry": Polygon(h3.h3_to_geo_boundary(c, geo_json=True))}
             for c in occupied]
    gdf = gpd.GeoDataFrame(polys, crs="EPSG:4326")
    gdf = gdf.merge(features[["zone_id", "center_lat", "center_lng"]], on="zone_id", how="left")
    gdf.to_file(OUT_GEOJSON, driver="GeoJSON")
    print(f"Saved → {OUT_GEOJSON} ({len(gdf)} hexagons)")


if __name__ == "__main__":
    main()
