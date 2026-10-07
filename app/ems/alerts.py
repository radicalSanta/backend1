"""
Determine the GreenPulse alert level and identify the
main environmental dimension requiring attention.

This module is deterministic. No LLM is involved.
"""


# =========================================================
# ALERT THRESHOLDS
# =========================================================

EMS_NORMAL_THRESHOLD = 80.0
EMS_WATCH_THRESHOLD = 60.0
EMS_WARNING_THRESHOLD = 40.0

DIMENSION_WARNING_THRESHOLD = 40.0
DIMENSION_CRITICAL_THRESHOLD = 20.0


# =========================================================
# ALERT LEVEL
# =========================================================

def get_alert_level(ems: float) -> str:
    """
    Convert the final EMS into an overall alert level.

    Higher EMS = better environmental condition.
    """

    if ems >= EMS_NORMAL_THRESHOLD:
        return "NORMAL"

    if ems >= EMS_WATCH_THRESHOLD:
        return "WATCH"

    if ems >= EMS_WARNING_THRESHOLD:
        return "WARNING"

    return "CRITICAL"


# =========================================================
# PRIMARY DRIVER
# =========================================================

def get_primary_driver(
    ground_stability: float,
    human_pressure: float,
    environmental_quality: float,
) -> str:
    """
    Identify the weakest environmental dimension.

    The dimension with the lowest score is considered
    the primary driver.
    """

    dimensions = {
        "ground_stability": ground_stability,
        "human_pressure": human_pressure,
        "environmental_quality": environmental_quality,
    }

    return min(
        dimensions,
        key=dimensions.get,
    )


# =========================================================
# DIMENSION ALERT
# =========================================================

def get_dimension_alert(score: float) -> str:
    """
    Determine the severity of an individual dimension.
    """

    if score >= EMS_NORMAL_THRESHOLD:
        return "NORMAL"

    if score >= EMS_WATCH_THRESHOLD:
        return "WATCH"

    if score >= EMS_WARNING_THRESHOLD:
        return "WARNING"

    return "CRITICAL"


# =========================================================
# COMPLETE ALERT RESULT
# =========================================================

def calculate_alert(
    ems: float,
    ground_stability: float,
    human_pressure: float,
    environmental_quality: float,
) -> dict:
    """
    Produce the complete deterministic alert result.
    """

    alert_level = get_alert_level(ems)

    primary_driver = get_primary_driver(
        ground_stability=ground_stability,
        human_pressure=human_pressure,
        environmental_quality=environmental_quality,
    )

    return {
        "alert_level": alert_level,
        "primary_driver": primary_driver,
        "ground_stability_alert": get_dimension_alert(
            ground_stability
        ),
        "human_pressure_alert": get_dimension_alert(
            human_pressure
        ),
        "environmental_quality_alert": get_dimension_alert(
            environmental_quality
        ),
    }