import pandas as pd
import geopandas as gpd
from typing import Dict, List, Tuple

def filter_df_based_on_zone(df: pd.DataFrame, zone_id: int) -> pd.DataFrame:
    """
    Filters the input DataFrame to include only entries from the specified zone_id.
    Works with only poi_spend_df or parking DataFrames.
    
    Parameters:
    - df: A DataFrame (must be either poi_spend_df or parking_df)
    - zone_id: The ID of the zone to filter by
    
    Returns:
    A filtered DataFrame containing only rows within the given zone
    """
    if 'zone_id' not in df.columns:
        raise ValueError("DataFrame must contain a 'zone_id' column")
    
    return df[df['zone_id'] == zone_id].copy()

def filter_pois_by_top_category(poi_spend_df: pd.DataFrame, top_category: str) -> pd.DataFrame:
    """
    Filters POIs to only include those that match the specified top-level category.
    
    Parameters:
    - poi_spend_df: A DataFrame with a 'TOP_CATEGORY' column
    - top_category: The category name to filter by (string)
    
    Returns:
    A filtered POI DataFrame containing only rows with the matching top category
    """
    if 'TOP_CATEGORY' not in poi_spend_df.columns:
        raise ValueError("DataFrame must contain a 'TOP_CATEGORY' column")
    
    return poi_spend_df[poi_spend_df['TOP_CATEGORY'] == top_category].copy()

def filter_pois_by_sub_category(poi_spend_df: pd.DataFrame, sub_category: str) -> pd.DataFrame:
    """
    Filters POIs to only include those that match the specified sub-category.
    
    Parameters:
    - poi_spend_df: A DataFrame with a 'SUB_CATEGORY' column
    - sub_category: The sub-category name to filter by (string)
    
    Returns:
    A filtered POI DataFrame containing only rows with the matching sub-category
    """
    if 'SUB_CATEGORY' not in poi_spend_df.columns:
        raise ValueError("DataFrame must contain a 'SUB_CATEGORY' column")
    
    return poi_spend_df[poi_spend_df['SUB_CATEGORY'] == sub_category].copy()
import os
from pyrosm import OSM
import geopandas as gpd

# Global cache
POI_CACHE = {}

def get_transport_pois_in_zone(zone_df, poi_type):
    """
    Retrieve transport POIs for all zones using a city-level .osm.pbf file.

    Parameters:
        zone_df (GeoDataFrame): Zones with 'zone_id' and 'geometry'
        poi_type (str): One of ['bus_stop', 'station', 'subway_entrance', 'aerodrome', 'taxi']

    Returns:
        dict: zone_id -> list of (lat, lon)
    """

    import json
    import os

    # Load config only once per module

    from config_utils import load_config

    config = load_config()


    pbf_path = config.get("transport_pbf_path")


    try:
        if not os.path.exists(pbf_path):
            raise FileNotFoundError(f"PBF not found: {pbf_path}")

        # Check cache
        cache_key = ("city_custom", poi_type)
        if cache_key in POI_CACHE:
            pois = POI_CACHE[cache_key]
        else:
            tag_mapping = {
                "bus_stop": {"highway": ["bus_stop"]},
                "station": {"railway": ["station"]},
                "subway_entrance": {"railway": ["subway_entrance"]},
                "aerodrome": {"aeroway": ["aerodrome"]},
                "taxi": {"amenity": ["taxi"]}
            }

            if poi_type not in tag_mapping:
                raise ValueError(f"Unsupported POI type: {poi_type}")

            osm = OSM(pbf_path)
            pois = osm.get_pois(custom_filter=tag_mapping[poi_type])
            pois = pois[pois.geometry.type == "Point"]

            if pois.crs != zone_df.crs:
                pois = pois.to_crs(zone_df.crs)

            POI_CACHE[cache_key] = pois

        # Spatial join
        joined = gpd.sjoin(pois, zone_df[['zone_id', 'geometry']], predicate="within", how="inner")

        # Group by zone
        result = joined.groupby('zone_id').geometry.apply(lambda g: [(pt.y, pt.x) for pt in g]).to_dict()

        # Fill in missing zones
        for zone_id in zone_df['zone_id']:
            if zone_id not in result:
                result[zone_id] = []

        return result

    except Exception as e:
        print(f"[ERROR] get_transport_pois_in_zone failed for {poi_type}: {e}")
        return {}


