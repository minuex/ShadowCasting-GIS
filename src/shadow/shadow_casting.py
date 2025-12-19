# src/shadow/shadow_casting.py

from shapely.geometry import LineString, Polygon
from shapely.affinity import translate
from typing import List, Tuple
import math
from shapely.ops import unary_union

def shadow_direction_vector(azimuth_deg: float) -> Tuple[float, float]:
    """
    방위각(도)을 단위 벡터(dx, dy)로 변환. 북=0°, 동=90°, 시계방향 기준.
    """
    theta_rad = math.radians((azimuth_deg + 180) % 360)  # 그림자 방향은 태양 반대
    dx = math.sin(theta_rad)
    dy = math.cos(theta_rad)
    return dx, dy

def cast_shadow(edge: LineString, height_m: float, azimuth_deg: float, altitude_deg: float) -> Polygon:
    """
    하나의 edge 선분과 건물 높이로 그림자 사다리꼴 생성.
    """
    if altitude_deg <= 0:
        return None  # 태양이 수평선 아래 → 그림자 없음

    length = height_m / math.tan(math.radians(altitude_deg))  # 그림자 길이
    dx, dy = shadow_direction_vector(azimuth_deg)

    a, b = list(edge.coords)
    a2 = (a[0] + dx * length, a[1] + dy * length)
    b2 = (b[0] + dx * length, b[1] + dy * length)

    return Polygon([a, b, b2, a2])

# 모든 edge -> 그림자 사다리꼴 생성 -> 합집합 해서 전체 그림자 폴리곤 반환
def cast_all_shadows(
    edges: List[LineString],
    height_m: float,
    azimuth_deg: float,
    altitude_deg: float,
) -> Polygon:

    shadows = [
        cast_shadow(edge, height_m, azimuth_deg, altitude_deg)
        for edge in edges
        if edge.length > 0
    ]
    shadows = [p for p in shadows if p is not None]
    if not shadows:
        return None
    return unary_union(shadows)
