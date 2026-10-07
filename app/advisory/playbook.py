"""
GreenPulse advisory playbook.

This module converts environmental conditions into
deterministic recommended actions.

No LLM logic belongs here.
"""


from dataclasses import dataclass


@dataclass
class PlaybookResult:
    action: str
    reason: str
    priority: str


def generate_playbook(
    alert_level: str,
    primary_driver: str,
    soil_score: float,
    rainfall_score: float,
    pir_score: float,
    sound_score: float,
    co2_score: float,
    aqi_score: float,
    temperature_score: float,
    humidity_score: float,
) -> PlaybookResult:

    # -----------------------------------------------------
    # GROUND CONDITIONS
    # -----------------------------------------------------

    if primary_driver == "ground_stability":

        if rainfall_score <= 25:
            return PlaybookResult(
                action="Inspect drainage and avoid disturbing saturated ground.",
                reason="Heavy rainfall is creating elevated ground stress.",
                priority="HIGH",
            )

        if soil_score <= 25:
            return PlaybookResult(
                action="Inspect the soil condition and avoid unnecessary ground disturbance.",
                reason="The local soil condition indicates high ground stress.",
                priority="HIGH",
            )

        if rainfall_score <= 50:
            return PlaybookResult(
                action="Monitor drainage and ground conditions.",
                reason="Recent rainfall is increasing ground stress.",
                priority="MEDIUM",
            )

        return PlaybookResult(
            action="Continue monitoring ground conditions.",
            reason="Ground stability is currently the weakest EMS dimension.",
            priority="MEDIUM",
        )

    # -----------------------------------------------------
    # HUMAN PRESSURE
    # -----------------------------------------------------

    if primary_driver == "human_pressure":

        if pir_score <= 25 and sound_score <= 25:
            return PlaybookResult(
                action="Investigate sustained human activity near the monitoring node.",
                reason="Both movement and sound indicators show elevated activity.",
                priority="HIGH",
            )

        if pir_score <= 40:
            return PlaybookResult(
                action="Monitor human movement around the monitored area.",
                reason="Elevated movement activity has been detected.",
                priority="MEDIUM",
            )

        if sound_score <= 40:
            return PlaybookResult(
                action="Monitor activity levels around the monitored area.",
                reason="Elevated sound activity has been detected.",
                priority="MEDIUM",
            )

        if co2_score <= 40:
            return PlaybookResult(
                action="Investigate elevated CO₂ and possible increased occupancy or activity.",
                reason="CO₂ indicates increased local human/activity pressure.",
                priority="MEDIUM",
            )

        return PlaybookResult(
            action="Continue monitoring human activity.",
            reason="Human pressure is currently the weakest EMS dimension.",
            priority="MEDIUM",
        )

    # -----------------------------------------------------
    # ENVIRONMENTAL QUALITY
    # -----------------------------------------------------

    if primary_driver == "environmental_quality":

        if aqi_score <= 25:
            return PlaybookResult(
                action="Investigate elevated particulate pollution in the monitored area.",
                reason="Air quality is contributing strongly to environmental stress.",
                priority="HIGH",
            )

        if temperature_score <= 25:
            return PlaybookResult(
                action="Monitor temperature conditions and potential heat or cold stress.",
                reason="Temperature is contributing strongly to environmental stress.",
                priority="HIGH",
            )

        if humidity_score <= 25:
            return PlaybookResult(
                action="Monitor humidity conditions and associated microclimate stress.",
                reason="Humidity is contributing strongly to environmental stress.",
                priority="MEDIUM",
            )

        return PlaybookResult(
            action="Continue monitoring environmental conditions.",
            reason="Environmental quality is currently the weakest EMS dimension.",
            priority="MEDIUM",
        )

    # -----------------------------------------------------
    # FALLBACK
    # -----------------------------------------------------

    return PlaybookResult(
        action="Continue environmental monitoring.",
        reason="No specific environmental driver requires intervention.",
        priority="LOW",
    )