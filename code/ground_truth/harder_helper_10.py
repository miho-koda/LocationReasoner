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
def harder_helper_10(
    top_category: bool,
    sub_category: bool,
    category_value: str,
    num_neighbors=10,
    required_neighbors_pass=3,
    threshold=400
):
    """
    Constraint:
        population(zone) / count_filtered_POIs(zone) >= threshold

    Filtering rules:
        - If top_category=True:     filter TOP_CATEGORY == category_value
        - If sub_category=True:     filter SUB_CATEGORY == category_value
        - If both True:             use BOTH filters (AND)
        - If both False:            use ALL POIs

    Must pass:
        - Always for my zone
        - At least `required_neighbors_pass` of nearest neighbors
    """

    # --- Load fresh data ---
    poi_df = get_poi_spend_dataset()
    zone_df = create_zone(poi_df)

    # ----------------------------
    # Build category filter
    # ----------------------------
    mask = pd.Series([True] * len(poi_df))

    if top_category:
        mask &= poi_df["TOP_CATEGORY"] == category_value

    if sub_category:
        mask &= poi_df["SUB_CATEGORY"] == category_value

    filtered_pois = poi_df[mask]   # POIs that count toward denominator

    passed_zones = []

    for zone_id in zone_df["zone_id"]:

        # -----------------------------
        # 1. Check the zone itself
        # -----------------------------
        population = get_population(zone_id, zone_df)

        poi_count_zone = len(filtered_pois[filtered_pois["zone_id"] == zone_id])

        if poi_count_zone == 0:
            continue  # Cannot compute → fail automatically

        ratio_zone = population / poi_count_zone

        if ratio_zone < threshold:
            continue  # Zone must pass its own requirement

        # -----------------------------
        # 2. Check nearest neighbors
        # -----------------------------
        neighbors = get_neighbor_zones(zone_df, zone_id, num_neighbors)

        neighbor_pass_count = 0

        for nbr in neighbors:
            nbr_pop = get_population(nbr, zone_df)
            nbr_poi_count = len(filtered_pois[filtered_pois["zone_id"] == nbr])

            if nbr_poi_count == 0:
                continue  # no denominator → treated as fail

            nbr_ratio = nbr_pop / nbr_poi_count

            if nbr_ratio >= threshold:
                neighbor_pass_count += 1

        # -----------------------------
        # 3. Confirm enough neighbors passed
        # -----------------------------
        if neighbor_pass_count >= required_neighbors_pass:
            passed_zones.append(zone_id)

    return zone_df[zone_df["zone_id"].isin(passed_zones)]

