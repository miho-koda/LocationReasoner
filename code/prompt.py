
dataframe_documentation = """
## DataFrame Documentation

### `poi_spend_df`

| Column Name                              | Description |
|------------------------------------------|-------------|
| `PLACEKEY`                               | Unique identifier for the point of interest (POI) |
| `LOCATION_NAME`                          | Name of the location or venue |
| `BRANDS`                                 | Associated brand(s) for the POI |
| `TOP_CATEGORY`                           | High-level business category (e.g., Restaurants, Health Services) |
| `SUB_CATEGORY`                           | More specific business type (e.g., Full-Service Restaurants) |
| `NAICS_CODE`                             | Industry classification code |
| `LATITUDE`                               | Latitude coordinate of the POI |
| `LONGITUDE`                              | Longitude coordinate of the POI |
| `STREET_ADDRESS`                         | Street address of the POI |
| `CITY`                                   | City in which the POI is located |
| `REGION`                                 | State or region abbreviation |
| `POSTAL_CODE`                            | Zip/postal code of the POI |
| `GEOMETRY_TYPE`                          | Type of geometry (e.g., Polygon, Point) |
| `POLYGON_WKT`                            | Well-Known Text (WKT) representation of the POI's boundary |
| `PHONE_NUMBER`                           | Contact phone number for the POI |
| `WKT_AREA_SQ_METERS`                     | Area of the POI polygon in square meters |
| `zone_id`                                | Zone ID assigned to the POI |

> The following groups of columns repeat across years (2019 to 2024). Replace `{{YYYY}}` with the desired year:

| Column Name (per year)                   | Description |
|------------------------------------------|-------------|
| `RAW_TOTAL_SPEND_{{YYYY}}`                | Total amount of money spent at this POI in the year |
| `RAW_NUM_TRANSACTIONS_{{YYYY}}`           | Total number of transactions conducted in the year |
| `RAW_NUM_CUSTOMERS_{{YYYY}}`              | Number of unique customers that visited in the year |
| `MEDIAN_SPEND_PER_TRANSACTION_{{YYYY}}`   | Median spend per transaction in the year |
| `MEDIAN_SPEND_PER_CUSTOMER_{{YYYY}}`      | Median spend per customer in the year |
| `SPEND_PCT_CHANGE_VS_PREV_YEAR_{{YYYY}}`  | Percent change in total spend compared to previous year |

---

### `parking_df`
| Column Name         | Description |
|---------------------|-------------|
| `PLACEKEY`          | Parking lot ID |
| `LATITUDE`, `LONGITUDE` | Location |
| `POLYGON_WKT`        | Parking lot geometry |
| `WKT_AREA_SQ_METERS` | Area of the parking lot |
| `RELATED_POI`        | List of PLACEKEYs served by the parking lot |
| `NAME`        | the state of the parking lot |

---

### `zone_df`
| Column Name        | Description |
|--------------------|-------------|
| `zone_id`           | Unique zone ID |
| `geometry`          | Polygon of the zone (shapely object) |
| `center_lat`        | Centroid latitude |
| `center_lng`        | Centroid longitude |
| `num_pois`          | Number of POIs in the zone |

---
"""

in_house_functions_documentation = """
### **Available Functions**
    (1) get_poi_spend_dataset():
    Description: Retrieve the POI dataset for Boston, MA
    Returns: poi_spend — a DataFrame containing point-of-interest data for the specified location and spending information across 2019 - 2024.
    Example: get_poi_spend_dataset() would return the POI dataset for Boston, MA.

    (2) get_parking_dataset():
    Description: Retrieve parking-related data for a specific city within Massachusetts State.
    Parameters:
    Returns: parking_df — a DataFrame containing parking zone data and availability.
    Example: get_parking_dataset() would return parking data for Massachusetts State.

    (3) create_zone(poi_spend_df):
    Description: Creates zone geometries and metadata based on clustered POIs based on the 'zone_id' column in poi_spend_df.
    Parameters:
    - poi_spend_df: A DataFrame with clustered POIs (must have a 'zone_id' column).
    Returns: zone_df — a GeoDataFrame of zones with polygon geometries.
    For each query, you want to create a zone_df and based on the query, you want to filter/delete rows in zone_df to find the suitable zones for the query. 
    Example: create_zone(poi_spend_df) returns zone-level geometries derived from POI clusters.

    (4) assign_parking_zones(parking_df, zone_df):
    Description: Assigns a zone_id to each parking location via spatial join.
    Parameters:
    - parking_df: DataFrame parking lot information.
    - zone_df: GeoDataFrame with zone polygons and 'zone_id'.
    Returns: parking_df — Updated parking_df with an added 'zone_id' column
    Example: assign_parking_zones(parking_df, zone_df) returns parking data with added zone associations.

    (5) filter_df_based_on_zone(df, zone_id):
    Description: Filters the input DataFrame to include only entries from the specified zone_id. Works with only poi_spend_df or parking DataFrames.
    Parameters:
    - df: A DataFrame (must be either poi_spend_df or parking_df).
    - zone_id: The ID of the zone to filter by.
    Returns: A filtered DataFrame containing only rows within the given zone.
    Example: filter_df_based_on_zone(poi_spend_df, 101) returns POIs in zone 101.

    (6) filter_pois_by_top_category(poi_spend_df, top_category):
    Description: Filters POIs to only include those that match the specified top-level category.
    Parameters:
    - poi_spend_df: A DataFrame with a 'TOP_CATEGORY' column.
    - top_category: The category name to filter by (string).
    Returns: A filtered POI DataFrame containing only rows with the matching top category.
    Example: filter_pois_by_top_category(poi_spend_df, "Clothing Stores") returns only clothing store POIs.

    (7) filter_pois_by_sub_category(poi_spend_df, sub_category):
    Description: Filters POIs to only include those that match the specified sub-category.
    Parameters:
    - poi_spend_df: A DataFrame with a 'SUB_CATEGORY' column.
    - sub_category: The sub-category name to filter by (string).
    Returns: A filtered POI DataFrame containing only rows with the matching sub-category.
    Example: filter_pois_by_sub_category(poi_spend_df, "Malls") returns only POIs categorized as malls.

    (8) get_zone_center(zone_df, zone_id):
    Description: Returns the center coordinates (latitude, longitude) of a given zone.
    Parameters:
    - zone_df: GeoDataFrame with 'zone_id', 'center_lat', and 'center_lng' columns.
    - zone_id: The ID of the zone to look up.
    Returns: A tuple (center_lat, center_lng).
    Example: get_zone_center(zone_df, 101) returns the center of zone 101 as (40.7128, -74.0060).

    (9) get_spendparam_years(poi_spend_df, spendparm, year):
    Description: Calculates a specific spending metric in a zone during a given year by aggregating values across all POIs in that zone.
    The agent must infer which `spendparm` to use based on the user query. Choose one of the following options:
    - RAW_TOTAL_SPEND: Total spend in dollars
    - RAW_NUM_TRANSACTIONS: Total number of transactions
    - RAW_NUM_CUSTOMERS: Unique customers during time range
    - MEDIAN_SPEND_PER_TRANSACTION: Median dollars per transaction
    - MEDIAN_SPEND_PER_CUSTOMER: Median dollars per customer
    - SPEND_PCT_CHANGE_VS_PREV_MONTH: Percent change from previous month
    - SPEND_PCT_CHANGE_VS_PREV_YEAR: Percent change from previous year
    Parameters:
    - poi_spend_df: A DataFrame containing POIs, including 'zone_id' and 'placekey'.
    - spendparm: The chosen metric to evaluate (must be one of the valid options above).
    - year: The year to calculate the spending metric for. Must be between 2019 and 2024.
    Returns: An integer or float representing the aggregated value of the chosen spendparm for the specified zone.
    Example: get_spendparam_years(poipoi_spend_df_df, RAW_TOTAL_SPEND, year) returns the total spending of this year.

    (10) get_num_parking(parking_df):
    Description: Counts the number of parking lots within a given zone.
    Parameters:
    - parking_df: A DataFrame that stores parking lot information.
    Returns: An integer count of parking lots within the zone.
    Example: get_num_parking(parking_df) returns the number of parking lots

    (11) get_largest_parking_lot_area(parking_df):
    Description: Retrieves the area (in square meters) of the largest parking lot.
    Parameters:
    - parking_df: A DataFrame with a 'WKT_AREA_SQ_METERS' column.
    Returns: A float value representing the area of the largest parking lot.
    Example: get_largest_parking_lot_area(parking_df) returns the area of the largest parking lot in square meters.

    (12) get_largest_parking_capacity(parking_df):
    Description: Calculates the parking capacity of the largest parking lot based on an estimated 30 square meters per space.
    Parameters:
    - parking_df: A DataFrame with a 'WKT_AREA_SQ_METERS' column.
    Returns: A float representing the estimated parking capacity of the largest lot.
    Example: get_largest_parking_capacity(parking_df) returns the maximum estimated number of parking spaces.

    (13) get_distance_km(lat1, lng1, lat2, lng2):
    Description: Calculates the Haversine distance (in kilometers) between two geographic coordinates.
    Parameters:
    - lat1, lng1: Latitude and longitude of the first point.
    - lat2, lng2: Latitude and longitude of the second point.
    Returns: A float representing the distance in kilometers.
    Example: get_distance_km(40.7128, -74.0060, 34.0522, -118.2437) returns the distance from NYC to LA.

    (14) get_neighbor_zones(zone_df, zone_id, num):
    Description: Finds the closest `num` neighboring zones to a given zone based on centroid-to-centroid distance.
    Parameters:
    - zone_df: GeoDataFrame containing geometries and 'zone_id'.
    - zone_id: The reference zone identifier.
    - num: Number of neighboring zones to return.
    Returns: A list of `zone_id`s representing the closest zones.
    Example: get_neighbor_zones(zone_df, 101, 5) returns the 5 nearest neighboring zones to zone 101.

    (15) get_population(zone_id, zone_df):
    Description: Retrieves the population of a specific zone.
    Parameters:
    - zone_id: The identifier of the zone.
    - zone_df: A GeoDataFrame containing zone geometries.
    Returns: An integer population estimate for that zone.
    Example: get_population(101, zone_df) returns the number of people living in zone 101.

    (16) get_transport_pois_in_zone(zone_df, poi_type):
    Description: Returns transport-related POIs within the geometry of a given zone.
    Parameters:
    - zone_df: A GeoDataFrame containing zone geometries.
    - poi_type: A string representing the type of transport POI. Options: "bus_stop", "station", "subway_entrance", "aerodrome", "taxi".
    Returns: A dictionary of zone_id as keys and list of (latitude, longitude) tuples representing matched POIs inside the zone. dictionary: {{zone_id: [(lat, lon), ...]}}
    Example: get_transport_pois_in_zone(zone_df, poi_df, "subway_entrance") returns coordinates of subway entrances in all zones.
""" 



geopandas_documentation = """
GeoPandas Documentation:

1. **Reading and Writing Files:**
- `geopandas.read_file(filepath)`: Reads a file and returns a GeoDataFrame.
- `GeoDataFrame.to_file(filename, driver="ESRI Shapefile")`: Writes a GeoDataFrame to a file.

2. **Data Structures:**
- `GeoDataFrame`: A tabular data structure that contains a collection of geometries and associated data.
- `GeoSeries`: A Series object designed to store shapely geometry objects.

3. **Geometric Operations:**
- `GeoSeries.buffer(distance)`: Returns a GeoSeries with buffered geometries.
- `GeoSeries.centroid`: Returns a GeoSeries of centroids for each geometry.
- `GeoSeries.convex_hull`: Returns the convex hull of each geometry.
- `GeoSeries.plot()`: Plots the GeoSeries geometries.

4. **Spatial Joins:**
- `geopandas.sjoin(left_df, right_df, how="inner", op="intersects")`: Spatial join between two GeoDataFrames.

5. **Coordinate Reference Systems (CRS):**
- `GeoDataFrame.set_crs(crs, allow_override=False)`: Sets the CRS for the GeoDataFrame.
- `GeoDataFrame.to_crs(crs)`: Transforms geometries to a new CRS.

6. **Aggregation and Dissolve:**
- `GeoDataFrame.dissolve(by=None, aggfunc="first")`: Aggregates geometries by a specified column.

7. **Plotting:**
- `GeoDataFrame.plot(column=None, cmap=None, legend=False)`: Plots the GeoDataFrame.

8. **Miscellaneous:**
- `geopandas.overlay(df1, df2, how="intersection")`: Performs spatial overlay between two GeoDataFrames.
- `geopandas.clip(gdf, mask, keep_geom_type=False)`: Clips points, lines, or polygon geometries to the mask extent.
"""

'''
 (3) assign_poi_zones(poi_spend_df, n_clusters=2000, random_state=42):
    Description: Assigns each POI to a zone using clustering.
    Parameters:
    - poi_spend_df: A DataFrame of POIs (must already be loaded).
    - n_clusters: The number of clusters to use, default is 2000. 
    Returns:
    - Updated poi_spend_df with an added 'zone_id' column.
    Example: assign_poi_zones(poi_spend_df, 2000) clusters POIs into 2000 zones and returns the updated poi_spend_df.
I'm looking to open a family entertainment center,

'''


############################################################REACT######################################################################################
# Prompt templates for POI/Zone Analysis Framework
REFLECTION_HEADER = """
    "You attempted to generate a zoning plan but were unsuccessful. "
    "The following reflection(s) analyze the previous failure and provide suggestions for a better strategy. "
    "Use them to improve your reasoning and avoid making the same mistakes.\n"
"""

REFLECTION_INSTRUCTION = """You are a reasoning agent for urban site selection. You previously attempted to plan a zoning strategy using data on parking, population, spending, and points of interest, but failed due to syntaxerrors or exhausting your allowed steps.

Below is your original query and a transcript of your reasoning process. In a few sentences, explain a likely reason for the failure. Then, describe a revised high-level plan that might avoid the same mistake. Be specific and concise. Use complete sentences.

Query: {query}

Scratchpad:
{scratchpad}

Reflection:"""



ZEROSHOT_REACT_INSTRUCTION = """
Analyze zones and POIs using interleaving 'Thought', 'Action', and 'Observation' steps. Ensure you gather valid information about zones, POIs, parking, spending patterns, and transportation. All information should be written in Notebook, which will then be input into the Analyzer tool. Note that nested use of tools is prohibited. 'Thought' can reason about the current situation, and 'Action' can use any of the available functions:

## Overall Task:
You are tasked with analyzing zones and points of interest (POIs) by interleaving the following steps:
- Thought (reason about what to do next)
- Action (choose and call exactly one function)
- Observation (record what you learned)

⚡ Important:
- Each Action must call exactly one function at a time.
- After every Action, you must wait for an Observation before proceeding.
- Nested tool calls are strictly prohibited.
- You can reference results from previous actions for chaining operations.
---


You have access to the following functions as tools. Each tool has a specific format, description, and example. You can use the provided functions to generate code.
    (6) filter_pois_by_top_category(poi_spend_df, top_category):
    Description: Filters POIs to only include those that match the specified top-level category.
    Parameters:
    - poi_spend_df: A DataFrame with a 'TOP_CATEGORY' column.
    - top_category: The category name to filter by (string).
    Returns: A filtered POI DataFrame containing only rows with the matching top category.
    Example: filter_pois_by_top_category(poi_spend_df, "Clothing Stores") returns only clothing store POIs.

    (7) filter_pois_by_sub_category(poi_spend_df, sub_category):
    Description: Filters POIs to only include those that match the specified sub-category.
    Parameters:
    - poi_spend_df: A DataFrame with a 'SUB_CATEGORY' column.
    - sub_category: The sub-category name to filter by (string).
    Returns: A filtered POI DataFrame containing only rows with the matching sub-category.
    Example: filter_pois_by_sub_category(poi_spend_df, "Malls") returns only POIs categorized as malls.

    (8) get_zone_center(zone_df, zone_id):
    Description: Returns the center coordinates (latitude, longitude) of a given zone.
    Parameters:
    - zone_df: GeoDataFrame with 'zone_id', 'center_lat', and 'center_lng' columns.
    - zone_id: The ID of the zone to look up.
    Returns: A tuple (center_lat, center_lng).
    Example: get_zone_center(zone_df, 101) returns the center of zone 101 as (40.7128, -74.0060).

    (9) get_spendparam_years(poi_spend_df, spendparm, year):
    Description: Calculates a specific spending metric in a zone during a given year by aggregating values across all POIs in that zone.
    The agent must infer which `spendparm` to use based on the user query. Choose one of the following options:
    - RAW_TOTAL_SPEND: Total spend in dollars
    - RAW_NUM_TRANSACTIONS: Total number of transactions
    - RAW_NUM_CUSTOMERS: Unique customers during time range
    - MEDIAN_SPEND_PER_TRANSACTION: Median dollars per transaction
    - MEDIAN_SPEND_PER_CUSTOMER: Median dollars per customer
    - SPEND_PCT_CHANGE_VS_PREV_MONTH: Percent change from previous month
    - SPEND_PCT_CHANGE_VS_PREV_YEAR: Percent change from previous year
    Parameters:
    - poi_spend_df: A DataFrame containing POIs, including 'zone_id' and 'placekey'.
    - spendparm: The chosen metric to evaluate (must be one of the valid options above).
    - year: The year to calculate the spending metric for. Must be between 2019 and 2024.
    Returns: An integer or float representing the aggregated value of the chosen spendparm for the specified zone.
    Example: get_spendparam_years(poipoi_spend_df_df, RAW_TOTAL_SPEND, year) returns the total spending of this year.

    (10) get_num_parking(parking_df):
    Description: Counts the number of parking lots within a given zone.
    Parameters:
    - parking_df: A DataFrame that stores parking lot information.
    Returns: An integer count of parking lots within the zone.
    Example: get_num_parking(parking_df) returns the number of parking lots

    (11) get_largest_parking_lot_area(parking_df):
    Description: Retrieves the area (in square meters) of the largest parking lot.
    Parameters:
    - parking_df: A DataFrame with a 'WKT_AREA_SQ_METERS' column.
    Returns: A float value representing the area of the largest parking lot.
    Example: get_largest_parking_lot_area(parking_df) returns the area of the largest parking lot in square meters.

    (12) get_largest_parking_capacity(parking_df):
    Description: Calculates the parking capacity of the largest parking lot based on an estimated 30 square meters per space.
    Parameters:
    - parking_df: A DataFrame with a 'WKT_AREA_SQ_METERS' column.
    Returns: A float representing the estimated parking capacity of the largest lot.
    Example: get_largest_parking_capacity(parking_df) returns the maximum estimated number of parking spaces.

    (13) get_distance_km(lat1, lng1, lat2, lng2):
    Description: Calculates the Haversine distance (in kilometers) between two geographic coordinates.
    Parameters:
    - lat1, lng1: Latitude and longitude of the first point.
    - lat2, lng2: Latitude and longitude of the second point.
    Returns: A float representing the distance in kilometers.
    Example: get_distance_km(40.7128, -74.0060, 34.0522, -118.2437) returns the distance from NYC to LA.

    (14) get_neighbor_zones(zone_df, zone_id, num):
    Description: Finds the closest `num` neighboring zones to a given zone based on centroid-to-centroid distance.
    Parameters:
    - zone_df: GeoDataFrame containing geometries and 'zone_id'.
    - zone_id: The reference zone identifier.
    - num: Number of neighboring zones to return.
    Returns: A list of `zone_id`s representing the closest zones.
    Example: get_neighbor_zones(zone_df, 101, 5) returns the 5 nearest neighboring zones to zone 101.

    (15) get_population(zone_id, zone_df):
    Description: Retrieves the population of a specific zone.
    Parameters:
    - zone_id: The identifier of the zone.
    - zone_df: A GeoDataFrame containing zone geometries.
    Returns: An integer population estimate for that zone.
    Example: get_population(101, zone_df) returns the number of people living in zone 101.

    (16) get_transport_pois_in_zone(zone_df, poi_type):
    Description: Returns transport-related POIs within the geometry of a given zone.
    Parameters:
    - zone_df: A GeoDataFrame containing zone geometries.
    - poi_type: A string representing the type of transport POI. Options: "bus_stop", "station", "subway_entrance", "aerodrome", "taxi".
    Returns: A dictionary of zone_id as keys and list of (latitude, longitude) tuples representing matched POIs inside the zone. dictionary: {{zone_id: [(lat, lon), ...]}}
    Example: get_transport_pois_in_zone(zone_df, "subway_entrance") returns coordinates of subway entrances in all zones.
    
(17) self_defined_logic(code):
    Description: Executes custom Python code to manipulate previous action outputs and access datasets.
    You have the following imports to use:  
        "import pandas as pd\n"
        "import numpy as np\n"
        "import math\n"
        "import geopandas as gpd\n"
        "from shapely.geometry import Point, Polygon, MultiPoint\n"
        "from collections import defaultdict, Counter\n"

    Parameters:
    - code: A multi-line Python string containing your custom code.
    
    Data Access:
    - Previous Action results are accessible using special variables:
      * For actions with "Needs Loop Over Zones: No":
        $action1, $action2, etc. contain the direct output of those actions
      * For actions with "Needs Loop Over Zones: Yes":
        $action1, $action2, etc. are dictionaries where:
          - Keys are zone_ids
          - Values are the function outputs for each zone
    - Predefined DataFrames: poi_spend_df, parking_df, and zone_df are directly accessible
    
    Requirements:
    - Your code MUST assign a variable called `result` which will be returned
    - No importing external libraries
    - No calling other functions/tools within the code
    - Include error handling for robust execution

    Examples:
    
    Example 1 (When previous action did NOT use loop):
    self_defined_logic[
        '''
        # $action1 contains a DataFrame from filter_pois_by_top_category without loop
        # Filter it further
        filtered_df = $action1[$action1['RAW_NUM_TRANSACTIONS_2023'] > 1000]
        result = filtered_df
        '''
    ]
    
    Example 2 (When previous action DID use loop):
    self_defined_logic[
        '''
        # $action2 is a dictionary where:
        # - Keys are zone_ids
        # - Values are DataFrames from get_transport_pois_in_zone with loop
        
        # Find zones with at least 3 subway entrances
        valid_zones = []
        for zone_id, entrances in $action2.items():
            if isinstance(entrances, list) and len(entrances) >= 3:
                valid_zones.append(zone_id)
                
        result = valid_zones
        '''
    ]
    
    Example 3 (Combining results from multiple actions):
    self_defined_logic[
        '''
        # $action1 is a dictionary from a looped population calculation
        # $action2 is a dictionary from a looped restaurant POI count
        
        valid_zones = []
        for zone_id, population in $action1.items():
            # Check if zone has enough population and restaurants
            if population > 10000 and zone_id in $action2:
                poi_count = len($action2[zone_id])
                if poi_count >= 5:
                    valid_zones.append(zone_id)
                    
        result = valid_zones
        '''
    ]

    
    Here is the documentation for the DataFrames you will be working with:
        ## DataFrame Documentation

        ### `poi_spend_df`

        | Column Name                              | Description |
        |------------------------------------------|-------------|
        | `PLACEKEY`                               | Unique identifier for the point of interest (POI) |
        | `LOCATION_NAME`                          | Name of the location or venue |
        | `BRANDS`                                 | Associated brand(s) for the POI |
        | `TOP_CATEGORY`                           | High-level business category (e.g., Restaurants, Health Services) |
        | `SUB_CATEGORY`                           | More specific business type (e.g., Full-Service Restaurants) |
        | `NAICS_CODE`                             | Industry classification code |
        | `LATITUDE`                               | Latitude coordinate of the POI |
        | `LONGITUDE`                              | Longitude coordinate of the POI |
        | `STREET_ADDRESS`                         | Street address of the POI |
        | `CITY`                                   | City in which the POI is located |
        | `REGION`                                 | State or region abbreviation |
        | `POSTAL_CODE`                            | Zip/postal code of the POI |
        | `GEOMETRY_TYPE`                          | Type of geometry (e.g., Polygon, Point) |
        | `POLYGON_WKT`                            | Well-Known Text (WKT) representation of the POI's boundary |
        | `PHONE_NUMBER`                           | Contact phone number for the POI |
        | `WKT_AREA_SQ_METERS`                     | Area of the POI polygon in square meters |
        | `zone_id`                                | Zone ID assigned to the POI |

        > The following groups of columns repeat across years (2019 to 2024). Replace `{{YYYY}}` with the desired year:

        | Column Name (per year)                   | Description |
        |------------------------------------------|-------------|
        | `RAW_TOTAL_SPEND_{{YYYY}}`                | Total amount of money spent at this POI in the year |
        | `RAW_NUM_TRANSACTIONS_{{YYYY}}`           | Total number of transactions conducted in the year |
        | `RAW_NUM_CUSTOMERS_{{YYYY}}`              | Number of unique customers that visited in the year |
        | `MEDIAN_SPEND_PER_TRANSACTION_{{YYYY}}`   | Median spend per transaction in the year |
        | `MEDIAN_SPEND_PER_CUSTOMER_{{YYYY}}`      | Median spend per customer in the year |
        | `SPEND_PCT_CHANGE_VS_PREV_YEAR_{{YYYY}}`  | Percent change in total spend compared to previous year |

        ---

        ### `parking_df`
        | Column Name         | Description |
        |---------------------|-------------|
        | `PLACEKEY`          | Parking lot ID |
        | `LATITUDE`, `LONGITUDE` | Location |
        | `POLYGON_WKT`        | Parking lot geometry |
        | `WKT_AREA_SQ_METERS` | Area of the parking lot |
        | `RELATED_POI`        | List of PLACEKEYs served by the parking lot |
        | `NAME`        | the state of the parking lot |

        ---

        ### `zone_df`
        | Column Name        | Description |
        |--------------------|-------------|
        | `zone_id`           | Unique zone ID |
        | `geometry`          | Polygon of the zone (shapely object) |
        | `center_lat`        | Centroid latitude |
        | `center_lng`        | Centroid longitude |
        | `num_pois`          | Number of POIs in the zone |

        ---

## Action Rules:
- Every Action must use the format: 
function_name[arg1, arg2, ...]
Needs Loop Over Zones: Yes or No
- Do not include any other text in the action.
- If an action requires zone_id as input but you want to loop through all zones, then you should put -1 as zone_id


- Only one function per Action. No combining tools.
- Always follow the Thought → Action → Observation sequence.
- Never perform multiple Actions in a row.

---## Data Chaining Guidelines:
When operations need to build on results from previous actions:
1. Use $action<n> to reference the result from Action n (e.g., $action1, $action2)
2. This allows chaining operations on previously computed results

When working with complex queries that require sequential operations:
1. Identify dependencies between operations
2. Use previous action results in subsequent actions
3. Build your analysis incrementally

Example for actions:
    Action 1: filter_pois_by_top_category[poi_spend_df, "Other Schools and Instruction"]
    Needs Loop Over Zones: Yes

    Action 2: filter_pois_by_sub_category[$action1, "Exam Preparation and Tutoring"]
    Needs Loop Over Zones: No

    Action 3: get_neighbor_zones(zone_df, -1, 4)
    Needs Loop Over Zones: Yes

## 🚨 Important Clarification about Looping:

When the user query involves **finding specific zones** that satisfy a condition (for example:  
"zones with parking lots larger than 12,000 square meters" or "zones with at least 10 parking spaces"),  
you **must loop over each zone individually**.

- set: `Needs Loop Over Zones: Yes`
- Even if a function can compute a global statistic across the whole dataset, you must apply it **zone-by-zone**.

- Do not write multiple Actions in a row. Always follow the pattern: Thought → Action → Observation → Thought → Action → Observation → ...

Note that nested use of tools is prohibited. 'Thought' can reason about the current situation, and 'Action' can use any of the available functions:


## Finishing Instructions:
- As soon as you find zones satisfying the query, immediately Finish:
    Finish[x, y, z]

- If no zones satisfy the query:
    Finish[None]

- If your analysis is general (not returning specific zones):
    Finish[Analysis complete: <summary>]

⚡ Do not continue searching after finding valid results.
⚡ Always stop immediately after finishing the required task.

---

## Summary:
- One Action = one function call only
- No nested or multi-tool actions
- Must alternate: Thought → Action → Observation
- Must clearly note if looping over zones
- Always Finish immediately after reaching a conclusion
Remember: Your goal is to answer the query efficiently. Do not perform unnecessary steps after finding the answer.

Query: {query}{scratchpad}"""




user_prompt_short = [
        #simple 1
        #I want to build a poi at a zone where there is atleast {num} parking spaces in 1 parking lot
        "I want to build a POI in a zone where there are at least 10 parking spaces.",
        "I want to open a new restaurant, but I need a location with at least 50 parking spots nearby.",
        "Looking for a spot to build a shopping mall—must have at least 200 parking spaces.",

        #simple 2
        #I want to build a zone where atleast 1 parking lot is bigger than {num} square meters            
        "I need to find land in for a logistics hub—must have at least one parking area greater than or equal to 15,000 square meters.",
        "Is there space to create an entertainment district with a parking lot over 6,000 square meters?",
        "Looking for a site to establish a retail zone with a parking lot larger than 8,000 square meters.",

        #simple 3
        #I want to build a poi at a zone where there is atleast {num} parking lots 
        "I want to build a food truck park in where the zone has at least 3 parking lots.",
        "Looking to open a drive-in theater in with at least 4 parking lots in the area.",
        "Need a spot in for a mini-golf course—zone must have at least 1 parking lot.",

        #simple 4
        #I want to open a clothing store with top category being {top category} and sub category being {sub category} , show me zones with less than {num} competitors in the same category
        "I want to open a clothing store, white plains with top category being {Other Schools and Instruction} and sub category being {Exam Preparation and Tutoring} , show me zones with less than 3 competitors in the same category", 
        "I want to open a clothing store in. Top category: {Other Amusement and Recreation Industries}, sub-category: {Fitness and Recreational Sports Centers}. Show me zones with fewer than 3 competitors in the same sub-category.",
        "Looking to launch a mental health practice. Top category: {Offices of Physicians}, sub-category: {Offices of Physicians, Mental Health Specialists}. Highlight areas with less than 2 competitors in this sub-category.",

        #simple 5
        #I want to look at zones where the {spend param} at year {year} is ≥ {num}
        "I want to look at zones where the raw total spend at year 2022 is ≥ 40000", 
        "I want to look at zones where the raw total spend at year 2019 is ≥ $45M.",
        "Analyze zones where raw total spend at year 2024 ≥ $6500000.",

        #simple 6
        #I want to open a restaurant in where the total population of my zone and my {num} closest neighboring zones is {num_2}
        "I want to open a restaurant where the total population of my zone and my 2 closest neighboring zones is greater than or equal to 10,000", 
        "I want to open an Italian restaurant where my zone plus 2 closest neighbors have at least 12,000 residents combined.",
        "Looking for a location to launch a food truck park - need my zone plus 3 adjacent zones to total atleast 15,000+ people.",

        #simple 7 
        #I want to open a restaurant. Show me zones with at least {num} POIs in the top category/sub category of {top category/sub category}.
        "I want to open a gastropub. Show me zones with at least 4 POIs in the top category of {Drinking Places (Alcoholic Beverages)}.",
        "Looking to launch a wine bar. Find me areas with 3+ {Beer, Wine, and Liquor Stores} as top category in the vicinity.",
        "I'm scouting locations for a craft cocktail lounge. Highlight zones containing 5+ poi with top category {Drinking Places (Alcoholic Beverages)}.",

        #simple 8: Show me zones with at least {num} POIs in any of these {top/sub categories}:  {top/sub category 1, top/sub category 2, top/sub category 3}
        "Show me zones with 8+ POIs in the sub-categories {Beauty Salons} or {Women's Clothing Stores} for a salon-retail hybrid.",
        "Find areas with 12+ POIs across the sub-categories {Drinking Places (Alcoholic Beverages)} and {Snack and Nonalcoholic Beverage Bars} for a nightlife district.",
        "Highlight zones with 6+ POIs in the sub-categories {Lessors of Residential Buildings and Dwellings} or {Elementary and Secondary Schools} for student housing.",

        #simple 9: I want to open a store where that zone has atleast {num} {transportation type}
        "I'm looking to launch a restaurant somewhere where there are at least 4 subway entrances nearby.",
        "Can you find me a zone with at least 6 bus stops? I'm planning to open a coffee shop.",
        "I want to open a bookstore where that area includes at least 3 stations.",

        #simple 10 ALL bosTON Filter zones where the distance from zone center to the nearest {transportation type} is < {num}
        "Filter zones where the distance from the zone centroid to the nearest bus stop is less than 200 meters.",
        "I need zones where the closest subway entrance is under 150 meters from the zone centroid.",
        "Show me zones where the distance to the nearest taxi stop is below 250 meters from the zone centroid.",


        #simple 11: Filter zones where at least {num}% of POIs are within {num} of a {transportation type}.”
        "Filter zones where at least 70% of POIs are within 500 meters of a subway entrance.",
        "I'm looking for zones where 60% or more of the POIs fall within 300 meters of a station.",
        "Show me zones where at least 80% of POIs are within 400 meters of a bus stop.",

        #simple 12: Filter zones where at least {num} of {transportation type} are within {dist} meters from the centroid.”
        "Filter zones where at least 6 stations are within 400 meters of the centroid.",
        "Filter zones where at least 3 bus stops are within 200 meters from the zone centroid.",
        "Find zones where at least 5 subway entrances are within 300 meters of the centroid.",

        #simple 13: Show me zones where at least {num} types of transportation are available in the zone
        "Show me zones where at least 3 types of transportation are available in the zone.",
        "I want to open a logistics hub — find zones with at least 4 distinct transportation types nearby.",
        "Highlight areas where 3 or more transportation types exist within the zone.",
        
        #simple 14 Find zones where at least {X}% of POIs belong to {top category or sub category}.”
        "Find zones where at least 40% of POIs are in sub category {Beauty Salons}.",
        "I'm looking for areas where 35% or more of all POIs are in top category {Restaurants and Other Eating Places}.",
        "Show me zones where over 50% of POIs fall under sub category {Snack and Nonalcoholic Beverage Bars}.",

        #simple 15 "Find zones where {sub category/top category} accounts for the highest number of POIs.”
        "Show me zones where sub category {Beauty Salons} is the singular most common POI type.",
        "I'm looking for areas where sub category {Full-Service Restaurants} is the dominant sub category in terms of POI count.",
        "Find zones where the singular most common POI type is sub category {Snack and Nonalcoholic Beverage Bars}.",

        #simple 16
        #Find zones where at least {num}% of total spend comes from {top category/sub category}.
        "I want to open a medical clinic where over 50% of the total spending in 2023 comes from top category {Offices of Physicians}.",
        "Find zones where at least 40% of the transaction volume in 2022 is from sub category {Couriers and Express Delivery Services}.",
        "Show me areas where 60% of the total dollars spent in 2023 went to top category {Legal Services}.",

        #simple 17 #todo: rerun
        #"Filter for zones that contain at least {num} POIs total."
        "Show me areas that contain at least 25 POIs — I'm planning a community café there.",
        "I need a zone with a minimum of 20 places of interest for my coworking space idea.",
        "Which zones have at least 15 establishments? I'm considering setting up a fitness studio.",

        #simple 18 #todo: rerun
        #"Show me zones where no single {top category/sub category} makes up more than {num}% of POIs."
        "I want areas where top category {Offices of Physicians} doesn't dominate more than 15% of POIs.",
        "Show me zones where the sub category {Offices of Lawyers} is no more than 20%.",
        "Avoid zones where top category {Offices of Physicians} takes up more than 9% of businesses.",

        #Medium 1: "I'm looking for zones where {raw total spend, raw num transactions, raw num customers} from {year start} to {year end} was more than {num}.", (simple 5)
        "I'm looking for zones where raw total spend from 2019 to 2021 was more than $22 million.",
        "Identify areas where over 400,000 transactions took place between 2020 and 2022.",
        "Show me zones with at least 150,000 unique customers across the years 2021 to 2023.",

        #Medium 2: "I'm looking for zones where {'MEDIAN_SPEND_PER_TRANSACTION', 'MEDIAN_SPEND_PER_CUSTOMER', 'SPEND_PCT_CHANGE_VS_PREV_YEAR'} from {year start} to {year end} was more than {num}.", (simple 5)
        "Looking for zones where the average median spend per transaction from 2020 to 2023 was above $45 — aiming for a mid-range retail spot.",
        "Show me areas where the average median spend per customer from 2021 to 2024 was over $300.",
        "Find zones that experienced an average yearly spend decline of less than -5% between 2019 and 2021 — might be a good place to introduce a discount brand.",


        #Medium 3: 2 spend constraints (simple 5)
        "I want to open a brunch spot where median spend per customer was ≤ $22 and yearly transactions ≥ 80,000 in 2023.",
        "Where can I put a BBQ joint? Need areas with 90,000+ yearly customers and ≥ 10% annual spending growth in 2021.",
        "Scouting locations for a vegan cafe - want zones with median spend per transaction ≤ $18 and 5%+ year-over-year spending growth in 2024.",

        #Medium 4: simple 2 AND/OR simple 3
        "I'm looking to develop a business plaza—need a zone with at least 5 parking lots and one lot over 9,000 square meters.",
        "Planning to open a medical center, and I want an area that either has at least 6 parking lots or one lot bigger than 12,000 square meters.",
        "I want to build a sports training facility where the zone includes at least 4 parking lots and one of them must exceed 10,000 square meters.",


        #Medium 5: simple 1 AND/OR simple 2
        "I'm looking to open a family entertainment center, and I need a parking lot with at least 100 parking spaces that is also larger than 2,000 square meters.",
        "Thinking about launching a big-box retail store—open to any zone that either has a parking lot with 300+ parking spaces or at least one lot over 5,000 square meters.",
        "I want to develop a new sports complex, but only if the site has a parking lot with at least 250 parking spots and a single parking lot bigger than 10,000 square meters.",


        #Medium 6: simple 1 AND/OR simple 3
        "I'm looking to build a lifestyle center, and I need a zone with at least 4 parking lots, one of which has at least 300 parking spaces.",
        "Planning a sports arena—only considering zones with at least 6 parking lots and one with over 500 parking spaces.",
        "Thinking of opening a regional conference center—must have at least 5 parking lots, with one offering no fewer than 400 spaces.",

        #Medium 7: simple 4 AND/OR simple 6
        "I want to open a clothing store with top category {Other Miscellaneous Store Retailers} and sub category {Art Dealers}. Show me zones with fewer than 4 competitors in the same sub-category and a combined population of at least 15,000 across the zone and its 3 closest neighbors.",
        "Thinking about launching a boutique. Top category: {Personal Care Services}, sub-category: {Beauty Salons}. I'm looking for zones with less than 5 competitors in the same category or where the zone plus 2 nearest neighbors have over 20,000 people.",
        "I want to open a Korean BBQ restaurant where the total population of my zone and 2 closest zones is at least 18,000, and the number of existing competitors in the same category is fewer than 3.",

        #Medium 8: simple 7 AND/OR simple 9
            "I want to open a ramen restaurant. Show me zones with at least 5 POIs in the top category {Restaurants and Other Eating Places} and at least 3 subway entrances nearby.",
        "Planning a gastropub—I'd like zones with at least 4 POIs in the top category {Drinking Places (Alcoholic Beverages)} and a minimum of 6 nearby bus stops.",
        "I'm scouting areas for a brunch café. I need zones that either have 3+ POIs in the sub category {Full-Service Restaurants} or at least 5 subway entrances within walking distance.",

        #Medium 9: simple 9 AND/OR simple 10
        "I'm looking to open a tea shop where there are at least 5 bus stops nearby and the closest bus stop is less than 180 meters from the zone centroid.",
        "Planning a boutique hotel—I'd like zones with at least 4 subway entrances or a subway entrance located within 150 meters of the zone centroid.",
        "I want to open a bookstore where the zone has at least 6 taxi stands and the nearest one is no more than 200 meters from the zone centroid.",

        #Medium 10: simple 11 AND/OR simple 9
        "I'm planning to open a community café where at least 65% of POIs are within 400 meters of a bus stop and the zone has at least 5 bus stops.",
        "I want to launcht a coworking lounge—preferably in zones with 60% or more POIs within 300 meters of a subway entrance in the zone or areas with at least 4 subway entrances.",
        "Looking to open a bookstore café. Show me zones where at least 70% of POIs are within 500 meters of a station in the zone and there are 3 or more stations.",

        #Medium 11: simple 4 AND/OR simple 3
        "I want to open a clothing store with top category {Personal Care Services} and sub category {Beauty Salons}. Show me zones with fewer than 3 competitors in the same category and at least 2 parking lots.",
        "Thinking about launching a boutique. Top category: {Other Amusement and Recreation Industries}, sub-category: {Fitness and Recreational Sports Centers}. I need a zone with fewer than 4 competitors or at least 3 parking lots in the area.",
        "Looking to open a clothing store with top category {Offices of Other Health Practitioners} and sub category {Offices of All Other Miscellaneous Health Practitioners}. Find me a zone with fewer than 2 competitors and at least 2 parking lots.",


        #Medium 12: simple 6 AND/OR simple 7
        "I want to open a tapas restaurant where my zone and 2 closest neighbors have a total population of at least 15,000 and the area includes at least 5 POIs in the top category {Full-Service Restaurants}.",
        "Thinking of launching a speakeasy bar—I'm looking for zones that either have 3+ POIs in the sub category {Drinking Places (Alcoholic Beverages)} or where the population of the zone plus 2 nearby zones exceeds 12,000.",
        "Looking to open a ramen shop. Show me areas with a combined population of at least 20,000 from my zone and 3 neighbors and at least 6 POIs in the category {Restaurants and Other Eating Places}.",

        #Medium 13: simple 8 AND/OR simple 10
        "I'm scouting locations for a high-traffic salon and retail space. Show me zones with at least 10 POIs in the sub-categories {Beauty Salons} or {Women's Clothing Stores}, and where the nearest bus stop is under 200 meters from the zone centroid.",
        "Looking to build a late-night food plaza—find me zones with 12+ POIs in sub category {Drinking Places (Alcoholic Beverages)} and {Snack and Nonalcoholic Beverage Bars}, and where the nearest subway entrance is less than 150 meters away.",
        "I want to open a hybrid tattoo parlor and juice bar. I need zones with at least 8 POIs in the categories {Beauty Salons} and {Snack and Nonalcoholic Beverage Bars}, and a taxi stop within 180 meters from the zone centroid.",

        #Medium 14: Find zones in {city}, {state} where at least {num}% of total  {raw total spend, raw num transactions, raw num customers}  comes from {top category}
        "Find zones where at least 35% of total raw total spend in 2020 comes from top category {Restaurants and Other Eating Places}.",
        "Show me zones where 40% or more of raw num transactions in 2021 come from top category {Gasoline Stations}.",
        "I'm looking for areas where at least 30% of total raw num customers in 2022 are from top category {Personal Care Services}.",

        #Medium 15: simple 17 AND/OR simple 18
        "Show me places where top category {Management of Companies and Enterprises} doesn't exceed 30% and there are at least 13 POIs.",
        "Show me places where top category {Software Publishers} doesn't exceed 30% and there are at least 5 POIs.",
        "I need zones that have at least 22 POIs and less than 20% in top category {Drinking Places (Alcoholic Beverages)}.",

        #Medium 16:simple 3 AND/OR simple 16
        'Looking to build a spa — find me areas where sub category {Advertising Agencies} dominates at least 40% of 2024 spend or has 2+ parking spots.',
        'Want to open a coffee lounge in a spot where sub category {Full-Service Restaurants} is strong — 50%+ of spend in 2022 — or somewhere with 4 parking spaces.',
        "I'm opening a family clinic and want zones where at least 60% of 2022 spending comes from sub category {Offices of Dentists} AND there's space for at least 2 parking lots.",

        #Hard 1: 3-7 spend params constraints together (simple 5)
        "I want to open a breakfast cafe — looking for zones where median spend per transaction was under $18, total spend was over $30 million, and there were at least 90,000 customers in 2022.",
        "Where should I open a boutique gym? I need areas with median spend per customer above $250, over 100,000 transactions, and a year-over-year spend growth rate of at least 6% in 2023.",
        "Thinking about launching a taco truck — I'm targeting zones with under $20 median spend per transaction, 50,000+ customers, a 10%+ year-over-year spending increase, and total spend above $15M in 2021.",    

        #Hard 2: Multiple spend params constraints together over multiple years (somple 5)
        "Looking to start a small movie theater — I'm after zones where the average median spend per customer from 2020 to 2023 was under $40, total spend exceeded $55 million, and the total number of customers was above 120,000 over that period.",
        "Scouting a place for a combo coffee/bookshop — I want zones with average year-over-year spend growth of at least 4%, average year-over-year spend increase above 10%, average median spend per transaction under $25, and total transactions over 180,000 from 2019 to 2022.",
        "Thinking about opening a family-owned pizzeria — looking for zones with total spend over $70M, average median spend per customer above $200, total customers over 250,000, and average year-over-year growth over 8% from 2021 through 2023.",

        #Hard 3: Medium 1 AND/OR Medium 2 AND/OR Simple 4
        "I want to open a brunch café with top category {Restaurants and Other Eating Places} and sub category {Full-Service Restaurants}, targeting zones with fewer than 3 competitors in the same sub category where the total number of transactions is > 300,000 from 2022 - 2024.",
        "I want to open a wellness studio with top category {Offices of Other Health Practitioners} and sub category {Offices of All Other Miscellaneous Health Practitioners}, but only in areas with fewer than 2 similar businesses where the total number of customers is > 120,000 from 2022 - 2024.",
        "I want to open a wine bar with top category {Beer, Wine, and Liquor Stores} and sub category {Beer, Wine, and Liquor Stores}, in zones with fewer than 4 competitors in the same category where total spend is > $40 million from 2022 - 2024.",

        #Hard 4: Simple 3 AND/OR Simple 4 AND/OR Simple 7
        "I'm planning to open a skincare bar with sub category {Beauty Salons}. Show me zones with fewer than 3 competitors in the same sub-category, at least 4 parking lots, and 6 or more POIs in the sub category {Beauty Salons}.",
        "I want to launch a minimalist clothing store with top category {Other Miscellaneous Store Retailers}. I need zones with fewer than 4 competitors, at least 3 parking lots, and 5 or more POIs in the top category {Other Miscellaneous Store Retailers}.",
        "Looking to open a health-food café with sub category {Snack and Nonalcoholic Beverage Bars}. I want zones with less than 3 competitors in the same sub-category, 4 or more parking lots, and at least 6 POIs in the sub category {Snack and Nonalcoholic Beverage Bars}.",

        #Hard 5: Simple 4 AND/OR Simple 6 AND/OR Simple 9
        "I want to open a wellness café with sub category {Snack and Nonalcoholic Beverage Bars}. Show me zones with fewer than 3 competitors in the same sub-category, at least 5 subway entrances nearby, and a combined population of at least 15,000 across the zone and 2 neighbors.",
        "Planning a boutique legal office with top category {Legal Services}. I need zones that have fewer than 4 competitors in the same top category, 4 or more bus stops nearby, and a total population of at least 18,000 with the zone and 3 surrounding zones combined.",
        "Looking to open a tutoring center with sub category {Exam Preparation and Tutoring}. I want zones with fewer than 2 competitors, 3+ nearby stations, and a minimum population of 12,000 across the zone and its 2 nearest neighbors.",

        #Hard 6: simple 4 AND/OR 6 NOT 3 --> todo. did not include sub/top 
        "I want to open a boutique clothing store with sub category {Women's Clothing Stores}. Show me zones with fewer than 3 competitors, a combined population of at least 12,000 with 2 nearby zones, but NOT zones with more than 2 parking lots — I'm targeting a pedestrian-heavy shopping area.",
        "Planning a walk-in hair studio with sub category {Beauty Salons}. I need fewer than 4 competitors, 10,000+ residents in the surrounding area, but I want zones with minimal car traffic — NOT more than 1 parking lot.",
        "Launching a luxury watch boutique with top category {Other Miscellaneous Store Retailers}. I want zones with fewer than 2 competitors, a population over 15,000 with neighbors, but NOT any place with 3 or more parking lots — aiming for high-foot-traffic districts.",

        #Hard 7: (3 AND 4) OR (6 AND NOT 7)
        "I'm planning to open a vegan café. Show me zones where there are at least 3 parking lots AND fewer than 2 competitors in sub category {Snack and Nonalcoholic Beverage Bars}, OR zones where the population of my zone and 2 neighbors exceeds 14,000 AND the number of POIs in {Full-Service Restaurants} is not more than 3 — I don't want areas already saturated with sit-down dining.",
        "Planning a food truck plaza. I want zones with 3 or more parking lots AND 6+ POIs in sub category {Snack and Nonalcoholic Beverage Bars}, OR zones with fewer than 2 competitors in the same sub category AND NOT more than 3 POIs in sub category {Drinking Places (Alcoholic Beverages)} — this isn't a nightlife spot.",
        "I want to open a boutique wine bar with sub category {Drinking Places (Alcoholic Beverages)}. Show me zones with 4 or more POIs in the sub category AND fewer than 3 competitors, OR zones with 3+ parking lots AND NOT a total population above 15,000 — targeting suburban charm, not urban density.",

        #Hard 8: (Simple 4 AND Simple 7) OR (Simple 9 AND NOT Simple 3)
        "I'm opening a career coaching office with sub category {Educational Support Services}. I want zones with fewer than 2 competitors AND at least 4 POIs in that sub category, OR zones with 4+ nearby bus stops AND NOT more than 2 parking lots — I'm aiming for foot-traffic-heavy academic districts.",
        "Planning a legal clinic with top category {Legal Services}. Find me zones that have under 3 competitors AND at least 5 POIs in the same top category, OR 5 or more subway entrances nearby AND NOT more than 2 parking lots — walkability is key.",
        "I want to launch a pop-up vegan dessert bar with sub category {Snack and Nonalcoholic Beverage Bars}. Target zones that have fewer than 3 competitors AND 6+ POIs, OR strong access with 4+ taxi stands AND NOT more than 1 parking lot — aiming for small-format urban placement.",

        #Hard 9: Simple 4 (competitor count) OR Simple 6 (population) AND NOT Simple 3 (parking lots) #NEED TO RE RUN THIS
        "I want to open a wellness studio. I'm looking for zones with fewer than 3 competitors in sub category {Other Personal Care Services} OR a population of at least 12,000 across 2 neighboring zones, but NOT zones with more than 2 parking lots — we're targeting walkable areas.",
        "Planning a tutoring center. I want zones that either have fewer than 2 competitors in sub category {Exam Preparation and Tutoring} OR population above 13,000 including 2 nearby zones, but NOT areas with 3 or more parking lots — this is a student-heavy district.",
        "Looking to launch a bakery café. I want either fewer than 3 competitors in sub category {Full-Service Restaurants} OR at least 15,000 people in this zone, but NOT zones with heavy parking less than 8— too suburban for my concept.",

        #Hard 10: Simple 7 (POI count) OR Simple 9 (transport access) AND NOT Simple 4 (competitor count)
        "I'm launching a late-night coffee spot. I want at least 5 POIs in sub category of {Snack and Nonalcoholic Beverage Bars} OR 4+ subway stops nearby, but NOT zones with more than 3 competitors in the same sub category.",
        "Looking to open a brunch café. Either the zone has 6+ POIs in sub category {Full-Service Restaurants} OR great transport via 5 bus stops, but NOT if 4 or more similar businesses exist.",
        "I want to open a barbershop. I'm looking for either 5+ POIs in sub category {Beauty Salons} OR at least 4 taxi stops, but NOT more than 3 competitors.",

        #Hard 11: Simple 6 (population) OR Simple 9 (transport) AND NOT Simple 10 (distance to transport POI)
        "I'm planning a co-working café. I want zones with at least 14,000 people across my zone and 2 neighbors OR at least 4 subway entrances, but NOT zones where the nearest station is more than 300 meters away — we need direct transit access.",
        "Opening a night market food stall. I want zones with either 13,000+ population including 3 nearby zones OR 5 bus stops, but NOT zones where the nearest bus stop is more than 250 meters from the centroid.",
        "I'm looking to set up a fast-casual eatery. The zone should either have strong public transit (5+ stops) OR 12,000+ population with 2 neighbors, but NOT if the nearest subway entrance is beyond walking range.",

        #Hard 12: Simple 3 (parking lots) OR Simple 7 (POI count) AND NOT Simple 6 (population) #rerun 
        "Looking to open a drive-in diner. I want zones with at least 4 parking lots OR 6 POIs in sub category {Full-Service Restaurants}, but NOT ones where the combined population across my zone and 2 neighbors exceeds 12,000 — I'm avoiding congested urban cores.",
        "Planning a car-based grocery pickup center. Either I need 5 parking lots OR 5+ POIs in  sub category {Snack and Nonalcoholic Beverage Bars}, but NOT if the surrounding population  across my zone and 4 neighbors exceeds 14,000 — I'm focused on suburban delivery hubs.",
        "I'm opening an automotive service hub. I want 3 or more parking lots OR 4 POIs in  sub category {Automotive Parts, Accessories, and Tire Stores}, but NOT zones with 15,000+ people — lower density is key for this model.",

        #Hard 13:(Simple 13 AND Simple 6) OR (Simple 4 AND NOT Simple 7) #rerun
        "Planning to open a neighborhood bank. Either the zone has 4 transport modes and 14,000+ people in 2 neighbors, OR there are fewer than 2 competitors in sub category {Commercial Banking} AND NOT more than 3 POIs in that space.",
        "Looking for a spot to open a boutique law office — give me zones with 3 or more transportation types AND at least 12,000 residents in 2 zones, OR areas with fewer than 2 competitors in sub category {Offices of Lawyers} AND NOT more than 2 POIs in that sub category.",
        "I'm launching a real estate satellite office. I want either zones with 3 types of transportation and 13,000+ with cloest nearby zone residents, OR areas with under 3 competitors in sub category {Offices of Real Estate Agents and Brokers} AND NOT 4 or more POIs in that sub category.",

        #Hard 14: (Simple 8 AND NOT Simple 3) OR (Simple 7 AND Simple 9)
        "I'm opening a lifestyle shop — show me zones with at least 5 POIs from sub categories {Beauty Salons} and {Snack and Nonalcoholic Beverage Bars} AND NOT more than 2 parking lots, OR zones with at least 4 POIs in sub category {Art Dealers} AND at least 3 bus stops nearby.",
        "Looking to launch a cultural venue. I want zones that include 6+ POIs across sub category {Drinking Places (Alcoholic Beverages)} and {Snack and Nonalcoholic Beverage Bars} AND NOT zones with more than 2 parking lots, OR areas with 5+ POIs in sub category {Full-Service Restaurants} and at least 4 subway entrances.",
        "I'm scouting locations for a local market. Either I want zones with at least 5 POIs from sub categories {Gasoline Stations with Convenience Stores} and {Beer, Wine, and Liquor Stores} AND NOT 3 or more parking lots, OR zones with 6 POIs in sub category {Full-Service Restaurants} and 5+ stations nearby.",

        #Hard 15: (Simple 4 AND Simple 6) NOT Simple 3 + Spend Filters #rerun
        "I'm planning a boutique smoothie bar in sub category {Snack and Nonalcoholic Beverage Bars}. Zones must have fewer than 2 competitors, 10,000+ population with nearby 1 zone, NOT more than 1 parking lot, and median spend per customer averaged over $180 between 2020–2023.",
        "Scouting areas for a youth-focused learning studio under sub category {Educational Support Services}. I need fewer than 3 competitors, population with 2 neighbors ≥ 12,000, NOT more than 2 parking lots, and yearly transactions > 180,000 in 2022.",
        "I'm opening a holistic health shop under {Other Personal Care Services}. Looking for zones with fewer than 3 competitors, population over 11,000 with adjacent 3 zones, NOT more than 2 parking lots, and average year-over-year spend growth > 7% from 2020–2023.",

        #NEW! Hard 16   simple_17 AND simple_16 NOT simple_14
        "Looking to launch a creative co-working café — needs at least 26 POIs AND strong local spending, like 50%+ from sub-category of {Full-Service Restaurants} in 2022, but I'm not interested if that same category dominates the area by 30%.",
        "For my next wellness studio, the perfect zone needs 35+ POIs and a strong sub category {Beauty Salons} spend — over 40% in 2023. But don't show me places where that category makes up more than 30% of POIs. Too much is too much.",
        "I'm opening a wellness hub and want a zone with at least 37 POIs, and more than 50% of total spending in 2019 should come from sub category {Educational Support Services}, but skip it if that category takes up more than 25% of all POIs — we need variety.",

        #new ! Hard 17 simple_15 OR simple_16 NOT simple_14
        "I'm looking for one of two scenarios: either the area is dominated by sub category {Offices of Dentists}, or top category {Educational Support Services} gets over 70% of spend in 2022. But if {Educational Support Services} also takes up more than 40% of POIs, it's a no-go for me.",
        "I'm choosing a launch site. Either the sub category {Beauty Salons} should be the most common type in the zone, **OR** the top category {Lessors of Real Estate} should contribute over 60% of spending in 2021. But if {Lessors of Real Estate} already dominates more than 30% of POIs, count that zone out — I want diversity.",
        "I'm choosing a launch site. Either the sub category {Other Automotive Mechanical and Electrical Repair and Maintenance} should be the most common type in the zone, **OR** the top category {Advertising, Public Relations, and Related Services} should contribute over 50% of spending in 2023. But if {Advertising, Public Relations, and Related Services} already dominates more than 40% of POIs, count that zone out — I want diversity.",

]
user_prompt = [
            #simple 1 I want to build a poi at a zone where there is atleast {num} parking spaces in 1 parking lot
            "I want to build a POI in a zone where there are at least 10 parking spaces.",
            "I want to open a new restaurant, but I need a location with at least 50 parking spots nearby.",
            "Looking for a spot to build a shopping mall—must have at least 200 parking spaces.",
            "I'm planning to construct a medical clinic. Are there zones with at a parking lot with least 30 parking spots available?",
            "Where could I put a new grocery store? It needs a parking lot with at least 80 parking spaces.",
            "I need to find a location for a movie theater, ideally a parking lot with 150+ parking spots.",
            "Is there an area with at least 40 parking spaces? I want to build a small hotel there.",
            "I want to build a truck stop with at least 100 parking spaces for semis and cars.",
            "Looking for land to open a drive-in movie theater—must have space for 200+ parked cars.",
            "Where could I build a large outlet mall with at least 500 parking spots?",
            "I need a location to construct a casino with a minimum of 300 parking spaces.",
            "Planning a regional hospital on a site with at least 150 parking spaces for staff and visitors.",
            "I'm scouting locations for a big-box retail store. Requires 250+ parking spots.",
            "Where could I build a theme park? I need space for at least 1,000 parked cars.",
            "I want to build a new hotel. I need a location with at least 100 parking spaces.",
            "I want to open a language tutoring hub with sub category 150 parking spaces.",
            "I need a location to construct a new office building. It must have at least 10 parking spaces.",
            "Is there a zone with at least 1 parking lot that has 60+ parking spaces? I want to build a mall there.",
            "I need to find a location for a new office building. It must have at least 22 parking spaces.",
            "I'm looking for a spot to open a new car dealership. It must have at least 80 parking spaces.",

            #simple 2 I want to build a zone where atleast 1 parking lot is bigger than {num} square meters            
            "I need to find land in for a logistics hub—must have at least one parking area greater than or equal to 15,000 square meters.",
            "Is there space to create an entertainment district with a parking lot over 6,000 square meters?",
            "Looking for a site to establish a retail zone with a parking lot larger than 8,000 square meters.",
            "I want to build a transportation hub in with at least one parking lot spanning 12,000+ square meters.",
            "Where in  could I develop a business park that includes a parking lot over 9,000 square meters?",
            "Planning an industrial zone —need at least one parking lot bigger than 5,500 square meters.",
            "I need to build a distribution center in  with at least one truck parking lot exceeding 20,000 square meters.",    
            "Looking for land in to develop a mega-church complex need at least one lot over 15,000 square meters.", 
            "Where in could I establish a theme park with a main parking area larger than 2000 square meters?",        
            "Planning a casino resort in - must have a parking facility bigger than 25000 square meters for guests and staff.",
            "I want to develop a regional shopping complex in with parking lots totaling over 4000 square meters.",  
            "Need to find a site in for a sports arena with at least one parking lot spanning 18,000+ square meters.",
            "Looking to build a truck stop plaza in with multiple parking areas, including one over 12,000 square meters for semis.",
            "Where in could I construct a convention center with parking facilities exceeding 2200 square meters?",
            "Planning a major outlet mall in - need parking infrastructure covering at least 3500 square meters.",
            "I'm scouting locations in for an auto testing facility that requires a paved area over 10000 square meters for vehicle storage.",
            "Looking for land in for a military vehicle storage facility – must have paved parking over 80,000 square meters.",
            "Planning a Super Walmart distribution hub in - requires a trailer parking lot exceeding 45,000 square meters.",
            "Where in could I develop a rodeo complex with attendee parking spanning 35,000+ square meters?",

            #simple 3 I want to build a poi at a zone where there is atleast {num} parking lots 
            "I want to build a food truck park in where the zone has at least 3 parking lots.",
            "Looking to open a drive-in theater in with at least 4 parking lots in the area.",
            "Need a spot in for a mini-golf course—zone must have at least 1 parking lot.",
            "Planning an urgent care clinic in where the zone includes at least 4 parking lots.",
            "Where in could I build a farmers market with at least 3 parking lots nearby?",
            "Want to create a coworking space in zone needs at least 2 parking lots.",
            "Looking for a location in for a trampoline park with at least 1 parking lot.",
            "Need to build a car wash in where the zone has at least 3 parking lots.",
            "Planning a wedding venue in with must have at least 9 parking lots in the zone.",
            "Where in could I put an indoor sports complex with at least 1 parking lot?",
            "Need to find a spot in for a pop-up market. Non-negotiable: the area must include 3+ parking lots.",
            "Dreaming of a cat café. Found any zones with at least 1 parking lot?",
            "City planners—where can I drop a food hall with 4 parking lots in its zone?",
            "Help! My axe-throwing business needs a home Priority: zones with 2+ parking lots.",
            "Is there a corner of zoned for a tiny bookstore + coffee shop? Must have at least 1 parking lot.",
            "Planning a vintage Airstream hotel in. Dealbreaker: less than 3 parking lots in the area.",
            "Pitching a rooftop cinema in. Investors demand at least 2 parking lots in the zone—where should I look?",
            "Seeking a zone in for an artisanal ice cream factory. Parking lot requirement: 1",
            "Want to convert an old warehouse into artist studios. How's the parking lot situation? Need at least 1 in the zone.",
            "I want to build a retro roller rink. But the zone absolutely needs at least 3 parking lots. Where should I look?", 

            #simple 4 I want to open a clothing store with top category being {top category} and sub category being {sub category} , show me zones with less than {num} competitors in the same category
            "I want to open a clothing store, white plains with top category being {Other Schools and Instruction} and sub category being {Exam Preparation and Tutoring} , show me zones with less than 3 competitors in the same category", 
            "I want to open a clothing store in. Top category: {Other Amusement and Recreation Industries}, sub-category: {Fitness and Recreational Sports Centers}. Show me zones with fewer than 3 competitors in the same sub-category.",
            "Looking to launch a mental health practice. Top category: {Offices of Physicians}, sub-category: {Offices of Physicians, Mental Health Specialists}. Highlight areas with less than 2 competitors in this sub-category.",
            "Planning a residential remodeling business. Top category: {Residential Building Construction}, sub-category: {Residential Remodelers}. Identify zones where competitors in this sub-category is under 4.",
            "I want to open a medical practice (Top category: {Offices of Physicians}). Show me zones with less than 3 competing clinics in this category.",
            "Looking to start a real estate agency (Top category: {Offices of Real Estate Agents and Brokers}). Where are areas with fewer than 2 competitor agencies?",
            "I want to open a real estate brokerage (Top category: {Offices of Real Estate Agents and Brokers}, Sub-category: {Offices of Real Estate Agents and Brokers}). Show me zones with fewer than 3 competing agencies in this exact category.",
            "Looking to start an alternative health practice (Top category: {Offices of Other Health Practitioners}, Sub-category: {Offices of All Other Miscellaneous Health Practitioners}). Identify areas with less than 2 competitors offering similar specialty services.",
            "Planning a commercial screen printing business (Top category: {Printing and Related Support Activities}, Sub-category: {Commercial Screen Printing}). Need zones with under 4 competitors in commercial printing.",
            "Scouting locations for a general dentistry practice. Top category: {Offices of Dentists}, Sub-category: {Offices of Dentists}. Where are areas with less than 5 competing dental offices?",
            "I want to open another dental clinic. Top category: {Offices of Dentists}, Sub-category: {Offices of Dentists}. Show me underserved zones with fewer than 3 competitors in general dentistry.",
            "Looking to establish a medical practice (excluding mental health). Top category: {Offices of Physicians}, Sub-category: {Offices of Physicians (except Mental Health Specialists)}. Highlight areas with less than 4 competing general physician offices.",
            "I want to open a farm-to-table restaurant. Top category: {Restaurants and Other Eating Places}. Show me food districts with fewer than 4 competing eateries in this style.",
            "Looking to establish a cardiology practice. Top category: {Offices of Physicians}. Identify neighborhoods with less than 3 competing physician offices.",
            "Planning an extreme sports gear shop. Top category: {Sporting Goods, Hobby, and Musical Instrument Stores}. Need areas with under 2 similar specialty retailers.",
            "Scouting locations for a renewable energy plant. Top category: {Electric Power Generation, Transmission and Distribution}. Where are industrial zones without existing solar/wind operations?",
            "Want to launch an environmental nonprofit. Top category: {Social Advocacy Organizations}. Show me cities with fewer than 3 similar advocacy groups in this region.",
            "Looking to start an organic blueberry farm. Top category: {Agriculture, Forestry, Fishing and Hunting}. Highlight agricultural zones with no competing berry farms within 5 miles.",
            "Planning a civil war museum. Top category: {Museums, Historical Sites, and Similar Institutions}. Identify tourist areas with less than 2 competing historical attractions.",
            "Need to open a premium pet bakery. Top category: {Specialty Food Stores}. Show me commercial zones with 0 existing pet treat shops.",
            "I want to open a cemetery. Top category: {Cemeteries and Crematories}. Show me counties with fewer than 3 existing memorial parks.",
            "Looking to start a charter bus company. Top category: {Bus and Other Motor Vehicle Transit Systems}. Identify regions with less than 5 competing transit operators.",
            "Planning a rock-climbing gym. Top category: {Fitness and Recreational Sports Centers}. Need areas with under 2 similar recreational facilities.",
            "Scouting locations for a wildlife sanctuary. Top category: {Nature Parks and Other Similar Institutions}. Where are undeveloped zones without competing nature attractions?",
            "Want to launch a premium jerky store. Top category: {All Other Specialty Food Stores}. Highlight food deserts with 0 artisanal meat retailers.",   
            "Looking to establish a student housing rental business. Top category: {Lessors of Residential Buildings and Dwellings}. Map college towns with less than 4 dedicated student housing providers.",
            "Need to open a mobile barber service. Top category: {Barber Shops}. Show me suburban areas with fewer than 3 traditional barbershops.",
           "Planning a COVID testing lab(Sub-category: {Medical Laboratories}). Identify healthcare corridors with under 5 competing labs.",
           "Want to create a courier service specializing in medical deliveries in (Sub-category: {Couriers and Express Delivery Services}). Find regions with less than 2 medical logistics competitors.",
           "Looking to start an anxiety treatment center (Sub-category: {Offices of Mental Health Practitioners (except Physicians)}). Highlight towns with fewer than 4 similar practices.",

            #simple 5 I want to look at zones where the {spend param} at year {year} is ≥ {num}
            "I want to look at zones where the raw total spend at year 2022 is ≥ 40000", 
            "I want to look at zones where the raw total spend at year 2019 is ≥ $45M.",
            "Analyze zones where raw total spend at year 2024 ≥ $6500000.",
            "Identify areas with raw total spend at year 2022 ≥ $850000.",
            "Filter zones where raw total spend at year 2023 ≥ $550000.",
            "Find areas with 500,000+ transactions in 2022.",
            "Identify locations that had 150,000+ customers in 2023.",
            "Highlight districts with median spend per transaction over $50 in 2021.",
            "Show zones where median spend per customer exceeded $200 in 2022.",
            "Show me zones with year-over-year spend growth over 250% in 2023.",
            "Identify areas experiencing a 70%+ annual spend increase in 2020",
            "Which districts had spending crashes of 60%+ in 2022",
            "Show me zones with stable yearly spending (±3% changes) in 2022",
            "Where did spending plummet 20%+ in 2024?", 
            "Find areas with consistent 5-10% yearly spending growth in 2022",
            "I want to open a boutique cafe where median spend per customer was ≤ $18 in 2022.",
            "Looking to build a family diner where total transactions were ≥ 80,000 in 2023.",
            "Need to find a location for my sushi restaurant - show me zones with median transaction values ≥ $45 in 2023.",


            #simple 6 I want to open a restaurant in where the total population of my zone and my {num} closest neighboring zones is {num_2}
            "I want to open a restaurant where the total population of my zone and my 2 closest neighboring zones is greater than or equal to 10,000", 
            "I want to open an Italian restaurant where my zone plus 2 closest neighbors have at least 12,000 residents combined.",
            "Looking for a location to launch a food truck park - need my zone plus 3 adjacent zones to total atleast 15,000+ people.",
            "Show me areas where I can open a Cuban cafe with at least 8,000 people in my zone and 1 closest neighboring zone.",
            "Find me locations for a seafood restaurant where my zone plus 2 surrounding zones contain greater than or equal to 18,000+ residents.",
            "I need to build a steakhouse - require my zone plus 4 closest neighbors to have 25,000 people minimum.",
            "Where can I put a craft brewery? Need my zone plus 3 neighboring areas to have 20,000+ population minimum.",  
            "Scouting for a hot chicken joint - must have greater than or equal to 10,000 people in my zone plus 2 adjacent zones.",
            "Find me spots to open a Mexican restaurant where my area plus 3 closest zones have at least 30,000 residents.",
            "Show me areas where I can open a cheesesteak place with at least 15,000 people in my zone and 1 closest neighbor.",

            #simple 7 I want to open a restaurant. Show me zones with at least {num} POIs in the top category/sub category of {top category/sub category}.
            "I want to open a gastropub. Show me zones with at least 4 POIs in the top category of {Drinking Places (Alcoholic Beverages)}.",
            "Looking to launch a wine bar. Find me areas with 3+ {Beer, Wine, and Liquor Stores} as top category in the vicinity.",
            "I'm scouting locations for a craft cocktail lounge. Highlight zones containing 5+ poi with top category {Drinking Places (Alcoholic Beverages)}.",
            "Planning a bistro. Identify areas with 4+ poi with top category {Restaurants and Other Eating Places} within the zone.",
            "I want to open a neighborhood pub. Show me locations with 3+ {Drinking Places (Alcoholic Beverages)} as top category already operating.",
            "I want to open a home decor boutique. Show me zones with at least 3 existing {Home Furnishings Stores} as top category nearby.",
            "Looking to launch a luxury watch shop. Find me areas with 4+ {Jewelry, Luggage, and Leather Goods Stores} as top category in the vicinity.",
            "I want to open a tutoring center. Show me zones with at least 3 {Elementary and Secondary Schools} as top category nearby.",
            "Looking to start a music academy. Find areas with 2+ {Other Schools and Instruction} as top category businesses already operating.",
            "I'm scouting locations for an educational toy store. Highlight zones containing 4+ {Educational Support Services} as top category providers.",
            "I want to open a boutique law firm. Show me zones with at least 4 existing {Legal Services} as top category providers nearby.",
            "Looking to launch a real estate agency. Find areas with 3+ poi with top category {Offices of Real Estate Agents and Brokers} in the vicinity.",
            "I'm scouting locations for a digital marketing startup. Highlight zones containing 5+ poi with top category {Advertising, Public Relations, and Related Services} firms.",            
            "I want to open a wine bar. Show me zones with at least 3 businesses in the sub-category {Drinking Places (Alcoholic Beverages)}.",
            "Looking to launch a juice bar. Find areas with 2+ establishments in the sub-category {Snack and Nonalcoholic Beverage Bars}.",
            "I'm scouting locations for a bridal boutique. Highlight zones containing 4+ stores in the sub-category {Women's Clothing Stores}.",
            "Planning a specialty grocery. Identify areas with 3+ businesses in the sub-category {Supermarkets and Other Grocery (except Convenience) Stores}.",
            "Where should I place my after-school program? Show me zones with 3+ facilities in the sub-category {Elementary and Secondary Schools}.",

           
            #simple 8: Show me zones with at least {num} POIs in any of these {top/sub categories}:  {top/sub category 1, top/sub category 2, top/sub category 3}
            "Show me zones with 8+ POIs in the sub-categories {Beauty Salons} or {Women's Clothing Stores} for a salon-retail hybrid.",
            "Find areas with 12+ POIs across the sub-categories {Drinking Places (Alcoholic Beverages)} and {Snack and Nonalcoholic Beverage Bars} for a nightlife district.",
            "Highlight zones with 6+ POIs in the sub-categories {Lessors of Residential Buildings and Dwellings} or {Elementary and Secondary Schools} for student housing.",
            "Identify locations with 15+ POIs in the sub-categories {Supermarkets and Other Grocery (except Convenience) Stores} and {Snack and Nonalcoholic Beverage Bars} for a grocery-cafe concept.",
            "Find zones with 10+ POIs in the sub-categories {Barber Shops}, {Jewelry Stores}, {Other Personal Care Services} for a barbershop chain.",
            "Highlight locations with 7+ POIs in the sub-categories {Women's Clothing Stores} and {Jewelry Stores} for boutique retail.", 
            "Show me zones with 9+ POIs in the sub-categories {Hair, Nail, and Skin Care Services} and {Nail Salons} for a beauty hub.",
            "Identify areas with 4+ POIs in the sub-categories {Other Personal Care Services} and {Barber Shops}, {Nail Salons} for neighborhood grooming services.", 
            "Show me zones with 15+ POIs across the sub-categories {Elementary and Secondary Schools}, {Educational Support Services}, and {Offices of Real Estate Agents and Brokers} for a family-oriented service hub.",
            "Find areas with 20+ POIs in the sub-categories {Offices of Lawyers}, {Educational Support Services}, and {Elementary and Secondary Schools} for an education-law corridor.", 
            "Highlight zones with 12+ POIs in the sub-categories {Residential Remodelers}, {Offices of Real Estate Agents and Brokers}, and {Elementary and Secondary Schools} for home services targeting families.", 
            "Identify locations with 25+ POIs across all five sub-categories: {Elementary and Secondary Schools}, {Educational Support Services}, {Offices of Lawyers}, {Residential Remodelers}, and {Offices of Real Estate Agents and Brokers} for a comprehensive professional district.",
            "Show me areas with 18+ POIs in the sub-categories {Offices of Real Estate Agents and Brokers}, {Residential Remodelers}, and {Educational Support Services} for a real estate renovation cluster.", 
            "Find zones with 30+ POIs across the sub-categories {Elementary and Secondary Schools}, {Educational Support Services}, and {Offices of Lawyers} for an elite education-legal hub.",
            "Highlight locations with 15+ POIs in the sub-categories {Residential Remodelers} and {Offices of Real Estate Agents and Brokers} for home improvement services.",
            
            #simple 9: I want to open a store where that zone has atleast {num} {transportation type}
            "I'm looking to launch a restaurant somewhere where there are at least 4 subway entrances nearby.",
            "Can you find me a zone with at least 6 bus stops? I'm planning to open a coffee shop.",
            "I want to open a bookstore where that area includes at least 3 stations.",
            "Is there a zone with at least 7 taxi spots? I'd like to set up a hotel there.",
            "Thinking about opening a bakery, but only if the area has 2 or more subway entrances.",
            "Looking for a location that has a minimum of 4 taxi services around the zone — planning to open a community center.",
            "I want to open a gym where the zone has at least 5 bus stops nearby.",
            "Looking to build a library where there are at least 3 subway entrances.",
            "Is there a good area with 4 or more stations? I want to open a movie theater.",
            "I'm planning to open a tech repair shop — the zone must have at least 2 aerodromes.",
            "Thinking of starting a farmer's market where the area includes at least 6 bus stops.",
            "Hoping to open a small hospital where the zone has no fewer than 5 taxi locations.",
            "Looking to open a pet grooming salon and I need the zone to have at least 3 stations.",
            "I'm considering a retail outlet, but only if the zone has at least 4 subway entrances.",
            "Find me a place with at least 2 aerodromes — I want to set up a logistics center.",
            "I want to open a rooftop bar, and I need at least 6 taxi stops in the surrounding zone.",

            #simple 10 ALL bosTON Filter zones where the distance from zone center to the nearest {transportation type} is < {num}
            "Filter zones where the distance from the zone centroid to the nearest bus stop within the zone is less than 200 meters.",
            "I need zones where the closest subway entrance within the zone is under 150 meters from the zone centroid.",
            "Show me zones where the distance to the nearest taxi stop within the zone is below 250 meters from the zone centroid.",
            "Can you find zones where the nearest subway entrance within the zone is within 100 meters of the zone centroid? I want something super walkable.",
            "Looking for zones where the distance from the zone centroid to the closest station within the zone is under 300 meters — trying to minimize commute time.",
            "I'm searching for a place where the nearest bus stop within the zone is no more than 250 meters from the zone centroid. Accessibility is key.",
            "Give me zones with a taxi stand within the zone less than 200 meters from the zone centroid — it's for a late-night diner idea.",
            "Are there any zones where the distance to the nearest aerodrome within the zone is less than 500 meters from the zone centroid?",
            "Trying to find zones where the zone centroid is less than 150 meters from the nearest station within the zone — thinking of foot traffic for a new coffee spot.",
            "I need a zone with the nearest bus stop within 100 meters from the zone centroid, and also need to be within the zone. Convenience matters for this project.",
            "Do any zones have a subway entrance within the zone closer than 200 meters from the zone centroid? Prioritizing public transport access.",
            "Looking at opening a clinic. Are there zones where the taxi stand within the zone is under 300 meters from the zone centroid?",
            "Interested in zones where the nearest station within the zone is no more than 180 meters from the zone centroid — the goal is max foot traffic.",
            "I want to open a general store. Any zones where the distance from the zone centroid to the closest taxi spot is under 900 meters and also within the zone?",
            "Show me zones where the nearest station within the zone is no more than 1,000 meters from the zone centroid — needs to be somewhat reachable.",
            "Can you check for zones where the subway entrance within the zone is less than 700 meters from the zone centroid? I know they're rare there, but worth checking.",
            "I'm considering opening a small clinic. Are there any zones where the bus stop within the zone is within 750 meters of the zone centroid?",
            "Can you check for zones where the subway entrance within the zone is less than 700 meters from the zone centroid? I know they’re rare there, but worth checking.",
            "I’m considering opening a small clinic. Are there any zones where the bus stop within the zone is within 750 meters of the zone centroid?",
            "Find me zones where the nearest taxi stand within the zone is under 950 meters from the zone centroid — thinking of a bed-and-breakfast setup.",
            "Looking at zones where the distance to the closest aerodrome within the zone is less than 1,500 meters from the zone centroid.",
            "Trying to scout areas with a station within the zone — ideally within 1,100 meters of the zone centroid. Tourist traffic is a big factor.",
            "Are there zones where the zone centroid is no more than 1,300 meters from the nearest bus stop within the zone? It’s for a small local art gallery.",

            #simple 11: Filter zones where at least {num}% of POIs are within {num} of a {transportation type}.”
            "Filter zones where at least 70% of POIs are within 500 meters of a subway entrance.",
            "I’m looking for zones where 60% or more of the POIs fall within 300 meters of a station.",
            "Show me zones where at least 80% of POIs are within 400 meters of a bus stop.",
            "Can you find zones where 65% of POIs are within 350 meters of a taxi stop?",
            "Looking for zones where at least 75% of POIs are located within 400 meters of a bus stop.",
            "I need zones where 60% of the POIs are within 500 meters of an aerodrome — accessibility by air matters here.",
            "Filter zones where no less than 85% of POIs are within 300 meters of a subway entrance.",
            "Are there any zones where 70% of POIs fall within 250 meters of a station?",
            "Show me areas where at least 90% of POIs are within 450 meters of a bus stop — trying to optimize foot traffic.",
            "Trying to locate zones where a minimum of 55% of POIs are within 600 meters of a taxi stop.",
            "I’m looking for zones where 80% or more of POIs are within 500 meters of a subway entrance — even if there’s only one.",
            "Find zones where at least 65% of POIs are located within 700 meters of an aerodrome.",
            "Seeking zones where 75% of POIs are within 350 meters of a nearby station — thinking about launching a shuttle service.",

            #simple 12: Filter zones where at least {num} of {transportation type} are within {dist} meters from the centroid.”
           "Filter zones where at least 6 stations are within 400 meters of the centroid.",
            "Filter zones where at least 3 bus stops are within 200 meters from the zone centroid.",
            "Find zones where at least 5 subway entrances are within 300 meters of the centroid.",
            "Show me zones that have at least 4 taxi stands located within 250 meters of the zone centroid.",
            "Highlight zones with at least 6 stations within 400 meters from the zone centroid.",
            "I’m looking for zones where at least 3 aerodromes are located within 500 meters from the centroid.",
            "Can you identify areas with at least 2 bus stops within 150 meters from the zone center?",
            "Find me zones that have at least 4 subway entrances within 350 meters of the centroid.",
            "Show zones where there are at least 6 taxi stands within 300 meters from the centroid.",
            "Filter for zones with at least 5 stations no more than 250 meters from the zone centroid.",
            "Locate zones where at least 3 subway entrances are within a 200-meter radius from the centroid.",
            "Find zones where at least 4 bus stops are within 300 meters from the zone centroid.",
            "Show me areas with at least 3 subway entrances located within 250 meters from the centroid.",

           
            #simple 13: Show me zones where at least {num} types of transportation are available in the zone
           "Show me zones where at least 3 types of transportation are available in the zone.",
            "I want to open a logistics hub — find zones with at least 4 distinct transportation types nearby.",
            "Highlight areas where 3 or more transportation types exist within the zone.",
            "Filter for zones with access to at least 2 types of transportation options like subway, taxi, and bus.",
            "Identify zones where at least 3 transportation types are available for easy commuter access.",
            "Find me locations where the zone supports 4 or more different types of transportation.",
            "Looking for zones that offer at least 3 types of transit options — ideal for opening a coworking space.",
            "Show me zones where there are at least 2 types of transportation infrastructure present.",
            "I’m scouting zones where 3 or more distinct transport modes are available within the zone.",
            "Where can I find zones with at least 4 different transportation types to support a new mixed-use development?",
            "Find zones where at least 2 types of transportation are available in the zone.",
            "Show me areas that offer at least 3 different transportation types for setting up a regional health center.",
            "I’m looking to launch a logistics point — filter for zones with at least 2 transportation types nearby.",
            "Highlight zones where the area supports 3 or more types of transit access.",
                
            #simple 14 Find zones where at least {X}% of POIs belong to {top category or sub category}.”
            "Find zones where at least 40% of POIs are in sub category {Beauty Salons}.",
            "I'm looking for areas where 35% or more of all POIs are in top category {Restaurants and Other Eating Places}.",
            "Show me zones where over 50% of POIs fall under sub category {Snack and Nonalcoholic Beverage Bars}.",
            "Can you locate zones where at least 60%+ of POIs belong to top category {Offices of Physicians}?",
            "Looking for zones where at least 45% of POIs are in sub category {Educational Support Services}.",
            "I need zones where 30% or more of POIs are under top category {Personal Care Services}.",
            "Show me zones where over half the POIs or just half are in sub category {Full-Service Restaurants}.",
            "Find me areas where at least 38% of POIs fall under sub category {Offices of Lawyers}.",
            "I'm searching for zones where at least 25% of POIs are in sub category {Couriers and Express Delivery Services}.",
            "Identify locations where 40%+ of POIs or more are classified as sub category {Gasoline Stations with Convenience Stores}.",
            "Find zones where 50% or more of POIs are in top category {Restaurants and Other Eating Places}.",
            "I'm looking for areas where at least 40% of POIs fall under sub category {Beer, Wine, and Liquor Stores}.",
            "Locate zones where 60%+ of POIs or more belong to top category {Personal Care Services}.",
            "I want to identify zones where over 35% or more of POIs are in sub category {Snack and Nonalcoholic Beverage Bars}.",
            "Searching for areas where atleast 42% of POIs are in sub category {Exam Preparation and Tutoring}.",
            "Highlight zones where at least 55% of POIs are categorized under sub category {Educational Support Services}.",
            "Find me zones where atleast 30% of POIs are in top category {Offices of Real Estate Agents and Brokers}.",

            #simple 15 “Find zones where {sub category/top category} accounts for the highest number of POIs.”
            "Show me zones where sub category {Beauty Salons} is the singular most common POI type.",
            "I'm looking for areas where sub category {Full-Service Restaurants} is the dominant sub category in terms of POI count.",
            "Find zones where the singular most common POI type is sub category {Snack and Nonalcoholic Beverage Bars}.",
            "Can you highlight areas where sub category {Offices of Dentists} outnumber all other sub categories?",
            "I'm trying to find zones where the leading POI sub category is {Gasoline Stations with Convenience Stores}.",
            "Identify zones where sub category {Art Dealers} appears more than any other.",
            "Locate zones where sub category {Educational Support Services} is the singular top POI type by count.",
            "I want to explore areas where sub category {Exam Preparation and Tutoring} is the most frequent POI type.",
            "Find areas where POIs from sub category {Other Personal Care Services} are the most prevalent.",
            "Looking for zones where sub category {Full-Service Restaurants} outnumber every other sub category.",
            "Find zones where top category {Personal Care Services} makes up the majority of POIs.",
            "Show me areas where the dominant POI top category is {Restaurants and Other Eating Places}.",
            "I'm interested in zones where {Offices of Physicians} is the most common top category.",
            "Locate zones where POIs under sub category {Educational Support Services} appear more than any other top category.",
            "Highlight areas where the singular leading POIs fall under top category {Other Schools and Instruction}.",
            "I'm looking for zones where {Offices of Real Estate Agents and Brokers} is the singular top POI category.",
            "Can you find areas where top category {Legal Services} dominates the POI landscape?",
            "Identify zones where most POIs fall under top category {Gasoline Stations}.",
            "Where does top category {Advertising, Public Relations, and Related Services} outnumber the rest?",
            "Explore zones where {Other Amusement and Recreation Industries} is the singular most common top category.",


            
            #simple 16
            #Find zones where at least {num}% of total spend comes from {top category/sub category}.
            "I want to open a medical clinic where over 50% of the total spending in 2023 comes from top category {Offices of Physicians}.",
            "Find zones where at least 40% of the transaction volume in 2022 is from sub category {Couriers and Express Delivery Services}.",
            "Show me areas where 60% of the total dollars spent in 2023 went to top category {Legal Services}.",
            "I’m targeting zones where over 35% of the total sales in 2022 come from sub category {Used Car Dealers}.",
            "Looking for regions where 45% of all customers in 2023 interacted with sub category {Offices of Lawyers}.",
            "Where in the city does top category {Other Amusement and Recreation Industries} contribute over 55% of the spending in 2022?",
            "Highlight zones where 30% of the spending in 2023 came from sub category {Fitness and Recreational Sports Centers}.",
            "I need locations where 70% of all visits in 2023 were to sub category {Offices of Dentists}.",
            "Show zones where top category {Automobile Dealers} accounts for at least 25% of all spend purchases in 2023.",
            "Are there any zones where half of all 2023 spending came from sub category {Nature Parks and Other Similar Institutions}?",
            "I’m looking to launch a grocery business in a zone where top category {Grocery Stores} make up 65%+ of total spending in 2022.",
            "Find areas where sub category {Residential Property Managers} contributed at least 33% of total dollars spent in 2023.",
            "Find zones where nearly 55% of customer traffic in 2022 was driven by sub category {Investment Advice}.",
            "Are there areas where over 45% of total dollars spent in 2023 went to sub category {Drinking Places (Alcoholic Beverages)}?",
            "Which zones in the city had over 70% of spending in 2022 from sub category {Offices of Dentists}?",
            "I want to focus on neighborhoods where most 2022 revenue — at least 60% — came from top category {Lessors of Real Estate}.",
            "Help me identify locations where sub catgeory {Child and Youth Services} contributed 30%+ of all 2023 transactions.",
            "Where did top category {Legal Services} represent at least 50% of total purchases in 2023?",
            "I need zones where more than 42% of total spending in 2022 came from sub category {Offices of Physicians, Mental Health Specialists}.",
            "Find me neighborhoods where 38% of total dollars spent in 2023 came from sub category {Civic and Social Organizations}.",



            #simple 17" Filter for zones that contain at least {num} POIs total."
            "Show me areas that contain at least 25 POIs — I'm planning a community café there.",
            "I need a zone with a minimum of 20 places of interest for my coworking space idea.",
            "Which zones have at least 15 establishments? I'm considering setting up a fitness studio.",
            "I want to find areas where there are at least 60 POIs — good for foot traffic and visibility.",
            "I'm launching a pet grooming service and need a zone with 20 or more active businesses.",
            "Highlight zones that have 5+ POIs total — I want a lively place for a music lounge.",
            "Looking to open a tutoring center — show me areas with at least 12 total POIs.",
            "Where can I find a district with 18 or more POIs? I want to build a local clinic.",
            "I want to target zones that have at least 50 POIs total — suitable for a multi-use space.",
            "Find me neighborhoods where 22 or more points of interest are present for my bookstore café.",
            "Looking for commercial zones with 30 or more POIs — ideal for launching a bike rental station.",
            "Are there any places with at least 16 POIs? I need it for a vegan food truck base.",
            "Which areas have 70+ POIs total? Planning to open a market stall there.",
            "I need a zone with a minimum of 27 POIs to launch a local makerspace.",
            "Filter for districts with at least 45 businesses — I want to test a new dessert bar.",
            "Show me urban areas with at least 13 POIs — could be good for my art gallery.",
            "I'm scouting for regions with no fewer than 38 POIs to open an event planning office.",
            "I want to explore neighborhoods with at least 19 active POIs to launch a consulting firm.",
            "Help me locate a zone with a minimum of 33 total POIs for a shared office incubator.",

            #simple 18 "Show me zones where no single {top category/sub category} makes up more than {num}% of POIs."
            "I want areas where top category {Offices of Physicians} doesn’t dominate more than 15% of POIs.",
            "Show me zones where the sub category {Offices of Lawyers} stays under or at 20%.",
            "Avoid zones where top category {Offices of Physicians} takes up more than 9% of businesses.",
            "Give me zones where no sub category like {Fitness and Recreational Sports Centers} accounts for more than 25%.",
            "Looking for diverse areas—no single top category such as {Offices of Other Health Practitioners} should go above 20%.",
            "I want to skip zones where the sub category {Investment Advice} represents more than 60% of POIs.",
            "Highlight zones where the largest top category like {Legal Services} stays below 45%.",
            "I’m looking for zones where sub category {Nature Parks and Other Similar Institutions} never goes over 35%.",
            "Only show me zones where top category {Management of Companies and Enterprises} is below 30%.",
            "Are there any areas where sub category {Residential Property Managers} doesn’t exceed 40% of the zone?",
            "I’m interested in zones where sub category {Used Car Dealers} stays under 20% representation.",
            "Avoid zones with top category {Offices of Real Estate Agents and Brokers} occupying more than 33%.",
            "Look for areas where the sub category {Child and Youth Services} maxes out at 30%.",
            "Give me zones where top category {Museums, Historical Sites, and Similar Institutions} doesn’t go over 25%.",
            "I’m avoiding zones where sub category {Civic and Social Organizations} exceeds 45% of POIs.",
            "Find zones where the sub category {All Other Amusement and Recreation Industries} is below 20%.",
            "Are there areas where the top category {Offices of Physicians} stays under 13%?",
            "Look for zones where no sub category like {Corporate, Subsidiary, and Regional Managing Offices} makes up more than 30%.",
            "Show me areas where the top category {Couriers and Express Delivery Services} doesn’t exceed 20%.",

            #Medium 1: "I’m looking for zones where {raw total spend, raw num transactions, raw num customers} from {year start} to {year end} was more than {num}.", (simple 5)
            "I’m looking for zones where raw total spend from 2019 to 2021 was more than $22 million.",
            "Identify areas where over 400,000 transactions took place between 2020 and 2022.",
            "Show me zones with at least 150,000 unique customers across the years 2021 to 2023.",
            "Analyze zones where raw total spend from 2020 to 2022 exceeded $18 million.",
            "Can you find districts that had more than 500,000 transactions from 2019 through 2021?",
            "I want to look at zones where the number of customers from 2021 to 2024 went beyond 300,000.",
            "Find areas with raw total spend above $60 million for the years 2020 through 2023.",
            "Highlight zones that had more than 700,000 transactions from 2019 to 2021.",
            "Show me locations with over 250,000 unique customers during the years 2020 to 2022.",
            "I’m looking for zones where raw total spend from 2020 to 2023 was more than $35 million.",
            "Identify districts with over 250,000 unique customers between 2021 and 2024.",
            "Show me areas where raw num transactions exceeded 500,000 across 2019 to 2022.",
            "Find zones where the number of customers from 2020 through 2022 surpassed 200,000.",
            "Analyze regions where raw total spend from 2019 to 2021 was over $40 million.",
            "Can you find zones where there were more than 350,000 transactions between 2021 and 2023?",
            "I want to examine zones where raw num customers from 2020 to 2023 was greater than 280,000.",
            "Filter for zones where raw total spend exceeded $55 million between 2019 and 2022.",
            "Highlight areas where there were more than 160,000 unique customers from 2021 to 2024.",
            "Search for zones where raw num transactions topped 600,000 from 2020 through 2023.",
            "I'm trying to identify zones where total spend was above $40 million between 2021 and 2023.",

            ##Medium 2: "I’m looking for zones where {'MEDIAN_SPEND_PER_TRANSACTION', 'MEDIAN_SPEND_PER_CUSTOMER', 'SPEND_PCT_CHANGE_VS_PREV_YEAR'} from {year start} to {year end} was more than {num}.", (simple 5)
            "Looking for zones where the average median spend per transaction from 2020 to 2023 was above $45 — aiming for a mid-range retail spot.",
            "Show me areas where the average median spend per customer from 2021 to 2024 was over $300.",
            "Find zones that experienced an average yearly spend decline of less than -5% between 2019 and 2021 — might be a good place to introduce a discount brand.",
            "I want to analyze parts where the average year-over-year spend change from 2020 to 2022 stayed consistently over 20%.",
            "Identify areas where the average median spend per transaction from 2019 to 2021 was more than $70 — targeting upscale shoppers.",
            "Looking at rural zones where the average spend per customer from 2020 to 2023 was at least $225.",
            "Highlight areas with an average year-over-year spend decline of less than -8% from 2021 to 2023 — might indicate underserved demand.",
            "Can you find locations where the average yearly spend growth between 2019 and 2021 was above 6%?",
            "Find zones where the average median spend per customer from 2021 to 2024 exceeded $275 — looking for steady, loyal buyers.",
            "I'm looking for zones where the average median spend per customer from 2020 to 2023 was above $280 — targeting wellness and lifestyle services.",
            "Show me areas where the average yearly spend growth from 2021 to 2024 exceeded 6%.",
            "Identify zones where the average median spend per transaction from 2019 to 2021 was greater than $55 — suitable for a premium casual dining concept.",
            "Find zones where average year-over-year spend change stayed above 10% between 2020 and 2023 — looking for signs of consistent economic growth.",
            "Highlight zones where average median spend per customer from 2021 through 2024 was over $190.",
            "I'm analyzing zones where average yearly spend change dropped below -3% from 2020 to 2022 — could be an opportunity to introduce value-focused services.",
            "Find zones where the average median spend per transaction exceeded $70 between 2021 and 2024.",
            "Look for areas with average year-over-year spend growth consistently greater than 12% from 2020 through 2023.",
            "I'm targeting upscale communities — show me zones where average median spend per customer was above $310 from 2019 to 2022.",
            
            #Medium 3: 2 spend constraints (simple 5)
            "I want to open a brunch spot where median spend per customer was ≤ $22 and yearly transactions ≥ 80,000 in 2023.",
            "Where can I put a BBQ joint? Need areas with 90,000+ yearly customers and ≥ 10% annual spending growth in 2021.",
            "Scouting locations for a vegan cafe - want zones with median spend per transaction ≤ $18 and 5%+ year-over-year spending growth in 2024.",
            "Need to open a convenience store where total transactions ≥ 300,000 and customer spend grew ≥ 7% year-over-year in 2023.",
            "Looking for a location for a food truck park - show me areas with ≥ 15,000 monthly customers and ≤ $9 median spend in 2022.",
            "Planning a bakery - find areas with 10%+ year-over-year spending growth and ≥ 20,000 transactions in 2021.",
            "Want to launch a taco stand where median spend per customer ≤ $14 and year-over-year growth ≥ 12% in 2023.",
            "Narrow down ALL zones to those meeting: 2022 median spend per customer ≤ $18 AND ≥ 8% year-over-year growth. Budget gym chain coming through.",
            "Show ONLY areas with 2023 total spend ≥ 15 million and ≤ 15 median transactions. Warehouse club candidate spots.",
            "Find me zones where 2024 yearly swings exceeded ±30% AND annual growth > 20%.",
            "I'll only consider zones where: 2023 vegan transactions ≥ 5,000/month AND median spend ≥ $22. Plant-based deli incoming.",
            "Zones with 2023 metrics where BOTH transactions ≥ 40,000/month AND median spend ≥ $30. Ritz-Carlton food hall territory.",
            "I'm opening a local bistro — I need zones where median spend per transaction was ≤ $20 and customer count was at least 90,000 in 2023.",
            "Looking for a pop-up juice bar location — show me areas with ≥ 5% year-over-year growth and median spend per customer > $200 in 2022.",
            "Planning to launch a family grill — interested in zones with total spend ≥ $60M and yearly spend growth > 4% in 2021.",
            "Scouting a space for a themed café — I want zones where customer count ≥ 120,000 and median spend per transaction ≤ $17 in 2024.",
            "Seeking a good location for a tea house — need areas with ≥ $45M in total spend and ≥ 300,000 transactions in 2023.",
            "I want to set up a farmer's market — find zones with ≥ 6% year-over-year spend growth and ≤ $22 median spend per customer in 2022.",
            "Launching a soul food kitchen — show me zones where year-over-year spend growth was ≥ 10% and customer count exceeded 150,000 in 2023.",
            "Looking for a dessert bar space — I need zones with ≥ 200,000 transactions and median spend per customer ≤ $18 in 2022.",
            "I’m evaluating zones for a community grocery — I want total spend ≥ $70M and at least 250,000 customers in 2023.",
            "Opening a fast-casual sandwich spot — interested in zones with median spend per transaction ≤ $16 and ≥ 5% year-over-year spending growth in 2021.",

            #Medium 4: simple 2 AND/OR simple 3
            "I’m looking to develop a business plaza—need a zone with at least 5 parking lots and one lot over 9,000 square meters.",
            "Planning to open a medical center, and I want an area that either has at least 6 parking lots or one lot bigger than 12,000 square meters.",
            "I want to build a sports training facility where the zone includes at least 4 parking lots and one of them must exceed 10,000 square meters.",
            "Looking to set up a distribution center—open to zones that either have 3 or more parking lots or one very large lot of at least 15,000 square meters.",
            "Thinking about launching a garden center, but I need at least 2 parking lots and one of them must be larger than 5,000 square meters.",
            "Considering a big-box retail location—must have at least 7 parking lots or one that’s bigger than 13,000 square meters.",
            "I want to build a cultural center, and I’m looking for zones with at least 4 parking lots and one that is over 6,500 square meters.",
            "Looking into developing a regional library—would prefer an area with at least 5 parking lots or one with a parking lot larger than 8,000 square meters.",
            "Planning a new co-working hub—I’m only considering zones that have at least 3 parking lots and one lot larger than 7,500 square meters.",
            "I want to open a logistics hub — the zone must have at least 4 parking lots and one of them needs to exceed 11,000 square meters.",
            "Looking to launch a large-scale garden center — open to zones with 6 or more parking lots or one lot that's at least 13,000 square meters.",
            "I’m scouting for a family recreation center where there are at least 5 parking lots and one is larger than 7,000 square meters.",
            "Planning a multi-use fitness complex — I’m open to zones that either have at least 3 parking lots or one oversized lot of 10,000+ square meters.",
            "Hoping to place a commercial car wash — the area should include at least 4 parking lots and one must be larger than 6,000 square meters.",
            "I’m working on a site for a local farmers' market — the location needs at least 2 parking lots or one that’s over 4,000 square meters.",
            "Looking to build a medical facility — zones with 5 or more parking lots and at least one lot larger than 9,500 square meters are ideal.",
            "Developing a church and community center — the area must include at least 6 parking lots or one over 12,000 square meters.",
            "I want to set up an auto dealership — show me zones with 4 or more parking lots and one that’s at least 10,000 square meters.",
            "Thinking about opening a fulfillment center — seeking zones that have either 3+ parking lots or a single lot larger than 8,000 square meters.",
            "Searching for space to open a performance venue—need at least 6 parking lots or a single one that’s over 10,000 square meters.",


            #Medium 5: simple 1 AND/OR simple 2
            "I'm looking to open a family entertainment center, and I need a parking lot with at least 100 parking spaces that is also larger than 2,000 square meters.",
            "Thinking about launching a big-box retail store—open to any zone that either has a parking lot with 300+ parking spaces or at least one lot over 5,000 square meters.",
            "I want to develop a new sports complex, but only if the site has a parking lot with at least 250 parking spots and a single parking lot bigger than 10,000 square meters.",
            "I'm planning to open a convention center, and I need a parking lot with at least 400 parking spaces that is also larger than 12,000 square meters.",
            "Looking for a site to build a new hospital—must have a parking lot with more than 200 spaces and an area greater than 8,000 square meters.",
            "I want to develop a luxury outlet mall, but only in zones where there’s a parking lot with at least 500 parking spots and over 15,000 square meters in size.",
            "I’m considering building a tech campus, and I need a parking lot with at least 350 parking spaces that’s also larger than 10,000 square meters.",
            "Looking to open a performing arts center—must have a parking lot with no fewer than 180 spaces and a total area above 6,000 square meters.",
            "I want to develop a high-traffic shopping plaza, and I’m only interested in zones with a parking lot offering at least 500 spaces and a footprint larger than 14,000 square meters.",
            "Planning a sports and recreation complex—I need a parking lot that includes over 275 spots and spans at least 9,000 square meters.",
            "Launching a mixed-use development, but the zone must include a parking lot with 220+ spaces and at least 7,500 square meters of area.",
            "Looking into building a university extension campus—I’m targeting zones where a parking lot has at least 300 spaces and covers more than 11,000 square meters.",
            "Thinking of opening a theme restaurant, and I need a parking lot with a minimum of 150 spots and 5,000+ square meters of surface.",
            "I want to construct a logistics center—must include a parking lot with 450+ spaces and at least 13,000 square meters in area.",
            "Searching for land to open a trade show venue—the lot must provide 375 parking spaces and exceed 10,500 square meters.",
            "I’m planning to build a film studio complex, and I need a parking lot with more than 320 parking spots and a minimum size of 9,500 square meters.",

            #Medium 6: simple 1 AND/OR simple 3
            "I’m looking to build a lifestyle center, and I need a zone with at least 4 parking lots, one of which has at least 300 parking spaces.",
            "Planning a sports arena—only considering zones with at least 6 parking lots and one with over 500 parking spaces.",
            "Thinking of opening a regional conference center—must have at least 5 parking lots, with one offering no fewer than 400 spaces.",
            "I want to open a premium outlet village, and I need a zone that includes at least 7 parking lots, with at least one lot providing 600 parking spots.",
            "Looking to develop a modern civic center—I’m targeting areas with a minimum of 3 parking lots and at least one that holds 250 cars.",
            "Scouting locations for a university extension campus—must include 4 or more parking lots, and one must have at least 350 parking spaces.",
            "I'm planning a tech innovation park, and I want at least 5 parking lots, one of which should include over 450 spaces.",
            "Considering building a public market—I need zones that offer at least 6 parking lots, with one having more than 500 parking spaces.",
            "Looking into developing a hotel and convention hub—there must be 3 or more parking lots and at least one accommodating 300+ cars.",
            "I’m exploring sites for a cultural museum — I want zones with at least 5 parking lots or a single lot offering 450+ parking spaces.",
            "Looking to open a recreation complex — I need zones that either have 6 or more parking lots or one large lot with 600 spaces.",
            "Planning a community tech center — show me zones that include 3+ parking lots or one parking lot with more than 300 spots.",
            "I want to launch a city innovation hub — I’m open to areas with 4 or more parking lots or a single lot that can hold 500 vehicles.",
            "Developing a science learning center — must have at least 3 parking lots or one lot with over 350 spaces.",
            "Scouting zones for a sustainable living expo — show me places with 6+ parking lots or one that has 550 or more spaces.",
            "Looking for a location for a civic makerspace — needs either 4 parking lots or one large lot with 450+ capacity.",
            "I'm setting up a business learning hub — open to zones with at least 5 parking lots or a single lot that holds 600 cars.",
            "Thinking of building a regional family center — I’m looking for zones that either offer 3+ parking lots or one that fits at least 300 cars.",
            "Hoping to launch a festival ground—only looking at areas with a minimum of 4 parking lots, one of which holds at least 375 parking spaces.",

            #Medium 7: simple 4 AND/OR simple 6
            "I want to open a clothing store with top category {Other Miscellaneous Store Retailers} and sub category {Art Dealers}. Show me zones with fewer than 4 competitors in the same sub-category and a combined population of at least 15,000 across the zone and its 3 closest neighbors.",
            "Thinking about launching a boutique. Top category: {Personal Care Services}, sub-category: {Beauty Salons}. I'm looking for zones with less than 5 competitors in the same category or where the zone plus 2 nearest neighbors have at least 20,000 people.",
            "I want to open a Korean BBQ restaurant where the total population of my zone and 2 closest zones is at least 18,000, and the number of existing competitors in the same category is fewer than 3.",
            "I want to open a clothing store with top category {Offices of Real Estate Agents and Brokers} and sub category {Offices of Real Estate Agents and Brokers}. Show me zones with fewer than 3 competitors in the same sub-category and no fewer than 12,000 people across the zone and its 2 closest neighbors.",
            "I'm planning to launch a Mediterranean restaurant. I need a zone where there are fewer than 5 similar restaurants in the same category or where the combined population of the zone and 3 nearby zones is at least 25,000.",
            "Looking to open a clothing store with top category {Advertising, Public Relations, and Related Services} and sub category {Advertising Agencies}. Show me zones that either have fewer than 2 competitors in the same category or a combined population at least 8,000 with 2 adjacent zones.",
            "I want to open a Thai restaurant where the zone and its 2 closest neighbors have at least 15,000 residents, and there are less than 4 restaurants in the same sub-category {Full-Service Restaurants} nearby.",
            "Thinking about opening a clothing boutique with top category {Educational Support Services} and sub category {Educational Support Services}. I'm looking for zones with fewer than 3 competitors in the same sub-category and a population of 10,000 or more across my zone and its 3 nearest neighbors.",
            "I want to open a ramen shop. I need a zone that has either fewer than 5 competitors in the same restaurant category or a population total of 18,000+ when including 2 closest neighboring zones.",
            "Looking to build a new upscale clothing store with top category {Legal Services} and sub category {Offices of Lawyers}. I’m searching for zones with fewer than 2 direct competitors and at least 14,000 residents total when combined with 3 neighboring zones.",
            "Planning to launch a family-owned restaurant where the number of competitors in the same sub-category is less than 6 and the population including 2 adjacent zones is 20,000 or more.",
            "I want to open a clothing shop with top category {Other Schools and Instruction} and sub category {Automobile Driving Schools}. Show me zones with fewer than 3 similar businesses or a population total at least 9,000 across my zone and 2 closest neighbors.",
            "Looking into opening a Korean restaurant—interested in zones with fewer than 4 competitors in sub category {Full-Service Restaurants} and more than 16,000+ residents across 2 nearest zones plus mine.",
            "Hoping to open a fashion store with top category {Personal Care Services} and sub category {Beauty Salons}. Show me zones that either have fewer than 3 competitors or a combined population of 10,000+ in the zone and its 2 neighbors.",
            "I'm planning a new Mexican restaurant. I want a location where my zone and 2 nearest neighbors have at least 12,000 people and fewer than 5 competing restaurants in the same sub-category of {Full-Service Restaurants}.",
            "I want to open a clothing outlet with top category {Other Amusement and Recreation Industries} and sub category {All Other Amusement and Recreation Industries}. The zone must have fewer than 4 competitors and a population of at least 13,000 when including 3 neighboring zones.",
            "Looking for a place to open a Vietnamese restaurant—I'd prefer a zone with fewer than 2 competitors in the same category or one with at least 9,000 people across the zone and its 2 neighbors.",
            "Thinking about opening a clothing boutique with top category {Offices of Other Health Practitioners} and sub category {Offices of All Other Miscellaneous Health Practitioners}. Show me zones with less than 3 similar businesses and a minimum combined population of at least 11,000 across 2 neighboring zones.",


            #Medium 8: simple 7 AND/OR simple 9
            "I want to open a ramen restaurant. Show me zones with at least 5 POIs in the top category {Restaurants and Other Eating Places} and at least 3 subway entrances nearby.",
            "Planning a gastropub—I'd like zones with at least 4 POIs in the top category {Drinking Places (Alcoholic Beverages)} and a minimum of 6 nearby bus stops.",
            "I'm scouting areas for a brunch café. I need zones that either have 3+ POIs in the sub category {Full-Service Restaurants} or at least 5 subway entrances within walking distance.",
            "Looking to launch a wine bar. Find me zones that include at least 4 POIs in the top category {Beer, Wine, and Liquor Stores} and also have 4 or more taxi stands nearby.",
            "I'm interested in opening a coffee shop. Show me zones with at least 6 POIs in the top category {Snack and Nonalcoholic Beverage Bars} or a minimum of 5 bus stops in the area.",
            "I want to open a sushi restaurant. Show me zones with at least 5 POIs in the top category {Full-Service Restaurants} and a minimum of 4 subway entrances nearby.",
            "Thinking of launching a lounge bar—I'm looking for areas with at least 3 POIs in the top category {Drinking Places (Alcoholic Beverages)} or 6 or more bus stops nearby.",
            "I want to start a coffee shop. Show me zones with at least 7 POIs in the sub category {Snack and Nonalcoholic Beverage Bars} and at least 5 subway entrances nearby.",
            "Looking to open a steakhouse. I'd prefer zones with at least 6 POIs in the top category {Restaurants and Other Eating Places} or at least 4 nearby taxi stands.",
            "I'm planning a bakery—show me zones with at least 4 POIs in the sub category {Full-Service Restaurants} and a minimum of 3 aerodromes within the area.",
            "Hoping to open a vegan café. I'm searching for zones with 3+ POIs in the top category {Restaurants and Other Eating Places} or 5 bus stops close by.",
            "Scouting areas for a pizza place. I want zones that have at least 4 POIs in the top category {Restaurants and Other Eating Places} and 6 or more taxi stands nearby.",
            "I'm looking to launch a tea house. Show me zones with at least 3 POIs in the sub category {Snack and Nonalcoholic Beverage Bars} or zones with 4 subway entrances.",
            "Thinking about opening a microbrewery—need zones with 4+ POIs in the top category {Beer, Wine, and Liquor Stores} and at least 3 nearby bus stops.",
            "I want to develop a casual dining restaurant. Show me zones with at least 5 POIs in the top category {Full-Service Restaurants} or at least 2 aerodromes within reach.",
            "I want to open a family-style restaurant. Show me zones that include at least 6 POIs in the top category {Full-Service Restaurants} and 4 or more subway entrances.",
            "Opening a brunch café—looking for zones with 3+ POIs in the sub category {Snack and Nonalcoholic Beverage Bars} and at least 3 aerodromes nearby.",
            "I'm interested in opening a wine bistro. Show me zones with at least 4 POIs in the top category {Beer, Wine, and Liquor Stores} or at least 5 nearby bus stops.",
            "Planning a seafood restaurant—show me zones that have at least 5 POIs in the top category {Restaurants and Other Eating Places} and 6 or more taxi stands.",
            "I want to open a salad bar. I’m looking for zones with a minimum of 4 POIs in the top category {Snack and Nonalcoholic Beverage Bars} and at least 2 subway entrances.",
            "Hoping to launch a ramen shop—preferably in areas with at least 3 POIs in the top category {Full-Service Restaurants} or zones with 4 bus stops nearby."

            #Medium 9: simple 9 AND/OR simple 10
            "I'm looking to open a tea shop where there are at least 5 bus stops nearby and the closest bus stop is less than 180 meters from the zone centroid.",
            "Planning a boutique hotel—I'd like zones with at least 4 subway entrances or a subway entrance located within 150 meters of the zone centroid.",
            "I want to open a bookstore where the zone has at least 6 taxi stands and the nearest one is no more than 200 meters from the zone centroid.",
            "I'm looking to open a food truck hub where there are at least 6 bus stops nearby and the nearest one is within 200 meters of the zone centroid.",
            "Planning to launch a small hotel—I'm targeting zones that either have at least 3 subway entrances or one located within 120 meters of the zone centroid.",
            "I want to open a coworking space where the area includes at least 4 taxi stands and the closest one is no more than 250 meters from the zone centroid.",
            "Thinking about setting up a cafe—I'd like zones that have at least 5 bus stops or one within 150 meters of the zone centroid.",
            "I’m planning to build a wellness clinic. Show me zones with 4 or more subway entrances and one that’s under 180 meters away from the zone centroid.",
            "Looking to open a gaming lounge—interested in areas with at least 6 nearby taxi spots or the closest one located within 230 meters of the centroid.",
            "I want to develop a student study space where there are at least 3 bus stops nearby and the closest one is no farther than 190 meters from the centroid.",
            "Thinking of opening a bookstore café—zones with 5+ subway entrances or one within 140 meters of the zone centroid would work best.",
            "Hoping to launch a gelato shop—I'm looking for zones with a minimum of 4 taxi stands and the closest one must be under 220 meters from the centroid.",
            "I'm looking to open a meditation studio where there are at least 4 bus stops nearby AND the nearest one is within 200 meters from the zone centroid.",
            "Planning a coworking café — show me zones with at least 3 subway entrances OR one that’s located within 160 meters of the zone centroid.",
            "Thinking about starting a mobile kitchen hub — interested in zones with 6+ nearby taxi stands AND the closest one no more than 180 meters from the centroid.",
            "I want to build a small community theater — either the zone includes at least 4 subway entrances OR one subway entrance is within 150 meters from the centroid.",
            "Opening a college hangout space — find zones with at least 3 nearby bus stops AND the closest one is under 190 meters from the zone center.",
            "Looking to start a digital nomad retreat — target zones that either have at least 5 taxi stands OR one within 250 meters of the zone centroid.",
            "I’m launching a breakfast bistro where there are at least 6 bus stops AND the closest is located within 170 meters from the centroid.",
            "Planning to open a learning center — want zones with at least 4 subway entrances OR the nearest one is no farther than 180 meters.",
            "Seeking a site for a 24/7 diner — look for zones with 5+ taxi spots nearby AND the nearest is under 200 meters from the zone centroid.",
            "Thinking of building a fitness center — show me zones with at least 4 bus stops OR one bus stop located within 140 meters of the zone centroid.",
            "Looking into a deli. Show me zones that either have 6+ bus stops nearby or one within 180 meters of the zone centroid.",



            #Medium 10: simple 11 AND/OR simple 9
            "I'm planning to open a community café where at least 65% of POIs are within 400 meters of a bus stop and the zone has at least 5 bus stops.",
            "I want to launcht a coworking lounge—preferably in zones with 60% or more POIs within 300 meters of a subway entrance in the zone or areas with at least 4 subway entrances.",
            "Looking to open a bookstore café. Show me zones where at least 70% of POIs are within 500 meters of a station in the zone and there are 3 or more stations.",
            "I'm scouting locations for a craft brewery—interested in zones with 75% of are POIs within 350 meters of a bus stop or zones that include at least 6 bus stops.",
            "I want to set up a vegan restaurant in a zone where 80% of POIs are within 400 meters of a subway entrance and the area includes no fewer than 4 subway entrances.",
            "I'm looking to open a community theater where at least 70% of POIs are within 400 meters of a subway entrance and there are at least 3 subway entrances nearby.",
            "I want to launch a small music venue in a zone where 60% or more of POIs are within 300 meters of a station or the area includes at least 4 stations.",
            "Planning to open a café-bookstore hybrid—I'm targeting zones where at least 75% of POIs are within 350 meters of a bus stop and the zone has at least 5 bus stops nearby.",
            "Thinking of launching a boutique wine bar. Show me zones with 65% of POIs within 300 meters of a subway entrance or 4 or more nearby subway entrances.",
            "I'd like to set up a coworking studio in an area where 80% of POIs are within 450 meters of a station and there are at least 6 stations nearby.",
            "Looking into opening a vegan café—interested in zones where 70% of POIs are within 400 meters of a bus stop or the area includes 5 or more bus stops.",
            "I'm hoping to open a dog-friendly coffee shop in zones where 60%+ of POIs are within 250 meters of a taxi stop and the zone has at least 4 taxi stops.",
            "I want to open a late-night ramen shop—show me zones where 65% of POIs are within 300 meters of a subway entrance and there are at least 3 subway entrances nearby.",
            "Planning a mobile food court. I'm looking for areas where at least 70% of POIs fall within 350 meters of a bus stop or the zone includes 6+ bus stops.",
            "Opening a fine-dining restaurant—interested in zones where 80% of POIs are within 500 meters of a station and there are at least 5 stations nearby.",
            "I'm launching a smoothie bar. Show me areas where at least 60% of POIs are within 300 meters of a taxi stop or zones that have 4 or more taxi spots.",
            "I want to open an upscale bakery—need a zone where at least 75% of POIs are within 400 meters of a subway entrance and there are at least 5 subway entrances nearby.",
            "Thinking of building a tech incubator. I want zones where 70%+ of POIs are within 350 meters of a station or zones with at least 4 stations.",
            "I'm planning to open a small jazz club where 80% of POIs are within 450 meters of a bus stop and the zone includes no fewer than 5 bus stops.",
            "Considering a themed diner—find me zones where at least 60% of POIs are within 250 meters of a taxi stand or zones that include 3 or more taxi stops.",
            "I want to open a bookstore café in a zone where 70% of POIs are within 400 meters of a station and the zone has 4 or more stations nearby.",
            "Launching a handmade goods market—I'm looking for areas with 65%+ of POIs within 300 meters of a bus stop or at least 5 bus stops in the vicinity.",
            "I want to build a plant-based brunch spot where at least 75% of POIs are within 350 meters of a subway entrance and there are at least 6 subway entrances nearby.",
            "Planning to open a night market—show me zones where at least 60% of POIs are within 250 meters of a taxi stop or the area includes 4+ taxi stands.",
            "Looking to launch a casual food court where 80% of POIs are within 450 meters of a bus stop and the area includes at least 5 bus stops.",

            #Medium 11: simple 4 AND/OR simple 3
            "I want to open a clothing store with top category {Personal Care Services} and sub category {Beauty Salons}. Show me zones with fewer than 3 competitors in the same category and at least 2 parking lots.",
            "Thinking about launching a boutique. Top category: {Other Amusement and Recreation Industries}, sub-category: {Fitness and Recreational Sports Centers}. I need a zone with fewer than 4 competitors or at least 3 parking lots in the area.",
            "Looking to open a clothing store with top category {Offices of Other Health Practitioners} and sub category {Offices of All Other Miscellaneous Health Practitioners}. Find me a zone with fewer than 2 competitors and at least 2 parking lots.",
            "I want to launch a fashion outlet. Top category: {Other Miscellaneous Store Retailers}, sub-category: {Art Dealers}. Show me zones with fewer than 5 competitors or zones with 4 or more parking lots.",
            "Planning to set up a sustainable clothing store. I want zones with fewer than 3 competitors in the same sub-category and a minimum of 3 parking lots nearby.",
            "I'm interested in opening a thrift store with top category {Educational Support Services} and sub category {Educational Support Services}. Show me zones with fewer than 4 competitors or areas that offer at least 2 parking lots.",
            "Looking to start a clothing store. Top category: {Advertising, Public Relations, and Related Services}, sub-category: {Advertising Agencies}. I want zones that have fewer than 2 competitors and at least 3 parking lots.",
            "I want to open a vintage clothing store with top category {Legal Services} and sub category {Offices of Lawyers}. Find me zones with fewer than 3 competitors or a zone that includes at least 5 parking lots.",
            "Opening a denim-focused clothing shop with top category {Offices of Real Estate Agents and Brokers} and sub category {Offices of Real Estate Agents and Brokers}. I'm looking for zones with fewer than 3 competitors and at least 4 parking lots in the area.",
            "Planning a trendy clothing store—top category {Other Schools and Instruction}, sub category {Automobile Driving Schools}. I want zones with fewer than 3 competitors or at least 2 parking lots nearby.",
            "I want to open a clothing store with top category {Personal Care Services} and sub category {Beauty Salons}. Show me zones that do NOT have more than 4 competitors and have at least 3 parking lots.",
            "Looking to launch a fashion brand—top category {Offices of Real Estate Agents and Brokers}, sub-category {Offices of Real Estate Agents and Brokers}. I want a zone that does NOT have fewer than 2 parking lots and has fewer than 5 competitors.",
            "Thinking of opening a minimalist clothing store with top category {Educational Support Services} and sub category {Educational Support Services}. Find zones that do NOT have more than 3 competitors and include at least 4 parking lots.",
            "I want to set up a streetwear shop—top category {Advertising, Public Relations, and Related Services}, sub-category {Advertising Agencies}. Show me zones with fewer than 4 competitors and NOT fewer than 3 parking lots.",
            "Planning a high-end boutique with top category {Other Amusement and Recreation Industries} and sub category {Fitness and Recreational Sports Centers}. I'm looking for zones that do NOT include more than 2 competitors or zones with at least 5 parking lots.",
            "Launching a thrift shop with top category {Legal Services} and sub category {Offices of Lawyers}. Find me zones that do NOT have more than 3 competitors and have no fewer than 2 parking lots.",
            "I want to open a modern apparel shop—top category {Other Miscellaneous Store Retailers}, sub-category {Art Dealers}. Show me areas that do NOT include more than 4 competitors and have 3 or more parking lots.",
            "Opening a tailoring studio—I'm looking for zones with fewer than 3 competitors in top category {Personal Care Services} and at least 2 nearby parking lots.",
            "I want to open a concept store—top category: {Educational Support Services}, sub-category: {Educational Support Services}. Zones with fewer than 4 competitors or at least 3 parking lots work for me.",
            "Thinking of starting a lifestyle brand. Show me zones with fewer than 2 competitors in {Legal Services} and a minimum of 4 parking lots.", 
            "Looking to launch a design atelier in zones with fewer than 3 businesses under top category {Advertising, Public Relations, and Related Services} or at least 3 parking lots in the area.", 
            "I’m scouting for a location for a consignment shop. I need fewer than 5 competitors in top category {Other Miscellaneous Store Retailers} and at least 2 parking lots.", 
            "I want to build a creative studio—top category: {Other Amusement and Recreation Industries}, sub-category: {Fitness and Recreational Sports Centers}. Give me zones with fewer than 4 competitors or 3 or more parking lots.", 

            #Medium 12: simple 6 AND/OR simple 7
            "I want to open a tapas restaurant where my zone and 2 closest neighbors have a total population of at least 15,000 and the area includes at least 5 POIs in the top category {Full-Service Restaurants}.",
            "Thinking of launching a speakeasy bar—I'm looking for zones that either have 3+ POIs in the sub category {Drinking Places (Alcoholic Beverages)} or where the population of the zone plus 2 nearby zones exceeds 12,000.",
            "Looking to open a ramen shop. Show me areas with a combined population of at least 20,000 from my zone and 3 neighbors and at least 6 POIs in the category {Restaurants and Other Eating Places}.",
            "I'm planning to open a vegan café—targeting zones that have 4 or more POIs in the sub category {Snack and Nonalcoholic Beverage Bars} or where the total population across the zone and 2 nearby ones is at least 10,000.",
            "I want to start a sushi restaurant where my zone plus 3 closest neighbors have a combined population of 18,000 and at least 5 POIs in the sub category {Full-Service Restaurants}.",
            "Thinking of opening a dessert bar—I'm looking for zones with at least 3 sub category {Snack and Nonalcoholic Beverage Bars} or 2 nearest neighbors plus my zone having at least 9,000 residents total.",
            "Looking to open a craft beer taproom. Show me zones where there are 4+ POIs in sub category {Drinking Places (Alcoholic Beverages)} and the total population of the zone and its 2 neighbors is no less than 14,000.",
            "I'm hoping to open a breakfast café—interested in zones that either have 5 or more POIs in the sub category {Full-Service Restaurants} or where the zone plus 2 closest neighbors have a population of 11,000 or more.",
            "I want to launch a casual dining spot in a zone where the total population with 3 neighboring zones is above 17,000 and there are at least 6 POIs in the top category {Restaurants and Other Eating Places}.",
            "Planning to open a trendy wine bar—show me zones with 5+ {Beer, Wine, and Liquor Stores} in the top category or a combined population of 20,000 across the zone and 2 nearby ones.",
            "I'm planning to open a gastropub. Show me zones where the combined population of my zone and 2 neighbors is not less than 12,000 and where there are not fewer than 4 POIs in the top category {Drinking Places (Alcoholic Beverages)}.",
            "Thinking of opening a taco shop—I'm looking for zones that do NOT have fewer than 10,000 residents across 3 nearby zones and include at least 5 POIs in the sub category {Full-Service Restaurants}.",
            "I want to open a vegan brunch café in a zone where the number of POIs in sub category {Snack and Nonalcoholic Beverage Bars} is not less than 4 and the combined population with 2 nearest zones is at least 11,000.",
            "Looking to open a food hall—interested in zones that do NOT have fewer than 6 POIs in the top category {Restaurants and Other Eating Places} and have a zone-plus-neighbors population of no less than 15,000.",
            "I'm launching a wine bistro. Show me zones where there are not fewer than 3 POIs in {Beer, Wine, and Liquor Stores} and the total population with 2 adjacent zones is not below 10,000.",
            "Considering a breakfast diner—looking for zones that either have 5+ POIs in the sub category {Full-Service Restaurants} or where my zone and 3 closest neighbors have NOT less than 13,000 residents.",
            "Planning to open a noodle bar. I want zones that include NOT fewer than 4 POIs in top category {Restaurants and Other Eating Places} and have a minimum population of 9,000 across my zone and two neighbors.",
            "Thinking about launching a smoothie shop where the zone and its 2 closest neighbors have NOT less than 12,500 residents and the area has 4 or more POIs in the sub category {Snack and Nonalcoholic Beverage Bars}.",
            "Looking for a spot to open a family-style restaurant. I'm targeting zones with not less than 14,000 residents (zone + 3 neighbors) and not fewer than 5 POIs in the top category {Full-Service Restaurants}.",
            "I want to start a Mediterranean café—zones with NOT fewer than 3 top category {Restaurants and Other Eating Places} and a combined population of no less than 10,000 with nearby zones.",

            #Medium 13: simple 8 AND/OR simple 10
            "I'm scouting locations for a high-traffic salon and retail space. Show me zones with at least 10 POIs in the sub-categories {Beauty Salons} or {Women's Clothing Stores}, and where the nearest bus stop is under 200 meters from the zone centroid.",
            "Looking to build a late-night food plaza—find me zones with 12+ POIs in sub category {Drinking Places (Alcoholic Beverages)} and {Snack and Nonalcoholic Beverage Bars}, and where the nearest subway entrance is less than 150 meters away.",
            "I want to open a hybrid tattoo parlor and juice bar. I need zones with at least 8 POIs in the categories {Beauty Salons} and {Snack and Nonalcoholic Beverage Bars}, and a taxi stop within 180 meters from the zone centroid.",
            "Thinking of launching a wellness and café combo—show me zones with 10+ POIs in {Beauty Salons} or {Snack and Nonalcoholic Beverage Bars}, and where the closest bus stop is less than 200 meters away.",
            "I want to start a nightlife venue—looking for areas with at least 14 POIs in {Drinking Places (Alcoholic Beverages)} and {Snack and Nonalcoholic Beverage Bars}, and the nearest station under 250 meters from the centroid.",
            "Opening a boutique gym and smoothie shop—show me zones with 9 or more POIs in {Fitness and Recreational Sports Centers} and {Snack and Nonalcoholic Beverage Bars}, and the closest subway entrance within 200 meters of the centroid.",
            "I'm scouting for a fashion-retail concept store. I need zones with at least 7 POIs in {Women's Clothing Stores} and {Beauty Salons}, and a bus stop within 150 meters of the zone centroid.",
            "Planning a food-and-drinks district—find me zones with a combined 11 POIs in {Drinking Places (Alcoholic Beverages)} and {Full-Service Restaurants}, and a taxi stand no more than 180 meters from the centroid.",
            "I'm opening a premium self-care hub. Show me zones with at least 10 POIs in {Beauty Salons} and a subway stop under 200 meters from the zone center.",
            "Looking to launch a late-night dessert lounge—show me zones with 8+ POIs in {Snack and Nonalcoholic Beverage Bars} and a bus stop less than 170 meters away from the centroid.",
            "I'm planning a beauty and wellness studio—show me zones with at least 9 POIs in {Beauty Salons} or {Other Personal Care Services}, and the nearest bus stop must be within 150 meters from the zone centroid.",
            "Looking to set up a cocktail and tapas bar—need zones with 10+ POIs in {Drinking Places (Alcoholic Beverages)} and {Full-Service Restaurants}, and a subway entrance less than 200 meters from the centroid.",
            "I want to open a fashion and beauty hub. Show me zones with 12 or more POIs in {Women's Clothing Stores} and {Beauty Salons}, and where the closest station is under 120 meters away.",
            "Scouting zones for a snack café and community market—must have at least 7 POIs in {Snack and Nonalcoholic Beverage Bars} and {Full-Service Restaurants}, and a nearby bus stop within 170 meters of the centroid.",
            "I’m looking to open a nightlife corner—zones with at least 13 POIs in {Drinking Places (Alcoholic Beverages)} and a station under 250 meters from the centroid would be ideal.",
            "Interested in starting a boutique gym and juice lounge. I want zones with 8+ POIs in {Fitness and Recreational Sports Centers} or {Snack and Nonalcoholic Beverage Bars}, and a taxi stand within 180 meters of the centroid.",
            "I want to launch a self-care pop-up. Find me zones with no fewer than 10 POIs in {Beauty Salons}, and the nearest bus stop must be under 200 meters from the zone centroid.",
            "Thinking of setting up a cocktail bar and dance venue. I’m targeting zones with 11+ POIs in {Drinking Places (Alcoholic Beverages)} or {Snack and Nonalcoholic Beverage Bars}, and a subway stop less than 150 meters away.",
            "I'm opening a skincare bar—looking for zones with 9 POIs in {Beauty Salons} or {Other Personal Care Services} and a taxi stop within 200 meters from the centroid.",
            "Launching a streetwear + beauty hybrid. I want zones that include at least 8 POIs in {Women's Clothing Stores} and {Beauty Salons}, and have a bus stop within 170 meters from the zone centroid.",

            #Medium 14: Find zones in {city}, {state} where at least {num}% of total  {raw total spend, raw num transactions, raw num customers}  comes from {top category}
            "Find zones where at least 35% of total raw total spend in 2020 comes from top category {Restaurants and Other Eating Places}.",
            "Show me zones where 40% or more of raw num transactions in 2021 come from top category {Gasoline Stations}.",
            "I’m looking for areas where at least 30% of total raw num customers in 2022 are from top category {Personal Care Services}.",
            "Identify zones where 50% or more of the total raw total spend in 2023 is attributed to top category {Offices of Physicians}.",
            "Filter zones where at least 45% of total raw num transactions in 2024 come from top category {Beer, Wine, and Liquor Stores}.",
            "Find me zones where at least 60% of the raw num customers in 2022 are tied to top category {Offices of Other Health Practitioners}.",
            "Looking for zones where at least 55% of raw total spend in 2021 is generated by top category {Advertising, Public Relations, and Related Services}.",
            "Show me zones where at least 50% of raw num transactions in 2020 are linked to top category {Full-Service Restaurants}.",
            "Highlight areas where 40% or more of total raw num customers in 2023 come from top category {Other Schools and Instruction}.",
            "I want zones where at least 35% of the raw total spend in 2019 is driven by top category {Legal Services}.",
            "Show me zones where 45% or more of raw num transactions in 2024 come from top category {Restaurants and Other Eating Places} and sub category {Full-Service Restaurants}.",
            "I’m looking for zones where at least 35% of raw num customers in 2021 are linked to top category {Offices of Physicians} and sub category {Offices of Physicians (except Mental Health Specialists)}.",
            "Identify areas where 50% or more of raw total spend in 2023 is driven by top category {Advertising, Public Relations, and Related Services} and sub category {Advertising Agencies}.",
            "Filter zones where at least 30% of raw num transactions in 2020 come from top category {Educational Support Services} and sub category {Educational Support Services}.",
            "Find me zones where at least 40% of raw num customers in 2022 are served by top category {Real Estate} and sub category {Offices of Real Estate Agents and Brokers}.",
            "Looking to identify zones where 60% or more of total raw total spend in 2024 is from top category {Health Care} and sub category {Offices of Dentists}.",
            "Show me zones where 50% or more of raw num transactions in 2019 come from top category {Food Services} and sub category {Snack and Nonalcoholic Beverage Bars}.",
            "Highlight zones where at least 55% of raw total spend in 2021 comes from top category {Religious, Grantmaking, Civic, Professional, and Similar Organizations} and sub category {Religious Organizations}.",
            "I want zones where 35% or more of raw num customers in 2020 are associated with top category {Educational Services} and sub category {Exam Preparation and Tutoring}.",

            #Medium 15: simple 17 AND/OR simple 18
            "Show me places where top category {Management of Companies and Enterprises} doesn't exceed 30% and there are at least 13 POIs.",
            "Show me places where top category {Software Publishers} doesn't exceed 30% and there are at least 5 POIs.",
            "I need zones that have at least 22 POIs and less than 20% in top category {Drinking Places (Alcoholic Beverages)}.",
            "Find zones with at least 8 POIs and no more than 20% from top category {Management of Companies and Enterprises}.",
            "I'm targeting zones where at least 24 POIs exist and fewer than 35% are from {Scheduled Passenger Air Transportation}.",
            "Help me locate zones with over 30 POIs, but top category {Medical and Diagnostic Laboratories} should be below 40%.",
            "I'm targeting zones where at least 23 POIs exist and fewer than 10% are from {Corporate, Subsidiary, and Regional Managing Offices}.",
            "I'm only interested in zones with 8+ POIs and not more than 40% tied to {Advertising, Public Relations, and Related Services}.",
            "Show me areas with 30+ POIs where sub category {Software Publishers} isn't too dominant — under 35%.",
            "Show me areas with 19+ POIs where sub category {Environment, Conservation and Wildlife Organizations} isn't too dominant — under 35%.",
            "Find zones with at least 27 POIs and no more than 10% from sub category {Software Publishers}.",
            "I need zones that have at least 13 POIs and less than 10% in top category {Offices of Other Health Practitioners}.",
            "Show me places where top category {Restaurants and Other Eating Places} doesn't exceed 35% and there are at least 29 POIs.",
            "I'm only interested in zones with 26+ POIs and not more than 25% tied to {Urban Transit Systems}.",
            "I'm targeting zones where at least 5 POIs exist and fewer than 30% are from {Offices of Lawyers}.",
            "Show me places where top category {Software Publishers} doesn't exceed 25% and there are at least 14 POIs.",
            "Seeking areas with lots of POIs — minimum 17 — and less than 20% from {Justice, Public Order, and Safety Activities}.",
            "Show me places where top category {Scheduled Air Transportation} doesn't exceed 25% and there are at least 26 POIs.", # I STARTED HERE
            "I'm only interested in zones with 26+ POIs and not more than 25% tied to {Software Publishers}.",
            "I'm targeting zones where at least 20 POIs exist and fewer than 20% are from {Investment Advice}.",
            "I'm only interested in zones with 5+ POIs and not more than 30% tied to {Scheduled Air Transportation}.",
            "I'm only interested in zones with 17+ POIs and not more than 35% tied to {Medical and Diagnostic Laboratories}.",
            "I need zones that have at least 30 POIs and less than 30% in top category {Offices of Physicians}.",
            "I'm hoping to find zones that have at least 22 POIs, but no more than 10% are from sub category {Lessors of Residential Buildings and Dwellings}.",
            "Looking for regions with over 6 POIs and sub category {Scheduled Passenger Air Transportation} capped at 40%.",
            "Seeking areas with lots of POIs — minimum 12 — and less than 25% from {Offices of Physicians}.",
            "Find me zones with a healthy mix — 20 or more POIs, and no more than 20% from sub category {Commuter Rail Systems}.",
            "I'm targeting zones where at least 21 POIs exist and fewer than 40% are from {Corporate, Subsidiary, and Regional Managing Offices}.",
            "I need zones that have at least 15 POIs and less than 20% in top category {Legal Services}.",
            "I'm okay with zones that either have at least 20 POIs or have sub category {Commuter Rail Systems} under 20%.",
            "A zone with 8+ POIs or with top category {Advertising, Public Relations, and Related Services} below 40% is fine.",
            "A zone with 30+ POIs or with top category {Medical and Diagnostic Laboratories} below 40% is fine.",
            "Either make sure there are 30 POIs, or top category {Offices of Physicians} is under 30%.",
            "I'm open to any area with enough POIs — say 26 — or where top category {Software Publishers} isn't too dominant, like under 25%.",
            "Either make sure there are 14 POIs, or top category {Software Publishers} is under 25%.",
            "Either give me zones with 24+ POIs, or ones where {Scheduled Passenger Air Transportation} stays below 35%.",
            "Either give me zones with 6+ POIs, or ones where {Scheduled Passenger Air Transportation} stays below 40%.",
            "I'm open to any area with enough POIs — say 17 — or where top category {Justice, Public Order, and Safety Activities} isn't too dominant, like under 20%.",
            "A zone with 29+ POIs or with top category {Restaurants and Other Eating Places} below 35% is fine.",



            #Medium 16:simple 3 AND/OR simple 16
            'Looking to build a spa — find me areas where sub category {Advertising Agencies} dominates at least 40% of 2024 spend or has 2+ parking spots.',
            'Want to open a coffee lounge in a spot where sub category {Full-Service Restaurants} is strong — 50%+ of spend in 2022 — or somewhere with 4 parking spaces.',
            "I'm opening a family clinic and want zones where at least 60% of 2022 spending comes from sub category {Offices of Dentists} AND there's space for at least 2 parking lots.",
            'Looking to build a spa — find me areas where sub category {Advertising Agencies} dominates at least 60% of 2024 spend or has 3+ parking spots.',
            "I'm exploring locations for a tutoring center — it should either have 30%+ of 2019's spend from top category {Legal Services} or decent parking: at least 2 lots.",
            "I'm opening a family clinic and want zones where at least 30% of 2020 spending comes from sub category {Offices of Dentists} AND there's space for at least 2 parking lots.",
            "I'm exploring locations for a tutoring center — it should either have 60%+ of 2023's spend from top category {Beer, Wine, and Liquor Stores} or decent parking: at least 5 lots.",
            "I'm opening a family clinic and want zones where at least 30% of 2019 spending comes from sub category {Offices of Real Estate Agents and Brokers} OR there's space for at least 4 parking lots.",
            'Planning a studio — ideally in places where sub category {Full-Service Restaurants} covers at least 60% of 2021 spending AND the zone has 3 or more parking lots.',
            "Trying to set up a restaurant — zones where top category {Restaurants and Other Eating Places} makes up 60%+ of 2019's spend or has 6+ parking spots would be ideal.",
            'Find me zones where top category {Restaurants and Other Eating Places} accounts for 30%+ of spending in 2021 AND there are at least 5 parking lots nearby.',
            "Trying to set up a restaurant — zones where top category {Legal Services} makes up 60%+ of 2019's spend or has 2+ parking spots would be ideal.",
            'I need a spot where top category {Beer, Wine, and Liquor Stores} dominates the market with at least 30% spend in 2019 AND 3+ parking options.',
            "Trying to set up a restaurant — zones where top category {Educational Support Services} makes up 60%+ of 2022's spend or has 5+ parking spots would be ideal.",
            'Want to open a coffee lounge in a spot where sub category {Offices of Real Estate Agents and Brokers} is strong — 50%+ of spend in 2024 — or somewhere with 3 parking spaces.',
            "I'm exploring locations for a tutoring center — it should either have 40%+ of 2022's spend from top category {Beer, Wine, and Liquor Stores} or decent parking: at least 4 lots.",
            'Want to open a coffee lounge in a spot where sub category {Full-Service Restaurants} is strong — 40%+ of spend in 2024 — or somewhere with 5 parking spaces.',
            'Planning a studio — ideally in places where sub category {Offices of Real Estate Agents and Brokers} covers at least 40% of 2021 spending OR the zone has 3 or more parking lots.',
            'I need a spot where top category {Educational Support Services} dominates the market with at least 50% spend in 2019 AND 2+ parking options.',
            'Planning a studio — ideally in places where sub category {Full-Service Restaurants} covers at least 60% of 2020 spending OR the zone has 4 or more parking lots.',
            "Trying to set up a restaurant — zones where top category {Restaurants and Other Eating Places} makes up 40%+ of 2023's spend or has 2+ parking spots would be ideal.",
            "I'm fine with zones where sub category {Full-Service Restaurants} takes up at least 30% of 2019's spend or where there's solid parking availability — say 2 lots.",
            "Trying to set up a restaurant — zones where top category {Educational Support Services} makes up 30%+ of 2021's spend or has 2+ parking spots would be ideal.",
            "I'm fine with zones where sub category {Offices of Real Estate Agents and Brokers} takes up at least 40% of 2022's spend or where there's solid parking availability — say 6 lots.",
            "I'm opening a family clinic and want zones where at least 40% of 2024 spending comes from sub category {Full-Service Restaurants} AND there's space for at least 4 parking lots.",
            "Trying to set up a restaurant — zones where top category {Beer, Wine, and Liquor Stores} makes up 50%+ of 2024's spend or has 3+ parking spots would be ideal.",
            'I need a spot where top category {Legal Services} dominates the market with at least 60% spend in 2020 OR 5+ parking options.',
            'Want to open a coffee lounge in a spot where sub category {Beauty Salons} is strong — 30%+ of spend in 2023 — or somewhere with 4 parking spaces.',
            "Trying to set up a restaurant — zones where top category {Advertising, Public Relations, and Related Services} makes up 40%+ of 2020's spend or has 2+ parking spots would be ideal.",
            "I'm fine with zones where sub category {Full-Service Restaurants} takes up at least 30% of 2022's spend or where there's solid parking availability — say 4 lots.", # SHOULD END HERE!!



            #Hard 1: 3-7 spend params constraints together (simple 5)
            "I want to open a breakfast cafe — looking for zones where median spend per transaction was under $18, total spend was over $30 million, and there were at least 90,000 customers in 2022.",
            "Where should I open a boutique gym? I need areas with median spend per customer above $250, over 100,000 transactions, and a year-over-year spend growth rate of at least 6% in 2023.",
            "Thinking about launching a taco truck — I’m targeting zones with under $20 median spend per transaction, 50,000+ customers, a 10%+ year-over-year spending increase, and total spend above $15M in 2021.",    
            "Looking to place a vintage bookstore. Ideal zones would have median spend per customer ≤ $35, total spend ≥ $40 million, transactions over 120,000, and year-over-year spend growth > 5% in 2024.",
            "Opening a food hall — I’m looking for zones with $70M+ in total spend, 200,000+ yearly transactions, median spend per transaction under $25, and at least 150,000 customers in 2022.", 
            "Thinking of opening a jazz bar — I’m looking for zones with at least $25 million in total spend, median spend per customer below $40, more than 80,000 customers, and year-over-year spend growth over 4% in 2023.",
            "Looking to start a craft brewery — need zones where transactions exceeded 150,000, median spend per transaction was under $30, and year-over-year spend growth was above 12% in 2022.",
            "Trying to find the right spot for a pet supply store — interested in zones with 60,000+ customers, total spend over $35M, median spend per customer at least $200, and a slight year-over-year spend drop no worse than -3% in 2021.",
            "Planning a farm-to-table restaurant — ideal zones should have median spend per transaction ≤ $28, customer count over 100,000, and total spend beyond $50M in 2024.",
            "I want to open an ice cream shop — looking for areas where median spend per customer was under $25, annual transactions were 90,000+, total spend surpassed $20M, and year-over-year spend growth was at least 5% in 2023.",
            "Exploring sites for a home goods store — want zones with more than $60M in total spend, median spend per customer ≥ $210, and spend growth vs previous year above 7% in 2022.",
            "Launching a tech repair kiosk — searching for zones with 110,000+ transactions, median spend per transaction below $20, and total spend ≥ $30 million in 2021.",
            "Looking to open a tea lounge — I want zones where total spend was above $45M, median spend per customer over $200, more than 70,000 customers, and year-over-year spend growth higher than 6% in 2022.",
            "Interested in placing a wine shop — I need areas where median spend per customer was less than $30, total spend above $25 million, transactions over 85,000, and a 3%+ year-over-year increase in 2023.",            
            "Hoping to set up a discount outlet — zones should have a median spend per transaction ≤ $22, total spend above $40M, 120,000+ customers, and a year-over-year increase of at least 9% in 2024.",

            #Hard 2: Multiple spend params constraints together over multiple years (somple 5)
            "Looking to start a small movie theater — I’m after zones where the average median spend per customer from 2020 to 2023 was under $40, total spend exceeded $55 million, and the total number of customers was above 120,000 over that period.",
            "Scouting a place for a combo coffee/bookshop — I want zones with average year-over-year spend growth of at least 4%, average year-over-year spend increase above 10%, average median spend per transaction under $25, and total transactions over 180,000 from 2019 to 2022.",
            "Thinking about opening a family-owned pizzeria — looking for zones with total spend over $70M, average median spend per customer above $200, total customers over 250,000, and average year-over-year growth over 8% from 2021 through 2023.",
            "I want to set up a community gym — show me zones where the average median spend per transaction was below $20, total spend was at least $60 million, total transactions exceeded 160,000, total customers surpassed 130,000, and average year-over-year spend growth was positive from 2020 to 2023.",
            "Exploring options for a farmers’ co-op — I’m targeting areas with a total of over 100,000 yearly transactions, total spend above $45M, average median spend per customer ≤ $35, total customer count above 150,000, and both average year-over-year and year-over-year spend growth positive from 2021 to 2024.",
            "Planning to open a boba tea shop — looking for zones where total spend exceeded $40 million, and the average median spend per transaction was under $18 from 2021 to 2023.",
            "I’m scouting locations for a cozy ski lodge café — want zones where total spend from 2020 to 2023 was above $60M, average median spend per customer was over $250, total customers exceeded 100,000, and average year-over-year spend growth was at least 3%.",
            "Trying to set up a health food market — searching for zones with more than 200,000 total transactions, total spend greater than $55M, average median spend per transaction under $22, and average year-over-year spend growth from 2019 to 2022.",
            "Launching a cultural center — I’m interested in zones where the total number of customers from 2021 to 2024 surpassed 180,000, average median spend per customer was over $190, and average year-over-year spend increased by at least 5%.",
            "I want to build a creative co-working space — show me zones where total transactions were over 150,000, average year-over-year spend growth was at least 4%, average year-over-year growth was positive, and the average median spend per transaction was under $30 from 2020 to 2023.",
            "Looking for a place to open a mid-size electronics store — I need zones with total spend over $70M, more than 300,000 total customers, and average median spend per transaction above $40 across 2021 to 2023.",
            "Planning a farmers’ market — I’m after zones where total spend was over $35M, total transactions were greater than 120,000, average median spend per customer was under $25, and both average year-over-year spend growth and year-over-year growth were consistently above 2% from 2019 to 2022.",
            "Exploring options for a local hardware store — looking for areas with total customers above 180,000, total spend exceeding $60M, average median spend per transaction under $28, and average year-over-year growth over 6% from 2020 to 2023.",
            "Scouting potential sites for an indie music venue — want zones with total spend over $80 million, more than 250,000 total transactions, average median spend per customer ≥ $200, and average year-over-year spend change over 4% from 2021 to 2024.",
            "Thinking of opening a large laundromat — I need zones with at least 100,000 total customers, average median spend per transaction below $15, average year-over-year growth not worse than -2%, and positive average year-over-year growth from 2020 to 2022.",

            #Hard 3: Medium 1 AND/OR Medium 2 AND/OR Simple 4
            "I want to open a brunch café with top category {Restaurants and Other Eating Places} and sub category {Full-Service Restaurants}, targeting zones with fewer than 3 competitors in the same sub category where the total number of transactions is > 300,000 from 2022 - 2024.",
            "I want to open a wellness studio with top category {Offices of Other Health Practitioners} and sub category {Offices of All Other Miscellaneous Health Practitioners}, but only in areas with fewer than 2 similar businesses where the total number of customers is > 120,000 from 2022 - 2024.",
            "I want to open a wine bar with top category {Beer, Wine, and Liquor Stores} and sub category {Beer, Wine, and Liquor Stores}, in zones with fewer than 4 competitors in the same category where total spend is > $40 million from 2022 - 2024.",
            "I want to open a drive-through coffee hut with top category {Gasoline Stations} and sub category {Gasoline Stations with Convenience Stores}, but only if there are fewer than 3 competitors and the total number of transactions is > 500,000 from 2022 - 2024.",
            "I'm thinking of launching a full-service brunch spot with top category {Restaurants and Other Eating Places} and sub category {Full-Service Restaurants}, in zones with fewer than 4 competitors, total spend > $60 million and total number of transactions > 400,000 from 2022 - 2024.",
            "Looking to open a sleek salon with top category {Personal Care Services} and sub category {Beauty Salons}, where there are fewer than 3 competing salons and total customers exceed 200,000 and total spend is above $35 million during 2022 to 2024.",
            "I want to start a tutoring franchise with top category {Other Schools and Instruction} and sub category {Exam Preparation and Tutoring}, targeting zones with fewer than 2 competitors in the same sub category, total number of transactions > 150,000 and total spend > $20 million from 2022 - 2024.",
            "Planning a cozy mental wellness clinic with top category {Offices of Physicians} and sub category {Offices of Physicians, Mental Health Specialists}, but only if there are fewer than 3 similar clinics and total customers above 90,000 with total spend exceeding $28 million from 2022 - 2024.",
            "Looking into opening a drive-thru coffee kiosk with top category {Gasoline Stations} and sub category {Gasoline Stations with Convenience Stores}, in zones with fewer than 4 competitors where total transactions are over 500,000 and total spend is more than $45 million from 2019 - 2023.",
            "Thinking about opening a boutique PR agency with top category {Advertising, Public Relations, and Related Services} and sub category {Advertising Agencies}, in areas with fewer than 3 firms in the same category where total customers are > 75,000 and total number of transactions > 120,000 from 2020 - 2021.",
            "I want to set up a specialized health practice with top category {Offices of Other Health Practitioners} and sub category {Offices of All Other Miscellaneous Health Practitioners}, in zones with fewer than 3 competitors, where total spend exceeds $32 million and total customers > 110,000 from 2022 - 2023.",
            "Opening a family-owned bookstore café with top category {Other Miscellaneous Store Retailers} and sub category {Art Dealers}, looking for areas with fewer than 2 competitors, total customers > 100,000 and total transactions > 250,000 from 2022 - 2024.",
            "Launching a real estate co-working lounge with top category {Lessors of Real Estate} and sub category {Lessors of Residential Buildings and Dwellings}, where there are fewer than 3 competitors, total spend > $85 million and customer count exceeds 180,000 between 2020 and 2022.",
            "Setting up a high-end liquor boutique with top category {Beer, Wine, and Liquor Stores} and sub category {Beer, Wine, and Liquor Stores}, in zones with fewer than 3 competitors where transactions are above 300,000 and total spend is over $70 million from 2022 - 2023.",
            "I'm planning to open a premium nail spa with top category {Personal Care Services} and sub category {Beauty Salons}, in areas with fewer than 3 competitors where the average median spend per customer is > $200, total number of customers > 180,000, and total spend > $50 million from 2022 - 2023.",
            "Looking to launch a real estate hub with top category {Lessors of Real Estate} and sub category {Lessors of Residential Buildings and Dwellings}, in zones with fewer than 4 competitors where average year-over-year spend growth is > 7%, total transactions > 220,000, and average median spend per transaction > $30 from 2022 - 2023.",
            "I want to open a creative ad studio with top category {Advertising, Public Relations, and Related Services} and sub category {Advertising Agencies}, but only if there are fewer than 3 similar businesses and the average yearly spend growth is > 5%, average median spend per customer > $250, and total spend exceeds $60 million from 2020 - 2024.",
            "Thinking about launching a kids tutoring center with top category {Other Schools and Instruction} and sub category {Exam Preparation and Tutoring}, where fewer than 2 competitors exist, the average median spend per transaction is ≤ $20, total transactions > 190,000, total customers > 80,000, and average spend change vs previous year is > 10% from 2019 - 2013.",
            "Exploring a business park café with top category {Restaurants and Other Eating Places} and sub category {Snack and Nonalcoholic Beverage Bars}, in zones with fewer than 3 competitors, total spend > $35 million, average median spend per customer > $180, total number of customers > 120,000, and average month-over-month spend growth > 4% from 2020 - 2024.",
            "I want to open a wellness clinic with top category {Offices of Physicians} and sub category {Offices of Physicians (except Mental Health Specialists)}, but only in zones with fewer than 2 competitors, average median spend per transaction > $45, total spend > $55 million, and total transactions > 280,000 from 2021 - 2022.",
            "Launching a boutique insurance firm with top category {Agencies, Brokerages, and Other Insurance Related Activities} and sub category {Insurance Agencies and Brokerages}, targeting zones with fewer than 2 competitors where total customers > 90,000, average spend change vs previous month > 3%, and total spend > $40 million from 2022 - 2023.",
            "Looking for a spot to set up a mental health center with top category {Offices of Physicians} and sub category {Offices of Physicians, Mental Health Specialists}, in areas with fewer than 3 competitors where average year-over-year spend growth > 12%, total customers > 110,000, and average median spend per customer > $220 from 2022 - 2024.",
            "Scouting for a location to open a high-end tutoring space with top category {Educational Support Services} and sub category {Educational Support Services}, targeting zones with fewer than 2 competitors where total number of customers > 70,000, average monthly spend growth > 4%, and average median spend per transaction > $28 from 2020 - 2024.",
            "Setting up a fine dining spot with top category {Restaurants and Other Eating Places} and sub category {Full-Service Restaurants}, but only in areas with fewer than 3 competitors where average median spend per customer > $300, total spend > $75 million, total customers > 250,000, and average year-over-year spend growth > 6% from 2021 - 2023.",


            #Hard 4: Simple 3 AND/OR Simple 4 AND/OR Simple 7
            "I'm planning to open a skincare bar with sub category {Beauty Salons}. Show me zones with fewer than 3 competitors in the same sub-category, at least 4 parking lots, and 6 or more POIs in the sub category {Beauty Salons}.",
            "I want to launch a minimalist clothing store with top category {Other Miscellaneous Store Retailers}. I need zones with fewer than 4 competitors, at least 3 parking lots, and 5 or more POIs in the top category {Other Miscellaneous Store Retailers}.",
            "Looking to open a health-food café with sub category {Snack and Nonalcoholic Beverage Bars}. I want zones with less than 3 competitors in the same sub-category, 4 or more parking lots, and at least 6 POIs in the sub category {Snack and Nonalcoholic Beverage Bars}.",
            "I'm thinking of setting up a juice + fitness hybrid with top category {Fitness and Recreational Sports Centers}. Show me zones with fewer than 2 competitors, a minimum of 3 parking lots, and at least 5 POIs in the top category {Fitness and Recreational Sports Centers}.",
            "Planning to open a modern bistro with sub category {Full-Service Restaurants}. I need zones with fewer than 5 competitors, not less than 4 parking lots, and at least 7 POIs in the sub category {Full-Service Restaurants}.",
            "I want to start a wine lounge with top category {Drinking Places (Alcoholic Beverages)}. Show me areas that have fewer than 3 competitors in the same top category, 3+ parking lots, and no fewer than 6 POIs in {Drinking Places (Alcoholic Beverages)}.",
            "Looking to open a luxury spa with sub category {Other Personal Care Services}. Find me zones that include fewer than 4 competitors in the same sub-category, at least 4 parking lots, and 5 or more POIs in the sub category {Other Personal Care Services}.",
            "I'm launching a hip boutique with top category {Offices of Real Estate Agents and Brokers}. I need zones with fewer than 3 competitors, 3 parking lots minimum, and at least 5 POIs in {Offices of Real Estate Agents and Brokers}.",
            "Opening a quick-service café with sub category {Snack and Nonalcoholic Beverage Bars}. I want zones that have less than 3 competitors in the same sub-category, a minimum of 3 parking lots, and 6+ POIs in the sub category {Snack and Nonalcoholic Beverage Bars}.",
            "I want to set up a beauty & nails bar with top category {Personal Care Services}. Show me zones where there are fewer than 4 competitors in the top category, at least 4 parking lots, and a minimum of 5 POIs in {Personal Care Services}.",
            "I'm opening a fashion studio with top category {Other Miscellaneous Store Retailers}. Show me zones that do NOT have more than 4 competitors in the same top category, have at least 3 parking lots, and NOT fewer than 5 POIs in {Other Miscellaneous Store Retailers}.",
            "I want to launch a plant-based café with sub category {Snack and Nonalcoholic Beverage Bars}. I need zones with fewer than 3 competitors, NOT fewer than 4 parking lots, and at least 6 POIs in the same sub-category.",
            "Looking to open a beauty retreat with sub category {Beauty Salons}. Find me zones that have fewer than 5 competitors OR zones that do NOT have fewer than 3 parking lots and contain at least 7 POIs in the sub category {Beauty Salons}.",
            "Planning a real estate lounge with top category {Offices of Real Estate Agents and Brokers}. Show me zones with NOT more than 2 competitors, a minimum of 4 parking lots, and NOT fewer than 6 POIs in the top category.",
            "I'm thinking of launching a nail and lash bar with sub category {Other Personal Care Services}. Find me zones where the number of competitors is NOT more than 3, with at least 3 parking lots, and 5+ POIs in the sub category.",
            "Opening a Mediterranean café with top category {Restaurants and Other Eating Places}. I want zones that do NOT have more than 4 competitors in the same top category, include 4 or more parking lots, and have NOT fewer than 8 POIs in {Restaurants and Other Eating Places}.",
            "Looking to set up a specialty fitness center with sub category {Fitness and Recreational Sports Centers}. Show me zones with fewer than 3 competitors, NOT fewer than 5 POIs in the sub-category, and zones that have at least 2 parking lots.",
            "I want to start a wine tasting room with top category {Drinking Places (Alcoholic Beverages)}. I’m targeting zones that have NOT more than 2 competitors, at least 3 parking lots, and NOT fewer than 6 POIs in the top category.",
            "Thinking of launching a fashion-and-beauty shop with sub category {Women's Clothing Stores}. Find me zones with fewer than 4 competitors, 3 or more parking lots, and at least 5 POIs in the same sub category.",
            "I'm scouting locations for a wellness bar with top category {Personal Care Services}. I need zones with NOT fewer than 4 parking lots, NOT more than 3 competitors in the top category, and at least 6 POIs in {Personal Care Services}.",

            #Hard 5: Simple 4 AND/OR Simple 6 AND/OR Simple 9
            "I want to open a wellness café with sub category {Snack and Nonalcoholic Beverage Bars}. Show me zones with fewer than 3 competitors in the same sub-category, at least 5 subway entrances nearby, and a combined population of at least 15,000 across the zone and 2 neighbors.",
            "Planning a boutique legal office with top category {Legal Services}. I need zones that have fewer than 4 competitors in the same top category, 4 or more bus stops nearby, and a total population of at least 18,000 with the zone and 3 surrounding zones combined.",
            "Looking to open a tutoring center with sub category {Exam Preparation and Tutoring}. I want zones with fewer than 2 competitors, 3+ nearby stations, and a minimum population of 12,000 across the zone and its 2 nearest neighbors.",
            "I’m launching a restaurant incubator with top category {Restaurants and Other Eating Places}. I need zones with fewer than 5 competitors, 6 or more bus stops nearby, and a combined population of atleast 20,000 with 2 neighbors.",
            "Thinking of opening a co-working hub with top category {Offices of Real Estate Agents and Brokers}. Show me zones with fewer than 3 competitors, at least 4 nearby subway entrances, and a population over atleast 14,000 across 2 closest zones.",
            "I want to set up a day spa with sub category {Beauty Salons}. The zone must have fewer than 4 competitors, 5 taxi stops nearby, and a combined population with 3 neighbors of at least 16,000.",
            "Planning a boutique law firm with top category {Legal Services}. I need areas with fewer than 2 competitors, 6 or more subway entrances, and a population of 25,000+ with the 2 nearest zones.",
            "Opening a child development center with sub category {Educational Support Services}. Find me zones with fewer than 3 competitors, 4 or more nearby bus stops, and 10,000+ population across 2 neighbors.",
            "Launching a microbrewery with top category {Drinking Places (Alcoholic Beverages)}. Show me zones with fewer than 5 competitors in the category, 5 subway entrances, and 18,000+ residents across 3 zones.",
            "Looking to open a fitness training studio with sub category {Fitness and Recreational Sports Centers}. I want zones with fewer than 3 competitors, at least 4 taxi stands nearby, and 12,000 people across 2 neighbors.",
            "I'm planning a legal office with top category {Legal Services}. The zone should have fewer than 4 competitors, 3+ bus stops nearby, and at least 13,000 population when adding 2 adjacent zones.",
            "I want to start a café near a college with sub category {Snack and Nonalcoholic Beverage Bars}. Show me zones with fewer than 2 competitors, 6 subway entrances, and a local+neighbor population of 17,000.",
            "Opening a vegan diner with top category {Restaurants and Other Eating Places}. I’m looking for fewer than 3 competitors, 5 nearby stations, and at least 14,000 population across the zone and 2 neighbors.",
            "Planning to set up a tutoring space with sub category {Exam Preparation and Tutoring}. The ideal zone will have fewer than 2 competitors, at least 4 bus stops, and 12,000+ population from 2 neighboring zones.",
            "Starting a creative media agency with top category {Advertising, Public Relations, and Related Services}. I want fewer than 3 competitors, 4+ subway entrances, and a population of no less than 16,000 across 2 zones.",
            "Launching a fine-dining restaurant with sub category {Full-Service Restaurants}. I need a zone with fewer than 4 competitors, 6 or more bus stops, and 20,000+ population across 3 zones.",
            "I'm planning a shopping boutique with sub category {Women's Clothing Stores}. Show me zones with fewer than 3 competitors, 5 nearby taxi stands, and a population of at least 13,000 with 2 neighbors.",
            "Setting up a commercial real estate office with top category {Offices of Real Estate Agents and Brokers}. I want fewer than 3 competitors, 4 or more bus stops, and at least 15,000 population across 2 surrounding zones.",
            "Looking to open a casual restaurant with sub category {Full-Service Restaurants}. Find zones with fewer than 5 competitors, 4+ subway entrances, and population with 2 neighbors exceeding 16,000.",
            "Opening a dessert café with sub category {Snack and Nonalcoholic Beverage Bars}. I'm targeting zones with fewer than 2 competitors, 3 or more nearby bus stops, and a combined population of 11,000 from the zone and 2 closest zones.",

            #Hard 6: simple 4 AND/OR 6 NOT 3 --> todo. did not include sub/top 
            "I want to open a boutique clothing store with sub category {Women's Clothing Stores}. Show me zones with fewer than 3 competitors, a combined population of at least 12,000 with 2 nearby zones, but NOT zones with more than 2 parking lots — I’m targeting a pedestrian-heavy shopping area.",
            "Planning a walk-in hair studio with sub category {Beauty Salons}. I need fewer than 4 competitors, 10,000+ residents in the surrounding area, but I want zones with minimal car traffic — NOT more than 1 parking lot.",
            "Launching a luxury watch boutique with top category {Other Miscellaneous Store Retailers}. I want zones with fewer than 2 competitors, a population over 15,000 with neighbors, but NOT any place with 3 or more parking lots — aiming for high-foot-traffic districts.",
            "I'm scouting zones to open a zero-waste beauty shop with sub category {Other Personal Care Services}. I want fewer than 2 competitors, at least 11,000 nearby residents, but NOT zones with more than 2 parking lots — I prefer pedestrian access.",
            "Looking to open a handmade goods studio with top category {Other Schools and Instruction}. Show me zones with fewer than 3 similar shops, over 10,000 population including two neighbors, but NOT zones filled with large parking lots.",
            "Opening a holistic wellness center with sub category {Other Personal Care Services}. I want fewer than 2 competitors and a combined population of 13,000+ — but avoid zones with more than 2 parking lots.",
            "I'm launching a design-forward retail shop. I need a zone with under 3 competitors in sub category of {Women's Clothing Stores}, 12,000+ people nearby, and NOT more than 1 parking lot — targeting dense, walkable districts.",
            "Thinking of opening a creative bookstore café. I want fewer than 4 competitors in sub category of {Snack and Nonalcoholic Beverage Bars}, at least 14,000 residents across the zone and two neighbors, and NOT more than 2 parking lots — this should feel local and urban.",
            "Looking for zones to open an independent cinema with top category {Drinking Places (Alcoholic Beverages)}. I want fewer than 2 competitors, over 10,000 residents, and NOT zones with large-scale parking infrastructure.",
            "I'm planning to open an eco-friendly home décor store with sub category {All Other Home Furnishings Stores}. I want fewer than 3 competitors, a combined population of at least 11,000 with neighbors, but NOT more than 2 parking lots — keeping it community-oriented.",
            "Looking to start a dog grooming salon with sub category {Other Personal Care Services}. I need zones with under 2 competitors, population above 12,000 including neighbors, and NOT zones with 3 or more parking lots — I want a cozy, foot-traffic-focused spot.",
            "Thinking about a photography studio with sub category {Photographic Services}. I want fewer than 3 similar businesses, 13,000+ nearby residents, but I don’t want to be in areas with too many parking lots — NOT more than 2 allowed.",
            "I’m scouting zones for a vegan clothing boutique in the sub category {Women's Clothing Stores} sub category. Show me places with under 2 competitors, over 10,000 people in adjacent zones, but NOT more than 1 parking lot — walkability is key.",
            "Opening a tech gear concept shop with top category {Other Miscellaneous Store Retailers}. I want fewer than 3 direct competitors, 14,000+ people nearby, but NOT more than 2 parking lots — avoid suburban sprawl zones.",
            "Planning a holistic therapy space with sub category {Offices of All Other Miscellaneous Health Practitioners}. I want fewer than 2 competitors, combined population of 12,000+, and NOT zones with more than 2 parking lots — prioritizing local access.",
            "Launching a curated toy store in sub category {Educational Support Services}. Fewer than 3 competitors, 11,000+ local + neighbor population, but NOT areas with more than 2 parking lots — it should feel like a downtown nook.",
            "I want to open a language tutoring hub with sub category {Exam Preparation and Tutoring}. Zones should have fewer than 2 competitors, population ≥ 10,000 with 2 nearby zones, and NOT over 2 parking lots — I’m aiming for a central, accessible district.",
            "Planning to open a local crafts market. Show me zones with fewer than 3 competitors in {Art Dealers}, population over 13,000 including 2 nearby zones, but NOT zones with 3+ parking lots.",


            #Hard 7: (3 AND 4) OR (6 AND NOT 7)
            "I'm planning to open a vegan café. Show me zones where there are at least 3 parking lots AND fewer than 2 competitors in sub category {Snack and Nonalcoholic Beverage Bars}, OR zones where the population of my zone and 2 neighbors exceeds 14,000 AND the number of POIs in {Full-Service Restaurants} is not more than 3 — I don’t want areas already saturated with sit-down dining.",
            "Planning a food truck plaza. I want zones with 3 or more parking lots AND 6+ POIs in sub category {Snack and Nonalcoholic Beverage Bars}, OR zones with fewer than 2 competitors in the same sub category AND NOT more than 3 POIs in sub category {Drinking Places (Alcoholic Beverages)} — this isn’t a nightlife spot.",
            "I want to open a boutique wine bar with sub category {Drinking Places (Alcoholic Beverages)}. Show me zones with 4 or more POIs in the sub category AND fewer than 3 competitors, OR zones with 3+ parking lots AND NOT a total population above 15,000 — targeting suburban charm, not urban density.",
            "I'm opening a rustic bakery. Show me zones with at least 2 parking lots AND fewer than 2 competitors in sub category {Snack and Nonalcoholic Beverage Bars}, OR zones where population with 2 nearby zones is over 12,000 AND NOT more than 3 POIs in sub category {Full-Service Restaurants}.",
            "Looking to set up a community art studio. I want zones with 3 or more parking lots AND fewer than 3 competitors in top category {Other Miscellaneous Store Retailers}, OR zones with 11,000+ residents across 2 neighbors AND NOT more than 4 POIs in sub category {Drinking Places (Alcoholic Beverages)}.",
            "Planning a cozy reading café. Find zones with at least 3 parking lots AND fewer than 2 competitors in sub category {Snack and Nonalcoholic Beverage Bars}, OR zones with 13,000+ people and NOT more than 3 POIs in top category {Restaurants and Other Eating Places}.",
            "I want to launch a DIY crafts store. Show me zones with 4+ parking lots AND fewer than 3 competitors in top category {Other Miscellaneous Store Retailers}, OR zones with at least 14,000 residents in the area AND NOT more than 3 POIs in sub category {Beauty Salons}.",
            "Looking to open a family-friendly café. Zones should have 3 or more parking lots AND under 3 competitors in sub category {Snack and Nonalcoholic Beverage Bars}, OR population of 15,000+ with neighbors AND NOT more than 4 POIs in sub category {Drinking Places (Alcoholic Beverages)}.",
            "I'm planning a secondhand bookstore. Target areas with 2+ parking lots AND fewer than 2 competitors in top category {Other Schools and Instruction}, OR at least 12,000 people nearby AND NOT more than 2 POIs in sub category {Snack and Nonalcoholic Beverage Bars}.",
            "Launching a health-oriented lunch café. Show me zones with at least 3 parking lots AND under 3 competitors in sub category {Full-Service Restaurants}, OR zones with 10,000+ population AND NOT more than 3 POIs in sub category {Drinking Places (Alcoholic Beverages)}.",
            "I want to open a small wine & cheese bar. Find zones with 2+ parking lots AND fewer than 2 competitors in sub category {Drinking Places (Alcoholic Beverages)}, OR zones with 11,000+ people AND NOT more than 3 POIs in sub category {Full-Service Restaurants}.",
            "I'm scouting zones for a community co-op café. I want at least 2 parking lots AND fewer than 2 competitors in sub category {Snack and Nonalcoholic Beverage Bars}, OR population over 12,000 with nearby zones AND NOT more than 4 POIs in {Restaurants and Other Eating Places}.",
            "Thinking of launching a bakery and tea spot. Show me zones with at least 3 parking lots AND under 3 competitors in sub category {Full-Service Restaurants}, OR areas with 14,000+ population across 2 neighbors AND NOT more than 3 POIs in sub category {Drinking Places (Alcoholic Beverages)}.",

            #Hard 8: (Simple 4 AND Simple 7) OR (Simple 9 AND NOT Simple 3)
            "I’m opening a career coaching office with sub category {Educational Support Services}. I want zones with fewer than 2 competitors AND at least 4 POIs in that sub category, OR zones with 4+ nearby bus stops AND NOT more than 2 parking lots — I’m aiming for foot-traffic-heavy academic districts.",
            "Planning a legal clinic with top category {Legal Services}. Find me zones that have under 3 competitors AND at least 5 POIs in the same top category, OR 5 or more subway entrances nearby AND NOT more than 2 parking lots — walkability is key.",
            "I want to launch a pop-up vegan dessert bar with sub category {Snack and Nonalcoholic Beverage Bars}. Target zones that have fewer than 3 competitors AND 6+ POIs, OR strong access with 4+ taxi stands AND NOT more than 1 parking lot — aiming for small-format urban placement.",
            "Looking to open a college-focused tutoring hub with sub category {Exam Preparation and Tutoring}. Show me zones that have fewer than 2 competitors AND 4 or more POIs, OR 4 bus stops nearby AND NOT zones with 3 or more parking lots.",
            "Opening a mindfulness coaching center with sub category {Other Personal Care Services}. I want zones that have at least 5 POIs AND fewer than 3 competitors, OR access to 5+ subway entrances AND NOT more than 2 parking lots — we’re trying to embed in walkable communities.",
            "Scouting zones for a family law firm with top category {Legal Services}. I want zones that include fewer than 3 competitors AND 5 POIs, OR zones with great access — 4 taxi stands minimum — and NOT more than 2 parking lots.",
            "Launching a leadership academy with sub category {Educational Support Services}. Show me zones that have fewer than 2 competitors AND 4+ POIs in the same sub category, OR 4 or more bus stops and NOT more than 1 parking lot — for urban student access.",
            "Opening a productivity café with sub category {Snack and Nonalcoholic Beverage Bars}. I want zones that have at least 4 POIs AND fewer than 3 competitors, OR 5 subway stops in close range AND NOT more than 2 parking lots — it’s meant for commuters and students.",
            "Planning a barbershop and product retail space with sub category {Beauty Salons}. Show me zones that have under 3 competitors AND at least 6 POIs in that sub category, OR zones with 4+ bus stops nearby AND NOT more than 2 parking lots — we’re looking to blend into local communities.",
            "I want to open a creative workshop lounge with sub category {Other Personal Care Services}. Target zones with at least 5 POIs AND fewer than 2 competitors, OR any place with 5 or more taxi stops AND NOT zones with heavy parking infrastructure.",

            #Hard 9: Simple 4 (competitor count) OR Simple 6 (population) AND NOT Simple 3 (parking lots) #NEED TO RE RUN THIS
            "I want to open a wellness studio. I’m looking for zones with fewer than 3 competitors in sub category {Other Personal Care Services} OR a population of at least 12,000 across 2 neighboring zones, but NOT zones with more than 2 parking lots — we’re targeting walkable areas.",
            "Planning a tutoring center. I want zones that either have fewer than 2 competitors in sub category {Exam Preparation and Tutoring} OR population above 13,000 including 2 nearby zones, but NOT areas with 3 or more parking lots — this is a student-heavy district.",
            "Looking to launch a bakery café. I want either fewer than 3 competitors in sub category {Full-Service Restaurants} OR at least 15,000 people in this zone, but NOT zones with heavy parking less than 8— too suburban for my concept.",
            "I want to open a plant-based diner. Either the zone has fewer than 2 competitors in sub category {Full-Service Restaurants} OR a population over 14,000 across 2 neighbors, but NOT if it has more than 2 parking lots — I’m aiming for pedestrian-heavy areas.",
            "Planning a boutique consulting office. I want fewer than 3 competitors in sub category {Legal Services} OR 13,000+ population with the 1 closest neighbor, but NOT zones with 3 or more parking lots.",
            "Looking to start a children’s learning space. The zone should either have fewer than 2 competitors in sub category {Educational Support Services} OR 15,000+ people near the closest 3 neighboring zones, but NOT with 3+ parking lots.",
            "I'm scouting for a gallery café. I want either fewer than 3 competitors in sub category {Art Dealers} OR a zone with at least 12,000 residents across 2 neighbors, but NOT high-parking areas — we want a walk-in audience. I need less than 14 parking lots",
            "Opening a healthy fast-casual kitchen. Either the zone has under 2 competitors in sub category {Full-Service Restaurants} OR strong population density of 20,000 in the zone, but NOT if there’s more than 2 parking lots.",
            "Looking to open a local therapy practice. The zone must have either under 3 competitors in sub category {Offices of Other Health Practitioners} OR more than 10,000 people with 3 closest neighbors, but NOT large parking availability. So less than 9 parking lots",
            "I'm opening a self-care hub. Show me zones with fewer than 2 competitors in sub category {Other Personal Care Services} OR at least 13,000 population in 3 zones, but NOT if the zone has 3 or more parking lots.",
            "Planning a local bookstore and bar. I want zones with fewer than 3 competitors in sub category {Educational Support Services} OR population over 12,000 with 4 closest neighbors, but NOT more than 2 parking lots — the idea is community-focused foot traffic.",
            "Thinking of opening a music tutoring center. I need either fewer than 2 competitors in sub category {Other Schools and Instruction} OR 11,000+ population with closest 2 neighbors, but NOT zones with high parking counts. Less than 8 parking lot please",
            "Launching a career prep center. Either under 3 competitors in sub category {Employment Placement Agencies} OR 13,000+ population in closest 2 zones is fine, but NOT if the parking lots exceed 2 — I want downtown foot access.",

            #Hard 10: Simple 7 (POI count) OR Simple 9 (transport access) AND NOT Simple 4 (competitor count)
            "I’m launching a late-night coffee spot. I want at least 5 POIs in sub category of {Snack and Nonalcoholic Beverage Bars} OR 4+ subway stops nearby, but NOT zones with more than 3 competitors in the same sub category.",
            "Looking to open a brunch café. Either the zone has 6+ POIs in sub category {Full-Service Restaurants} OR great transport via 5 bus stops, but NOT if 4 or more similar businesses exist.",
            "I want to open a barbershop. I’m looking for either 5+ POIs in sub category {Beauty Salons} OR at least 4 taxi stops, but NOT more than 3 competitors.",
            "Launching a boba tea shop. Show me zones with either 6 POIs in sub category {Snack and Nonalcoholic Beverage Bars} OR at least 5 subway entrances, but NOT high local competition.",
            "Planning a craft beer bar. I need zones with either 4 POIs in sub category {Drinking Places} OR 4+ nearby bus stops, but NOT 3+ competitors.",
            "Opening a dog-friendly juice bar. I want either 5 POIs in sub category {Snack and Nonalcoholic Beverage Bars} OR strong public transit, but NOT zones where competition is too high.",
            "I want a vegan cafe. Either 6 POIs in the right sub category OR 5+ bus stops, but not more than 2 competing businesses.", #check here
            "Scouting locations for a retro-style diner. The zone should either have 5 POIs in sub category {Full-Service Restaurants} OR access to 4 or more subway entrances, but NOT saturated with competitors.",
            "Looking for a zone to open a community coffeehouse. I want either 4 POIs in sub category {Snack and Nonalcoholic Beverage Bars} OR 5 bus stops, but avoid zones with 4 or more competitors.",
            "Opening a fitness-friendly cafe. I need either 6 POIs in {Snack and Nonalcoholic Beverage Bars} OR 4 subway stops, but NOT zones with more than 3 competitors in the same space.",
            "I'm planning a hangout cafe. I want either 4 POIs in sub category {Full-Service Restaurants} OR 4+ taxi stands, but I won’t consider places with more than 3 competitors in that sub category.",
            "Thinking of opening a themed café. I’ll take either 4 POIs in sub category {Snack and Nonalcoholic Beverage Bars} OR strong transport access with 6+ bus stops, but I’m out if 4+ rivals are in that sub category.",
            "Thinking of opening a themed café. I’ll take either 4 POIs in sub category {Full-Service Restaurants} OR strong transport access with 6+ light rail stops, but I’m out if 3+ rivals are in that sub category.",
            "Launching a brunch spot — show me zones with 4 POIs in sub category {Beauty Salons} OR great public access with 6 subway entrances, but avoid areas with 2+ similar businesses in that sub category.",
            "I want a zone with either 6+ POIs in sub category {Snack and Nonalcoholic Beverage Bars} OR 6+ taxi stands nearby, but not if the competition exceeds 4 in that sub category.",
            "I want a zone with either 6+ POIs in sub category {Full-Service Restaurants} OR 6+ light rail stops nearby, but not if the competition exceeds 3 in that sub category.",
            "I'm scouting a zone for a dessert bar. Either the area has 4+ POIs in sub category {Beauty Salons} OR at least 6 nearby taxi stands, but NOT if there are more than 4 competitors in that sub category.",
            "I want a zone with either 5+ POIs in sub category {Juice and Smoothie Bars} OR 4+ taxi stands nearby, but not if the competition exceeds 3 in that sub category.",
            "I want a zone with either 6+ POIs in sub category {Drinking Places} OR 5+ bus stops nearby, but not if the competition exceeds 2 in that sub category.",


            #Hard 11: Simple 6 (population) OR Simple 9 (transport) AND NOT Simple 10 (distance to transport POI)
            "I'm planning a co-working café. I want zones with at least 14,000 people across my zone and 2 neighbors OR at least 4 subway entrances, but NOT zones where the nearest station is more than 300 meters away — we need direct transit access.",
            "Opening a night market food stall. I want zones with either 13,000+ population including 3 nearby zones OR 5 bus stops, but NOT zones where the nearest bus stop is more than 250 meters from the centroid.",
            "I’m looking to set up a fast-casual eatery. The zone should either have strong public transit (5+ stops) OR 12,000+ population with 2 neighbors, but NOT if the nearest subway entrance is beyond walking range. The nearest station should be less than 800 meters away",
            "I want to open a ramen bar. Either the population across 2 neighboring zones is 14,000+ OR the zone has 5+ subway stops, but NOT if the nearest station is more than 300 meters from the centroid.",
            "Launching a career development center. I want zones with either high population density of 10,000+ or 4+ transit access points, but NOT where the walk to a stop exceeds 250 meters.",
            "Looking to open a legal services center. I want either 15,000+ people at this zone OR 5 nearby transit stops, but NOT long walking distances — under 200 meters only.",
            "Opening a mobility hub café. Either the population with 2 neighbors is above 13,000 OR there are 5 taxi stops nearby, but NOT if the nearest one is more than 300m away.",
            "Scouting areas for a quick service restaurant. The zone must have either high population of 12,000+ or good bus coverage, but NOT zones with poor centroid proximity to the nearest bus stop, which should not exceed 80m.",
            "I want to open a suburban bakery. Zones + 1 neighbor zone should either have 14,000+ population or 4+ subway entrances, but NOT if walking distance to transit exceeds 250m.",
            "Launching a high school test prep center. I want population + 3 neighbors ≥ 12,000 OR 5 bus stops, but NOT zones with transit farther than 300 meters from the centroid.",
            "Starting a co-op coworking space. Either the local+1 neighbor population is atleast 8,000 or there are 4+ taxi stops, but NOT zones that are poorly connected within walking distance, the nearest taxi should not exceed 100m.",
            "Opening a green juice bar. Give me zones with good foot traffic (13,000+ people) or 4+ nearby stations, but NOT if any of them are farther than 250m from the centroid.",
            "Launching a student hangout. Zones must have population over 12,000 OR 5 subway stops, but NOT ones where the nearest is more than 300 meters away.",
            'Launching a professional certification office. I want zones with either 13000+ residents in the area OR access to 4+ subway entrances, but NOT if the nearest is beyond 300 meters — accessibility is key.',
            'Looking for a spot to open a freelancer-friendly espresso bar. Either 14000+ people nearby OR at least 5 stations, but I’m not interested if transit is farther than 250m from the center of the zone.',
            'Launching a professional certification office. I want zones with either 15000+ residents in the area OR access to 6+ bus stops, but NOT if the nearest is beyond 300 meters — accessibility is key.',
            'Launching a professional certification office. I want zones with either 15000+ residents in the area OR access to 6+ stations, but NOT if the nearest is beyond 300 meters — accessibility is key.',
            'Planning a counseling and therapy center. Zones must have either 6+ bus stops OR 13000+ people with neighbors, but NOT if the nearest stop is more than 300m — it needs to be convenient.',
            'Launching a professional certification office. I want zones with either 12000+ residents in the area OR access to 5+ transit hubs, but NOT if the nearest is beyond 300 meters — accessibility is key.',
            'Looking for a spot to open a freelancer-friendly espresso bar. Either 15000+ people nearby OR at least 4 taxi stands, but I’m not interested if transit is farther than 250m from the center of the zone.',
            "I'm considering zones for a youth development center. I want either a combined population of 15000+ with 2 neighbors OR 5 stations, but NOT if the nearest one is more than 300 meters away — walkability matters.",
            "I'm considering zones for a youth development center. I want either a combined population of 14000+ with 2 neighbors OR 6 stations, but NOT if the nearest one is more than 200 meters away — walkability matters.",
            "I'm scouting a location for a coding bootcamp hub. I want areas with either strong transit (6+ taxi stands) OR a population of 15000+ with neighbors, but NOT if the closest stop is more than 250 meters from the centroid.",


            #Hard 12: Simple 3 (parking lots) OR Simple 7 (POI count) AND NOT Simple 6 (population) #rerun 
            "Looking to open a drive-in diner. I want zones with at least 4 parking lots OR 6 POIs in sub category {Full-Service Restaurants}, but NOT ones where the combined population across my zone and 2 neighbors exceeds 12,000 — I’m avoiding congested urban cores.",
            "Planning a car-based grocery pickup center. Either I need 5 parking lots OR 5+ POIs in  sub category {Snack and Nonalcoholic Beverage Bars}, but NOT if the surrounding population  across my zone and 4 neighbors exceeds 14,000 — I’m focused on suburban delivery hubs.",
            "I'm opening an automotive service hub. I want 3 or more parking lots OR 4 POIs in  sub category {Automotive Parts, Accessories, and Tire Stores}, but NOT zones with 15,000+ people — lower density is key for this model.",
            "I'm opening a drive-in movie café. I want zones with at least 4 parking lots OR 5 POIs in  sub category {Snack and Nonalcoholic Beverage Bars}, but NOT where population with 2 neighbors exceeds 12,000 — this is a low-density format.",
            "Launching an outdoor food court. I want zones with 5 parking lots OR 6 POIs in  sub category {Full-Service Restaurants}, but NOT zones with 14,000+ residents.",
            "Scouting a retail garden supply store. I need 3+ parking lots OR 5 POIs in  top category {Other Miscellaneous Store Retailers}, but NOT if the surrounding population across 5 closest zones is dense, should not exceed 25,000",
            "Opening a rural-focused health food market. Either give me 4 parking lots OR 6+ POIs in top category {Lessors of Real Estate}, but  my zone and 2 neighbors should not exceed 13,000+ population in total.",
            "Planning a pet supply warehouse. I want zones with 4 parking lots OR at least 5 POIs in the sub category {Full-Service Restaurants}, but NOT dense residential neighborhoods with more than 80000 people in my zone.",
            "Looking to open a lakefront food hub. Either 3+ parking lots OR 6 POIs in sub category {Full-Service Restaurants}, but NOT if the zone has 12,000+ residents with closest 3 neighbors.",
            "Launching a specialty gear outlet. Give me zones with 4 parking lots OR 5 POIs in top category {Other Miscellaneous Store Retailers}, but NOT with zone population over 13,000.",
            "Opening a family drive-in bistro. I want zones with at least 5 parking lots OR 6 POIs in sub category {Full-Service Restaurants}, but NOT more than 14,000 people nearby 4 closest zones.",
            "Looking to open an outdoor kids’ market. Either 4 parking lots or 5 POIs in sub category {Full-Service Restaurants} is fine, but NOT zones with 13,000+ population across this zone and the closest neighbor zone.",
            "Starting a rural spa. Show me zones with either 3+ parking lots OR 6 POIs in sub category{Beauty Salons}, but NOT zones with high density population across 2 neighbors exceeding 88000.",
            "I'm planning a rural pop-up market. I need zones with at least 5 parking lots OR 5 POIs in sub category {Snack and Nonalcoholic Beverage Bars}, but NOT zones with more than 12,000 people across 2 neighboring zones — I want breathing room.",
            "I'm planning a rural pop-up market. I need zones with at least 5 parking lots OR 4 POIs in sub category {Other Miscellaneous Store Retailers}, but NOT zones with more than 14,000 people across 2 neighboring zones — I want breathing room.",
            "Planning a spacious DIY warehouse. Either 5 parking lots OR 4+ POIs in sub category {Snack and Nonalcoholic Beverage Bars} will do, but avoid high-density zones with over 14,000 people.",
            "Launching a seasonal drive-in food plaza. Zones with at least 3 parking lots OR 6 POIs in sub category {Beauty Salons} are ideal, but skip those with over 13,000 people in the area across 3 closest zones.",
            "Launching a seasonal drive-in food plaza. Zones with at least 4 parking lots OR 6 POIs in sub category {Farm and Garden Equipment Merchant Wholesalers} are ideal, but skip those with over 12,000 people in the zone.",
            "Launching a seasonal drive-in food plaza. Zones with at least 4 parking lots OR 4 POIs in sub category {Other Miscellaneous Store Retailers} are ideal, but skip those with over 12,000 people in this and one closest zone.",
            "Looking to open a family-focused general store. Either 5+ parking lots or 5 POIs in sub category {Snack and Nonalcoholic Beverage Bars}, but NOT if population exceeds 12,000 in 3 closest zones. My customers hate crowding.",
            "Looking to open a family-focused general store. Either 5+ parking lots or 6 POIs in sub category {Beauty Salons}, but NOT if population exceeds 12,000 in this zone. My customers hate crowding.",
            "Planning a spacious DIY warehouse. Either 4 parking lots OR 4+ POIs in sub category {Full-Service Restaurants} will do, but avoid high-density zones with over 14,000 people.",
            
            #Hard 13:(Simple 13 AND Simple 6) OR (Simple 4 AND NOT Simple 7) #uncomment
            "Planning to open a neighborhood bank. Either the zone has 4 or more transport modes and 14,000+ people in 2 neighbors plus itself, OR there are fewer than 2 competitors in sub category {Commercial Banking} AND NOT more than 3 POIs in that space.",
            "Looking for a spot to open a boutique law office — give me zones with 3 or more transportation types AND at least 12,000 residents in 2 zones plus itself, OR areas with less than 2 competitors in sub category {Offices of Lawyers} AND NOT more than 2 POIs in that sub category.",
            "I'm launching a real estate satellite office. I want either zones with 3 types of transportation and 13,000+ with one closest nearby zone residents, OR areas with under 3 competitors in sub category {Offices of Real Estate Agents and Brokers} AND NOT more than POIs in that sub category.",
            "Hunting for a zone to open a mental health center. Show me zones with at least 3 distinct transportation types AND atleast 14,000 people with its closest neighbor, OR fewer than 2 competitors in sub category {Offices of Physicians, Mental Health Specialists} AND NOT zones with 4+ POIs in that sub category.",
            "I want to build a small creative studio — give me zones with at least 3 types of transport AND population above 12,000 with 2 neighboring zones, OR areas with fewer than 3 competitors in sub category {Advertising Agencies} AND NOT more than 2 POIs in that sub category.",
            "I'm planning a satellite insurance branch. Either the zone has 4 transportation types and 13,000+ people with closest 2 neighbors, OR fewer than 2 competitors in sub category {Insurance Agencies and Brokerages} AND NOT 3+ POIs in that category.",
            "Looking to open a local prep academy. I'd like zones with at least 3 transportation types AND population over 12,000 across this zone and 2 neighboring zones, OR areas with under 3 competitors in sub category {Exam Preparation and Tutoring} AND NOT zones with 4+ POIs in that space.",
            "Opening a tech-focused dentist's office. I need zones with 3+ transport types and 14,000 people near this and the 2 closest zones, OR zones with fewer than 2 competitors in sub category {Offices of Dentists} AND NOT more than 2 POIs in the same sub category.",
            "Thinking about launching a small wellness consultancy. Either zones should have 3+ transportation modes and over 13,000 population, OR fewer than 3 competitors in sub category {Offices of All Other Miscellaneous Health Practitioners} AND NOT 4 or more POIs nearby in that sub category.",
            "I'm looking to expand with a compact studio — either zones have 3+ transportation options and 12,000+ residents across 2 neighbors, OR there are fewer than 3 competitors in sub category {Offices of Lawyers} AND NOT more than 3 POIs in that sub category.",
            "I'm opening a wellness outpost. Either the zone has 3 modes of transport and 13,000+ people in this zone, OR fewer than 2 competitors exist in sub category {Offices of Real Estate Agents and Brokers} AND NOT more than 2 POIs of that type.",
            "I'm looking to expand with a compact studio — either zones have 4+ transportation options and 13,000+ residents across 2 neighbors, OR there are fewer than 2 competitors in sub category {Insurance Agencies and Brokerages} AND NOT more than 2 POIs in that sub category.",
            "Planning a creative writing retreat site. I want zones with 4+ transport access points and over 12,000 residents across 2 neighbors, OR a place with fewer than 2 competitors in sub category {Snack and Nonalcoholic Beverage Bars} AND NOT more than 2 POIs from that group.",
            "I'm searching for a zone for a public health annex. Give me spots with at least 4 kinds of transportation and 14,000+ residents in 2 adjacent zones, OR areas with fewer than 3 competitors in sub category {Offices of All Other Miscellaneous Health Practitioners} AND NOT zones with 2+ of those POIs.",
            "I'm opening a wellness outpost. Either the zone has 3 modes of transport and 14,000+ people near me and my closest zone, OR fewer than 2 competitors exist in sub category {Offices of All Other Miscellaneous Health Practitioners} AND NOT more than 2 POIs of that type.",
            "I'm searching for a zone for a public health annex. Give me spots with at least 3 kinds of transportation and 12,000+ residents in 2 adjacent zones, OR areas with fewer than 3 competitors in sub category {Offices of Physicians, Mental Health Specialists} AND NOT zones with 2+ of those POIs.",
            "I'm looking to expand with a compact studio — either zones have 4+ transportation options and 12,000+ residents across 2 neighbors, OR there are fewer than 2 competitors in sub category {Offices of Real Estate Agents and Brokers} AND NOT more than 3 POIs in that sub category.",
            "I'm searching for a zone for a public health annex. Give me spots with at least 3 kinds of transportation and 14,000+ residents in 2 adjacent zones, OR areas with fewer than 2 competitors in sub category {Offices of Lawyers} AND NOT zones with 3+ of those POIs.",
            "Planning a creative writing retreat site. I want zones with 4+ transport access points and over 14,000 residents across 3 neighbors, OR a place with fewer than 3 competitors in sub category {Offices of Physicians, Mental Health Specialists} AND NOT more than 3 POIs from that group.",


            #Hard 14: (Simple 8 AND NOT Simple 3) OR (Simple 7 AND Simple 9)
            "I'm opening a lifestyle shop — show me zones with at least 5 POIs from sub categories {Beauty Salons} and {Snack and Nonalcoholic Beverage Bars} AND NOT more than 2 parking lots, OR zones with at least 4 POIs in sub category {Art Dealers} AND at least 3 bus stops nearby.",
            "Looking to launch a cultural venue. I want zones that include 6+ POIs across sub category {Drinking Places (Alcoholic Beverages)} and {Snack and Nonalcoholic Beverage Bars} AND NOT zones with more than 2 parking lots, OR areas with 5+ POIs in sub category {Full-Service Restaurants} and at least 4 subway entrances.",
            "I'm scouting locations for a local market. Either I want zones with at least 5 POIs from sub categories {Gasoline Stations with Convenience Stores} and {Beer, Wine, and Liquor Stores} AND NOT 3 or more parking lots, OR zones with 6 POIs in sub category {Full-Service Restaurants} and 5+ stations nearby.",
            "Trying to open a walk-in tutoring center — show me zones with 4 or more POIs in sub categories {Exam Preparation and Tutoring} and {Elementary and Secondary Schools} AND NOT zones with more than 2 parking lots, OR areas with 5 POIs in sub category {Educational Support Services} and at least 4 taxi stands.",
            "Planning a nightlife spot. I need zones with 5+ POIs in sub categories {Drinking Places (Alcoholic Beverages)} and {Snack and Nonalcoholic Beverage Bars} AND NOT zones with 3 or more parking lots, OR at least 4 POIs in sub category {Beer, Wine, and Liquor Stores} and 3 nearby stations.",
            "I'm scouting for a food + drink plaza — either zones with at least 6 POIs from sub categories {Snack and Nonalcoholic Beverage Bars} and {Full-Service Restaurants} AND NOT more than 2 parking lots, OR areas with 4 POIs in sub category {Drinking Places (Alcoholic Beverages)} and at least 5 subway entrances.",
            "I want to open a tech wellness bar. Find me zones with 4+ POIs from sub categories {Beauty Salons} and {Snack and Nonalcoholic Beverage Bars} AND NOT more than 2 parking lots, OR zones with 5 POIs in sub category {Other Personal Care Services} and 4 nearby bus stops.",
            "Launching a studio café — show me zones with 5 POIs across sub category {Full-Service Restaurants} and sub category {Drinking Places (Alcoholic Beverages)} AND NOT zones that have more than 2 parking lots, OR areas with at least 6 POIs in sub category {Snack and Nonalcoholic Beverage Bars} and 3+ taxi stops nearby.",
            "Looking to place a small wine and arts lounge — find zones with 4 POIs across sub category {Art Dealers} and {Drinking Places (Alcoholic Beverages)} AND NOT areas with 3 or more parking lots, OR show zones with 5 POIs in sub category {Beer, Wine, and Liquor Stores} and at least 4 subway entrances.",
            "I'm evaluating sites for a hybrid gallery café. Either find zones with 6 POIs in sub categories {Art Dealers} and {Snack and Nonalcoholic Beverage Bars} AND NOT more than 2 parking lots, OR zones with 5 POIs in sub category {Full-Service Restaurants} and 4 nearby bus stops.",
            "I'm scouting a creative hub — show me zones with 4+ POIs from sub categories {Art Dealers} and sub category {Drinking Places (Alcoholic Beverages)} AND NOT more than 2 parking lots, OR zones with 6 POIs in sub category {Other Personal Care Services} and at least 5 bus stops.",
            "Launching a cozy venue — zones with 6+ POIs across {Full-Service Restaurants} and {Beer, Wine, and Liquor Stores} AND NOT zones with 2+ parking lots, OR spots with 5+ POIs in sub category {Elementary and Secondary Schools} and 4 or more transit hubs nearby.",
            "I'm looking at two layouts — either zones with 5 POIs across sub categories {Drinking Places (Alcoholic Beverages)} and {Gasoline Stations with Convenience Stores} AND NOT more than 3 parking lots, OR 6 POIs in sub category {Other Personal Care Services} and at least 4 transit hubs.",
            "Planning a hybrid retail concept. I want zones with at least 5 POIs from {Beer, Wine, and Liquor Stores} and {Full-Service Restaurants} AND NOT zones with 2+ parking lots, OR areas with 5+ POIs in sub category {Exam Preparation and Tutoring} and 5+ transit hubs nearby.",
            "I'm scouting a creative hub — show me zones with 6+ POIs from sub categories {Snack and Nonalcoholic Beverage Bars} and {Art Dealers} AND NOT more than 2 parking lots, OR zones with 6 POIs in sub category {Art Dealers} and at least 3 stations.",
            "Planning a hybrid retail concept. I want zones with at least 4 POIs from sub categories{Gasoline Stations with Convenience Stores} and {Elementary and Secondary Schools} AND NOT zones with 3+ parking lots, OR areas with 5+ POIs in sub category {Beauty Salons} and 5+ bus stops nearby.",
            "I'm scouting a creative hub — show me zones with 6+ POIs from sub categories {Elementary and Secondary Schools} and {Drinking Places (Alcoholic Beverages)} AND NOT more than 2 parking lots, OR zones with 6 POIs in sub category {Drinking Places (Alcoholic Beverages)} and at least 3 bus stops.",
            "Launching a cozy venue — zones with 6+ POIs across sub category {Drinking Places (Alcoholic Beverages)} and {Beauty Salons} AND NOT zones with 3+ parking lots, OR spots with 5+ POIs in sub category {Beer, Wine, and Liquor Stores} and 4 or more transit hubs nearby.",
            "I'm scouting a creative hub — show me zones with 6+ POIs from sub categories {Gasoline Stations with Convenience Stores} and {Snack and Nonalcoholic Beverage Bars} AND NOT more than 2 parking lots, OR zones with 5 POIs in sub category {Educational Support Services} and at least 4 taxi stands.",
            "Planning a hybrid retail concept. I want zones with at least 5 POIs from sub categories {Art Dealers} and {Drinking Places (Alcoholic Beverages)} AND NOT zones with 2+ parking lots, OR areas with 4+ POIs in sub category {Exam Preparation and Tutoring} and 4+ stations nearby.",

            #Hard 15: (Simple 4 AND Simple 6) NOT Simple 3 + Spend Filters #rerun
            "I'm planning a boutique smoothie bar in sub category {Snack and Nonalcoholic Beverage Bars}. Zones must have fewer than 2 competitors, 10,000+ population with nearby 1 zone, NOT more than 1 parking lot, and median spend per customer averaged over $180 between 2020–2023.",
            "Scouting areas for a youth-focused learning studio under sub category {Educational Support Services}. I need fewer than 3 competitors, population with 2 neighbors ≥ 12,000, NOT more than 2 parking lots, and yearly transactions > 180,000 in 2022.",
            "I'm opening a holistic health shop under {Other Personal Care Services}. Looking for zones with fewer than 3 competitors, population over 11,000 with adjacent 3 zones, NOT more than 2 parking lots, and average year-over-year spend growth > 7% from 2020–2023.",
            "Launching a plant-based café — I want under 3 competitors in sub category {Full-Service Restaurants}, at least 14,000 residents across my zone and 2 neighbors, NOT more than 2 parking lots, and total customer count from 2021 to 2024 must exceed 200,000.",
            "Seeking zones to open a home fragrance studio in sub category {All Other Home Furnishings Stores}. I need fewer than 2 competitors, 12,000+ residents in this zone, NOT more than 2 parking lots, and raw total spend above $40M from 2019–2022.",
            "I want to open a book café under sub category {Snack and Nonalcoholic Beverage Bars}. The zone must have fewer than 4 competitors, over 10,000 total population including 2 neighbors, NOT more than 2 parking lots, and average median spend per transaction > $22 from 2020 to 2023.",
            "Looking for a zone to open a design stationery shop under sub category {Other Miscellaneous Store Retailers}. Fewer than 2 competitors, population > 12,000 across 2 neighbor zones, NOT more than 1 parking lot, and average yearly spend growth > 4% between 2021–2024.",
            "Planning a boutique wine and spirits shop under sub category {Beer, Wine, and Liquor Stores}. I need fewer than 3 competitors, 10,000+ residents across my zone and 2 neighbors, NOT more than 2 parking lots, and median spend per customer > $240 from 2020 to 2023.",
            "I'm planning a mental wellness studio with sub category {Offices of Physicians, Mental Health Specialists}. I want zones with fewer than 2 competitors, combined population over 14,000 with 3 neighbors, NOT more than 2 parking lots, and average median spend per customer > $210 from 2020 to 2023.",
            "Looking to set up a mobile tech repair shop under sub category {Other Miscellaneous Store Retailers}. I need zones with fewer than 3 competitors, population across 2 neighbor zones > 12,000, NOT more than 1 parking lot, and total spend from 2021–2024 should exceed $38 million.",
            "Seeking a location for a small business accelerator under top category {Offices of Real Estate Agents and Brokers}. Must have fewer than 3 competitors, total local + 1 neighbor population above 10,000, NOT more than 2 parking lots, and spend growth year-over-year averaged over 8% between 2020 and 2023.",
            "I'm opening a student learning lounge under sub category {Exam Preparation and Tutoring}. Looking for areas with fewer than 2 competitors, population with 2 neighboring zones ≥ 13,000, NOT more than 1 parking lot, and more than 120,000 total transactions in 2023.",
            "Thinking of launching a quiet tea house under sub category {Snack and Nonalcoholic Beverage Bars}. Need zones with under 3 competitors, population across 4 neighbors above 11,000, NOT more than 2 parking lots, and median spend per transaction > $20 averaged from 2019 to 2022.",
            "Scouting a spot to open a language tutoring center in sub category {Educational Support Services}. I want fewer than 2 competitors, 12,000+ residents with 3 neighbors, NOT more than 2 parking lots, and customer counts > 90,000 from 2021 to 2023.",
            "Planning to open a fitness-themed bookstore café with sub category {Snack and Nonalcoholic Beverage Bars}. Show me zones with fewer than 3 competitors, at least 13,000 combined population with 2 neighbors, NOT more than 2 parking lots, and spend growth yearly > 4% across 2020–2023.",
            "Looking for zones to open a women-owned interior design concept store under sub category {Architectural Services}. I need fewer than 3 competitors, more than 12,000 people in my zone and 2 adjacent zones, NOT more than 1 parking lot, and total customers > 140,000 from 2021–2024.",
            "Launching a secondhand design boutique with sub category {Art Dealers}. I want fewer than 2 competitors, at least 11,000 population across 5 neighbors, NOT more than 2 parking lots, and raw total spend > $42M from 2020 to 2023.",

            #NEW! Hard 16   simple_17 AND simple_16 NOT simple_14
            "Looking to launch a creative co-working café — needs at least 26 POIs AND strong local spending, like 50%+ from sub-category of {Full-Service Restaurants} in 2022, but I’m not interested if that same category dominates the area by 30%.",
            "For my next wellness studio, the perfect zone needs 35+ POIs and a strong sub category {Beauty Salons} spend — over 40% in 2023. But don’t show me places where that category makes up more than 30% of POIs. Too much is too much.",
            "I'm opening a wellness hub and want a zone with at least 37 POIs, and more than 50% of total spending in 2019 should come from sub category {Educational Support Services}, but skip it if that category takes up more than 25% of all POIs — we need variety.",
            "I'm scouting a neighborhood for a family café. I want at least 39 POIs in the zone, and over 40% of spending in 2021 should come from sub category {Beauty Salons}, but it shouldn’t be overrun — cap that category at 30% of total POIs.",
            "I’m planning a boutique gym — give me a spot with at least 21 businesses, where folks spend at least 60% of their money in 2024 on sub category {Offices of Dentists}, but I’ll pass if that’s more than 30% of what's actually there.",
            "Looking to launch a creative co-working café — needs at least 45 POIs AND strong local spending, like 50%+ from sub category of {Snack and Nonalcoholic Beverage Bars} in 2020, but I’m not interested if that same category dominates the area (>25% of POIs).",
            "I'm opening a wellness hub and want a zone with at least 28 POIs, and more than 60% of total spending in 2020 should come from sub category of {Offices of Dentists}, but skip it if that category takes up more than 30% of all POIs — we need variety.",
            "Looking to launch a creative co-working café — needs at least 22 POIs AND strong local spending, like 60%+ from sub category of{Beauty Salons} in 2019, but I’m not interested if that same category dominates the area (>30% of POIs).",
            "I'm scouting a neighborhood for a family café. I want at least 45 POIs in the zone, and over 50% of spending in 2022 should come from sub-category of {Full-Service Restaurants}, but it shouldn’t be overrun — cap that category at 25% of total POIs.",
            "I'm opening a wellness hub and want a zone with at least 25 POIs, and more than 70% of total spending in 2024 should come from sub category {Offices of Dentists}, but skip it if that category takes up more than 30% of all POIs — we need variety.",
            "For my next wellness studio, the perfect zone needs 36+ POIs and a strong sub category {Beauty Salons} spend — over 60% in 2024. But don’t show me places where that category makes up more than 30% of POIs. Too much is too much.",
            "Looking to launch a creative co-working café — needs at least 24 POIs AND strong local spending, like 70%+ from from sub-category of {Snack and Nonalcoholic Beverage Bars} in 2020, but I’m not interested if that same category dominates the area (>25% of POIs).",
            "I'm scouting a neighborhood for a family café. I want at least 20 POIs in the zone, and over 70% of spending in 2021 should come from from sub-category of {Beauty Salons}, but it shouldn’t be overrun — cap that category at 35% of total POIs.",
            "I’m planning a boutique gym — give me a spot with at least 23 businesses, where folks spend at least 70% of their money in 2021 on sub category {Full-Service Restaurants}, but I’ll pass if that’s more than 30% of what's actually there.",
            "I'm opening a wellness hub and want a zone with at least 27 POIs, and more than 50% of total spending in 2020 should come from sub category {Beauty Salons}, but skip it if that category takes up more than 25% of all POIs — we need variety.",
            "Looking to launch a creative co-working café — needs at least 45 POIs AND strong local spending, like 40%+ from sub-category of {Educational Support Services} in 2024, but I’m not interested if that same category dominates the area (>35% of POIs).",
            "I'm scouting a neighborhood for a family café. I want at least 35 POIs in the zone, and over 50% of spending in 2021 should come from sub-category of {Full-Service Restaurants}, but it shouldn’t be overrun — cap that category at 30% of total POIs.",
            "Looking to launch a creative co-working café — needs at least 33 POIs AND strong local spending, like 60%+ from sub-category of {Full-Service Restaurants} in 2019, but I’m not interested if that same category dominates the area (>30% of POIs).",
            "I’m planning a boutique gym — give me a spot with at least 21 businesses, where folks spend at least 60% of their money in 2022 on sub category {Full-Service Restaurants}, but I’ll pass if that’s more than 25% of what's actually there.",
            "For my next wellness studio, the perfect zone needs 45+ POIs and a strong sub category {Educational Support Services} spend — over 60% in 2020. But don’t show me places where that category makes up more than 25% of POIs. Too much is too much.",
            "I'm opening a wellness hub and want a zone with at least 22 POIs, and more than 60% of total spending in 2023 should come from sub category {Offices of Dentists}, but skip it if that category takes up more than 30% of all POIs — we need variety.",
            "Looking to launch a creative co-working café — needs at least 41 POIs AND strong local spending, like 40%+ from sub category {Educational Support Services} in 2023, but I’m not interested if that same category dominates the area (>35% of POIs).",
            "I'm opening a wellness hub and want a zone with at least 39 POIs, and more than 60% of total spending in 2020 should come from sub category {Offices of Dentists}, but skip it if that category takes up more than 25% of all POIs — we need variety.",
            "For my next wellness studio, the perfect zone needs 43+ POIs and a strong sub category {Snack and Nonalcoholic Beverage Bars} spend — over 60% in 2023. But don’t show me places where that category makes up more than 25% of POIs. Too much is too much.",
            "I'm opening a wellness hub and want a zone with at least 39 POIs, and more than 50% of total spending in 2023 should come from sub category {Beauty Salons}, but skip it if that category takes up more than 30% of all POIs — we need variety.",
            "Looking to launch a creative co-working café — needs at least 45 POIs AND strong local spending, like 50%+ from sub category {Snack and Nonalcoholic Beverage Bars} in 2019, but I’m not interested if that same category dominates the area (>25% of POIs).",
            "Looking to launch a creative co-working café — needs at least 23 POIs AND strong local spending, like 70%+ from sub category {Snack and Nonalcoholic Beverage Bars} in 2023, but I’m not interested if that same category dominates the area (>35% of POIs).",
            "I'm scouting a neighborhood for a family café. I want at least 34 POIs in the zone, and over 60% of spending in 2021 should come from sub category {Beauty Salons}, but it shouldn’t be overrun — cap that category at 30% of total POIs.",
            "Looking to launch a creative co-working café — needs at least 28 POIs AND strong local spending, like 60%+ from sub-category of {Full-Service Restaurants} in 2022, but I’m not interested if that same category dominates the area (>25% of POIs).",



            #new ! Hard 17 simple_15 OR simple_16 NOT simple_14
            "I'm looking for one of two scenarios: either the area is dominated by sub category {Offices of Dentists}, or top category {Educational Support Services} gets over 70% of spend in 2022. But if {Educational Support Services} also takes up more than 40% of POIs, it's a no-go for me.",
            "I'm choosing a launch site. Either the sub category {Beauty Salons} should be the most common type in the zone, **OR** the top category {Lessors of Real Estate} should contribute over 60% of spending in 2021. But if {Lessors of Real Estate} already dominates more than 30% of POIs, count that zone out — I want diversity.",
            "I'm choosing a launch site. Either the sub category {Other Automotive Mechanical and Electrical Repair and Maintenance} should be the most common type in the zone, **OR** the top category {Advertising, Public Relations, and Related Services} should contribute over 50% of spending in 2023. But if {Advertising, Public Relations, and Related Services} already dominates more than 40% of POIs, count that zone out — I want diversity.",
            "I'm looking for one of two scenarios: either the area is dominated by sub category {Beauty Salons}, or top category {Educational Support Services} gets over 70% of spend in 2020. But if {Educational Support Services} also takes up more than 40% of POIs, it's a no-go for me.",
            "For my new project, I'm okay with areas where sub category {Jewelry Stores} leads in POI count, or top category {Legal Services} owns at least 50% of 2022's spend. Just avoid places where {Legal Services} overwhelms more than 40% of businesses.",
            "For my new project, I'm okay with areas where sub category {Other Automotive Mechanical and Electrical Repair and Maintenance} leads in POI count, or top category {Lessors of Real Estate} owns at least 40% of 2024's spend. Just avoid places where {Lessors of Real Estate} overwhelms more than 35% of businesses.",
            "I'm looking for one of two scenarios: either the area is dominated by sub category {Offices of Physicians, Mental Health Specialists}, or top category {Restaurants and Other Eating Places} gets over 40% of spend in 2020. But if {Restaurants and Other Eating Places} also takes up more than 35% of POIs, it's a no-go for me.",
            "I'm looking for one of two scenarios: either the area is dominated by sub category {Other Personal Care Services}, or top category {Offices of Physicians} gets over 60% of spend in 2020. But if {Offices of Physicians} also takes up more than 35% of POIs, it's a no-go for me.",
            "I'm looking for one of two scenarios: either the area is dominated by sub category {Hotels (except Casino Hotels) and Motels}, or top category {Advertising, Public Relations, and Related Services} gets over 50% of spend in 2020. But if {Advertising, Public Relations, and Related Services} also takes up more than 35% of POIs, it's a no-go for me.",
            "For my new project, I'm okay with areas where sub category {Lessors of Residential Buildings and Dwellings} leads in POI count, or top category {Legal Services} owns at least 40% of 2020's spend. Just avoid places where {Legal Services} overwhelms more than 25% of businesses.",
            "I'm choosing a launch site. Either the sub category {Full-Service Restaurants} should be the most common type in the zone, **OR** the top category {Advertising, Public Relations, and Related Services} should contribute over 60% of spending in 2019. But if {Advertising, Public Relations, and Related Services} already dominates more than 40% of POIs, count that zone out — I want diversity.",
            "I'm looking for one of two scenarios: either the area is dominated by sub category {Jewelry Stores}, or top category {Advertising, Public Relations, and Related Services} gets over 60% of spend in 2022. But if {Advertising, Public Relations, and Related Services} also takes up more than 25% of POIs, it's a no-go for me.",
            "For my new project, I'm okay with areas where sub category {Offices of Physicians, Mental Health Specialists} leads in POI count, or top category {Advertising, Public Relations, and Related Services} owns at least 50% of 2022's spend. Just avoid places where {Advertising, Public Relations, and Related Services} overwhelms more than 30% of businesses.",
            "I'm choosing a launch site. Either the sub category {Lessors of Residential Buildings and Dwellings} should be the most common type in the zone, **OR** the top category {Educational Support Services} should contribute over 70% of spending in 2021. But if {Educational Support Services} already dominates more than 30% of POIs, count that zone out — I want diversity.",
            "I'm choosing a launch site. Either the sub category {Lessors of Residential Buildings and Dwellings} should be the most common type in the zone, **OR** the top category {Lessors of Real Estate} should contribute over 50% of spending in 2022. But if {Lessors of Real Estate} already dominates more than 30% of POIs, count that zone out — I want diversity.",
            "I'm torn between zones: one where sub category {Travel Agencies} is the most common, or one where top category {Offices of Physicians} brings in over 60% of total spending in 2021. Still, skip zones where that top category exceeds 40% of all POIs — I want room to breathe.",
            "I'm torn between zones: one where sub category {Other Personal Care Services} is the most common, or one where top category {Offices of Physicians} brings in over 70% of total spending in 2022. Still, skip zones where that top category exceeds 35% of all POIs — I want room to breathe.",
            "I'm looking for one of two scenarios: either the area is dominated by sub category {General Automotive Repair}, or top category {Restaurants and Other Eating Places} gets over 50% of spend in 2023. But if {Restaurants and Other Eating Places} also takes up more than 30% of POIs, it's a no-go for me.",
            "I'm choosing a launch site. Either the sub category {Travel Agencies} should be the most common type in the zone, **OR** the top category {Offices of Physicians} should contribute over 50% of spending in 2021. But if {Offices of Physicians} already dominates more than 25% of POIs, count that zone out — I want diversity.",
            "For my new project, I'm okay with areas where sub category {Offices of Physicians, Mental Health Specialists} leads in POI count, or top category {Lessors of Real Estate} owns at least 60% of 2021's spend. Just avoid places where {Lessors of Real Estate} overwhelms more than 40% of businesses.",
            "I'm torn between zones: one where sub category {Hotels (except Casino Hotels) and Motels} is the most common, or one where top category {Advertising, Public Relations, and Related Services} brings in over 50% of total spending in 2019. Still, skip zones where that top category exceeds 30% of all POIs — I want room to breathe.",
            "I'm choosing a launch site. Either the sub category {General Automotive Repair} should be the most common type in the zone, **OR** the top category {Legal Services} should contribute over 70% of spending in 2023. But if {Legal Services} already dominates more than 25% of POIs, count that zone out — I want diversity.",
            "I'm torn between zones: one where sub category {General Automotive Repair} is the most common, or one where top category {Restaurants and Other Eating Places} brings in over 60% of total spending in 2022. Still, skip zones where that top category exceeds 30% of all POIs — I want room to breathe.",
            "For my new project, I'm okay with areas where sub category {Hotels (except Casino Hotels) and Motels} leads in POI count, or top category {Educational Support Services} owns at least 60% of 2020's spend. Just avoid places where {Educational Support Services} overwhelms more than 30% of businesses.",
            "For my new project, I'm okay with areas where sub category {Exam Preparation and Tutoring} leads in POI count, or top category {Advertising, Public Relations, and Related Services} owns at least 70% of 2021's spend. Just avoid places where {Advertising, Public Relations, and Related Services} overwhelms more than 35% of businesses.",
            "For my new project, I'm okay with areas where sub category {Other Automotive Mechanical and Electrical Repair and Maintenance} leads in POI count, or top category {Educational Support Services} owns at least 70% of 2023's spend. Just avoid places where {Educational Support Services} overwhelms more than 40% of businesses.",
            "For my new project, I'm okay with areas where sub category {Exam Preparation and Tutoring} leads in POI count, or top category {Offices of Physicians} owns at least 60% of 2020's spend. Just avoid places where {Offices of Physicians} overwhelms more than 30% of businesses.",
            "I'm torn between zones: one where sub category {Exam Preparation and Tutoring} is the most common, or one where top category {Lessors of Real Estate} brings in over 40% of total spending in 2021. Still, skip zones where that top category exceeds 40% of all POIs — I want room to breathe.",
            "For my new project, I'm okay with areas where sub category {Limited-Service Restaurants} leads in POI count, or top category {Educational Support Services} owns at least 50% of 2019's spend. Just avoid places where {Educational Support Services} overwhelms more than 35% of businesses.",
            "For my new project, I'm okay with areas where sub category {Jewelry Stores} leads in POI count, or top category {Restaurants and Other Eating Places} owns at least 70% of 2022's spend. Just avoid places where {Restaurants and Other Eating Places} overwhelms more than 35% of businesses."
]


