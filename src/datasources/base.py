from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional

import geopandas as gpd

# bbox는 항상 WGS84(lon/lat), 계산할땐 INTERNAL_CRS로 변환
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
    target_crs: str = "EPSG:4326"          
    default_height_m: float = 10.0         
    keep_raw_properties: bool = True       


class BuildingSource(ABC):
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
