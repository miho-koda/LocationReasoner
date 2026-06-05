"""
Maps clean NL alias names → SafeGraph TOP_CATEGORY strings and column names.

The LLM spec-generation prompt uses the clean aliases (e.g. "restaurants"),
which map to cnt_restaurants / dist_to_restaurants_m feature columns.
The feature builder uses CATEGORY_MAP to aggregate SafeGraph POI rows.
"""

# Clean alias → SafeGraph TOP_CATEGORY (verified against Boston dataset)
CATEGORY_MAP = {
    # Food & drink
    "restaurants":    "Restaurants and Other Eating Places",
    "bars":           "Drinking Places (Alcoholic Beverages)",
    "specialty_food": "Specialty Food Stores",
    "beer_wine":      "Beer, Wine, and Liquor Stores",
    # Retail
    "grocery":        "Grocery Stores",
    "clothing":       "Clothing Stores",
    "electronics":    "Electronics and Appliance Stores",
    "department_stores": "Department Stores",
    "furniture":      "Home Furnishings Stores",
    "health_stores":  "Health and Personal Care Stores",
    "gas_stations":   "Gasoline Stations",
    "automotive":     "Automotive Parts, Accessories, and Tire Stores",
    # Healthcare
    "physicians":     "Offices of Physicians",
    "hospitals":      "General Medical and Surgical Hospitals",
    "dentists":       "Offices of Dentists",
    "outpatient":     "Outpatient Care Centers",
    # Education & culture
    "universities":   "Colleges, Universities, and Professional Schools",
    "schools":        "Elementary and Secondary Schools",
    "museums":        "Museums, Historical Sites, and Similar Institutions",
    "daycare":        "Child Day Care Services",
    # Services
    "banks":          "Depository Credit Intermediation",
    "legal":          "Legal Services",
    "real_estate":    "Offices of Real Estate Agents and Brokers",
    "personal_care":  "Personal Care Services",
    "hotels":         "Traveler Accommodation",
    "recreation":     "Other Amusement and Recreation Industries",
    # Civic
    "transit_systems": "Urban Transit Systems",
    "religious":      "Religious Organizations",
    "civic":          "Civic and Social Organizations",
}

# Aliases for which we compute distance-to-nearest columns
DISTANCE_CATEGORIES = [
    "restaurants",
    "hospitals",
    "universities",
    "grocery",
    "museums",
]

# Spending columns aggregated per zone (most recent reliable year = 2023)
SPEND_YEAR = 2023

# Column name helpers for spending
def spend_total_col(): return "spend_total"
def spend_transactions_col(): return "spend_num_transactions"
def spend_customers_col(): return "spend_num_customers"
def spend_median_txn_col(): return "spend_median_per_txn"
def spend_median_customer_col(): return "spend_median_per_customer"
def spend_pct_change_col(): return "spend_pct_change"

# Transport count columns
def cnt_bus_stops_col(): return "cnt_bus_stops"
def cnt_subway_col(): return "cnt_subway_entrances"

# Parking columns
def cnt_parking_col(): return "cnt_parking"
def parking_capacity_col(): return "parking_capacity"

# Population column
def population_col(): return "population"


def cnt_col(alias: str) -> str:
    return f"cnt_{alias}"


def dist_col(alias: str) -> str:
    return f"dist_to_{alias}_m"


def safegraph_name(alias: str) -> str:
    return CATEGORY_MAP[alias]


def all_count_columns() -> list:
    return [cnt_col(a) for a in CATEGORY_MAP] + ["cnt_parking"]


def all_distance_columns() -> list:
    return [dist_col(a) for a in DISTANCE_CATEGORIES]
