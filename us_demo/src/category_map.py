"""
Maps clean NL alias names → SafeGraph TOP_CATEGORY strings and column names.

The LLM spec-generation prompt uses the clean aliases (e.g. "restaurants"),
which map to cnt_restaurants / dist_to_restaurants_m feature columns.
The feature builder uses CATEGORY_MAP to aggregate SafeGraph POI rows.
"""

# Clean alias → SafeGraph TOP_CATEGORY (verified against Boston dataset)
CATEGORY_MAP = {
    "restaurants":    "Restaurants and Other Eating Places",
    "physicians":     "Offices of Physicians",
    "hospitals":      "General Medical and Surgical Hospitals",
    "grocery":        "Grocery Stores",
    "clothing":       "Clothing Stores",
    "electronics":    "Electronics and Appliance Stores",
    "banks":          "Depository Credit Intermediation",
    "museums":        "Museums, Historical Sites, and Similar Institutions",
    "recreation":     "Other Amusement and Recreation Industries",
    "hotels":         "Traveler Accommodation",
    "dentists":       "Offices of Dentists",
    "universities":   "Colleges, Universities, and Professional Schools",
    "specialty_food": "Specialty Food Stores",
    "bars":           "Drinking Places (Alcoholic Beverages)",
    "gas_stations":   "Gasoline Stations",
    "health_stores":  "Health and Personal Care Stores",
    "real_estate":    "Offices of Real Estate Agents and Brokers",
    "legal":          "Legal Services",
    "personal_care":  "Personal Care Services",
    "transit":        "Urban Transit Systems",
}

# Aliases for which we compute distance-to-nearest columns
DISTANCE_CATEGORIES = [
    "restaurants",
    "hospitals",
    "universities",
    "grocery",
    "museums",
]


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
