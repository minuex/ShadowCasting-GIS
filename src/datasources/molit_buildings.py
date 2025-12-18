# src/datasources/molit_buildings.py
from __future__ import annotations

import os
import tempfile
from typing import Optional

import geopandas as gpd
import requests
from dotenv import load_dotenv
import pandas as pd

from .base import BBox, BuildingFetchOptions, BuildingSource, normalize_height_from_hr

# .env (환경변수=키/도메인) 로드
load_dotenv()


class MolitBuildingsWFS(BuildingSource):
    """
    VWorld NED 건물공간정보 WFS (getBldgisSpceWFS)
    - typename: dt_d010
    - EPSG:4326 bbox order is (ymin, xmin, ymax, xmax)
    - hr: height (m), ar: area (㎡)
    """
    name = "molit_wfs_dt_d010"

    def __init__(
        self,
        api_key: Optional[str] = None,
        domain: Optional[str] = None,
        typename: str = "dt_d010",
        timeout_s: int = 30,
    ):
        self.api_key = api_key or os.getenv("VWORLD_KEY")
        self.domain = domain or os.getenv("VWORLD_DOMAIN") 
        self.typename = typename
        self.timeout_s = timeout_s

        self.url = "https://api.vworld.kr/ned/wfs/getBldgisSpceWFS"

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
        print("HEAD(200):", r.text[:200])  # 앞 200자만

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
                {"height_m": [], "source": []},
                geometry=[],
                crs=opts.target_crs,
            )

        # 폴리곤만 유지
        gdf = gdf[gdf.geometry.type.isin(["Polygon", "MultiPolygon"])].copy()

#################높이 컬럼 매핑##################
        # 높이 hr -> height_m
        # (혹시 문자열/None 섞여 있는 것도 처리
        height_col = ["hg", "hr"]

        height_col = next((c for c in height_col if c in gdf.columns), None)

        if height_col is not None:
            s = gdf[height_col].astype(str).str.replace("m", "", regex=False).str.strip()
            gdf["height_m"] = pd.to_numeric(s, errors="coerce")
        else:
            gdf["height_m"] = pd.NA

        gdf["height_m"] = gdf["height_m"].fillna(opts.default_height_m).astype(float)   

        gdf["source"] = self.name

        # 표준 CRS로 변환
        if gdf.crs is None:
            gdf = gdf.set_crs("EPSG:4326")
        gdf = gdf.to_crs(opts.target_crs)

        if opts.keep_raw_properties:
            return gdf
        else:
            return gdf[["height_m", "source", "geometry"]]  
        
        print("height_col:", height_col, "height_m head:", gdf["height_m"].head().tolist())
