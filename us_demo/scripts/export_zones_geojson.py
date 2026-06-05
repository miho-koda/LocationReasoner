"""Export Boston zone_df.parquet → output/zones.geojson for Leaflet."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ZONE_PARQUET = ROOT / "icml" / "preloaded_data" / "zone_df.parquet"
OUT_DIR = Path(__file__).resolve().parents[1] / "output"
OUT_GEOJSON = OUT_DIR / "zones.geojson"

import geopandas as gpd

def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Reading {ZONE_PARQUET} ...")
    gdf = gpd.read_parquet(ZONE_PARQUET)
    print(f"  Shape: {gdf.shape}")
    print(f"  Columns: {list(gdf.columns)}")
    print(f"  CRS: {gdf.crs}")
    print(f"  Sample:\n{gdf[['zone_id','center_lat','center_lng','num_pois']].head(3)}")

    if gdf.crs is None:
        gdf = gdf.set_crs("EPSG:4326")
    elif str(gdf.crs) != "EPSG:4326":
        gdf = gdf.to_crs("EPSG:4326")

    # Keep only the columns Leaflet needs
    export = gdf[["zone_id", "center_lat", "center_lng", "num_pois", "geometry"]].copy()
    export["zone_id"] = export["zone_id"].astype(int)

    print(f"Writing {OUT_GEOJSON} ...")
    export.to_file(OUT_GEOJSON, driver="GeoJSON")
    print(f"Done. {len(export)} zones exported.")

if __name__ == "__main__":
    main()
