"""
One-time data preloader for Claude Code experiment.
Loads Boston POI+spend, creates zones, assigns parking, and serializes to parquet.
Run from the code/ directory: cd code && python ../icml/preload_data.py
"""
import sys
import os

# Setup paths — preload_data.py is in code/utils/; code/ is one level up
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CODE_DIR = os.path.dirname(SCRIPT_DIR)
BASE_DIR = os.path.dirname(CODE_DIR)
sys.path.insert(0, CODE_DIR)
os.chdir(CODE_DIR)

import pandas as pd
import geopandas as gpd
from site_selection.loader import get_poi_spend_dataset, get_parking_dataset
from site_selection.zone import create_zone

OUTPUT_DIR = os.path.join(SCRIPT_DIR, "preloaded_data")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def main():
    print("Loading POI + spend dataset (Boston)...")
    poi_spend_df = get_poi_spend_dataset()
    print(f"  Loaded {len(poi_spend_df)} POIs")

    print("Creating zones...")
    zone_df = create_zone(poi_spend_df)
    zone_df = zone_df.set_crs(epsg=4326, allow_override=True)
    print(f"  Created {len(zone_df)} zones")

    print("Loading parking dataset...")
    parking_df = get_parking_dataset()
    print(f"  Loaded {len(parking_df)} parking lots")

    print("Assigning parking to zones (direct spatial join)...")
    parking_gdf = gpd.GeoDataFrame(
        parking_df.copy(),
        geometry=gpd.points_from_xy(parking_df['LONGITUDE'], parking_df['LATITUDE']),
        crs="EPSG:4326"
    )
    joined = gpd.sjoin(
        parking_gdf,
        zone_df[['zone_id', 'geometry']],
        how="inner",
        predicate="within"
    )
    joined.drop(columns=["index_right"], inplace=True, errors="ignore")
    parking_df = joined
    print(f"  {len(parking_df)} parking lots assigned to zones")

    # Save to parquet
    poi_path = os.path.join(OUTPUT_DIR, "poi_spend_df.parquet")
    zone_path = os.path.join(OUTPUT_DIR, "zone_df.parquet")
    parking_path = os.path.join(OUTPUT_DIR, "parking_df.parquet")

    print("Saving parquets...")
    poi_spend_df.to_parquet(poi_path, index=False)
    zone_df.to_parquet(zone_path, index=False)
    parking_df.to_parquet(parking_path, index=False)

    print(f"Done! Saved to {OUTPUT_DIR}")
    print(f"  poi_spend_df: {len(poi_spend_df)} rows")
    print(f"  zone_df: {len(zone_df)} rows")
    print(f"  parking_df: {len(parking_df)} rows")


if __name__ == "__main__":
    main()
