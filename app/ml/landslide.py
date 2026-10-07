from pathlib import Path
import joblib
import pandas as pd
from ..models_landslide_features import engineer_features, DAYS

BASE = Path(__file__).resolve().parents[2] / "models" / "landslide"
ARTIFACT_PATH = BASE / "landslide_model.joblib"


def _load_artifact():
    if not ARTIFACT_PATH.exists() or ARTIFACT_PATH.stat().st_size == 0:
        raise RuntimeError(
            "Landslide model artifact is missing. Put the trained landslide_model.joblib "
            "from the upstream landslide repository into models/landslide/."
        )
    return joblib.load(ARTIFACT_PATH)


def predict(payload: dict) -> dict:
    artifact = _load_artifact()
    row = {**payload.get("extra_features", {}), "slope": payload["slope"]}
    for var in ("precip", "temp", "humidity", "wind", "air"):
        values = payload[var]
        if len(values) != DAYS:
            raise ValueError(f"{var} must contain {DAYS} values")
        for i, value in enumerate(values):
            row[f"{var}{i}"] = value
    if payload.get("lat") is not None:
        row["lat"] = payload["lat"]
    if payload.get("lon") is not None:
        row["lon"] = payload["lon"]
    feats = engineer_features(pd.DataFrame([row]))
    X = feats.reindex(columns=artifact["feature_columns"])
    prob = float(artifact["model"].predict_proba(X)[:, 1][0])
    return {
        "probability": round(prob, 4),
        "prediction": prob >= 0.5,
        "riskLevel": "Low" if prob < 0.3 else "Medium" if prob < 0.6 else "High",
        "keyFactors": {
            key: round(float(feats.iloc[0][key]), 3)
            for key in ("rain_1d", "rain_3d", "rain_7d", "rain_30d", "antecedent_rainfall_index", "slope")
            if key in feats.columns
        },
    }
