# src/datasources/base.py
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional

import geopandas as gpd

# bbox는 항상 WGS84(lon/lat)로 받고, 계산은 나중에 INTERNAL_CRS로 변환하는 구조
@dataclass(frozen=True)
class BBox:
    west: float
    south: float
    east: float
    north: float

    def validate(self) -> None:
        if not (-180.0 <= self.west <= 180.0 and -180.0 <= self.east <= 180.0):
            raise ValueError(f"Invalid longitude in bbox: {self.west}, {self.east}")
        if not (-90.0 <= self.south <= 90.0 and -90.0 <= self.north <= 90.0):
            raise ValueError(f"Invalid latitude in bbox: {self.south}, {self.north}")
        if self.west >= self.east:
            raise ValueError(f"west must be < east (got {self.west} >= {self.east})")
        if self.south >= self.north:
            raise ValueError(f"south must be < north (got {self.south} >= {self.north})")


@dataclass(frozen=True)
class BuildingFetchOptions:
    target_crs: str = "EPSG:4326"          # CRS of returned GeoDataFrame
    default_height_m: float = 10.0         # fallback if no height is available
    keep_raw_properties: bool = True       # keep original columns


class BuildingSource(ABC):
    """
    Fetch buildings as polygons with a normalized height_m column (meters).
    """
    name: str = "base"

    @abstractmethod
    def fetch(self, bbox: BBox, opts: BuildingFetchOptions) -> gpd.GeoDataFrame:
        raise NotImplementedError


def safe_float(x: Any) -> Optional[float]:
    if x is None:
        return None
    s = str(x).strip()
    if s.lower() in {"nan", "none", ""}:
        return None
    try:
        return float(s.replace("m", "").strip())
    except Exception:
        return None


def normalize_height_from_hr(props: Dict[str, Any], default_height_m: float) -> float:
    for key in ["buld_hg", "hg", "hr"]:
        v = safe_float(props.get(key))
        if v is not None:
            return v
    return float(default_height_m)
