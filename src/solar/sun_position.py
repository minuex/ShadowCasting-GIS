# src/solar/sun_position.py

from datetime import datetime
from typing import Tuple
from astral.sun import azimuth, elevation
from astral import LocationInfo
import pytz

# 위도, 경도, 시각 → 태양 방위각(azimuth), 고도각(altitude) 반환 (단위: 도)
# 방위각 : 북=0°, 동=90°, 남=180°, 서=270° (시계방향)
# 고도각 : 수평선 기준 (0° = 지평선, 음수면 지면 아래)
# 리턴값 : azimuth, altitude

def get_sun_position(
    lat: float,
    lon: float,
    dt: datetime,
    tz_str: str = "Asia/Seoul",
) -> Tuple[float, float]:
    """
    위도, 경도, 시각 → 태양 방위각 / 고도각 반환 (단위: degree)

    Azimuth:
        - North = 0°
        - East = 90°
        - Clockwise positive

    Altitude (Elevation):
        - 0° = horizon
        - < 0° = below horizon
    """
    tz = pytz.timezone(tz_str)
    dt_local = dt.astimezone(tz)

    location = LocationInfo(latitude=lat, longitude=lon)

    az = azimuth(location.observer, dt_local)
    alt = elevation(location.observer, dt_local)

    return az, alt