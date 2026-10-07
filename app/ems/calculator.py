"""
Calculate the final GreenPulse Environmental Monitoring Score (EMS).

The three higher-level dimensions are combined into one
0-100 environmental score.

The weights are GreenPulse design choices and are not
official regulatory or scientific weighting standards.
"""


# =========================================================
# FINAL EMS WEIGHTS
# =========================================================

GROUND_WEIGHT = 0.40
HUMAN_WEIGHT = 0.30
ENVIRONMENTAL_WEIGHT = 0.30


# =========================================================
# EMS CALCULATION
# =========================================================

def calculate_ems(
    ground_stability: float,
    human_pressure: float,
    environmental_quality: float,
) -> float:
    """
    Calculate the final GreenPulse EMS.

    Higher EMS = better overall environmental condition.

    Returns:
        EMS score from 0 to 100.
    """

    ems = (
        ground_stability * GROUND_WEIGHT
        + human_pressure * HUMAN_WEIGHT
        + environmental_quality * ENVIRONMENTAL_WEIGHT
    )

    return round(
        max(0.0, min(100.0, ems)),
        2,
    )