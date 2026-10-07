from dataclasses import dataclass

import numpy as np
import openmeteo_requests
import requests_cache
from retry_requests import retry


OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"


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
class OpenMeteoContext:
    latitude: float
    longitude: float

    rainfall_1h: float | None
    rainfall_24h: float | None
    rainfall_72h: float | None

    surface_pressure_hpa: float | None


# ---------------------------------------------------------
# Fetch weather data
# ---------------------------------------------------------

def fetch_open_meteo(
    latitude: float,
    longitude: float,
) -> OpenMeteoContext:
    """
    Fetch weather context from Open-Meteo.

    Used by GreenPulse for:

        rainfall_1h
        rainfall_24h
        rainfall_72h
        surface_pressure_hpa

    Rainfall is later converted into a GreenPulse
    rainfall score by the EMS layer.

    Surface pressure is context only and is NOT used
    as an EMS risk score.
    """

    params = {
        "latitude": latitude,
        "longitude": longitude,

        "hourly": [
            "rain",
            "surface_pressure",
        ],

        "current": [
            "rain",
            "surface_pressure",
        ],

        "past_days": 3,
        "forecast_days": 1,

        "timezone": "auto",
    }

    responses = openmeteo.weather_api(
        OPEN_METEO_URL,
        params=params,
    )

    if not responses:
        raise RuntimeError(
            "Open-Meteo Weather API returned no response"
        )

    response = responses[0]

    # -----------------------------------------------------
    # Current conditions
    # -----------------------------------------------------

    current = response.Current()

    current_time = current.Time()

    current_surface_pressure = (
        current.Variables(1).Value()
    )

    # -----------------------------------------------------
    # Hourly data
    # -----------------------------------------------------

    hourly = response.Hourly()

    hourly_rain = hourly.Variables(0).ValuesAsNumpy()

    hourly_time = np.arange(
        hourly.Time(),
        hourly.TimeEnd(),
        hourly.Interval(),
        dtype=np.int64,
    )

    # -----------------------------------------------------
    # Historical rainfall only
    #
    # IMPORTANT:
    #
    # The API contains forecast values because
    # forecast_days=1 is requested.
    #
    # Never include those forecast values when calculating
    # historical rainfall totals.
    # -----------------------------------------------------

    historical_rain = []

    for timestamp, rain in zip(
        hourly_time,
        hourly_rain,
    ):
        if timestamp > current_time:
            continue

        if np.isnan(rain):
            continue

        historical_rain.append(float(rain))

    # -----------------------------------------------------
    # Rainfall accumulation
    # -----------------------------------------------------

    rainfall_1h = _sum_last(
        historical_rain,
        1,
    )

    rainfall_24h = _sum_last(
        historical_rain,
        24,
    )

    rainfall_72h = _sum_last(
        historical_rain,
        72,
    )

    # -----------------------------------------------------
    # Surface pressure
    # -----------------------------------------------------

    surface_pressure_hpa = None

    if current_surface_pressure is not None:
        surface_pressure_hpa = float(
            current_surface_pressure
        )

    # -----------------------------------------------------
    # Return
    # -----------------------------------------------------

    return OpenMeteoContext(
        latitude=latitude,
        longitude=longitude,

        rainfall_1h=rainfall_1h,
        rainfall_24h=rainfall_24h,
        rainfall_72h=rainfall_72h,

        surface_pressure_hpa=surface_pressure_hpa,
    )


# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------

def _sum_last(
    values: list[float],
    count: int,
) -> float | None:
    """
    Sum the most recent `count` historical hourly
    rainfall values.

    Open-Meteo rainfall values are hourly precipitation
    amounts, so summing the hourly values gives the
    accumulated rainfall for the requested period.
    """

    if not values:
        return None

    recent_values = values[-count:]

    if not recent_values:
        return None

    return float(sum(recent_values))