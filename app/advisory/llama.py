"""
GreenPulse Llama advisory generator.

Llama is responsible only for converting a deterministic
GreenPulse decision into a concise human-readable advisory.

The EMS calculation, alert level, driver, and action are
determined by the backend before Llama is called.
"""

from dataclasses import dataclass
from app.advisory.validator import validate_advisory

import requests


OLLAMA_URL = "http://localhost:11434/api/generate"

# Change this to "llama3.2:3b" on the final machine.
OLLAMA_MODEL = "llama3.2:1b"

OLLAMA_TIMEOUT = 30


@dataclass
class AdvisoryResult:
    advisory: str
    source: str


def generate_advisory(
    ems: float,
    alert_level: str,
    primary_driver: str,
    action: str,
    reason: str,
) -> AdvisoryResult:
    """
    Generate a human-readable environmental advisory.

    Llama does not make environmental decisions.
    It only converts the already-determined playbook
    result into readable language.
    """

    prompt = _build_prompt(
        ems=ems,
        alert_level=alert_level,
        primary_driver=primary_driver,
        action=action,
        reason=reason,
    )

    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
            },
            timeout=OLLAMA_TIMEOUT,
        )

        response.raise_for_status()

        data = response.json()

        advisory = data.get("response", "").strip()

        if validate_advisory(
            advisory=advisory,
            alert_level=alert_level,
            action=action,
            reason=reason,
        ):
            return AdvisoryResult(
                advisory=advisory,
                source="llama",
            )

        return AdvisoryResult(
            advisory=_fallback_advisory(
                alert_level=alert_level,
                action=action,
                reason=reason,
            ),
            source="fallback",
        )

    except requests.RequestException:
        return AdvisoryResult(
            advisory=_fallback_advisory(
                alert_level=alert_level,
                action=action,
                reason=reason,
            ),
            source="fallback",
        )


def _build_prompt(
    ems: float,
    alert_level: str,
    primary_driver: str,
    action: str,
    reason: str,
) -> str:
    """
    Build a constrained prompt for Llama.

    The model is explicitly instructed not to change
    the backend's decision.
    """

    return f"""
You are the GreenPulse environmental advisory assistant.

Convert the provided system decision into a short,
clear environmental advisory.

You MUST follow the provided decision.
Do not change the alert level.
Do not invent measurements.
Do not invent causes.
Do not recommend a different action.

System data:
EMS: {ems}
Alert level: {alert_level}
Primary driver: {primary_driver}
Reason: {reason}
Required action: {action}

Write 2-3 concise sentences.

Mention:
1. The current environmental condition.
2. The main reason.
3. The recommended action.

Do not mention that you are an AI or language model.
""".strip()


def _fallback_advisory(
    alert_level: str,
    action: str,
    reason: str,
) -> str:
    """
    Deterministic fallback used when Ollama is unavailable.
    """

    return (
        f"GreenPulse status: {alert_level}. "
        f"{reason} {action}"
    )