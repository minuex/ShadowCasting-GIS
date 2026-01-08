# 디버깅용 (건물 footprint -> GeoJSON)
from __future__ import annotations

from pathlib import Path
import geopandas as gpd


def export_buildings_geojson(gdf_buildings: gpd.GeoDataFrame, out_path: str | Path) -> Path:
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if gdf_buildings.empty:
        raise ValueError("gdf_buildings is empty.")

    if gdf_buildings.crs is None:
        raise ValueError("gdf_buildings has no CRS.")

    gdf = gdf_buildings.to_crs("EPSG:4326")
    gdf.to_file(out_path, driver="GeoJSON")
    return out_path
