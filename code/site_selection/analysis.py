def get_spendparam_years(poi_spend_df, spendparm, year):
    """
    Computes an aggregated or average spending metric for a specified year across all POIs.

    Parameters:
    - poi_spend_df (pd.DataFrame): DataFrame containing POI-level data with time-specific spending columns.
    - spendparm (str): The base name of the spending parameter to compute. Must be one of:
        - Aggregated: {'RAW_TOTAL_SPEND', 'RAW_NUM_TRANSACTIONS', 'RAW_NUM_CUSTOMERS'}
        - Averaged: {'MEDIAN_SPEND_PER_TRANSACTION', 'MEDIAN_SPEND_PER_CUSTOMER', 'SPEND_PCT_CHANGE_VS_PREV_YEAR'}
    - year (int or str): The year of interest (e.g., 2022). The function looks for a column in the format '{spendparm}_{year}'.

    Returns:
    - float: 
        - Sum of values if the parameter is an aggregated metric.
        - Mean of values if the parameter is an averaged metric.
        - 0.0 if no valid data is found or an error occurs.
    
    Raises:
    - ValueError: If `spendparm` is invalid or the column for the specified year does not exist in the DataFrame.
    """
    try:
        aggregate_params = {
            'RAW_TOTAL_SPEND',
            'RAW_NUM_TRANSACTIONS',
            'RAW_NUM_CUSTOMERS'
        }

        average_params = {
            'MEDIAN_SPEND_PER_TRANSACTION',
            'MEDIAN_SPEND_PER_CUSTOMER',
            'SPEND_PCT_CHANGE_VS_PREV_YEAR'
        }

        valid_params = aggregate_params.union(average_params)
        year = str(year)
        column_name = f"{spendparm}_{year}"

        if spendparm not in valid_params:
            raise ValueError(f"Invalid spend parameter: {spendparm}")
        if column_name not in poi_spend_df.columns:
            raise ValueError(f"Column {column_name} not found in DataFrame")

        # Drop NA values to avoid skewing the result
        values = poi_spend_df[column_name].dropna()

        if values.empty:
            return 0.0

        return values.sum() if spendparm in aggregate_params else values.mean()

    except Exception as e:
        print(f"❌ Error in get_spendparam_years: {str(e)}")
        return 0.0


def get_num_parking(parking_df):
    """
    Returns the number of parking lots in a specific zone.

    Parameters:
    - parking_df: DataFrame with parking lot data (must include LATITUDE and LONGITUDE).
    - zone_id: The zone ID to filter by.

    Returns:
    - Integer count of parking lots in the specified zone.
    """
    return len(parking_df)


def get_largest_parking_lot_area(parking_df):
    """
    Returns the area (in square meters) of the largest parking lot in the specified zone.

    Parameters:
    - parking_df: DataFrame with 'zone_id' and 'WKT_AREA_SQ_METERS' columns.
    - zone_id: The zone to filter by.

    Returns:
    - Maximum area (float) of a parking lot in the zone. Returns 0 if no lots exist.
    """
    if parking_df.empty or 'WKT_AREA_SQ_METERS' not in parking_df.columns:
        return 0

    return parking_df['WKT_AREA_SQ_METERS'].max()


def get_largest_parking_capacity(parking_df):
    """
    Returns the estimated number of parking spaces in the largest parking lot,
    based on WKT area divided by 30 square meters per space.

    Parameters:
    - parking_df: DataFrame with a 'WKT_AREA_SQ_METERS' column.

    Returns:
    - Maximum estimated parking space count (float).
    """
    if parking_df.empty or 'WKT_AREA_SQ_METERS' not in parking_df.columns:
        return 0

    return max(parking_df['WKT_AREA_SQ_METERS'] / 30)

import math

def get_distance_km(lat1, lng1, lat2, lng2):
    """
    Calculates the haversine distance between two geographic coordinates.

    Parameters:
    - lat1, lng1: Latitude and longitude of point 1.
    - lat2, lng2: Latitude and longitude of point 2.

    Returns:
    - Distance in kilometers (float).
    """
    R = 6371.0  # Radius of the Earth in kilometers

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lng2 - lng1)

    a = math.sin(delta_phi / 2.0)**2 + \
        math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0)**2

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = R * c

    return distance
