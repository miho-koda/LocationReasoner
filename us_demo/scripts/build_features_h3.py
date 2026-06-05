"""
Build zone_features.parquet using H3 resolution-8 hexagons instead of k-means.

Only cells with at least 1 POI are included (~268 cells for Boston).
Outputs:
  us_demo/output/zone_features.parquet
  us_demo/output/zones.geojson
"""

import sys
from pathlib import Path

import h3
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Polygon
import math

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.category_map import CATEGORY_MAP, DISTANCE_CATEGORIES, cnt_col, dist_col

POI_PARQUET     = ROOT / "icml" / "preloaded_data" / "poi_spend_df.parquet"
PARKING_PARQUET = ROOT / "icml" / "preloaded_data" / "parking_df.parquet"
OUT_DIR         = Path(__file__).resolve().parents[1] / "output"
OUT_FEATURES    = OUT_DIR / "zone_features.parquet"
OUT_GEOJSON     = OUT_DIR / "zones.geojson"

H3_RES = 8


def haversine_vectorized(lat1, lng1, lats2, lngs2):
    R = 6_371_000
    phi1, phi2 = math.radians(lat1), np.radians(lats2)
    dphi = np.radians(lats2 - lat1)
    dlam = np.radians(lngs2 - lng1)
    a = np.sin(dphi / 2)**2 + math.cos(phi1) * np.cos(phi2) * np.sin(dlam / 2)**2
    return R * 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # ── load POIs ──────────────────────────────────────────────────────────
    print("Loading POIs ...")
    poi = pd.read_parquet(POI_PARQUET, columns=["TOP_CATEGORY", "LATITUDE", "LONGITUDE"])
    poi = poi.dropna(subset=["LATITUDE", "LONGITUDE"])
    print(f"  {len(poi):,} POIs loaded")

    # ── assign H3 cells ────────────────────────────────────────────────────
    print(f"Assigning H3 resolution-{H3_RES} cells ...")
    poi["zone_id"] = poi.apply(
        lambda r: h3.geo_to_h3(r.LATITUDE, r.LONGITUDE, H3_RES), axis=1
    )
    occupied = sorted(poi["zone_id"].unique())
    print(f"  {len(occupied)} occupied H3 cells")

    # ── build zone centroid table ──────────────────────────────────────────
    print("Computing zone centroids ...")
    centroids = []
    for cell in occupied:
        lat, lng = h3.h3_to_geo(cell)
        centroids.append({"zone_id": cell, "center_lat": lat, "center_lng": lng})
    features = pd.DataFrame(centroids)

    # ── count columns ──────────────────────────────────────────────────────
    print("Building count columns ...")
    for alias, safegraph_cat in CATEGORY_MAP.items():
        subset = poi[poi["TOP_CATEGORY"] == safegraph_cat]
        counts = subset.groupby("zone_id").size().rename(cnt_col(alias))
        features = features.merge(counts, on="zone_id", how="left")
        features[cnt_col(alias)] = features[cnt_col(alias)].fillna(0).astype(int)

    # ── distance columns ───────────────────────────────────────────────────
    print("Building distance columns ...")
    for alias in DISTANCE_CATEGORIES:
        safegraph_cat = CATEGORY_MAP[alias]
        subset = poi[poi["TOP_CATEGORY"] == safegraph_cat].dropna(
            subset=["LATITUDE", "LONGITUDE"]
        )
        col = dist_col(alias)
        if subset.empty:
            features[col] = float("inf")
            print(f"  {col}: no POIs, filling inf")
            continue
        poi_lats = subset["LATITUDE"].values
        poi_lngs = subset["LONGITUDE"].values
        dists = []
        for _, row in features.iterrows():
            d = haversine_vectorized(row["center_lat"], row["center_lng"], poi_lats, poi_lngs)
            dists.append(float(d.min()))
        features[col] = dists
        print(f"  {col}: min={min(dists):.0f}m  max={max(dists):.0f}m")

    # ── save features ──────────────────────────────────────────────────────
    print(f"\nFeatures shape: {features.shape}")
    features.to_parquet(OUT_FEATURES, index=False)
    print(f"Saved features → {OUT_FEATURES}")

    # ── build GeoJSON ──────────────────────────────────────────────────────
    print("\nBuilding zones.geojson ...")
    polygons = []
    for cell in occupied:
        boundary = h3.h3_to_geo_boundary(cell, geo_json=True)
        polygons.append({
            "zone_id": cell,
            "geometry": Polygon(boundary),
        })
    gdf = gpd.GeoDataFrame(polygons, crs="EPSG:4326")
    gdf = gdf.merge(
        features[["zone_id", "center_lat", "center_lng"]],
        on="zone_id", how="left"
    )
    gdf.to_file(OUT_GEOJSON, driver="GeoJSON")
    print(f"Saved GeoJSON → {OUT_GEOJSON}  ({len(gdf)} hexagons)")

    # ── quick sanity check ─────────────────────────────────────────────────
    print(f"\nSample:\n{features[['zone_id','center_lat','center_lng','cnt_restaurants','cnt_physicians']].head(5)}")


if __name__ == "__main__":
    main()
