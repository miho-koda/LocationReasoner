
from typing import Dict, List
import pandas as pd
import numpy as np
import math

def haversine_m(lat1, lon1, lat2, lon2) -> float:
    R = 6371000.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlmb/2)**2
    return 2 * R * math.asin(math.sqrt(a))

def _nearest_distance_for_points(lat, lon, pts: np.ndarray) -> float:
    """
    pts: array of shape (N, 2) with columns [lat, lon]. Returns meters.
    """
    if pts.size == 0:
        return float("inf")
    # Naive vectorized haversine to all points
    lats = pts[:,0]; lons = pts[:,1]
    R = 6371000.0
    phi1 = math.radians(lat)
    phi2 = np.radians(lats)
    dphi = np.radians(lats - lat)
    dlmb = np.radians(lons - lon)
    a = np.sin(dphi/2.0)**2 + np.cos(phi1) * np.cos(phi2) * np.sin(dlmb/2.0)**2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
    dists = R * c
    return float(dists.min())

def category_counts(poi_with_zone: pd.DataFrame) -> pd.DataFrame:
    """
    Returns a wide DF indexed by zone_id with count columns per category: cnt_<category>
    """
    g = poi_with_zone.groupby(["zone_id","category"]).size().unstack(fill_value=0)
    g = g.add_prefix("cnt_")
    g.index.name = "zone_id"
    return g.reset_index()

def add_nearest_distance_features(zone_df: pd.DataFrame, poi_df: pd.DataFrame, categories: List[str]) -> pd.DataFrame:
    """
    For each category in 'categories', compute distance in meters from zone centroid
    to nearest POI in that category. Adds columns: dist_to_<category>_m
    """
    out = zone_df.copy()
    for cat in categories:
        cat_pts = poi_df.loc[poi_df["category"] == cat, ["lat","lon"]].dropna().to_numpy()
        col = f"dist_to_{cat}_m"
        out[col] = [
            _nearest_distance_for_points(float(r.center_lat), float(r.center_lng), cat_pts)
            for r in out.itertuples(index=False)
        ]
    return out
