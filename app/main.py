import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.database import get_db, engine, Base
from app.model import SensorReading
from app.schema import SensorReadingCreate, SensorReadingResponse
from app.mqtt_client import start_mqtt
import app.mqtt_client as mqtt_client
from app.connection_manager import manager
from app.ems.pipeline import run_ems_pipeline
from app.dashboard_ml import router as dashboard_ml_router


# Create database tables if they don't already exist
Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Hand the running event loop to the MQTT thread so it can
    # schedule WebSocket broadcasts from on_message
    mqtt_client.set_main_loop(asyncio.get_event_loop())

    # Start MQTT subscriber. If the broker isn't reachable, don't let
    # that take down the API.
    mqtt_client_instance = None

    try:
        mqtt_client_instance = start_mqtt()
        print("GreenPulse MQTT subscriber started")
    except Exception as e:
        print(f"MQTT broker unavailable, continuing without it: {e}")

    yield

    # Stop MQTT subscriber when FastAPI shuts down
    if mqtt_client_instance:
        mqtt_client_instance.loop_stop()
        mqtt_client_instance.disconnect()
        print("GreenPulse MQTT subscriber stopped")


app = FastAPI(
    title="GreenPulse Backend",
    lifespan=lifespan
)


app.include_router(dashboard_ml_router)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def home():
    return {
        "message": "GreenPulse API is running"
    }


@app.post(
    "/readings",
    response_model=SensorReadingResponse,
    status_code=201
)
def create_reading(
    payload: SensorReadingCreate,
    db: Session = Depends(get_db)
):
    reading = SensorReading(
        **payload.model_dump()
    )

    db.add(reading)
    db.commit()
    db.refresh(reading)

    return reading


@app.get(
    "/latest",
    response_model=SensorReadingResponse
)
def latest(
    db: Session = Depends(get_db)
):
    reading = (
        db.query(SensorReading)
        .order_by(SensorReading.time.desc())
        .first()
    )

    if not reading:
        raise HTTPException(
            status_code=404,
            detail="No telemetry found"
        )

    return reading


@app.get("/dashboard/current")
def dashboard_current(
    db: Session = Depends(get_db),
):
    """
    Return the current GreenPulse dashboard state.

    The EMS pipeline uses the complete ESP32 telemetry,
    including temperature_score and humidity_score.

    The dashboard intentionally exposes only the raw
    temperature and humidity values, not their internal
    EMS scores.
    """

    # -----------------------------------------------------
    # Get latest telemetry
    # -----------------------------------------------------

    reading = (
        db.query(SensorReading)
        .order_by(SensorReading.time.desc())
        .first()
    )

    if not reading:
        raise HTTPException(
            status_code=404,
            detail="No telemetry found"
        )

    # -----------------------------------------------------
    # Run complete EMS pipeline
    # -----------------------------------------------------

    try:
        result = run_ems_pipeline(
            telemetry=reading
        )

    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"EMS pipeline unavailable: {str(e)}"
        )

    # -----------------------------------------------------
    # Dashboard response
    # -----------------------------------------------------

    return {
        "ems": {
            "score": result.ems,
            "ground_stability": result.ground_stability,
            "human_pressure": result.human_pressure,
            "environmental_quality": result.environmental_quality,
            "alert_level": result.alert_level,
            "primary_driver": result.primary_driver,
            "advisory": result.advisory,
        },

        "local_telemetry": {
            "temperature_c": reading.temperature_c,
            "humidity_percent": reading.humidity_percent,
            "soil_score": reading.soil_score,
            "sound_score": reading.sound_score,
            "pir_score": reading.pir_score,
            "co2_ppm": reading.co2_ppm,
        },

        "environmental_context": {
            "rainfall_1h": result.rainfall_1h,
            "rainfall_24h": result.rainfall_24h,
            "rainfall_72h": result.rainfall_72h,
            "rainfall_score": result.rainfall_score,
            "aqi": result.aqi,
            "aqi_category": result.aqi_category,
            "aqi_score": result.aqi_score,
            "surface_pressure_hpa": result.surface_pressure_hpa,
        },
    }


@app.get(
    "/history",
    response_model=list[SensorReadingResponse]
)
def history(
    db: Session = Depends(get_db)
):
    return (
        db.query(SensorReading)
        .order_by(SensorReading.time.desc())
        .limit(10)
        .all()
    )


@app.get(
    "/readings/all",
    response_model=list[SensorReadingResponse]
)
def get_all_readings(
    db: Session = Depends(get_db)
):
    return (
        db.query(SensorReading)
        .order_by(SensorReading.time.desc())
        .all()
    )


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)