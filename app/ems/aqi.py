from dataclasses import dataclass


# =========================================================
# CPCB / NAQI BREAKPOINTS
#
# Concentrations: µg/m³
# PM2.5 and PM10: 24-hour concentrations
#
# Format:
# (
#     concentration_low,
#     concentration_high,
#     aqi_low,
#     aqi_high,
# )
# =========================================================

PM25_BREAKPOINTS = [
    (0.0, 30.0, 0, 50),
    (31.0, 60.0, 51, 100),
    (61.0, 90.0, 101, 200),
    (91.0, 120.0, 201, 300),
    (121.0, 250.0, 301, 400),
]

PM10_BREAKPOINTS = [
    (0.0, 50.0, 0, 50),
    (51.0, 100.0, 51, 100),
    (101.0, 250.0, 101, 200),
    (251.0, 350.0, 201, 300),
    (351.0, 430.0, 301, 400),
]


# =========================================================
# RESULT
# =========================================================

@dataclass
class AQIResult:
    pm25_sub_index: int | None
    pm10_sub_index: int | None

    aqi: int | None
    category: str | None


# =========================================================
# MAIN AQI CALCULATION
# =========================================================

def calculate_aqi(
    pm25_24h: float | None,
    pm10_24h: float | None,
) -> AQIResult:
    """
    Calculate GreenPulse AQI from 24-hour PM2.5 and PM10.

    The pollutant with the highest valid sub-index
    determines the overall AQI.
    """

    pm25_sub_index = calculate_sub_index(
        concentration=pm25_24h,
        breakpoints=PM25_BREAKPOINTS,
    )

    pm10_sub_index = calculate_sub_index(
        concentration=pm10_24h,
        breakpoints=PM10_BREAKPOINTS,
    )

    valid_indices = [
        value
        for value in (
            pm25_sub_index,
            pm10_sub_index,
        )
        if value is not None
    ]

    if not valid_indices:
        return AQIResult(
            pm25_sub_index=None,
            pm10_sub_index=None,
            aqi=None,
            category=None,
        )

    aqi = max(valid_indices)

    return AQIResult(
        pm25_sub_index=pm25_sub_index,
        pm10_sub_index=pm10_sub_index,
        aqi=aqi,
        category=get_aqi_category(aqi),
    )


# =========================================================
# POLLUTANT SUB-INDEX
# =========================================================

def calculate_sub_index(
    concentration: float | None,
    breakpoints: list[tuple[float, float, int, int]],
) -> int | None:
    """
    Convert pollutant concentration into an AQI
    sub-index using linear interpolation.

    Formula:

        I =
        ((I_high - I_low) /
         (C_high - C_low))
        * (C - C_low)
        + I_low

    Values above the highest published breakpoint
    are capped at AQI 500.
    """

    if concentration is None:
        return None

    concentration = float(concentration)

    if concentration < 0:
        return None

    # -----------------------------------------------------
    # Above highest CPCB breakpoint
    # -----------------------------------------------------

    highest_concentration = breakpoints[-1][1]

    if concentration > highest_concentration:
        return 500

    # -----------------------------------------------------
    # Find matching breakpoint
    # -----------------------------------------------------

    for (
        concentration_low,
        concentration_high,
        aqi_low,
        aqi_high,
    ) in breakpoints:

        if (
            concentration_low
            <= concentration
            <= concentration_high
        ):
            sub_index = (
                (
                    (aqi_high - aqi_low)
                    / (concentration_high - concentration_low)
                )
                * (concentration - concentration_low)
                + aqi_low
            )

            return round(sub_index)

    return None


# =========================================================
# AQI CATEGORY
# =========================================================

def get_aqi_category(
    aqi: int,
) -> str:

    if aqi <= 50:
        return "GOOD"

    if aqi <= 100:
        return "SATISFACTORY"

    if aqi <= 200:
        return "MODERATE"

    if aqi <= 300:
        return "POOR"

    if aqi <= 400:
        return "VERY POOR"

    return "SEVERE"