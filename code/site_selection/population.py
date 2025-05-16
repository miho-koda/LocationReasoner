import geopandas as gpd
import pandas as pd
import os
import zipfile
GLOBAL_SHP = None

import os
import pandas as pd
import geopandas as gpd
from shapely.prepared import prep



from config_utils import load_config

config = load_config()


POP_DIR = config.get("population_dir")


def preload_population_shapefile():
    global GLOBAL_SHP

    try:
        csv_path = os.path.join(POP_DIR, "Massachusetts.csv")
        shp_dir = os.path.join(POP_DIR, "shp")

        pop = pd.read_csv(csv_path, skiprows=1)
        pop["GEOID"] = pop["Geography"].str.replace("1500000US", "", regex=False)
        pop = pop[["GEOID", "Estimate!!Total"]].rename(columns={"Estimate!!Total": "population"})

        shp_file = next((os.path.join(shp_dir, f) for f in os.listdir(shp_dir) if f.endswith(".shp")), None)
        if not shp_file:
            raise FileNotFoundError("No .shp file found in the 'shp' directory")

        shp = gpd.read_file(shp_file).to_crs("EPSG:4326")
        shp = shp.merge(pop, on="GEOID")

        # Prepare geometries once for faster intersection
        shp["prepared_geom"] = shp["geometry"].apply(prep)

        GLOBAL_SHP = shp
        print("✅ Population shapefile preloaded with prepared geometries.")

    except Exception as e:
        print(f"❌ Failed to preload shapefile: {e}")
        GLOBAL_SHP = None



import os
import pandas as pd
import geopandas as gpd

# Global variables
GLOBAL_SHP = None
POPULATION_DF = None  # New global variable to store pre-computed populations

def precompute_all_zone_populations(zone_df):
    """
    Precompute population for all zones and store in a dataframe
    """
    global GLOBAL_SHP, POPULATION_DF
    
    try:
        if GLOBAL_SHP is None:
            preload_population_shapefile()
            
        if GLOBAL_SHP is None:
            raise ValueError("Failed to load population shapefile")
            
        # Create empty dataframe to store results
        POPULATION_DF = pd.DataFrame(columns=['zone_id', 'population'])
        
        # Process all zones
        populations = []
        for zone_id in zone_df['zone_id'].unique():
            zone_geom = zone_df.loc[zone_df['zone_id'] == zone_id, 'geometry'].iloc[0]
            
            # Use spatial index if available, otherwise do direct intersection
            if hasattr(GLOBAL_SHP, 'sindex'):
                possible_matches_idx = list(GLOBAL_SHP.sindex.intersection(zone_geom.bounds))
                possible_matches = GLOBAL_SHP.iloc[possible_matches_idx]
                matches = possible_matches[possible_matches.geometry.intersects(zone_geom)]
            else:
                matches = GLOBAL_SHP[GLOBAL_SHP.geometry.intersects(zone_geom)]
                
            pop = int(matches["population"].sum())
            populations.append({'zone_id': zone_id, 'population': pop})
            
        # Create dataframe from results
        POPULATION_DF = pd.DataFrame(populations)
        POPULATION_DF.set_index('zone_id', inplace=True)
        
        print(f"✅ Population precomputed for {len(POPULATION_DF)} zones")
        return POPULATION_DF
        
    except Exception as e:
        print(f"❌ Error precomputing zone populations: {str(e)}")
        return None

def get_population(zone_id, zone_df):
    """
    Get population for a specific zone.
    If zone is not in precomputed populations, calculate it directly instead of returning 0.
    """
    global POPULATION_DF, GLOBAL_SHP
    
    try:
        # Check if we have precomputed populations
        if POPULATION_DF is None:
            print("ℹ️ Population data not precomputed. Computing now...")
            precompute_all_zone_populations(zone_df)
        
        # If the zone is in our precomputed dataframe, return that value
        if zone_id in POPULATION_DF.index:
            return POPULATION_DF.loc[zone_id, 'population']
        else:
            # Zone not found in precomputed data, calculate it directly
            #print(f"⚠️ Zone ID {zone_id} not found in precomputed populations, calculating directly")
            
            # Make sure GLOBAL_SHP is loaded
            if GLOBAL_SHP is None:
                preload_population_shapefile()
            
            # Get zone geometry
            if zone_id in zone_df['zone_id'].values:
                zone_geom = zone_df.loc[zone_df['zone_id'] == zone_id, 'geometry'].iloc[0]
                
                # Find population shapefile areas that intersect with this zone
                if hasattr(GLOBAL_SHP, 'sindex'):
                    possible_matches_idx = list(GLOBAL_SHP.sindex.intersection(zone_geom.bounds))
                    possible_matches = GLOBAL_SHP.iloc[possible_matches_idx]
                    matches = possible_matches[possible_matches.geometry.intersects(zone_geom)]
                else:
                    matches = GLOBAL_SHP[GLOBAL_SHP.geometry.intersects(zone_geom)]
                
                # Calculate population
                pop = int(matches["population"].sum())
                
                # Add to our precomputed dataframe for future use
                if POPULATION_DF is not None:
                    POPULATION_DF.loc[zone_id] = pop
                
                return pop
            else:
                print(f"❌ Zone ID {zone_id} not found in zone dataframe")
                return 0
    
    except Exception as e:
        print(f"❌ Error retrieving population for zone {zone_id}: {str(e)}")
        # Fall back to 0 only if there's an error
        return 0
    

