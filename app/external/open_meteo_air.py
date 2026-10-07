from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import numpy as np
import openmeteo_requests
import requests_cache
from retry_requests import retry


OPEN_METEO_AIR_URL = (
    "https://air-quality-api.open-meteo.com/v1/air-quality"
)


# ---------------------------------------------------------
# Open-Meteo client
# ---------------------------------------------------------

cache_session = requests_cache.CachedSession(
    ".cache",
    expire_after=3600,
)

retry_session = retry(
    cache_session,
    retries=5,
    backoff_factor=0.2,
)

openmeteo = openmeteo_requests.Client(
    session=retry_session,
)


# ---------------------------------------------------------
# Data structure
# ---------------------------------------------------------

@dataclass
class OpenMeteoAirContext:
    latitude: float
    longitude: float

    pm10_current: float | None
    pm25_current: float | None

    pm10_24h: float | None
    pm25_24h: float | None


# ---------------------------------------------------------
# Fetch air-quality data
# ---------------------------------------------------------

def fetch_open_meteo_air(
    latitude: float,
    longitude: float,
) -> OpenMeteoAirContext:
    """
    Fetch PM10 and PM2.5 data from Open-Meteo.

    Open-Meteo returns both historical and forecast hourly
    values because past_days and forecast_days are requested.

    For GreenPulse:

    - current values = latest available historical hourly value
    - 24h values = average of valid historical values from
      the previous 24-hour window
    - forecast values are never included in the 24h average

    This module does not calculate AQI or EMS.
    """

    params = {
        "latitude": latitude,
        "longitude": longitude,

        "hourly": [
            "pm10",
            "pm2_5",
        ],

        "past_days": 3,
        "forecast_days": 1,

        "domains": "cams_global",
    }

    responses = openmeteo.weather_api(
        OPEN_METEO_AIR_URL,
        params=params,
    )

    if not responses:
        raise RuntimeError(
            "Open-Meteo Air Quality API returned no response"
        )

    response = responses[0]
    hourly = response.Hourly()

    # -----------------------------------------------------
    # Build hourly timestamps.
    #
    # hourly.Time() is the first timestamp.
    # hourly.TimeEnd() is the end timestamp.
    # hourly.Interval() is the spacing between values.
    #
    # Therefore we construct the complete timestamp array.
    # -----------------------------------------------------

    hourly_time = np.arange(
        hourly.Time(),
        hourly.TimeEnd(),
        hourly.Interval(),
        dtype=np.int64,
    )

    pm10_values = hourly.Variables(0).ValuesAsNumpy()
    pm25_values = hourly.Variables(1).ValuesAsNumpy()

    if hourly_time.size == 0:
        raise RuntimeError(
            "Open-Meteo Air Quality API returned no timestamps"
        )

    # -----------------------------------------------------
    # Historical 24-hour window
    # -----------------------------------------------------

    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=24)

    pm10_24h_values: list[float] = []
    pm25_24h_values: list[float] = []

    latest_pm10: float | None = None
    latest_pm25: float | None = None

    # -----------------------------------------------------
    # Process hourly values
    # -----------------------------------------------------

    for index, timestamp in enumerate(hourly_time):

        timestamp_dt = datetime.fromtimestamp(
            int(timestamp),
            tz=timezone.utc,
        )

        # Ignore forecast/future values.
        if timestamp_dt > now:
            continue

        # Keep only the previous 24-hour window.
        if timestamp_dt < cutoff:
            continue

        # -------------------------------------------------
        # PM10
        # -------------------------------------------------

        pm10 = pm10_values[index]

        if not np.isnan(pm10):
            pm10_float = float(pm10)

            pm10_24h_values.append(pm10_float)

            latest_pm10 = pm10_float

        # -------------------------------------------------
        # PM2.5
        # -------------------------------------------------

        pm25 = pm25_values[index]

        if not np.isnan(pm25):
            pm25_float = float(pm25)

            pm25_24h_values.append(pm25_float)

            latest_pm25 = pm25_float

    # -----------------------------------------------------
    # Calculate 24-hour averages
    # -----------------------------------------------------

    pm10_24h = _average(pm10_24h_values)
    pm25_24h = _average(pm25_24h_values)

    # -----------------------------------------------------
    # Return
    # -----------------------------------------------------

    return OpenMeteoAirContext(
        latitude=latitude,
        longitude=longitude,

        pm10_current=latest_pm10,
        pm25_current=latest_pm25,

        pm10_24h=pm10_24h,
        pm25_24h=pm25_24h,
    )


# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------

def _average(
    values: list[float],
) -> float | None:
    """
    Calculate the arithmetic mean of valid values.
    """

    if not values:
        return None

    return float(sum(values) / len(values))