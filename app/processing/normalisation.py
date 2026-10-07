def normalize(
    value: float,
    minimum: float,
    maximum: float,
) -> float:
    """
    Normalize a value to a 0–100 range.

    Values below minimum are clamped to 0.
    Values above maximum are clamped to 100.
    """

    if maximum <= minimum:
        raise ValueError("maximum must be greater than minimum")

    normalized = (
        (value - minimum)
        / (maximum - minimum)
    ) * 100.0

    return max(0.0, min(100.0, normalized))

