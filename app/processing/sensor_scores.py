"""
Convert external environmental measurements into
0-100 scores used by the GreenPulse EMS.

ESP32-derived scores such as soil_score, sound_score,
pir_score, temperature_score, humidity_score, and
co2_score are not handled here.
"""


# =========================================================
# AQI SCORE
# =========================================================

def calculate_aqi_score(aqi: float | None) -> float | None:
    """
    Convert CPCB AQI (0-500) into a GreenPulse EMS score.

    100 = lowest air-quality stress
    0   = highest air-quality stress

    This is a GreenPulse normalization and is not
    itself a CPCB AQI value.
    """

    if aqi is None:
        return None

    aqi = float(aqi)

    if aqi < 0:
        return None

    # AQI above 500 is treated as maximum stress.
    aqi = min(aqi, 500.0)

    # Linear normalization:
    #
    # AQI 0   -> 100
    # AQI 500 -> 0
    #
    score = 100.0 - (aqi / 5.0)

    return round(max(0.0, min(100.0, score)), 2)


# =========================================================
# RAINFALL SCORE
# =========================================================

def calculate_rainfall_score(
    rainfall_1h: float | None,
    rainfall_24h: float | None,
    rainfall_72h: float | None,
) -> float | None:
    """
    Calculate a GreenPulse rainfall stress score.

    The score represents ground/environmental stress caused
    by rainfall accumulation and short-term intensity.

    100 = low rainfall-related stress
    0   = very high rainfall-related stress

    The 24-hour rainfall value is the primary indicator.
    Short-term 1-hour rainfall and accumulated 72-hour
    rainfall can increase the estimated stress.
    """

    values = [
        value
        for value in (
            rainfall_1h,
            rainfall_24h,
            rainfall_72h,
        )
        if value is not None
    ]

    if not values:
        return None

    rainfall_1h = _non_negative(rainfall_1h)
    rainfall_24h = _non_negative(rainfall_24h)
    rainfall_72h = _non_negative(rainfall_72h)

    # -----------------------------------------------------
    # 24-hour rainfall component
    #
    # Based on IMD rainfall intensity categories.
    # -----------------------------------------------------

    score_24h = _score_24h_rainfall(rainfall_24h)

    # -----------------------------------------------------
    # 1-hour intensity component
    #
    # Strong short-duration rainfall should increase
    # ground-stress assessment even when 24h accumulation
    # is still relatively low.
    # -----------------------------------------------------

    score_1h = _score_1h_rainfall(rainfall_1h)

    # -----------------------------------------------------
    # 72-hour accumulation component
    #
    # Persistent rainfall can create additional ground
    # stress even when the current hour is relatively dry.
    # -----------------------------------------------------

    score_72h = _score_72h_rainfall(rainfall_72h)

    # Use the strongest observed rainfall stress.
    #
    # This avoids hiding a severe short-duration event
    # behind a relatively low 24h average.
    scores = [
        score
        for score in (
            score_1h,
            score_24h,
            score_72h,
        )
        if score is not None
    ]

    if not scores:
        return None

    return round(min(scores), 2)


# =========================================================
# 24-HOUR RAINFALL
# =========================================================

def _score_24h_rainfall(
    rainfall: float | None,
) -> float | None:
    """
    Score 24-hour accumulated rainfall.

    IMD-inspired rainfall categories:

    0-15.5 mm       -> very low/light
    15.6-64.4 mm    -> moderate
    64.5-115.5 mm   -> heavy
    115.6-204.4 mm  -> very heavy
    >=204.5 mm      -> extremely heavy
    """

    if rainfall is None:
        return None

    if rainfall <= 15.5:
        return 100.0

    if rainfall <= 64.4:
        return 80.0

    if rainfall <= 115.5:
        return 50.0

    if rainfall <= 204.4:
        return 25.0

    return 0.0


# =========================================================
# 1-HOUR RAINFALL
# =========================================================

def _score_1h_rainfall(
    rainfall: float | None,
) -> float | None:
    """
    Score short-duration rainfall intensity.

    This is used to detect sudden intense rainfall events.
    """

    if rainfall is None:
        return None

    if rainfall <= 5.0:
        return 100.0

    if rainfall <= 10.0:
        return 80.0

    if rainfall <= 20.0:
        return 60.0

    if rainfall <= 40.0:
        return 30.0

    return 0.0


# =========================================================
# 72-HOUR RAINFALL
# =========================================================

def _score_72h_rainfall(
    rainfall: float | None,
) -> float | None:
    """
    Score accumulated rainfall over 72 hours.

    This captures persistent wet conditions that may not
    be visible from the current 1-hour rainfall value.
    """

    if rainfall is None:
        return None

    if rainfall <= 30.0:
        return 100.0

    if rainfall <= 100.0:
        return 80.0

    if rainfall <= 200.0:
        return 60.0

    if rainfall <= 300.0:
        return 30.0

    return 0.0


# =========================================================
# HELPERS
# =========================================================

def _non_negative(
    value: float | None,
) -> float | None:
    """
    Prevent negative rainfall values from entering
    the scoring calculations.
    """

    if value is None:
        return None

    return max(0.0, float(value))