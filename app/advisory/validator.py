"""
Validate Llama-generated GreenPulse advisories.

The backend remains the source of truth for:
    - EMS
    - alert level
    - primary driver
    - reason
    - recommended action

This module only checks whether the generated text is
consistent enough to be shown to the user.
"""


def validate_advisory(
    advisory: str,
    alert_level: str,
    action: str,
    reason: str,
) -> bool:
    """
    Perform basic validation of a generated advisory.

    Returns:
        True  -> advisory is acceptable
        False -> use deterministic fallback
    """

    if not advisory:
        return False

    advisory = advisory.strip()

    # Avoid obviously broken output.
    if len(advisory) < 20:
        return False

    # Reject responses that contain common model
    # uncertainty/failure phrases.
    forbidden_phrases = [
        "i don't know",
        "i do not know",
        "i cannot determine",
        "i can't determine",
        "as an ai",
        "as a language model",
    ]

    advisory_lower = advisory.lower()

    for phrase in forbidden_phrases:
        if phrase in advisory_lower:
            return False

    # The alert level should appear in the advisory.
    if alert_level.lower() not in advisory_lower:
        return False

    # Check that the advisory contains at least some
    # meaningful portion of the deterministic action.
    action_keywords = _extract_keywords(action)

    if action_keywords:
        matched_keywords = sum(
            1
            for keyword in action_keywords
            if keyword in advisory_lower
        )

        # At least one meaningful action keyword should
        # survive the Llama rewrite.
        if matched_keywords == 0:
            return False

    return True


def _extract_keywords(text: str) -> list[str]:
    """
    Extract simple meaningful keywords from the
    deterministic action.

    This is intentionally lightweight; it is not an NLP
    system.
    """

    stop_words = {
        "the",
        "and",
        "or",
        "to",
        "of",
        "a",
        "an",
        "in",
        "on",
        "for",
        "with",
        "is",
        "are",
        "avoid",
        "continue",
    }

    words = text.lower().replace(".", "").split()

    return [
        word
        for word in words
        if len(word) >= 5 and word not in stop_words
    ]