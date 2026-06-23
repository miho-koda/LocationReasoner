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
from site_selection.analysis import get_spendparam_years
from site_selection.filter import filter_df_based_on_zone, filter_pois_by_top_category, get_transport_pois_in_zone
from site_selection.population import get_population
import operator



def harder_helper_5(
    include_my_zone=True,
    num_neighbors=2,
    threshold=3000,
    transport_types=None
):
    """
    Constraint:
    Sum of population in my zone + nearest neighbors divided by
    the number of transport types in the zone ≥ threshold.

    transport_types: list of transport types to count, e.g.,
        ["bus_stop", "subway_entrance", "taxi", "station", "aerodrome"]
    """

    if transport_types is None:
        transport_types = ["bus_stop", "subway_entrance", "taxi", "station", "aerodrome"]

    poi_df = get_poi_spend_dataset()
    zone_df = create_zone(poi_df)
    survived_zones = []

    # ---- Precompute transport types presence per zone ----
    transport_presence = {zone_id: set() for zone_id in zone_df["zone_id"]}

    for transport_type in transport_types:
        transport_map = get_transport_pois_in_zone(zone_df, transport_type)
        for zone_id, locations in transport_map.items():
            if locations:
                transport_presence[zone_id].add(transport_type)

    for zone_id in zone_df["zone_id"]:

        # ---- Determine zones to aggregate ----
        zones_to_aggregate = []
        if include_my_zone:
            zones_to_aggregate.append(zone_id)
        neighbors = get_neighbor_zones(zone_df, zone_id, num_neighbors)
        zones_to_aggregate.extend(neighbors)

        # ---- Aggregate population ----
        total_population = sum(get_population(zid, zone_df) for zid in zones_to_aggregate)

        # ---- Count transport types in the main zone ----
        num_transport_types = len(transport_presence.get(zone_id, set()))
        if num_transport_types == 0:
            continue

        # ---- Compute population per transport type ----
        pop_per_transport = total_population / num_transport_types

        # ---- Check threshold ----
        if pop_per_transport >= threshold:
            survived_zones.append(zone_id)

    return zone_df[zone_df["zone_id"].isin(survived_zones)]

