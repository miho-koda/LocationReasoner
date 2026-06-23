'''
Mini Complex Query types

1. {40%} of total spend from {beg - end} for top/sub category {top_category} > x for my zone and 3 of my nearest zone.

2. average median spend of from {beg - end} for top/sub category {top_category} > x for my zone and 3 of my nearest zone.

3. the total spend from end year is atleast 3 times more than start year for my zone and atleast 3/5 of my nearest neighbors.

4. "The total population in my zone and 3 nearest zones, divided by the total number of POIs in the top category 'Fitness' in those zones, ≥ 500."

5. Sum of population in the zone + 2 nearest neighbors ÷ number of transport types in the zone ≥ 3,000 each needs to satisfy

6. "Zones where at least 2 sub-categories in {'Gym', 'Yoga Studio', 'Pilates Studio'} each have ≥ 3 POIs in each zone AND the sum of those POIs ÷ total POIs in zone ≥ 0.25."

7. At least 3 types of transportation AND at least 50% of POIs within 150m of any transport type euclidean distance

8. Sub-category 'Coffee Shops' has ≤ 40% of total POIs in my zone AND in at least 2 of 5 nearest neighbors

9. Population density (population ÷ zone area) in my zone + 2 nearest neighbors ≥ 3,000

10. Population in my zone ÷ total number of POIs in top category "Fitness" ≥ 400, must happen in my zone and 3/10 of my nearest neighbor zones
'''

import json
import os

# Load calibrated parameter ranges
_param_ranges_path = os.path.join(os.path.dirname(__file__), 'parameter_ranges.json')
try:
    with open(_param_ranges_path, 'r') as f:
        PARAM_RANGES = json.load(f)
    print("✅ Loaded calibrated parameter ranges")
except FileNotFoundError:
    print("⚠️ parameter_ranges.json not found - using fallback defaults")
    PARAM_RANGES = {
        'query_1_spend_percentage': {'percent_min': 0.08, 'percent_max': 0.20},
        'query_2_avg_median_spend': {'threshold_min': 10, 'threshold_max': 30},
        'query_3_growth': {'threshold_min': 1.5, 'threshold_max': 2.5},
        'query_4_population_per_poi': {'threshold_min': 200, 'threshold_max': 800},
        'query_5_population_per_transport': {'threshold_min': 1500, 'threshold_max': 3500},
        'query_6_multiple_categories': {
            'min_pois_per_category_min': 2,
            'min_pois_per_category_max': 6,
            'ratio_threshold_min': 0.08,
            'ratio_threshold_max': 0.18,
            'num_categories_required_max': 3
        },
        'query_7_transport_proximity': {
            'distance_threshold_km_min': 1.0,
            'distance_threshold_km_max': 2.5,
            'poi_proximity_ratio_min': 0.25,
            'poi_proximity_ratio_max': 0.65,
            'min_transport_types_max': 3
        },
        'query_8_category_fraction': {'max_fraction_min': 0.10, 'max_fraction_max': 0.25},
        'query_9_population_density': {'threshold_min': 3000, 'threshold_max': 8000},
        'query_10_population_over_category': {'threshold_min': 200, 'threshold_max': 800}
    }

TOP_CATEGORY = ['Museums, Historical Sites, and Similar Institutions',
'Other Amusement and Recreation Industries',
'Lessors of Real Estate',
'Other Miscellaneous Manufacturing',
'Taxi and Limousine Service',
'Offices of Other Health Practitioners',
'Offices of Physicians',
'Couriers and Express Delivery Services',
'Activities Related to Real Estate',
'Other Financial Investment Activities',
'Grocery Stores',
'Automobile Dealers',
'Other Personal Services',
'Urban Transit Systems',
'Gambling Industries',
'Restaurants and Other Eating Places',
'Individual and Family Services',
'Drinking Places (Alcoholic Beverages)',
'Management, Scientific, and Technical Consulting Services',
'Management of Companies and Enterprises',
'Beer, Wine, and Liquor Stores',
'Building Equipment Contractors']


SUB_CATEGORY = ['Beauty Salons', 'Museums, Historical Sites, and Similar Institutions',
'Other Amusement and Recreation Industries',
'Lessors of Real Estate',
'Other Miscellaneous Manufacturing',
'Taxi and Limousine Service',
'Offices of Other Health Practitioners',
'Offices of Physicians',
'Fitness and Recreational Sports Centers',
'Lessors of Residential Buildings and Dwellings',
'Corporate, Subsidiary, and Regional Managing Offices',
'Offices of Lawyers',
'Offices of Dentists',
'Offices of Physicians (except Mental Health Specialists)',
'Couriers and Express Delivery Services',
'Residential Property Managers',
'Investment Advice',
'Parking Lots and Garages',
'Bus and Other Motor Vehicle Transit Systems',
'Nature Parks and Other Similar Institutions']
import random

def choose_year_range():
    years = list(range(2019, 2025))
    # start can't be 2024
    start = random.choice(years[:-1])
    end_candidates = [y for y in years if y > start]
    end = random.choice(end_candidates)
    return start, end


def build_zone_scope(include_my_zone, num_neighbors):
    if include_my_zone and num_neighbors > 0:
        if num_neighbors == 1:
            return "my zone plus 1 nearby zone"
        return f"my zone plus {num_neighbors} nearby zones"
    elif include_my_zone and num_neighbors == 0:
        return "my zone only"
    elif not include_my_zone and num_neighbors > 0:
        if num_neighbors == 1:
            return "1 nearby zone"
        return f"{num_neighbors} nearby zones"
    else:
        return "the area"


def generate_single_values():
    # Use calibrated ranges for query 1
    percent = round(random.uniform(
        PARAM_RANGES['query_1_spend_percentage']['percent_min'],
        PARAM_RANGES['query_1_spend_percentage']['percent_max']
    ), 2)
    start_year, end_year = choose_year_range()

    # choose category type
    is_top = random.choice([True, False])
    category_type = "top category" if is_top else "sub category"
    category_name = random.choice(TOP_CATEGORY if is_top else SUB_CATEGORY)

    include_my_zone = random.choice([True, False])
    num_neighbors = random.randint(0, 8)
    operator_str = random.choice([">=", ">"])

    zone_scope = build_zone_scope(include_my_zone, num_neighbors)

    # return values + scope for language generation
    return {
        "percent": percent,
        "start_year": start_year,
        "end_year": end_year,
        "top_category": is_top,
        "category_type": category_type,
        "category_name": f"{{{category_name}}}",
        "include_my_zone": include_my_zone,
        "num_neighbors": num_neighbors,
        "operator_str": operator_str,
        "zone_scope": zone_scope
    }

# ============== COMPLEX QUERY 1 ==============
SPEND_PERCENTAGE_TEMPLATES = [
    "I'm looking for neighborhoods where people are clearly gravitating toward the {category_type} {category_name}—specifically where it represents {operator_str} {percent}% of total spend across {zone_scope} between {start_year} and {end_year}. I'm trying to identify places where this category shapes the local vibe.",
    "Find zones such that the {category_type} {category_name} accounts for {operator_str} {percent}% of total spending in {zone_scope} from {start_year} to {end_year}. This helps pinpoint areas dominated by this category.",
    "Show me areas where {category_type} {category_name} makes up {operator_str} {percent}% of all spend across {zone_scope} during {start_year}–{end_year}. I want to see where this category has significant market share.",
    "Check zones where the {category_type} {category_name} contributes {operator_str} {percent}% of total spending in {zone_scope} between {start_year} and {end_year}."
]

SPEND_PERCENTAGE_CLAUSE_TEMPLATES = [
    "the {category_type} {category_name} represents {operator_str} {percent}% of total spend across {zone_scope} between {start_year} and {end_year}",
    "{category_type} {category_name} contributes {operator_str} {percent}% of total spending in {zone_scope} from {start_year}–{end_year}",
    "at least {percent}% of total spend from {start_year} to {end_year} comes from {category_type} {category_name} in {zone_scope}",
]

def complex_query_1(n=10):
    output = []

    for _ in range(n):
        vals = generate_single_values()

        # Generate full query
        template = random.choice(SPEND_PERCENTAGE_TEMPLATES)
        query = template.format(**vals)

        # Generate clause
        clause_template = random.choice(SPEND_PERCENTAGE_CLAUSE_TEMPLATES)
        clause = clause_template.format(**vals)

        # build clean parameter dict for tuple
        param_dict = {
            "percent": vals["percent"],
            "start_year": vals["start_year"],
            "end_year": vals["end_year"],
            "top_category": vals["top_category"],
            "category_name": vals["category_name"][1:-1],
            "include_my_zone": vals["include_my_zone"],
            "num_neighbors": vals["num_neighbors"],
            "operator_str": vals["operator_str"]
        }

        output.append((query, param_dict, clause))

    return output

# ============== COMPLEX QUERY 2 ==============
AVG_MEDIAN_SPEND_TEMPLATES = [
    "I'm evaluating zones where the {category_type} {category_name} has an average median spend {operator_str} {threshold} between {start_year}–{end_year} across {zone_scope}. I want to see if this category consistently performs well.",
    "Look for zones such that the {category_type} {category_name} exceeds an average median spend of {threshold} from {start_year} to {end_year}, considering {zone_scope}. This helps me identify high-spend areas.",
    "Can you find zones where {category_type} {category_name} averages a median spend {operator_str} {threshold} over {start_year}–{end_year}, including {zone_scope}? I'm focusing on zones with strong spending in this category.",
    "Show me neighborhoods where the {category_type} {category_name} has a median spend average {operator_str} {threshold} during {start_year}–{end_year} across {zone_scope}. I want reliable spending hotspots."
]

AVG_MEDIAN_SPEND_CLAUSE_TEMPLATES = [
    "the {category_type} {category_name} has an average median spend {operator_str} {threshold} between {start_year} and {end_year} across {zone_scope}",
    "{category_type} {category_name} exceeds an average median spend of {threshold} from {start_year} to {end_year} in {zone_scope}",
    "the average median spend for {category_type} {category_name} is {operator_str} {threshold} over {start_year}–{end_year} in {zone_scope}",
]

def complex_query_2(n=10):
    output = []

    for _ in range(n):
        percent = round(random.uniform(0.01, 0.40), 2)  # optional: for extra info
        start_year, end_year = choose_year_range()

        # choose category type
        is_top = random.choice([True, False])
        category_name = random.choice(TOP_CATEGORY if is_top else SUB_CATEGORY)
        category_type = "top category" if is_top else "sub category"

        include_my_zone = random.choice([True, False])
        num_neighbors = random.randint(0, 8)
        operator_str = random.choice([">=", ">"])
        # Use calibrated range
        threshold = random.randint(
            PARAM_RANGES['query_2_avg_median_spend']['threshold_min'],
            PARAM_RANGES['query_2_avg_median_spend']['threshold_max']
        )

        zone_scope = build_zone_scope(include_my_zone, num_neighbors)

        # For query text, wrap category name in {}

        vals = {
            "start_year": start_year,
            "end_year": end_year,
            "top_category": is_top,
            "category_name": f"{{{category_name}}}",
            "category_type": category_type,
            "threshold": threshold,
            "include_my_zone": include_my_zone,
            "num_neighbors": num_neighbors,
            "operator_str": operator_str,
            "zone_scope": zone_scope,
        }

        # Generate full query
        template = random.choice(AVG_MEDIAN_SPEND_TEMPLATES)
        query = template.format(**vals)

        # Generate clause
        clause_template = random.choice(AVG_MEDIAN_SPEND_CLAUSE_TEMPLATES)
        clause = clause_template.format(**vals)

        param_dict = {
            "start_year": start_year,
            "end_year": end_year,
            "top_category": is_top,
            "category_name": category_name,
            "threshold": threshold,
            "include_my_zone": include_my_zone,
            "num_neighbors": num_neighbors,
            "operator_str": operator_str
        }

        output.append((query, param_dict, clause))

    return output

# ============== COMPLEX QUERY 3 ==============
ZONE_GROWTH_TEMPLATES = [
    "I'm looking for zones where total spending increased significantly: specifically, the spend in {end_year} is at least {threshold}x the spend in {start_year} across {zone_scope}. I want to make sure there is strong growth.",
    "Find neighborhoods where spending grew by a factor of {threshold} between {start_year} and {end_year}, considering {zone_scope}. At least {min_neighbors_pass} of the neighbor zones must meet this growth as well.",
    "Check for zones where the total spend in {end_year} is {threshold} times or more than in {start_year}, including {zone_scope}. I'm only interested if most of the nearby zones also follow this trend.",
    "Show me zones that experienced strong growth: spend in {end_year} ≥ {threshold}x spend in {start_year} across {min_neighbors_pass} out of {zone_scope} of the neighboring zones."
]

ZONE_GROWTH_CLAUSE_TEMPLATES = [
    "spend in {end_year} is at least {threshold}× spend in {start_year} across {zone_scope}",
    "total spending grew by a factor of {threshold} from {start_year} to {end_year} in {zone_scope}, with at least {min_neighbors_pass} zones meeting this threshold",
    "the zone shows strong growth with {end_year} spend being {threshold} times {start_year} spend, applying to at least {min_neighbors_pass} zones",
]

def complex_query_3(n=10):
    output = []

    for _ in range(n):
        start_year, end_year = choose_year_range()
        include_my_zone = random.choice([True, False])
        num_neighbors = random.randint(0, 8)
        min_neighbors_pass = random.randint(1, max(1, num_neighbors))
        # Use calibrated range
        threshold = round(random.uniform(
            PARAM_RANGES['query_3_growth']['threshold_min'],
            PARAM_RANGES['query_3_growth']['threshold_max']
        ), 1)

        zone_scope = build_zone_scope(include_my_zone, num_neighbors)

        vals = {
            "start_year": start_year,
            "end_year": end_year,
            "threshold": threshold,
            "include_my_zone": include_my_zone,
            "num_neighbors": num_neighbors,
            "min_neighbors_pass": min_neighbors_pass,
            "zone_scope": zone_scope
        }

        # Generate full query
        template = random.choice(ZONE_GROWTH_TEMPLATES)
        query = template.format(**vals)

        # Generate clause
        clause_template = random.choice(ZONE_GROWTH_CLAUSE_TEMPLATES)
        clause = clause_template.format(**vals)

        param_dict = {
            "start_year": start_year,
            "end_year": end_year,
            "threshold": threshold,
            "include_my_zone": include_my_zone,
            "num_neighbors": num_neighbors,
            "min_neighbors_pass": min_neighbors_pass
        }

        output.append((query, param_dict, clause))

    return output

# ============== COMPLEX QUERY 4 ==============
POPULATION_PER_POI_TEMPLATES = [
    "I'm interested in zones where the total population across {zone_scope}, divided by the number of {category_type} {category_braced}, is at least {threshold}. This helps identify areas with strong demand relative to supply.",
    "Find zones such that population over number of pois in {category_type} {category_braced} in {zone_scope} is ≥ {threshold}. I want to make sure both my zone and nearby zones are sufficiently populated compared to the number of these locations.",
    "Check for zones where the population-to-number of pois in {category_type} {category_braced} ratio reaches {threshold} across {zone_scope}. This ensures that the local population can support these types of venues.",
    "Show me zones where the total population divided by number of pois in {category_type} {category_braced} in {zone_scope} is at least {threshold}, including both my zone and selected nearby zones."
]

POPULATION_PER_POI_CLAUSE_TEMPLATES = [
    "the total population divided by number of POIs in {category_type} {category_braced} is at least {threshold} in {zone_scope}",
    "population-to-POI ratio for {category_type} {category_braced} reaches {threshold} across {zone_scope}",
    "the ratio of population over {category_type} {category_braced} POIs is ≥ {threshold} in {zone_scope}",
]

def complex_query_4(n=10):
    output = []

    for _ in range(n):
        include_my_zone = random.choice([True, False])
        num_neighbors = random.randint(0, 8)
        # Use calibrated range
        threshold = random.randint(
            PARAM_RANGES['query_4_population_per_poi']['threshold_min'],
            PARAM_RANGES['query_4_population_per_poi']['threshold_max']
        )

        # Decide category type
        top_category_flag = random.choice([True, False])
        sub_category_flag = not top_category_flag
        category_value = random.choice(TOP_CATEGORY if top_category_flag else SUB_CATEGORY)
        category_type = "top category" if top_category_flag else "sub category"
        category_braced = f"{{{category_value}}}"

        zone_scope = build_zone_scope(include_my_zone, num_neighbors)

        vals = {
            "include_my_zone": include_my_zone,
            "num_neighbors": num_neighbors,
            "threshold": threshold,
            "category_type": category_type,
            "category_value": category_value,
            "category_braced": category_braced,
            "zone_scope": zone_scope
        }

        # Generate full query
        template = random.choice(POPULATION_PER_POI_TEMPLATES)
        query = template.format(**vals)

        # Generate clause
        clause_template = random.choice(POPULATION_PER_POI_CLAUSE_TEMPLATES)
        clause = clause_template.format(**vals)

        param_dict = {
            "include_my_zone": include_my_zone,
            "num_neighbors": num_neighbors,
            "top_category": top_category_flag,
            "sub_category": sub_category_flag,
            "category_value": category_value,
            "threshold": threshold
        }

        output.append((query, param_dict, clause))

    return output

# ============== COMPLEX QUERY 5 ==============
POPULATION_PER_TRANSPORT_TEMPLATES = [
    "I'm looking for zones where the total population across {zone_scope} divided by the number of transport types is at least {threshold}. Each zone needs to meet this requirement to ensure adequate coverage.",
    "Find neighborhoods such that population over transport types in {zone_scope} ≥ {threshold} for each zone. This ensures both my zone and nearby zones are well served by transportation options.",
    "Check for zones where the population-to-transport-type ratio reaches {threshold} across {zone_scope} for each zone. I want to make sure every zone can support its transport network.",
    "Show me zones where the sum of population divided by the number of transport types in {zone_scope} is at least {threshold} for each zone, including my zone and its neighbors."
]

POPULATION_PER_TRANSPORT_CLAUSE_TEMPLATES = [
    "the total population across {zone_scope} divided by the number of transport types is at least {threshold} for each zone",
    "population over transport types in {zone_scope} is ≥ {threshold} for each zone",
    "the population-to-transport-type ratio reaches {threshold} across {zone_scope} for each zone",
]

def complex_query_5(n=10):
    output = []

    for _ in range(n):
        include_my_zone = random.choice([True, False])
        num_neighbors = random.randint(0, 8)
        # Use calibrated range
        threshold = random.randint(
            PARAM_RANGES['query_5_population_per_transport']['threshold_min'],
            PARAM_RANGES['query_5_population_per_transport']['threshold_max']
        )

        zone_scope = build_zone_scope(include_my_zone, num_neighbors)

        vals = {
            "include_my_zone": include_my_zone,
            "num_neighbors": num_neighbors,
            "threshold": threshold,
            "zone_scope": zone_scope
        }

        # Generate full query
        template = random.choice(POPULATION_PER_TRANSPORT_TEMPLATES)
        query = template.format(**vals)

        # Generate clause
        clause_template = random.choice(POPULATION_PER_TRANSPORT_CLAUSE_TEMPLATES)
        clause = clause_template.format(**vals)

        param_dict = {
            "include_my_zone": include_my_zone,
            "num_neighbors": num_neighbors,
            "threshold": threshold
        }

        output.append((query, param_dict, clause))

    return output

# ============== COMPLEX QUERY 6 ==============
import random

SUBCATEGORY_POI_RATIO_TEMPLATES = [
    "I'm evaluating zones where at least {num_categories_required} {category_type} among {category_braced_list} have ≥ {min_pois_per_category} POIs, and the sum of these POIs divided by the total POIs in the zone is ≥ {ratio_threshold}.",
    "Find zones such that {num_categories_required} {category_type} from {category_braced_list} meet the minimum of {min_pois_per_category} POIs each, with their combined share ≥ {ratio_threshold} of all POIs in the zone.",
    "Check zones where at least {num_categories_required} {category_type} in {category_braced_list} have {min_pois_per_category} or more POIs each, and together they make up ≥ {ratio_threshold} of the zone's total POIs.",
    "Show me zones where a minimum of {num_categories_required} {category_type} from {category_braced_list} each have ≥ {min_pois_per_category} POIs, and the total of these POIs over all POIs in the zone is ≥ {ratio_threshold}."
]

SUBCATEGORY_POI_RATIO_CLAUSE_TEMPLATES = [
    "at least {num_categories_required} {category_type} among {category_braced_list} have ≥ {min_pois_per_category} POIs each, and their combined share is ≥ {ratio_threshold} of total POIs",
    "{num_categories_required} {category_type} from {category_braced_list} meet the minimum of {min_pois_per_category} POIs each, with combined share ≥ {ratio_threshold}",
    "at least {num_categories_required} {category_type} in {category_braced_list} have {min_pois_per_category}+ POIs each and together make up ≥ {ratio_threshold} of zone POIs",
]

def complex_query_6(n=10, TOP_CATEGORY=TOP_CATEGORY, SUB_CATEGORY=SUB_CATEGORY):
    output = []

    for _ in range(n):
        # Randomly choose top or sub category
        top_category_flag = random.choice([True, False])
        sub_category_flag = not top_category_flag

        category_pool = TOP_CATEGORY if top_category_flag else SUB_CATEGORY

        # Pick 3-10 categories from the pool
        num_categories = random.randint(3, min(10, len(category_pool)))
        category_values = random.sample(category_pool, num_categories)

        # Wrap each category in {} for query text
        category_braced_list = ", ".join(f"{{{c}}}" for c in category_values)

        # Use calibrated ranges
        num_categories_required = random.randint(2, min(
            PARAM_RANGES['query_6_multiple_categories']['num_categories_required_max'],
            num_categories  # Can't require more categories than we have
        ))

        min_pois_per_category = random.randint(
            PARAM_RANGES['query_6_multiple_categories']['min_pois_per_category_min'],
            PARAM_RANGES['query_6_multiple_categories']['min_pois_per_category_max']
        )

        ratio_threshold = round(random.uniform(
            PARAM_RANGES['query_6_multiple_categories']['ratio_threshold_min'],
            PARAM_RANGES['query_6_multiple_categories']['ratio_threshold_max']
        ), 2)

        vals = {
            "num_categories_required": num_categories_required,
            "category_type": "top category" if top_category_flag else "sub-category",
            "category_braced_list": category_braced_list,
            "min_pois_per_category": min_pois_per_category,
            "ratio_threshold": ratio_threshold
        }

        # Generate full query
        template = random.choice(SUBCATEGORY_POI_RATIO_TEMPLATES)
        query = template.format(**vals)

        # Generate clause
        clause_template = random.choice(SUBCATEGORY_POI_RATIO_CLAUSE_TEMPLATES)
        clause = clause_template.format(**vals)

        # Build parameter dict (without braces)
        param_dict = {
            "num_categories_required": num_categories_required,
            "top_category": top_category_flag,
            "sub_category": sub_category_flag,
            "category_values": category_values,
            "min_pois_per_category": min_pois_per_category,
            "ratio_threshold": ratio_threshold
        }

        output.append((query, param_dict, clause))

    return output

# ============== COMPLEX QUERY 7 ==============
TRANSPORT_PROXIMITY_TEMPLATES = [
    "I'm looking for zones where at least {min_transport_types} types of transportation are present, and at least {poi_proximity_ratio} of POIs are within {distance_threshold_km} km of any transport type.",
    "Find zones such that {poi_proximity_ratio} of POIs lie within {distance_threshold_km} km of at least {min_transport_types} transport types.",
    "Check areas where there are at least {min_transport_types} transportation types, and half or more of the POIs are within {distance_threshold_km} km of these transport options.",
    "Show me zones where a minimum of {min_transport_types} transport types exist, and at least {poi_proximity_ratio} of all POIs are within {distance_threshold_km} km Euclidean distance from any transport type."
]

TRANSPORT_PROXIMITY_CLAUSE_TEMPLATES = [
    "at least {min_transport_types} transport types exist AND {poi_proximity_ratio} of POIs are within {distance_threshold_km} km of any transport",
    "{poi_proximity_ratio} of POIs lie within {distance_threshold_km} km of at least {min_transport_types} transport types",
    "there are ≥ {min_transport_types} transportation types with {poi_proximity_ratio} of POIs within {distance_threshold_km} km distance",
]

def complex_query_7(n=10):
    output = []

    for _ in range(n):
        # Use calibrated ranges
        min_transport_types = random.randint(1,
            PARAM_RANGES['query_7_transport_proximity']['min_transport_types_max']
        )
        poi_proximity_ratio = round(random.uniform(
            PARAM_RANGES['query_7_transport_proximity']['poi_proximity_ratio_min'],
            PARAM_RANGES['query_7_transport_proximity']['poi_proximity_ratio_max']
        ), 2)
        distance_threshold_km = round(random.uniform(
            PARAM_RANGES['query_7_transport_proximity']['distance_threshold_km_min'],
            PARAM_RANGES['query_7_transport_proximity']['distance_threshold_km_max']
        ), 1)

        vals = {
            "min_transport_types": min_transport_types,
            "poi_proximity_ratio": poi_proximity_ratio,
            "distance_threshold_km": distance_threshold_km
        }

        # Generate full query
        template = random.choice(TRANSPORT_PROXIMITY_TEMPLATES)
        query = template.format(**vals)

        # Generate clause
        clause_template = random.choice(TRANSPORT_PROXIMITY_CLAUSE_TEMPLATES)
        clause = clause_template.format(**vals)

        param_dict = {
            "min_transport_types": min_transport_types,
            "poi_proximity_ratio": poi_proximity_ratio,
            "distance_threshold_km": distance_threshold_km
        }

        output.append((query, param_dict, clause))

    return output

# ============== COMPLEX QUERY 8 ==============
SUBCATEGORY_FRACTION_TEMPLATES = [
    "I'm looking for zones where the {category_type} {{{category_value}}} makes up no more than {max_fraction} of total POIs in {zone_scope}, and the same holds for at least {min_neighbors_satisfy} of {num_neighbors} neighboring zones.",
    "Find zones such that {category_type} {{{category_value}}} accounts for at most {max_fraction} of all POIs in {zone_scope}, with at least {min_neighbors_satisfy} out of {num_neighbors} nearby zones also satisfying this limit.",
    "Check zones where {category_type} {{{category_value}}} is ≤ {max_fraction} of total POIs in {zone_scope}, and this condition applies to at least {min_neighbors_satisfy} of {num_neighbors} closest zones.",
    "Show me areas where the {category_type} {{{category_value}}} comprises no more than {max_fraction} of POIs in {zone_scope}, while at least {min_neighbors_satisfy} of {num_neighbors} nearby zones also meet this threshold."
]

SUBCATEGORY_FRACTION_CLAUSE_TEMPLATES = [
    "the {category_type} {{{category_value}}} makes up no more than {max_fraction} of total POIs in {zone_scope}, with at least {min_neighbors_satisfy} of {num_neighbors} neighbors meeting this",
    "{category_type} {{{category_value}}} accounts for at most {max_fraction} of all POIs in {zone_scope}, applying to {min_neighbors_satisfy} out of {num_neighbors} nearby zones",
    "{category_type} {{{category_value}}} is ≤ {max_fraction} of total POIs in {zone_scope} and at least {min_neighbors_satisfy} of {num_neighbors} zones satisfy this",
]

def complex_query_8(n=10):
    output = []

    for _ in range(n):
        # Randomly choose top or sub category
        top_category_flag = random.choice([True, False])
        sub_category_flag = not top_category_flag
        category_type = "top category" if top_category_flag else "sub-category"

        # Pick a category from appropriate list
        category_value = random.choice(TOP_CATEGORY if top_category_flag else SUB_CATEGORY)

        # Use calibrated range
        max_fraction = round(random.uniform(
            PARAM_RANGES['query_8_category_fraction']['max_fraction_min'],
            PARAM_RANGES['query_8_category_fraction']['max_fraction_max']
        ), 2)

        # Include zone & neighbors
        include_my_zone = random.choice([True, False])
        num_neighbors = random.randint(1, 8)
        min_neighbors_satisfy = random.randint(1, num_neighbors)

        # Build zone scope description
        if include_my_zone and num_neighbors > 0:
            zone_scope = f"my zone plus {num_neighbors} nearby zones" if num_neighbors > 1 else "my zone plus 1 nearby zone"
        elif include_my_zone and num_neighbors == 0:
            zone_scope = "my zone only"
        elif not include_my_zone and num_neighbors > 0:
            zone_scope = f"{num_neighbors} nearby zones" if num_neighbors > 1 else "1 nearby zone"
        else:
            zone_scope = "the area"

        vals = {
            "category_type": category_type,
            "category_value": category_value,
            "max_fraction": max_fraction,
            "zone_scope": zone_scope,
            "num_neighbors": num_neighbors,
            "min_neighbors_satisfy": min_neighbors_satisfy
        }

        # Generate full query
        template = random.choice(SUBCATEGORY_FRACTION_TEMPLATES)
        query = template.format(**vals)

        # Generate clause
        clause_template = random.choice(SUBCATEGORY_FRACTION_CLAUSE_TEMPLATES)
        clause = clause_template.format(**vals)

        param_dict = {
            "top_category": top_category_flag,
            "sub_category": sub_category_flag,
            "category_value": category_value,
            "max_fraction": max_fraction,
            "include_my_zone": include_my_zone,
            "num_neighbors": num_neighbors,
            "min_neighbors_satisfy": min_neighbors_satisfy
        }

        output.append((query, param_dict, clause))

    return output

# ============== COMPLEX QUERY 9 ==============
POPULATION_DENSITY_TEMPLATES = [
    "I'm looking for zones where the population density (population ÷ area) in {zone_scope} is at least {threshold} people per km².",
    "Find zones such that the population density in {zone_scope} meets or exceeds {threshold} people per km².",
    "Check zones where my zone plus {num_neighbors} nearest neighbors have a population density of at least {threshold} people per km².",
    "Show me areas where the combined population density in {zone_scope} reaches at least {threshold} people per km²."
]

POPULATION_DENSITY_CLAUSE_TEMPLATES = [
    "the population density (population ÷ area) in {zone_scope} is at least {threshold} people per km²",
    "population density in {zone_scope} meets or exceeds {threshold} people per km²",
    "the combined population density in {zone_scope} reaches at least {threshold} people per km²",
]

def complex_query_9(n=10):
    output = []

    for _ in range(n):
        include_my_zone = random.choice([True, False])
        num_neighbors = random.randint(1, 8)
        # Use calibrated range
        threshold = random.randint(
            PARAM_RANGES['query_9_population_density']['threshold_min'],
            PARAM_RANGES['query_9_population_density']['threshold_max']
        )

        # Build zone scope description
        if include_my_zone and num_neighbors > 0:
            zone_scope = f"my zone plus {num_neighbors} nearest zones" if num_neighbors > 1 else "my zone plus 1 nearest zone"
        elif include_my_zone and num_neighbors == 0:
            zone_scope = "my zone only"
        elif not include_my_zone and num_neighbors > 0:
            zone_scope = f"{num_neighbors} nearest zones" if num_neighbors > 1 else "1 nearest zone"
        else:
            zone_scope = "the area"

        vals = {
            "zone_scope": zone_scope,
            "num_neighbors": num_neighbors,
            "threshold": threshold
        }

        # Generate full query
        template = random.choice(POPULATION_DENSITY_TEMPLATES)
        query = template.format(**vals)

        # Generate clause
        clause_template = random.choice(POPULATION_DENSITY_CLAUSE_TEMPLATES)
        clause = clause_template.format(**vals)

        param_dict = {
            "include_my_zone": include_my_zone,
            "num_neighbors": num_neighbors,
            "threshold": threshold
        }

        output.append((query, param_dict, clause))

    return output

# ============== COMPLEX QUERY 10 ==============
POPULATION_OVER_CATEGORY_TEMPLATES = [
    "I'm evaluating zones where the {category_type} {{{category_value}}} has a population ratio of at least {threshold} (population ÷ total POIs) in my zone and at least {required_neighbors_pass} of {num_neighbors} nearest zones.",
    "Find zones such that the population divided by the number of {category_type} {{{category_value}}} POIs reaches at least {threshold} in my zone and at least {required_neighbors_pass} out of {num_neighbors} neighboring zones.",
    "Check zones where my zone have a population over {category_type} {{{category_value}}} POIs ratio ≥ {threshold}, with at least {required_neighbors_pass} out of {num_neighbors} nearest neighbors meeting this threshold.",
    "Show me areas where the {category_type} {{{category_value}}} population-to-POI ratio is at least {threshold} in my zone and in at least {required_neighbors_pass} of {num_neighbors} closest zones."
]

POPULATION_OVER_CATEGORY_CLAUSE_TEMPLATES = [
    "the {category_type} {{{category_value}}} has a population-to-POI ratio of at least {threshold} in my zone and in at least {required_neighbors_pass} of {num_neighbors} nearest zones",
    "population divided by {category_type} {{{category_value}}} POIs reaches {threshold} in my zone and {required_neighbors_pass} out of {num_neighbors} neighbors",
    "the population over {category_type} {{{category_value}}} ratio is ≥ {threshold} in my zone and at least {required_neighbors_pass} of {num_neighbors} nearby zones",
]

def complex_query_10(n=10):
    output = []

    for _ in range(n):
        # Choose top or sub category
        top_category_flag = random.choice([True, False])
        sub_category_flag = not top_category_flag
        category_type = "top category" if top_category_flag else "sub-category"
        category_value = random.choice(TOP_CATEGORY if top_category_flag else SUB_CATEGORY)

        num_neighbors = random.randint(1, 10)
        required_neighbors_pass = random.randint(1, num_neighbors)
        # Use calibrated range
        threshold = random.randint(
            PARAM_RANGES['query_10_population_over_category']['threshold_min'],
            PARAM_RANGES['query_10_population_over_category']['threshold_max']
        )

        vals = {
            "category_type": category_type,
            "category_value": category_value,
            "num_neighbors": num_neighbors,
            "required_neighbors_pass": required_neighbors_pass,
            "threshold": threshold
        }

        # Generate full query
        template = random.choice(POPULATION_OVER_CATEGORY_TEMPLATES)
        query = template.format(**vals)

        # Generate clause
        clause_template = random.choice(POPULATION_OVER_CATEGORY_CLAUSE_TEMPLATES)
        clause = clause_template.format(**vals)

        param_dict = {
            "top_category": top_category_flag,
            "sub_category": sub_category_flag,
            "category_value": category_value,
            "num_neighbors": num_neighbors,
            "required_neighbors_pass": required_neighbors_pass,
            "threshold": threshold
        }

        output.append((query, param_dict, clause))

    return output
