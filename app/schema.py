from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict


class SensorReadingCreate(BaseModel):

    temperature_c: float | None = Field(None, ge=-50, le=100)
    temperature_score: float | None = Field(None, ge=0, le=100)
    humidity_percent: float | None = Field(None, ge=0, le=100)
    humidity_score: float | None = Field(None, ge=0, le=100)

    soil_moisture: float | None = Field(None, ge=0)
    soil_score: float | None = Field(None, ge=0, le=100)

    sound_activity: float | None = Field(None, ge=0)
    sound_score: float | None = Field(None, ge=0, le=100)

    pir_activity: float | None = Field(None, ge=0)
    pir_score: float | None = Field(None, ge=0, le=100)

    co2_ppm: float | None = Field(None, ge=0)
    co2_score: float | None = Field(None, ge=0, le=100)

    latitude: float | None = Field(None, ge=-90, le=90)
    longitude: float | None = Field(None, ge=-180, le=180)

    gps_source: str | None = None


class SensorReadingResponse(SensorReadingCreate):

    id: int
    time: datetime

    model_config = ConfigDict(from_attributes=True)