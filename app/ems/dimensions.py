"""
Calculate GreenPulse environmental dimension scores.

This module combines already-normalized 0-100 parameter scores
into three higher-level dimensions:

    Ground Stability
    Human Pressure
    Environmental Quality

The weights below are GreenPulse design choices. They are not
official regulatory or scientific weighting standards.
"""


# =========================================================
# DIMENSION WEIGHTS
# =========================================================

GROUND_SOIL_WEIGHT = 0.70
GROUND_RAINFALL_WEIGHT = 0.30

HUMAN_PIR_WEIGHT = 0.50
HUMAN_SOUND_WEIGHT = 0.30
HUMAN_CO2_WEIGHT = 0.20

ENV_AQI_WEIGHT = 0.50
ENV_TEMPERATURE_WEIGHT = 0.25
ENV_HUMIDITY_WEIGHT = 0.25


# =========================================================
# GROUND STABILITY
# =========================================================

def calculate_ground_stability(
    soil_score: float,
    rainfall_score: float,
) -> float:
    """
    Calculate Ground Stability from:

        Soil score
        Rainfall score

    Higher score = better ground stability.
    """

    return round(
        (
            soil_score * GROUND_SOIL_WEIGHT
            + rainfall_score * GROUND_RAINFALL_WEIGHT
        ),
        2,
    )


# =========================================================
# HUMAN PRESSURE
# =========================================================

def calculate_human_pressure(
    pir_score: float,
    sound_score: float,
    co2_score: float,
) -> float:
    """
    Calculate Human Pressure from:

        PIR score
        Sound score
        CO2 score

    Higher score = lower human/environmental pressure.

    The individual scores are assumed to already follow
    the GreenPulse convention:

        100 = low pressure
        0   = high pressure
    """

    return round(
        (
            pir_score * HUMAN_PIR_WEIGHT
            + sound_score * HUMAN_SOUND_WEIGHT
            + co2_score * HUMAN_CO2_WEIGHT
        ),
        2,
    )


# =========================================================
# ENVIRONMENTAL QUALITY
# =========================================================

def calculate_environmental_quality(
    aqi_score: float,
    temperature_score: float,
    humidity_score: float,
) -> float:
    """
    Calculate Environmental Quality from:

        AQI score
        Temperature score
        Humidity score

    Higher score = better environmental conditions.
    """

    return round(
        (
            aqi_score * ENV_AQI_WEIGHT
            + temperature_score * ENV_TEMPERATURE_WEIGHT
            + humidity_score * ENV_HUMIDITY_WEIGHT
        ),
        2,
    )


# =========================================================
# ALL DIMENSIONS
# =========================================================

def calculate_dimensions(
    soil_score: float,
    rainfall_score: float,
    pir_score: float,
    sound_score: float,
    co2_score: float,
    aqi_score: float,
    temperature_score: float,
    humidity_score: float,
) -> dict[str, float]:
    """
    Calculate all GreenPulse environmental dimensions.

    Returns:
        {
            "ground_stability": ...,
            "human_pressure": ...,
            "environmental_quality": ...
        }
    """

    ground_stability = calculate_ground_stability(
        soil_score=soil_score,
        rainfall_score=rainfall_score,
    )

    human_pressure = calculate_human_pressure(
        pir_score=pir_score,
        sound_score=sound_score,
        co2_score=co2_score,
    )

    environmental_quality = calculate_environmental_quality(
        aqi_score=aqi_score,
        temperature_score=temperature_score,
        humidity_score=humidity_score,
    )

    return {
        "ground_stability": ground_stability,
        "human_pressure": human_pressure,
        "environmental_quality": environmental_quality,
    }