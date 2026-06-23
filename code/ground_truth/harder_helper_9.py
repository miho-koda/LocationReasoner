import sys
import os

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))             
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "..", ".."))

CODE_DIR = os.path.join(PROJECT_ROOT, "code")
if CODE_DIR not in sys.path:
    sys.path.insert(0, CODE_DIR)

import re

import operator
import pandas as pd
from site_selection.loader import get_poi_spend_dataset
from site_selection.zone import create_zone, get_neighbor_zones
from site_selection.analysis import get_spendparam_years, get_distance_km
from site_selection.filter import filter_df_based_on_zone, filter_pois_by_top_category, get_transport_pois_in_zone
from site_selection.population import get_population
import operator
def harder_helper_9(
    include_my_zone=True,
    num_neighbors=2,
    threshold=3000   # population per km²
):
    """
    Constraint:
    (Sum population of selected zones) / (Sum area of selected zones in km²) ≥ threshold

    Zones considered = my zone (optional) + N nearest neighbors.
    """

    # --- Load POIs and build zones ---
    poi_df = get_poi_spend_dataset()
    zone_df = create_zone(poi_df)     # ALWAYS EPSG:4326 (lat/lng degrees)

    survived_zones = []

    # --- Prepare a projected version just for area computation ---
    zone_df_proj = zone_df.to_crs(epsg=3857)  # meters

    for zone_id in zone_df["zone_id"]:

        # ----- Determine which zones to evaluate -----
        selected_zones = []

        if include_my_zone:
            selected_zones.append(zone_id)

        neighbors = get_neighbor_zones(zone_df, zone_id, num_neighbors)
        selected_zones.extend(neighbors)

        # ----- Aggregate population + area -----
        total_population = 0
        total_area_m2 = 0

        for zid in selected_zones:
            # Population from internal function
            pop = get_population(zid, zone_df)
            total_population += pop

            # Area from projected geometry
            geom = zone_df_proj.loc[zone_df_proj["zone_id"] == zid, "geometry"].iloc[0]
            total_area_m2 += geom.area

        if total_area_m2 <= 0:
            continue

        # Convert area to km²
        area_km2 = total_area_m2 / 1_000_000
        density = total_population / area_km2

        if density >= threshold:
            survived_zones.append(zone_id)

    return zone_df[zone_df["zone_id"].isin(survived_zones)]
