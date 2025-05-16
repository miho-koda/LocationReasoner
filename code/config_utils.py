# config_utils.py

import os
import json

def get_project_root():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def resolve_paths(config_dict, base_path):
    """
    Convert all string values in the config to absolute paths
    if they are relative paths.
    """
    resolved = {}
    for key, val in config_dict.items():
        if isinstance(val, str) and not os.path.isabs(val):
            resolved[key] = os.path.abspath(os.path.join(base_path, val))
        else:
            resolved[key] = val
    return resolved

def load_config(filename="config.json", search_paths=None):
    project_root = get_project_root()

    if search_paths is None:
        search_paths = [project_root, os.path.join(project_root, "code")]

    for path in search_paths:
        candidate = os.path.join(path, filename)
        if os.path.exists(candidate):
            with open(candidate, "r") as f:
                raw_config = json.load(f)
            config = resolve_paths(raw_config, project_root)
            config["project_root"] = project_root
            return config

    raise FileNotFoundError(f"{filename} not found in search paths: {search_paths}")
