from sqlalchemy import Column, Integer, Float, Text, TIMESTAMP
from sqlalchemy.sql import func
from database import Base


class SensorReading(Base):
    __tablename__ = "sensor_readings"

    id = Column(Integer, primary_key=True, index=True)
    time = Column(TIMESTAMP, server_default=func.now(), nullable=False)

    # Local environmental telemetry
    temperature_c = Column(Float)
    temperature_score = Column(Float)
    humidity_percent = Column(Float)
    humidity_score = Column(Float)

    # Soil
    soil_moisture = Column(Float)
    soil_score = Column(Float)

    # Sound
    sound_activity = Column(Float)
    sound_score = Column(Float)

    # Human activity
    pir_activity = Column(Float)
    pir_score = Column(Float)

    # CO2
    co2_ppm = Column(Float)
    co2_score = Column(Float)

    # GPS
    latitude = Column(Float)
    longitude = Column(Float)
    gps_source = Column(Text)