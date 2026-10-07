from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from model import SensorReading
from ml.landslide import predict as predict_landslide
from ml.pollution import predict as predict_pollution
from ems.pipeline import run_ems_pipeline

router = APIRouter(prefix="/dashboard", tags=["Dashboard ML"])


@router.get("/readings")
def dashboard_readings(db: Session = Depends(get_db)):
    reading = db.query(SensorReading).order_by(SensorReading.time.desc()).first()
    if not reading:
        raise HTTPException(404, "No telemetry found")

    try:
        ems = run_ems_pipeline(telemetry=reading)
    except Exception as exc:
        raise HTTPException(503, f"EMS pipeline unavailable: {exc}") from exc

    history_rows = (
        db.query(SensorReading)
        .order_by(SensorReading.time.desc())
        .limit(48)
        .all()
    )

    pollution = None
    pollution_error = None
    try:
        # GreenPulse's DB does not currently store the pollution model's
        # PM/NO2/SO2/CO/O3 hourly columns, so do not fabricate them.
        pollution_history = [
            {
                "timestamp": row.time,
                "PM2.5": None,
                "PM10": None,
                "NO2": None,
                "SO2": None,
                "CO": None,
                "O3": None,
                "Temp_C": row.temperature_c,
                "Humidity_%": row.humidity_percent,
                "Wind_Speed_mps": None,
                "Wind_Direction_deg": None,
                "Pressure_hPa": None,
                "Rain_mm": None,
                "Station_ID": 1,
            }
            for row in reversed(history_rows)
        ]
        pollution = predict_pollution(pollution_history)
    except Exception as exc:
        pollution_error = str(exc)

    return {
        "timestamp": reading.time,
        "environmentalMonitoringScore": ems.ems,
        "pollution": pollution,
        "landslide": None,
        "sensors": {
            "temperature": reading.temperature_c,
            "humidity": reading.humidity_percent,
            "soil": reading.soil_score,
            "sound": reading.sound_score,
            "pir": reading.pir_score,
            "co2": reading.co2_ppm,
        },
        "rainfall": {
            "1h": ems.rainfall_1h,
            "24h": ems.rainfall_24h,
            "72h": ems.rainfall_72h,
            "score": ems.rainfall_score,
        },
        "ems": {
            "groundStability": ems.ground_stability,
            "humanPressure": ems.human_pressure,
            "environmentalQuality": ems.environmental_quality,
            "alertLevel": ems.alert_level,
            "primaryDriver": ems.primary_driver,
        },
        "advisory": {
            "message": ems.advisory,
            "action": ems.action,
            "reason": ems.reason,
            "priority": ems.priority,
        },
        "mlStatus": {
            "pollution": "ok" if pollution is not None else pollution_error,
            "landslide": "artifact-ready but requires a slope + 36-day weather adapter",
        },
    }
