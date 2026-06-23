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
import operator
def harder_helper_7(
    min_transport_types=3,
    poi_proximity_ratio=0.5,
    distance_threshold_km = 0
):
    """
    Constraint:
    Zones where:
    1. There are at least `min_transport_types` transport types present.
    2. At least `poi_proximity_ratio` fraction of POIs are within `distance_threshold_km` km of any transport POI.
    """

    transport_types = ["bus_stop", "subway_entrance", "taxi", "station", "aerodrome"]
    poi_df = get_poi_spend_dataset()
    zone_df = create_zone(poi_df)
    survived_zones = []

    for zone_id in zone_df["zone_id"]:

        # ---- Count transport types and collect transport POIs ----
        transport_count = 0
        all_transport_coords = []
        for t_type in transport_types:
            transport_map = get_transport_pois_in_zone(zone_df, t_type)
            coords = transport_map.get(zone_id, [])
            if coords:
                transport_count += 1
                all_transport_coords.extend(coords)

        if transport_count < min_transport_types or not all_transport_coords:
            continue

        # ---- Get POIs in zone ----
        zone_pois = filter_df_based_on_zone(poi_df, zone_id)
        if zone_pois.empty:
            continue

        poi_coords = zone_pois[["LATITUDE", "LONGITUDE"]].values

        # ---- Check distances ----
        within_count = 0
        for lat_poi, lng_poi in poi_coords:
            for lat_tr, lng_tr in all_transport_coords:
                dist_km = get_distance_km(lat_poi, lng_poi, lat_tr, lng_tr)
                if dist_km <= distance_threshold_km:
                    within_count += 1
                    break  # Only count each POI once

        fraction_within = within_count / len(zone_pois)
        if fraction_within >= poi_proximity_ratio:
            survived_zones.append(zone_id)

    return zone_df[zone_df["zone_id"].isin(survived_zones)]
