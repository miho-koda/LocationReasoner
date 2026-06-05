"""
Build us_demo/output/zone_features.parquet from Boston SafeGraph data.

Output shape: (1998, ~27) — one row per zone with:
  zone_id, center_lat, center_lng
  cnt_<alias>  for each alias in CATEGORY_MAP  (+ cnt_parking)
  dist_to_<alias>_m  for each alias in DISTANCE_CATEGORIES
"""

import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.category_map import CATEGORY_MAP, DISTANCE_CATEGORIES, cnt_col, dist_col

ZONE_PARQUET    = ROOT / "icml" / "preloaded_data" / "zone_df.parquet"
POI_PARQUET     = ROOT / "icml" / "preloaded_data" / "poi_spend_df.parquet"
PARKING_PARQUET = ROOT / "icml" / "preloaded_data" / "parking_df.parquet"
OUT_DIR         = Path(__file__).resolve().parents[1] / "output"
OUT_FEATURES    = OUT_DIR / "zone_features.parquet"


def haversine_vectorized(lat1: float, lng1: float,
                         lats2: np.ndarray, lngs2: np.ndarray) -> np.ndarray:
    """Distance in metres from one point to many."""
    R = 6_371_000
    phi1, phi2 = math.radians(lat1), np.radians(lats2)
    dphi  = np.radians(lats2 - lat1)
    dlam  = np.radians(lngs2 - lng1)
    a = np.sin(dphi / 2) ** 2 + math.cos(phi1) * np.cos(phi2) * np.sin(dlam / 2) ** 2
    return R * 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # ── load base data ─────────────────────────────────────────────────────
    print("Loading zone_df ...")
    import geopandas as gpd
    zone_gdf = gpd.read_parquet(ZONE_PARQUET)
    zone_df  = pd.DataFrame(zone_gdf[["zone_id", "center_lat", "center_lng"]])
    zone_df["zone_id"] = zone_df["zone_id"].astype(int)

    print("Loading poi_spend_df ...")
    poi = pd.read_parquet(POI_PARQUET, columns=["zone_id", "TOP_CATEGORY", "LATITUDE", "LONGITUDE"])
    poi["zone_id"] = poi["zone_id"].astype(int)

    print("Loading parking_df ...")
    parking = pd.read_parquet(PARKING_PARQUET, columns=["zone_id"])
    parking["zone_id"] = parking["zone_id"].astype(int)

    features = zone_df.copy()

    # ── count columns ──────────────────────────────────────────────────────
    print("Building count columns ...")
    for alias, safegraph_cat in CATEGORY_MAP.items():
        subset = poi[poi["TOP_CATEGORY"] == safegraph_cat]
        counts = subset.groupby("zone_id").size().rename(cnt_col(alias))
        features = features.merge(counts, on="zone_id", how="left")
        features[cnt_col(alias)] = features[cnt_col(alias)].fillna(0).astype(int)

    # parking: preloaded parking_df is empty for Boston, skip silently

    # ── distance columns ───────────────────────────────────────────────────
    print("Building distance columns ...")
    for alias in DISTANCE_CATEGORIES:
        safegraph_cat = CATEGORY_MAP[alias]
        subset = poi[poi["TOP_CATEGORY"] == safegraph_cat].dropna(subset=["LATITUDE", "LONGITUDE"])
        col = dist_col(alias)

        if subset.empty:
            features[col] = float("inf")
            print(f"  {col}: no POIs found, filling inf")
            continue

        poi_lats = subset["LATITUDE"].values
        poi_lngs = subset["LONGITUDE"].values

        dists = []
        for _, row in features.iterrows():
            d = haversine_vectorized(row["center_lat"], row["center_lng"], poi_lats, poi_lngs)
            dists.append(float(d.min()))
        features[col] = dists
        print(f"  {col}: min={min(dists):.0f}m  max={max(dists):.0f}m")

    # ── save ───────────────────────────────────────────────────────────────
    print(f"\nFinal shape: {features.shape}")
    print(f"Columns: {list(features.columns)}")
    print(f"\nSample:\n{features[['zone_id','cnt_restaurants','cnt_pharmacies','dist_to_restaurants_m']].head(5)}")
    features.to_parquet(OUT_FEATURES, index=False)
    print(f"\nSaved → {OUT_FEATURES}")


if __name__ == "__main__":
    main()
