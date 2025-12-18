# src/io/smoke_test.py
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


from src.datasources.base import BBox

if __name__ == "__main__":
    bbox = BBox(west=127.0, south=37.49, east=127.02, north=37.51)
    bbox.validate()
    print("BBox OK:", bbox.as_tuple())
