import asyncio
import json
import os

import paho.mqtt.client as mqtt

from app.database import SessionLocal
from app.model import SensorReading
from app.connection_manager import manager


MQTT_BROKER = os.getenv("MQTT_BROKER", "192.168.2.229")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_TOPIC = os.getenv("MQTT_TOPIC", "greenpulse/telemetry")

main_loop = None


def set_main_loop(loop):
    global main_loop
    main_loop = loop


def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        print("Connected to MQTT broker")

        client.subscribe(MQTT_TOPIC)

        print(f"Subscribed to: {MQTT_TOPIC}")

    else:
        print(f"MQTT connection failed: {reason_code}")


def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode())

        print("MQTT telemetry received:")
        print(data)

        reading = SensorReading(**data)

        db = SessionLocal()

        try:
            db.add(reading)
            db.commit()
            db.refresh(reading)

            print(f"Saved telemetry with ID: {reading.id}")

            if main_loop:
                asyncio.run_coroutine_threadsafe(
                    manager.broadcast({
                        "id": reading.id,
                        "time": reading.time.isoformat(),

                        # Local telemetry
                        "temperature_c": reading.temperature_c,
                        "humidity_percent": reading.humidity_percent,

                        # Soil
                        "soil_moisture": reading.soil_moisture,
                        "soil_score": reading.soil_score,

                        # Sound
                        "sound_activity": reading.sound_activity,
                        "sound_score": reading.sound_score,

                        # PIR
                        "pir_activity": reading.pir_activity,
                        "pir_score": reading.pir_score,

                        # CO2
                        "co2_ppm": reading.co2_ppm,
                        "co2_score": reading.co2_score,

                        # GPS
                        "latitude": reading.latitude,
                        "longitude": reading.longitude,
                        "gps_source": reading.gps_source,
                    }),
                    main_loop
                )

        finally:
            db.close()

    except json.JSONDecodeError:
        print("Invalid JSON received from MQTT")

    except Exception as e:
        print(f"MQTT processing error: {e}")


def start_mqtt():
    client = mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION2
    )

    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(
        MQTT_BROKER,
        MQTT_PORT
    )

    client.loop_start()

    return client