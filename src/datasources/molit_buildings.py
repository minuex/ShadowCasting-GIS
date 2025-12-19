# src/datasources/molit_buildings.py
from __future__ import annotations

import os
import tempfile
from typing import Optional

import geopandas as gpd
import requests
from dotenv import load_dotenv
import pandas as pd

from .base import BBox, BuildingFetchOptions, BuildingSource

# .env (환경변수=키/도메인) 로드
load_dotenv()

# GIS건물일반정보WFS조회
class MolitBuildingsWFS(BuildingSource):
    name = "molit_wfs_dt_d162"

    def __init__(
        self,
        api_key: Optional[str] = None,
        domain: Optional[str] = None,
        typename: str = "dt_d162",
        timeout_s: int = 30,
    ):
        self.api_key = api_key or os.getenv("VWORLD_KEY")
        self.domain = domain or os.getenv("VWORLD_DOMAIN") 
        self.typename = typename
        self.timeout_s = timeout_s

        self.url = "https://api.vworld.kr/ned/wfs/getGisGnrlBuildingWFS"

    def fetch(self, bbox: BBox, opts: BuildingFetchOptions) -> gpd.GeoDataFrame:
        bbox.validate()

        # EPSG:4326 bbox: (ymin, xmin, ymax, xmax)
        ymin, xmin, ymax, xmax = bbox.south, bbox.west, bbox.north, bbox.east
        bbox_param = f"{ymin},{xmin},{ymax},{xmax},EPSG:4326"

        params = {
            "key": self.api_key,
            "domain": self.domain,
            "typename": self.typename,
            "bbox": bbox_param,
            "maxFeatures": 1000,  # 문서상 최대 1000
            "resultType": "results",
            "srsName": "EPSG:4326",
            "output": "text/xml; subtype=gml/2.1.2",
        }
        
        print("Request URL:", self.url)
        print("Request Params:", params)

        r = requests.get(self.url, params=params, timeout=self.timeout_s)
        r.raise_for_status()

        ct = r.headers.get("Content-Type", "")
        print("HTTP:", r.status_code, "Content-Type:", ct)
        print("HEAD(200):", r.text[:200]) 

        if "xml" not in ct.lower() and "gml" not in ct.lower():
            raise RuntimeError(f"Unexpected response Content-Type: {ct}\nHEAD:\n{r.text[:500]}")

        if "Exception" in r.text or "error" in r.text.lower():
            raise RuntimeError(f"WFS returned error XML/HTML:\n{r.text[:800]}") 

        with tempfile.NamedTemporaryFile(suffix=".gml", delete=False) as f:
            f.write(r.content)
            tmp_path = f.name

        try:
            gdf = gpd.read_file(tmp_path) 
        finally:
            try:
                os.remove(tmp_path)
            except OSError:
                pass

        if gdf.empty:
            return gpd.GeoDataFrame(
                {"height_m": [], "ground_floors": [], "total_area": []},
                geometry=[],
                crs=opts.target_crs,
            )

#############################################################################
        # 폴리곤만 유지
        gdf = gdf[gdf.geometry.type.isin(["Polygon", "MultiPolygon"])].copy()

        field_mapping = {
            "buld_hg": "height_m",  # 건물 높이 (m)
            "ground_floor_co": "floors",  # 지상층수
            "buld_totar": "total_area"  # 건물 연면적 (㎡)
        }

        gdf = gdf.rename(columns=field_mapping)
        gdf = gdf[["height_m", "floors", "total_area", "geometry"]]
        
        # 결측치, 정규화, 중복제거
        # height
        gdf["height_m"] = (gdf["height_m"].astype(str).str.replace("m", "", regex=False).str.strip())
        gdf["height_m"] = pd.to_numeric(gdf["height_m"], errors="coerce")
        gdf["height_m"] = gdf["height_m"].fillna(opts.default_height_m).astype(float)

        # total_area
        gdf["total_area"] = pd.to_numeric(gdf["total_area"], errors="coerce")

        #geometry
        gdf["geometry"] = gdf["geometry"].buffer(0)
        gdf = gdf[~gdf.geometry.is_empty & gdf.geometry.notnull()]

        gdf["__geom_wkb__"] = gdf.geometry.apply(lambda g: g.wkb)
        gdf = gdf.drop_duplicates(subset="__geom_wkb__").drop(columns="__geom_wkb__")

        # 4326으로 변환
        if gdf.crs is None:
            gdf = gdf.set_crs("EPSG:4326")
        gdf = gdf.to_crs(opts.target_crs)

        return gdf
