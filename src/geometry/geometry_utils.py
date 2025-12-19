# src/geometry/cleanup.py
from shapely.geometry import Polygon, MultiPolygon, LineString
from typing import List
import geopandas as gpd

def clean_geometry(geom):
    if geom is None:
        return None
    if not geom.is_valid:
        geom = geom.buffer(0)
    return geom

# 폴리곤 외곽에서 엣지 선분들을 추출
# interior ring은 무시
def extract_edges(geom: Polygon | MultiPolygon) -> List[LineString]:
    edges = []

    if geom.geom_type == "Polygon":
        rings = [geom.exterior]
    elif geom.geom_type == "MultiPolygon":
        rings = [p.exterior for p in geom.geoms]
    else:
        return edges  # point, line 등은 무시

    for ring in rings:
        coords = list(ring.coords)
        for i in range(len(coords) - 1):
            a, b = coords[i], coords[i + 1]
            edge = LineString([a, b])
            if edge.length > 0:
                edges.append(edge)

    return edges
