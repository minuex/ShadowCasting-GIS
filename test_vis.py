import folium
import geopandas as gpd
from datetime import datetime

from src.config.crs import to_4326, to_5179
from src.datasources import BBox, BuildingFetchOptions, MolitBuildingsWFS
from src.shadow.shadow_casting import cast_all_shadows
from src.geometry.geometry_utils import extract_edges, clean_geometry
from src.solar.sun_position import get_sun_position


# 건물 로드
bbox = BBox(west=127.355, south=36.370, east=127.375, north=36.380)
src = MolitBuildingsWFS()
opts = BuildingFetchOptions(target_crs="EPSG:4326", default_height_m=10.0)
gdf = src.fetch(bbox, opts)

# 태양 위치 계산 (대전, 2023-12-24 10:00)
azimuth, elevation = get_sun_position(
    lat=36.375,
    lon=127.365,  
    dt=datetime(2023, 12, 24, 10, 0, 0),
    tz_str="Asia/Seoul",
)

print(f"Azimuth: {azimuth:.2f}°, Elevation: {elevation:.2f}°")

# 지도 생성
m = folium.Map(location=[36.3745, 127.365], zoom_start=18)

# 그림자 계산
shadow_polygons = []

# 좌표 변환: WGS84 → EPSG:5179 (계산용)
gdf_5179 = to_5179(gdf)

for _, row in gdf_5179.iterrows():
    geom = clean_geometry(row.geometry)
    edges = extract_edges(geom)
    shadow = cast_all_shadows(edges, row.height_m, azimuth, elevation)
    if shadow:
        shadow_polygons.append(shadow)

shadow_gdf = gpd.GeoDataFrame(geometry=shadow_polygons, crs="EPSG:5179")
shadow_gdf = to_4326(shadow_gdf)

# 건물 GeoJSON 추가 (표시용: EPSG:4326)
folium.GeoJson(
    gdf,
    name="Buildings",
    style_function=lambda x: {
        "color": "blue",
        "fillColor": "blue",
        "weight": 1,
        "fillOpacity": 0.4,
    },
).add_to(m)

# 그림자 GeoJSON 추가
folium.GeoJson(
    shadow_gdf,
    name="Shadows",
    style_function=lambda x: {
        "color": "black",
        "fillColor": "black",
        "weight": 0,
        "fillOpacity": 0.5,
    },
).add_to(m)

folium.LayerControl(collapsed=False).add_to(m)

m.save("outputs/shadow_map.html")
