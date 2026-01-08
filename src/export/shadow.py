from __future__ import annotations

from pathlib import Path
from typing import Optional
import geopandas as gpd


def export_shadow_geojson(
    gdf_shadow: gpd.GeoDataFrame,
    out_path: str | Path,
    *,
    source: str = "building",
    azimuth: Optional[float] = None,
    elevation: Optional[float] = None,
    time_local: Optional[str] = None,
) -> Path:
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if gdf_shadow.empty:
        raise ValueError("gdf_shadow is empty.")

    if gdf_shadow.crs is None:
        raise ValueError("gdf_shadow has no CRS.")

    gdf = gdf_shadow.to_crs("EPSG:4326").copy()

    gdf["source"] = source
    if azimuth is not None:
        gdf["sun_az"] = float(azimuth)
    if elevation is not None:
        gdf["sun_el"] = float(elevation)
    if time_local is not None:
        gdf["time_local"] = time_local

    gdf.to_file(out_path, driver="GeoJSON")
    return out_path