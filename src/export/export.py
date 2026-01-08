from __future__ import annotations

import geopandas as gpd
from datetime import datetime

from src.config.crs import to_4326, to_5179
from src.datasources import BBox, BuildingFetchOptions, MolitBuildingsWFS
from src.shadow.shadow_casting import cast_all_shadows
from src.geometry.geometry_utils import extract_edges, clean_geometry
from src.solar.sun_position import get_sun_position

from src.export.buildings import export_buildings_geojson
from src.export.shadow import export_shadow_geojson


def main():
    # 건물 로드 (KAIST 캠퍼스 좌표)
    bbox = BBox(west=127.355, south=36.370, east=127.375, north=36.380)
    src = MolitBuildingsWFS()
    opts = BuildingFetchOptions(target_crs="EPSG:4326", default_height_m=10.0)
    gdf = src.fetch(bbox, opts)  # EPSG:4326

    # 태양 위치 계산
    dt_local = datetime(2023, 12, 24, 10, 0, 0)
    azimuth, elevation = get_sun_position(
        lat=36.375,
        lon=127.365,
        dt=dt_local,
        tz_str="Asia/Seoul",
    )
    print(f"Azimuth: {azimuth:.2f}°, Elevation: {elevation:.2f}°")

    # 그림자 계산
    shadow_polygons = []
    gdf_5179 = to_5179(gdf)

    for _, row in gdf_5179.iterrows():
        geom = clean_geometry(row.geometry)
        edges = extract_edges(geom)
        shadow = cast_all_shadows(edges, row.height_m, azimuth, elevation)
        if shadow:
            shadow_polygons.append(shadow)

    shadow_gdf = gpd.GeoDataFrame(geometry=shadow_polygons, crs="EPSG:5179")
    shadow_gdf = to_4326(shadow_gdf)

    # Export (Cesium 업로드용)
    export_buildings_geojson(gdf, "outputs/buildings.geojson")
    export_shadow_geojson(
        shadow_gdf,
        "outputs/shadow.geojson",
        source="building",
        azimuth=azimuth,
        elevation=elevation,
        time_local=dt_local.isoformat(timespec="minutes"),
    )

    print("outputs/buildings.geojson, outputs/shadow.geojson 생성")


if __name__ == "__main__":
    main()