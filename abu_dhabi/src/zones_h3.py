# src/zones_h3.py
from typing import Tuple, List
import pandas as pd
import json

# Try v4 import first, fall back to v3 layout
try:
    import h3 as _h3  # v4
except Exception:
    from h3 import h3 as _h3  # v3

def _to_cell(lat: float, lng: float, res: int) -> str:
    if hasattr(_h3, "latlng_to_cell"):       # v4
        return _h3.latlng_to_cell(lat, lng, res)
    return _h3.geo_to_h3(lat, lng, res)      # v3

def _cell_to_latlng(cell: str) -> Tuple[float, float]:
    if hasattr(_h3, "cell_to_latlng"):       # v4
        lat, lng = _h3.cell_to_latlng(cell)
    else:                                    # v3
        lat, lng = _h3.h3_to_geo(cell)
    return float(lat), float(lng)

def _cell_boundary_geojson(cell: str) -> List[List[float]]:
    """
    Return the hex boundary as GeoJSON ring: [[lng, lat], ...]
    Handles both v3 and v4 without using geo_json= kwarg.
    """
    if hasattr(_h3, "cell_to_boundary"):     # v4
        coords = _h3.cell_to_boundary(cell)  # typically [(lat, lng), ...]
    elif hasattr(_h3, "h3_to_geo_boundary"): # v3
        # v3 has a geo_json=True arg, but avoid kwargs for max compat
        coords = _h3.h3_to_geo_boundary(cell, True)
    else:
        from h3 import h3 as _legacy
        coords = _legacy.h3_to_geo_boundary(cell, True)

    ring = []
    for c in coords:
        # normalize tuple vs object
        try:
            lat, lng = float(c[0]), float(c[1])
        except Exception:
            lat, lng = float(c.lat), float(c.lng)
        ring.append([lng, lat])  # GeoJSON order
    # ensure closed ring
    if ring and (ring[0] != ring[-1]):
        ring.append(ring[0])
    return ring

def assign_h3_zones(poi_df: pd.DataFrame, h3_res: int = 8) -> pd.DataFrame:
    """
    Adds 'zone_id' column as H3 cell at the chosen resolution.
    """
    poi_df = poi_df.copy()
    poi_df["zone_id"] = [
        _to_cell(float(lat), float(lon), h3_res)
        for lat, lon in zip(poi_df["lat"].values, poi_df["lon"].values)
    ]
    return poi_df

def build_zone_df(poi_with_zone: pd.DataFrame) -> pd.DataFrame:
    zones = []
    for zid in sorted(poi_with_zone["zone_id"].unique()):
        lat, lng = _cell_to_latlng(zid)
        zones.append({"zone_id": zid, "center_lat": lat, "center_lng": lng})
    return pd.DataFrame(zones)

def zones_to_geojson(zone_df: pd.DataFrame, out_path: str):
    features = []
    for _, z in zone_df.iterrows():
        boundary = _cell_boundary_geojson(z["zone_id"])  # [[lng,lat],...]
        features.append({
            "type": "Feature",
            "geometry": {"type": "Polygon", "coordinates": [boundary]},
            "properties": {
                "zone_id": z["zone_id"],
                "center_lat": z["center_lat"],
                "center_lng": z["center_lng"],
            },
        })
    gj = {"type": "FeatureCollection", "features": features}
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(gj, f, ensure_ascii=False)
