from src.datasources import BBox, BuildingFetchOptions, MolitBuildingsWFS
from dotenv import load_dotenv
load_dotenv()

if __name__ == "__main__":
    bbox = BBox( #Kaist 인위연 좌표
        west=127.364,
    south=36.374,
    east=127.366,
    north=36.375
)

    src = MolitBuildingsWFS()
    opts = BuildingFetchOptions(target_crs="EPSG:4326", default_height_m=10.0)

    gdf = src.fetch(bbox, opts)

    print("rows:", len(gdf))
    print("crs:", gdf.crs)
    print("cols:", list(gdf.columns))
    print(gdf[["height_m"]].head()) 
