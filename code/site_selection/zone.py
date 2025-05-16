import pandas as pd
from sklearn.cluster import MiniBatchKMeans
from shapely.geometry import Point, Polygon, MultiPoint
from scipy.spatial import ConvexHull
import geopandas as gpd
import numpy as np

def assign_poi_zones(poi_df, n_clusters=2000):
    """
    Assigns a zone_id to each POI using MiniBatchKMeans clustering and returns:
    - Updated poi_df with 'zone_id' column
    - zone_df: list of zone geometries and metadata
    """
    if poi_df.empty:
        print("POI DataFrame is empty. Cannot assign zones.")
        return poi_df, pd.DataFrame()

    print('Dividing POIs into zones...')

    coords = poi_df[['LATITUDE', 'LONGITUDE']].values
    kmeans = MiniBatchKMeans(n_clusters=n_clusters, batch_size=10000).fit(coords)
    poi_df['zone_id'] = kmeans.labels_
    
    return poi_df


def create_zone(poi_df):
    """
    Creates zone geometries and metadata based on clustered POIs (must have 'zone_id').
    Returns a GeoDataFrame of zones with polygon geometries.
    """
    if 'zone_id' not in poi_df.columns:
        raise ValueError("POI DataFrame must contain a 'zone_id' column")

    zones = []
    for zone_id in poi_df['zone_id'].unique():
        zone_points = poi_df[poi_df['zone_id'] == zone_id][['LONGITUDE', 'LATITUDE']].values
        if len(zone_points) == 0:
            continue

        if len(zone_points) < 3:
            multipoint = MultiPoint([Point(p) for p in zone_points])
            zone_geometry = multipoint.buffer(0.01)
        else:
            try:
                hull = ConvexHull(zone_points)
                hull_points = zone_points[hull.vertices]
                hull_points = np.append(hull_points, [hull_points[0]], axis=0)
                zone_geometry = Polygon(hull_points)
            except:
                multipoint = MultiPoint([Point(p) for p in zone_points])
                zone_geometry = multipoint.buffer(0.01)

        centroid = zone_geometry.centroid
        zones.append({
            'zone_id': zone_id,
            'geometry': zone_geometry,
            'center_lat': centroid.y,
            'center_lng': centroid.x,
            'num_pois': len(zone_points)
        })

    zone_df = gpd.GeoDataFrame(zones, geometry='geometry', crs="EPSG:4326")
    return zone_df


def assign_parking_zones(parking_df, zone_df):
    """
    Assigns a zone_id to each parking location via spatial join.
    Removes parking locations that don't fall within any zone.
    Given zone_df is baed on poi_df, which can be based on city or region(State), so there are probably rows where no zone_id id assigned to some parking since they are processed as region(State). Parking lots that doesn't fall within any zone are removed.

    Parameters:
    - parking_df: DataFrame with 'LATITUDE' and 'LONGITUDE' columns.
    - zone_df: GeoDataFrame with zone polygons and 'zone_id'.

    Returns:
    -  parking locations and assigned 'zone_id', excluding unmatched locations.
    """
    if parking_df.empty or zone_df.empty:
        print("Either parking_df or zone_df is empty. Skipping zone assignment.")
        return parking_df

    # Convert parking_df to GeoDataFrame using point geometries
    parking_gdf = gpd.GeoDataFrame(
        parking_df.copy(),
        geometry=gpd.points_from_xy(parking_df['LONGITUDE'], parking_df['LATITUDE']),
        crs="EPSG:4326"
    )

    # Ensure CRS matches
    if zone_df.crs != "EPSG:4326":
        zone_df = zone_df.to_crs("EPSG:4326")

    # Spatial join: assign zone_id to each parking point
    joined = gpd.sjoin(
        parking_gdf,
        zone_df[['zone_id', 'geometry']],
        how="inner",          # Changed from "left" to "inner" to keep only matched points
        predicate="within"    # Match points that fall inside zone polygons
    )

    # Clean up join metadata
    joined.drop(columns=["index_right"], inplace=True, errors="ignore")

    # Print info about dropped parking spaces
    dropped_count = len(parking_df) - len(joined)
    if dropped_count > 0:
        print(f"Removed {dropped_count} parking spaces that didn't fall within any zone")
        print(f"Remaining parking spaces: {len(joined)}")

    return joined

def get_neighbor_zones(zone_df, zone_id, num):
    """
    Finds the `num` closest zones to the given `zone_id` using centroid-to-centroid distance.
    Projects geometries to an appropriate projected CRS (UTM) before calculating distances.

    Parameters:
    - zone_id: the reference zone
    - num: number of neighbors to return
    - zone_df: GeoDataFrame with zone geometries and 'zone_id' column

    Returns:
    - List of nearest zone_ids (excluding the input zone)
    """
    if zone_id not in zone_df['zone_id'].values:
        raise ValueError(f"Zone ID {zone_id} not found in zone_df.")

    if 'geometry' not in zone_df.columns:
        raise ValueError("zone_df must contain a 'geometry' column.")

    # Get the center point of the target zone to determine UTM zone
    target_zone = zone_df[zone_df['zone_id'] == zone_id].iloc[0]
    target_lon = target_zone.geometry.centroid.x
    target_lat = target_zone.geometry.centroid.y
    
    # Calculate UTM zone number
    utm_zone = int((target_lon + 180) / 6) + 1
    
    # Determine if we're in northern or southern hemisphere
    hemisphere = 'north' if target_lat > 0 else 'south'
    
    # Construct EPSG code for the appropriate UTM zone
    # UTM zones are 32601-32660 for northern hemisphere
    # and 32701-32760 for southern hemisphere
    epsg = 32600 + utm_zone if hemisphere == 'north' else 32700 + utm_zone
    
    # Project the geometries to the appropriate UTM zone
    zone_df_projected = zone_df.copy()
    zone_df_projected = zone_df_projected.to_crs(epsg=epsg)
    
    # Calculate centroids in the projected CRS
    zone_df_projected['centroid'] = zone_df_projected.geometry.centroid
    
    # Get target centroid
    target_centroid = zone_df_projected.loc[zone_df_projected['zone_id'] == zone_id, 'centroid'].values[0]
    
    # Compute distances to all other centroids (now in meters)
    distances = []
    for _, row in zone_df_projected.iterrows():
        other_id = row['zone_id']
        if other_id == zone_id:
            continue
        # Distance will now be in meters since we're using a projected CRS
        dist = target_centroid.distance(row['centroid'])
        distances.append((other_id, dist))
    
    # Sort and return closest zone_ids
    distances.sort(key=lambda x: x[1])
    return [zid for zid, _ in distances[:num]]





def get_zone_center(zone_df, zone_id):
    """
    Returns the center coordinates (latitude, longitude) of a given zone.
    
    Parameters:
    - zone_df: GeoDataFrame with 'zone_id', 'center_lat', and 'center_lng' columns.
    - zone_id: The ID of the zone to look up.
    
    Returns: A tuple (center_lat, center_lng).
    """
    zone = zone_df[zone_df['zone_id'] == zone_id]
    if zone.empty:
        raise ValueError(f"Zone {zone_id} not found in zone_df")
    
    return (zone['center_lat'].iloc[0], zone['center_lng'].iloc[0])

   