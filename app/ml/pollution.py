from pathlib import Path
import pickle
import joblib
import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parents[2] / "models" / "pollution"


def _load_artifacts():
    model_path = BASE / "pollution_model.pkl"
    features_path = BASE / "model_features.pkl"
    targets_path = BASE / "target_columns.pkl"
    if not model_path.exists() or model_path.stat().st_size == 0:
        raise RuntimeError(
            "Pollution model artifact is missing or empty. The upstream pollution repository "
            "contains an empty pollution_model.pkl; place the trained model at models/pollution/pollution_model.pkl."
        )
    if not features_path.exists() or not targets_path.exists():
        raise RuntimeError("Pollution feature/target artifacts are missing.")
    with features_path.open("rb") as f:
        features = pickle.load(f)
    with targets_path.open("rb") as f:
        targets = pickle.load(f)
    return joblib.load(model_path), features, targets


def predict(history: list[dict]) -> dict:
    if len(history) < 25:
        raise ValueError("pollution model requires at least 25 historical hourly readings")
    model, features, targets = _load_artifacts()
    df = pd.DataFrame(history).copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values("timestamp")
    for col in ["PM2.5","PM10","NO₂","SO₂","CO","O₃","Temp_C","Humidity_%","Wind_Speed_mps","Wind_Direction_deg","Pressure_hPa","Rain_mm"]:
        if col not in df:
            df[col] = np.nan
    for col in ["NO₂","SO₂","CO","O₃","Temp_C","Humidity_%"]:
        for n in range(1, 6):
            df[f"{col}_ROC_{n}h"] = df[col].diff(n)
    for col in ["PM2.5", "PM10"]:
        for n in range(1, 6):
            df[f"{col}_lag_{n}h"] = df[col].shift(n)
        for n in (3, 6, 12, 24):
            df[f"{col}_rolling_mean_{n}h"] = df[col].rolling(n).mean()
    df["hour"] = df.timestamp.dt.hour
    df["day_of_week"] = df.timestamp.dt.dayofweek
    df["month"] = df.timestamp.dt.month
    df["hour_sin"] = np.sin(2 * np.pi * df.hour / 24)
    df["hour_cos"] = np.cos(2 * np.pi * df.hour / 24)
    df["dow_sin"] = np.sin(2 * np.pi * df.day_of_week / 7)
    df["dow_cos"] = np.cos(2 * np.pi * df.day_of_week / 7)
    wd = np.deg2rad(df["Wind_Direction_deg"])
    df["wind_dir_sin"] = np.sin(wd)
    df["wind_dir_cos"] = np.cos(wd)
    df["season_monsoon"] = df.month.isin([6, 7, 8, 9]).astype(int)
    df["season_post_monsoon"] = df.month.isin([10, 11]).astype(int)
    df["season_summer"] = df.month.isin([3, 4, 5]).astype(int)
    df["season_winter"] = df.month.isin([12, 1, 2]).astype(int)
    station = df.iloc[-1].get("Station_ID", history[-1].get("station_id", 1))
    for i in range(1, 6):
        df[f"station_{i}"] = int(str(station).endswith(str(i)) or station == i)
    X = df.iloc[[-1]].reindex(columns=features)
    pred = model.predict(X)[0]
    return {t: float(v) for t, v in zip(targets, pred)}
