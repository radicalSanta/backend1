""" 
GreenPulse EMS pipeline.

This module orchestrates the complete deterministic EMS flow:

    latest ESP32 telemetry
        +
    Open-Meteo weather
        +
    Open-Meteo air quality
        ↓
    rainfall score
    AQI
    AQI score
        ↓
    EMS dimensions
        ↓
    overall EMS
        ↓
    alert level
    primary driver
        ↓
    deterministic playbook
        ↓
    Llama advisory
        ↓
    validated advisory

The pipeline does not calculate ESP32-derived sensor scores.
Those scores are expected to come from the ESP32.
"""

from dataclasses import dataclass

from app.ems.aqi import calculate_aqi
from app.ems.alerts import calculate_alert
from app.ems.calculator import calculate_ems
from app.ems.dimensions import calculate_dimensions

from app.advisory.llama import generate_advisory
from app.advisory.playbook import generate_playbook

from app.processing.sensor_scores import (
    calculate_aqi_score,
    calculate_rainfall_score,
)

from app.external.open_meteo import fetch_open_meteo
from app.external.open_meteo_air import fetch_open_meteo_air


# =========================================================
# RESULT
# =========================================================


@dataclass
class EMSPipelineResult:
    """
    Complete result produced by the GreenPulse EMS pipeline.
    """

    # -----------------------------------------------------
    # EMS
    # -----------------------------------------------------

    ems: float

    ground_stability: float
    human_pressure: float
    environmental_quality: float

    # -----------------------------------------------------
    # Alert
    # -----------------------------------------------------

    alert_level: str
    primary_driver: str

    # -----------------------------------------------------
    # Advisory
    # -----------------------------------------------------

    advisory: str
    advisory_source: str

    # -----------------------------------------------------
    # Playbook
    # -----------------------------------------------------

    action: str
    reason: str
    priority: str

    # -----------------------------------------------------
    # External context
    # -----------------------------------------------------

    rainfall_1h: float | None
    rainfall_24h: float | None
    rainfall_72h: float | None
    rainfall_score: float | None

    pm25_24h: float | None
    pm10_24h: float | None

    aqi: int | None
    aqi_category: str | None
    aqi_score: float | None

    surface_pressure_hpa: float | None


# =========================================================
# MAIN PIPELINE
# =========================================================
# =====================================================
# LOCATION CONFIGURATION
# =====================================================

SHILLONG_LATITUDE = 25.5788
SHILLONG_LONGITUDE = 91.8933


def resolve_location(telemetry) -> tuple[float, float, str]:
    """
    Resolve the location used by external APIs.

    Priority:
    1. Valid ESP32 GPS coordinates
    2. Shillong fallback coordinates

    Returns:
        (latitude, longitude, source)
    """

    latitude = telemetry.latitude
    longitude = telemetry.longitude

    # -------------------------------------------------
    # Try ESP32 GPS
    # -------------------------------------------------

    if latitude is not None and longitude is not None:
        try:
            latitude = float(latitude)
            longitude = float(longitude)

            if (
                -90.0 <= latitude <= 90.0
                and -180.0 <= longitude <= 180.0
            ):
                return latitude, longitude, "GPS"

        except (TypeError, ValueError):
            pass

    # -------------------------------------------------
    # Shillong fallback
    # -------------------------------------------------

    return (
        SHILLONG_LATITUDE,
        SHILLONG_LONGITUDE,
        "FALLBACK",
    )


def run_ems_pipeline(
    telemetry,
) -> EMSPipelineResult:
    """
    Run the complete GreenPulse EMS pipeline.

    Args:
        telemetry:
            Latest SensorReading/database telemetry object.

    Returns:
        EMSPipelineResult containing the complete EMS state.
    """

    # =====================================================
    # 1. RESOLVE LOCATION
    # =====================================================

    latitude, longitude, location_source = resolve_location(
        telemetry
    )

    # =====================================================
    # 2. FETCH WEATHER
    # =====================================================

    weather = fetch_open_meteo(
        latitude=latitude,
        longitude=longitude,
    )

    # =====================================================
    # 3. FETCH AIR QUALITY
    # =====================================================

    air = fetch_open_meteo_air(
        latitude=latitude,
        longitude=longitude,
    )

    # =====================================================
    # 4. CALCULATE RAINFALL SCORE
    # =====================================================

    rainfall_score = calculate_rainfall_score(
        rainfall_1h=weather.rainfall_1h,
        rainfall_24h=weather.rainfall_24h,
        rainfall_72h=weather.rainfall_72h,
    )

    if rainfall_score is None:
        raise ValueError(
            "Unable to calculate rainfall score"
        )

    # =====================================================
    # 5. CALCULATE AQI
    # =====================================================

    aqi_result = calculate_aqi(
        pm25_24h=air.pm25_24h,
        pm10_24h=air.pm10_24h,
    )

    if aqi_result.aqi is None:
        raise ValueError(
            "Unable to calculate AQI"
        )

    # =====================================================
    # 6. CALCULATE AQI SCORE
    # =====================================================

    aqi_score = calculate_aqi_score(
        aqi_result.aqi
    )

    if aqi_score is None:
        raise ValueError(
            "Unable to calculate AQI score"
        )

    # =====================================================
    # 7. READ ESP32 SCORES
    # =====================================================

    required_scores = {
        "soil_score": telemetry.soil_score,
        "pir_score": telemetry.pir_score,
        "sound_score": telemetry.sound_score,
        "co2_score": telemetry.co2_score,
        "temperature_score": getattr(
            telemetry,
            "temperature_score",
            None,
        ),
        "humidity_score": getattr(
            telemetry,
            "humidity_score",
            None,
        ),
    }

    missing_scores = [
        name
        for name, value in required_scores.items()
        if value is None
    ]

    if missing_scores:
        raise ValueError(
            "Missing ESP32 EMS scores: "
            + ", ".join(missing_scores)
        )

    soil_score = float(
        required_scores["soil_score"]
    )

    pir_score = float(
        required_scores["pir_score"]
    )

    sound_score = float(
        required_scores["sound_score"]
    )

    co2_score = float(
        required_scores["co2_score"]
    )

    temperature_score = float(
        required_scores["temperature_score"]
    )

    humidity_score = float(
        required_scores["humidity_score"]
    )

    # =====================================================
    # 8. CALCULATE THREE EMS DIMENSIONS
    # =====================================================

    dimensions = calculate_dimensions(
        soil_score=soil_score,
        rainfall_score=rainfall_score,

        pir_score=pir_score,
        sound_score=sound_score,
        co2_score=co2_score,

        aqi_score=aqi_score,
        temperature_score=temperature_score,
        humidity_score=humidity_score,
    )

    ground_stability = dimensions[
        "ground_stability"
    ]

    human_pressure = dimensions[
        "human_pressure"
    ]

    environmental_quality = dimensions[
        "environmental_quality"
    ]

    # =====================================================
    # 9. CALCULATE FINAL EMS
    # =====================================================

    ems = calculate_ems(
        ground_stability=ground_stability,
        human_pressure=human_pressure,
        environmental_quality=environmental_quality,
    )

    # =====================================================
    # 10. DETERMINE ALERT + PRIMARY DRIVER
    # =====================================================

    alert = calculate_alert(
        ems=ems,
        ground_stability=ground_stability,
        human_pressure=human_pressure,
        environmental_quality=environmental_quality,
    )

    alert_level = alert["alert_level"]
    primary_driver = alert["primary_driver"]

    # =====================================================
    # 11. GENERATE DETERMINISTIC PLAYBOOK
    # =====================================================

    playbook = generate_playbook(
        alert_level=alert_level,
        primary_driver=primary_driver,

        soil_score=soil_score,
        rainfall_score=rainfall_score,

        pir_score=pir_score,
        sound_score=sound_score,
        co2_score=co2_score,

        aqi_score=aqi_score,
        temperature_score=temperature_score,
        humidity_score=humidity_score,
    )

    # =====================================================
    # 12. GENERATE Llama ADVISORY
    # =====================================================

    advisory_result = generate_advisory(
        ems=ems,
        alert_level=alert_level,
        primary_driver=primary_driver,
        action=playbook.action,
        reason=playbook.reason,
    )

    # =====================================================
    # 13. RETURN COMPLETE PIPELINE RESULT
    # =====================================================

    return EMSPipelineResult(

        # EMS
        ems=ems,

        ground_stability=ground_stability,
        human_pressure=human_pressure,
        environmental_quality=environmental_quality,

        # Alert
        alert_level=alert_level,
        primary_driver=primary_driver,

        # Advisory
        advisory=advisory_result.advisory,
        advisory_source=advisory_result.source,

        # Playbook
        action=playbook.action,
        reason=playbook.reason,
        priority=playbook.priority,

        # Weather
        rainfall_1h=weather.rainfall_1h,
        rainfall_24h=weather.rainfall_24h,
        rainfall_72h=weather.rainfall_72h,
        rainfall_score=rainfall_score,

        surface_pressure_hpa=(
            weather.surface_pressure_hpa
        ),

        # Air quality
        pm25_24h=air.pm25_24h,
        pm10_24h=air.pm10_24h,

        aqi=aqi_result.aqi,
        aqi_category=aqi_result.category,
        aqi_score=aqi_score,
    )