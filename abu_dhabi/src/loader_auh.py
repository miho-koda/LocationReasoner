
import pandas as pd

REQUIRED_COLS = {"category", "lat", "lon"}

def load_pois(csv_path: str) -> pd.DataFrame:
    """
    Load Abu Dhabi OSM POIs (combined CSV) exported by your Overpass script.
    Expected columns include at least: category, lat, lon.
    Returns a cleaned DataFrame with only what we need.
    """
    df = pd.read_csv(csv_path)
    missing = REQUIRED_COLS - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    # Keep essential columns
    keep = [c for c in ["osm_uid","osm_type","osm_id","name","category","lat","lon","_raw_tags"] if c in df.columns]
    df = df[keep].copy()

    # Drop rows without valid coordinates
    df = df.dropna(subset=["lat","lon"])
    return df
