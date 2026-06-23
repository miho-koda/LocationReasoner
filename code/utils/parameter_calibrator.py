"""
Parameter Calibrator for Complex Queries

This script analyzes the dataset to determine realistic parameter ranges for each query type.
Goal: Ensure each query returns 20-70% of zones (not 0, not all).

Run once to generate parameter_ranges.json, which complex_query.py will use.
"""

import json
import os
import sys
import pandas as pd
import numpy as np

# Ensure code/ root is on path so existing imports resolve
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from site_selection.loader import get_poi_spend_dataset
from site_selection.zone import create_zone, get_neighbor_zones
from site_selection.population import get_population
from site_selection.filter import get_transport_pois_in_zone
import random

# Target coverage range
MIN_COVERAGE = 0.20  # At least 20% of zones should match
MAX_COVERAGE = 0.70  # At most 70% of zones should match


def calibrate_parameter(test_values, evaluation_function, total_zones, verbose=True):
    """
    Test different parameter values and find those giving 20-70% zone coverage.

    Args:
        test_values: List of values to test
        evaluation_function: Function that takes a value and returns count of matching zones
        total_zones: Total number of zones in dataset
        verbose: Print progress

    Returns:
        dict with min, max, and valid values
    """
    results = []

    for value in test_values:
        matching_count = evaluation_function(value)
        coverage = matching_count / total_zones

        if verbose:
            print(f"    Value {value}: {matching_count} zones ({coverage:.1%})")

        if MIN_COVERAGE <= coverage <= MAX_COVERAGE:
            results.append(value)

    if len(results) == 0:
        print(f"    ⚠️ WARNING: No values in target range, using closest")
        # Fall back to values closest to target range
        coverages = [(v, evaluation_function(v) / total_zones) for v in test_values]
        # Find values closest to 40% (middle of range)
        sorted_by_distance = sorted(coverages, key=lambda x: abs(x[1] - 0.40))
        results = [sorted_by_distance[0][0], sorted_by_distance[1][0] if len(sorted_by_distance) > 1 else sorted_by_distance[0][0]]

    return {
        'min': min(results),
        'max': max(results),
        'valid_values': results
    }


def calibrate_query_1(poi_spend_df, zone_df):
    """Query 1: Spend Percentage"""
    print("\n📊 Calibrating Query 1: Spend Percentage")

    # Calculate spend percentages for each zone-category
    total_zones = len(zone_df)

    # Aggregate spend by zone and category
    spend_cols = [col for col in poi_spend_df.columns if col.startswith('RAW_TOTAL_SPEND_')]

    test_values = [0.02, 0.05, 0.08, 0.10, 0.12, 0.15, 0.18, 0.20, 0.25, 0.30, 0.40]

    def evaluate(threshold):
        zones_matching = set()
        for zone_id in zone_df['zone_id']:
            zone_pois = poi_spend_df[poi_spend_df['zone_id'] == zone_id]
            if len(zone_pois) == 0:
                continue

            # Calculate total spend for zone
            total_spend = zone_pois[spend_cols].sum().sum()
            if total_spend == 0:
                continue

            # Check each category
            for category in zone_pois['TOP_CATEGORY'].unique():
                cat_pois = zone_pois[zone_pois['TOP_CATEGORY'] == category]
                cat_spend = cat_pois[spend_cols].sum().sum()
                pct = cat_spend / total_spend

                if pct >= threshold:
                    zones_matching.add(zone_id)
                    break

        return len(zones_matching)

    result = calibrate_parameter(test_values, evaluate, total_zones)
    return {'percent_min': result['min'], 'percent_max': result['max']}


def calibrate_query_2(poi_spend_df, zone_df):
    """Query 2: Average Median Spend"""
    print("\n📊 Calibrating Query 2: Average Median Spend")

    total_zones = len(zone_df)
    median_cols = [col for col in poi_spend_df.columns if col.startswith('MEDIAN_SPEND_PER_TRANSACTION_')]

    test_values = [5, 8, 10, 12, 15, 20, 25, 30, 35, 40, 50]

    def evaluate(threshold):
        zones_matching = set()
        for zone_id in zone_df['zone_id']:
            zone_pois = poi_spend_df[poi_spend_df['zone_id'] == zone_id]
            if len(zone_pois) == 0:
                continue

            # For each category, calculate average median spend
            for category in zone_pois['TOP_CATEGORY'].unique():
                cat_pois = zone_pois[zone_pois['TOP_CATEGORY'] == category]
                avg_median = cat_pois[median_cols].mean().mean()  # Mean across POIs and years

                if pd.notna(avg_median) and avg_median >= threshold:
                    zones_matching.add(zone_id)
                    break

        return len(zones_matching)

    result = calibrate_parameter(test_values, evaluate, total_zones)
    return {'threshold_min': result['min'], 'threshold_max': result['max']}


def calibrate_query_3(poi_spend_df, zone_df):
    """Query 3: Growth Rates"""
    print("\n📊 Calibrating Query 3: Growth Rates")

    total_zones = len(zone_df)
    years = [2019, 2020, 2021, 2022, 2023, 2024]

    test_values = [1.2, 1.3, 1.5, 1.7, 2.0, 2.3, 2.5, 3.0, 4.0, 5.0]

    def evaluate(threshold):
        zones_matching = set()
        for zone_id in zone_df['zone_id']:
            zone_pois = poi_spend_df[poi_spend_df['zone_id'] == zone_id]
            if len(zone_pois) == 0:
                continue

            # Check growth between any year pair
            for i in range(len(years) - 1):
                year1, year2 = years[i], years[i + 1]
                col1 = f'RAW_TOTAL_SPEND_{year1}'
                col2 = f'RAW_TOTAL_SPEND_{year2}'

                spend1 = zone_pois[col1].sum()
                spend2 = zone_pois[col2].sum()

                if spend1 > 0 and spend2 > 0:
                    growth = spend2 / spend1
                    if growth >= threshold:
                        zones_matching.add(zone_id)
                        break

            if zone_id in zones_matching:
                break

        return len(zones_matching)

    result = calibrate_parameter(test_values, evaluate, total_zones)
    return {'threshold_min': result['min'], 'threshold_max': result['max']}


def calibrate_query_4(poi_spend_df, zone_df):
    """Query 4: Population per POI"""
    print("\n📊 Calibrating Query 4: Population per POI")

    total_zones = len(zone_df)

    # Get populations for all zones (this will take time)
    print("  Loading population data...")
    populations = {}
    for zone_id in zone_df['zone_id']:
        try:
            populations[zone_id] = get_population(zone_id, zone_df)
        except:
            populations[zone_id] = 0

    test_values = [50, 100, 150, 200, 300, 400, 500, 700, 1000, 1500, 2000]

    def evaluate(threshold):
        zones_matching = set()
        for zone_id in zone_df['zone_id']:
            zone_pois = poi_spend_df[poi_spend_df['zone_id'] == zone_id]
            if len(zone_pois) == 0:
                continue

            pop = populations.get(zone_id, 0)
            if pop == 0:
                continue

            # Check any category
            for category in zone_pois['TOP_CATEGORY'].unique():
                cat_count = len(zone_pois[zone_pois['TOP_CATEGORY'] == category])
                if cat_count > 0:
                    ratio = pop / cat_count
                    if ratio >= threshold:
                        zones_matching.add(zone_id)
                        break

        return len(zones_matching)

    result = calibrate_parameter(test_values, evaluate, total_zones)
    return {'threshold_min': result['min'], 'threshold_max': result['max']}


def calibrate_query_5(poi_spend_df, zone_df):
    """Query 5: Population per Transport Type"""
    print("\n📊 Calibrating Query 5: Population per Transport Type")

    total_zones = len(zone_df)

    # Get populations
    print("  Loading population data...")
    populations = {}
    for zone_id in zone_df['zone_id']:
        try:
            populations[zone_id] = get_population(zone_id, zone_df)
        except:
            populations[zone_id] = 0

    # Get transport data
    print("  Loading transport data...")
    transport_types = ['bus_stop', 'station', 'subway_entrance', 'aerodrome', 'taxi']
    transport_data = {}
    for t_type in transport_types:
        try:
            transport_data[t_type] = get_transport_pois_in_zone(zone_df, t_type)
        except Exception as e:
            print(f"    Warning: Could not load {t_type}: {e}")
            transport_data[t_type] = {}

    test_values = [500, 1000, 1500, 2000, 2500, 3000, 4000, 5000]

    def evaluate(threshold):
        zones_matching = 0
        for zone_id in zone_df['zone_id']:
            pop = populations.get(zone_id, 0)
            if pop == 0:
                continue

            # Count transport types present
            num_types = sum(1 for t in transport_types if len(transport_data.get(t, {}).get(zone_id, [])) > 0)

            if num_types > 0:
                ratio = pop / num_types
                if ratio >= threshold:
                    zones_matching += 1

        return zones_matching

    result = calibrate_parameter(test_values, evaluate, total_zones)
    return {'threshold_min': result['min'], 'threshold_max': result['max']}


def calibrate_query_6(poi_spend_df, zone_df):
    """Query 6: Multiple Categories POI Ratio"""
    print("\n📊 Calibrating Query 6: Multiple Categories POI Ratio")

    total_zones = len(zone_df)

    # Calibrate min_pois_per_category
    print("  Calibrating min_pois_per_category...")
    poi_test_values = [2, 3, 4, 5, 6, 8, 10, 12, 15, 20, 25]

    def evaluate_pois(threshold):
        zones_matching = 0
        for zone_id in zone_df['zone_id']:
            zone_pois = poi_spend_df[poi_spend_df['zone_id'] == zone_id]
            if len(zone_pois) == 0:
                continue

            # Count categories with >= threshold POIs
            categories_meeting = 0
            for category in zone_pois['TOP_CATEGORY'].unique():
                cat_count = len(zone_pois[zone_pois['TOP_CATEGORY'] == category])
                if cat_count >= threshold:
                    categories_meeting += 1

            # Need at least 2 categories to meet threshold
            if categories_meeting >= 2:
                zones_matching += 1

        return zones_matching

    poi_result = calibrate_parameter(poi_test_values, evaluate_pois, total_zones)

    # Calibrate ratio_threshold
    print("  Calibrating ratio_threshold...")
    ratio_test_values = [0.05, 0.08, 0.10, 0.12, 0.15, 0.18, 0.20, 0.25, 0.30, 0.40, 0.50]

    def evaluate_ratio(threshold):
        zones_matching = 0
        for zone_id in zone_df['zone_id']:
            zone_pois = poi_spend_df[poi_spend_df['zone_id'] == zone_id]
            total_pois = len(zone_pois)
            if total_pois == 0:
                continue

            # Get top 2 categories by count
            category_counts = zone_pois['TOP_CATEGORY'].value_counts()
            if len(category_counts) < 2:
                continue

            top_2_count = category_counts.iloc[:2].sum()
            ratio = top_2_count / total_pois

            if ratio >= threshold:
                zones_matching += 1

        return zones_matching

    ratio_result = calibrate_parameter(ratio_test_values, evaluate_ratio, total_zones)

    return {
        'min_pois_per_category_min': poi_result['min'],
        'min_pois_per_category_max': poi_result['max'],
        'ratio_threshold_min': ratio_result['min'],
        'ratio_threshold_max': ratio_result['max'],
        'num_categories_required_max': 3  # Hardcoded: don't require more than 3
    }


def calibrate_query_7(poi_spend_df, zone_df):
    """Query 7: Transport Proximity (sampling 50 zones)"""
    print("\n📊 Calibrating Query 7: Transport Proximity (sampling 50 zones)")

    # Sample 50 random zones for efficiency
    sampled_zones = random.sample(list(zone_df['zone_id']), min(50, len(zone_df)))

    # Use conservative defaults since this is expensive
    print("  Using conservative defaults for transport proximity")

    return {
        'distance_threshold_km_min': 1.0,
        'distance_threshold_km_max': 2.5,
        'poi_proximity_ratio_min': 0.25,
        'poi_proximity_ratio_max': 0.65,
        'min_transport_types_max': 3  # Don't require more than 3 types
    }


def calibrate_query_8(poi_spend_df, zone_df):
    """Query 8: Category Fraction Limit"""
    print("\n📊 Calibrating Query 8: Category Fraction Limit")

    total_zones = len(zone_df)

    test_values = [0.05, 0.08, 0.10, 0.12, 0.15, 0.18, 0.20, 0.25, 0.30, 0.40]

    def evaluate(threshold):
        zones_matching = 0
        for zone_id in zone_df['zone_id']:
            zone_pois = poi_spend_df[poi_spend_df['zone_id'] == zone_id]
            total_pois = len(zone_pois)
            if total_pois == 0:
                continue

            # Find max category fraction
            category_counts = zone_pois['TOP_CATEGORY'].value_counts()
            max_fraction = category_counts.iloc[0] / total_pois if len(category_counts) > 0 else 0

            if max_fraction <= threshold:
                zones_matching += 1

        return zones_matching

    result = calibrate_parameter(test_values, evaluate, total_zones)
    return {'max_fraction_min': result['min'], 'max_fraction_max': result['max']}


def calibrate_query_9(poi_spend_df, zone_df):
    """Query 9: Population Density"""
    print("\n📊 Calibrating Query 9: Population Density")

    total_zones = len(zone_df)

    # Get populations
    print("  Loading population data...")
    populations = {}
    for zone_id in zone_df['zone_id']:
        try:
            populations[zone_id] = get_population(zone_id, zone_df)
        except:
            populations[zone_id] = 0

    # Calculate areas (project to EPSG:3857 like harder_helper_9)
    print("  Calculating zone areas...")
    zone_df_proj = zone_df.to_crs(epsg=3857)

    test_values = [1000, 2000, 3000, 4000, 5000, 6000, 8000, 10000, 12000, 15000]

    def evaluate(threshold):
        zones_matching = 0
        for zone_id in zone_df['zone_id']:
            pop = populations.get(zone_id, 0)
            if pop == 0:
                continue

            geom = zone_df_proj.loc[zone_df_proj['zone_id'] == zone_id, 'geometry'].iloc[0]
            area_km2 = geom.area / 1_000_000

            if area_km2 > 0:
                density = pop / area_km2
                if density >= threshold:
                    zones_matching += 1

        return zones_matching

    result = calibrate_parameter(test_values, evaluate, total_zones)
    return {'threshold_min': result['min'], 'threshold_max': result['max']}


def calibrate_query_10(poi_spend_df, zone_df):
    """Query 10: Population over Category (same as Query 4)"""
    print("\n📊 Calibrating Query 10: Population over Category")
    print("  Using same logic as Query 4...")

    return calibrate_query_4(poi_spend_df, zone_df)


def calibrate_all_queries():
    """Main calibration function"""
    print("="*80)
    print("PARAMETER CALIBRATOR")
    print("="*80)
    print(f"Target: Each query should match {MIN_COVERAGE:.0%} to {MAX_COVERAGE:.0%} of zones")
    print("="*80)

    # Load data
    print("\n📂 Loading data...")
    poi_spend_df = get_poi_spend_dataset()
    zone_df = create_zone(poi_spend_df)
    print(f"✅ Loaded {len(poi_spend_df)} POIs across {len(zone_df)} zones")

    # Calibrate each query
    ranges = {}

    try:
        ranges['query_1_spend_percentage'] = calibrate_query_1(poi_spend_df, zone_df)
    except Exception as e:
        print(f"❌ Query 1 failed: {e}")
        ranges['query_1_spend_percentage'] = {'percent_min': 0.08, 'percent_max': 0.20}

    try:
        ranges['query_2_avg_median_spend'] = calibrate_query_2(poi_spend_df, zone_df)
    except Exception as e:
        print(f"❌ Query 2 failed: {e}")
        ranges['query_2_avg_median_spend'] = {'threshold_min': 10, 'threshold_max': 30}

    try:
        ranges['query_3_growth'] = calibrate_query_3(poi_spend_df, zone_df)
    except Exception as e:
        print(f"❌ Query 3 failed: {e}")
        ranges['query_3_growth'] = {'threshold_min': 1.5, 'threshold_max': 2.5}

    try:
        ranges['query_4_population_per_poi'] = calibrate_query_4(poi_spend_df, zone_df)
    except Exception as e:
        print(f"❌ Query 4 failed: {e}")
        ranges['query_4_population_per_poi'] = {'threshold_min': 200, 'threshold_max': 800}

    try:
        ranges['query_5_population_per_transport'] = calibrate_query_5(poi_spend_df, zone_df)
    except Exception as e:
        print(f"❌ Query 5 failed: {e}")
        ranges['query_5_population_per_transport'] = {'threshold_min': 1500, 'threshold_max': 3500}

    try:
        ranges['query_6_multiple_categories'] = calibrate_query_6(poi_spend_df, zone_df)
    except Exception as e:
        print(f"❌ Query 6 failed: {e}")
        ranges['query_6_multiple_categories'] = {
            'min_pois_per_category_min': 2,
            'min_pois_per_category_max': 6,
            'ratio_threshold_min': 0.08,
            'ratio_threshold_max': 0.18,
            'num_categories_required_max': 3
        }

    try:
        ranges['query_7_transport_proximity'] = calibrate_query_7(poi_spend_df, zone_df)
    except Exception as e:
        print(f"❌ Query 7 failed: {e}")
        ranges['query_7_transport_proximity'] = {
            'distance_threshold_km_min': 1.0,
            'distance_threshold_km_max': 2.5,
            'poi_proximity_ratio_min': 0.25,
            'poi_proximity_ratio_max': 0.65,
            'min_transport_types_max': 3
        }

    try:
        ranges['query_8_category_fraction'] = calibrate_query_8(poi_spend_df, zone_df)
    except Exception as e:
        print(f"❌ Query 8 failed: {e}")
        ranges['query_8_category_fraction'] = {'max_fraction_min': 0.10, 'max_fraction_max': 0.25}

    try:
        ranges['query_9_population_density'] = calibrate_query_9(poi_spend_df, zone_df)
    except Exception as e:
        print(f"❌ Query 9 failed: {e}")
        ranges['query_9_population_density'] = {'threshold_min': 3000, 'threshold_max': 8000}

    try:
        ranges['query_10_population_over_category'] = calibrate_query_10(poi_spend_df, zone_df)
    except Exception as e:
        print(f"❌ Query 10 failed: {e}")
        ranges['query_10_population_over_category'] = {'threshold_min': 200, 'threshold_max': 800}

    # Save to JSON — write to code/queries/parameter_ranges.json
    _code_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_path = os.path.join(_code_dir, 'queries', 'parameter_ranges.json')
    with open(output_path, 'w') as f:
        json.dump(ranges, f, indent=2)

    print("\n" + "="*80)
    print(f"✅ Calibration complete! Saved to: {output_path}")
    print("="*80)
    print("\nNext step: complex_query.py will automatically use these ranges")

    return ranges


if __name__ == "__main__":
    calibrate_all_queries()
