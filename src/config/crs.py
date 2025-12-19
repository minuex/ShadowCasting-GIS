# src/config/crs.py
#WGS84_EPSG = 4326  # 위경도 / WGS84
#PROJECTED_EPSG = 5179  # UTM-K (미터 연산용)

def to_5179(gdf):
    return gdf.to_crs(epsg=5179)

def to_4326(gdf):
    return gdf.to_crs(epsg=4326)