import random
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from ml.landslide import predict as predict_landslide

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


def _series(current: float, spread: float, days: int = 36) -> list[float]:
    values = []
    value = current
    for _ in range(days):
        value += random.uniform(-spread, spread)
        values.append(round(value, 2))
    return values


def _rainfall_series() -> list[float]:
    values = [round(random.uniform(0, 8), 2) for _ in range(36)]
    if random.random() > 0.45:
        values[0] = round(random.uniform(15, 45), 2)
        values[1] = round(random.uniform(8, 30), 2)
        values[2] = round(random.uniform(5, 20), 2)
    return values


@router.get("/readings")
def dashboard_readings():
    temperature = round(random.uniform(25.5, 29.5), 1)
    humidity = random.randint(65, 88)
    soil = random.randint(45, 72)
    noise = random.randint(55, 78)
    co2 = random.randint(420, 560)
    slope = 32.0
    rainfall = _rainfall_series()

    payload = {
        "slope": slope,
        "lat": 25.58,
        "lon": 91.89,
        "precip": rainfall,
        "temp": _series(temperature, 0.8),
        "humidity": _series(float(humidity), 2.0),
        "wind": _series(4.5, 1.5),
        "air": _series(18.0, 2.0),
        "extra_features": {},
    }

    try:
        landslide = predict_landslide(payload)
        landslide_status = "ok"
    except Exception as exc:
        landslide = {
            "probability": None,
            "prediction": None,
            "riskLevel": "Unavailable",
            "keyFactors": {},
        }
        landslide_status = str(exc)

    rainfall_24h = round(sum(rainfall[:1]), 2)
    rainfall_72h = round(sum(rainfall[:3]), 2)

    ems = round(
        max(
            0,
            min(
                100,
                100
                - abs(temperature - 25) * 2
                - max(0, humidity - 70) * 0.3
                - max(0, noise - 60) * 0.25
                - max(0, soil - 65) * 0.2,
            ),
        ),
        1,
    )

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "locationId": "ward-lake",
        "environmentalMonitoringScore": ems,
        "sensors": {
            "temperature": temperature,
            "humidity": humidity,
            "soil": soil,
            "sound": noise,
            "pir": random.randint(25, 60),
            "co2": co2,
        },
        "rainfall": {
            "1h": rainfall[0],
            "24h": rainfall_24h,
            "72h": rainfall_72h,
            "score": round(min(100, rainfall_72h * 1.4), 1),
        },
        "landslide": landslide,
        "mlStatus": {
            "landslide": landslide_status,
        },
    }
