import pandas as pd
import os
import glob
import gzip
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing
import time
import functools
import traceback
import os
import json
import pandas as pd




from config_utils import load_config

config = load_config()



POI_SPEND_PATH = config.get("poi_spend_path")
PARKING_PATH = config.get("parking_path")


def get_poi_spend_dataset():
    """
    Load the POI spend dataset for all years.
    """
    
    poi_spend_df = pd.read_csv(POI_SPEND_PATH)
    return poi_spend_df



def get_parking_dataset():
    """
    Load parking dataset for a specific state and optionally filter by city.
    
   
    Returns:
        pandas.DataFrame: Parking dataset, filtered by city if specified
    """
    parking_df = pd.read_csv(PARKING_PATH)
    return parking_df

