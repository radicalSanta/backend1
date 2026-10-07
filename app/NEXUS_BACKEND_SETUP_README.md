# NEXUS Backend — Setup & Run Guide

This guide sets up the NEXUS FastAPI backend, Mosquitto MQTT broker, and Neon PostgreSQL on a new Linux/EndeavourOS laptop.

## Architecture

```text
ESP32
  |
  | MQTT
  v
Mosquitto :1883
  |
  | nexus/telemetry
  v
FastAPI + MQTT Subscriber :8000
  |
  v
Neon PostgreSQL
```

---

## 1. Prerequisites

Check Python and Git:

```bash
python --version
git --version
```

If Git is missing on Arch/EndeavourOS:

```bash
sudo pacman -S git
```

---

## 2. Clone the Backend

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
cd GreenPlus-backend
```

If the backend is inside `app`:

```bash
cd app
```

Check:

```bash
ls
```

Expected:

```text
main.py
database.py
model.py
schema.py
mqtt_client.py
requirements.txt
```

---

## 3. Create the Python Virtual Environment

Inside `app`:

```bash
python -m venv .venv
source .venv/bin/activate
```

You should see `(.venv)` in the terminal.

Upgrade pip:

```bash
python -m pip install --upgrade pip
```

---

## 4. Install Python Dependencies

Preferred:

```bash
pip install -r requirements.txt
```

If requirements.txt is not ready:

```bash
pip install fastapi uvicorn sqlalchemy psycopg2-binary python-dotenv pydantic paho-mqtt
```

Then save dependencies:

```bash
pip freeze > requirements.txt
```

---

## 5. Configure Neon PostgreSQL

Create `.env`:

```bash
nano .env
```

Add:

```env
DATABASE_URL=YOUR_NEON_DATABASE_CONNECTION_STRING
MQTT_BROKER=YOUR_LAPTOP_LAN_IP
MQTT_PORT=1883
MQTT_TOPIC=nexus/telemetry
```

Example structure:

```env
DATABASE_URL=postgresql://username:password@ep-example-pooler.region.aws.neon.tech/dbname?sslmode=require
MQTT_BROKER=10.36.232.114
MQTT_PORT=1883
MQTT_TOPIC=nexus/telemetry
```

Do not commit `.env`.

Add to `.gitignore`:

```gitignore
.venv/
__pycache__/
.env
```

Test Neon:

```bash
python -c "from database import engine; conn = engine.connect(); print('Neon PostgreSQL connection successful'); conn.close()"
```

Expected:

```text
Neon PostgreSQL connection successful
```

---

## 6. Install and Start Mosquitto

On EndeavourOS / Arch:

```bash
sudo pacman -S mosquitto
```

Enable and start:

```bash
sudo systemctl enable --now mosquitto
```

Check:

```bash
sudo systemctl status mosquitto
```

Check port 1883:

```bash
ss -ltnp | grep 1883
```

---

## 7. Configure Mosquitto for LAN Access

Edit:

```bash
sudo nano /etc/mosquitto/mosquitto.conf
```

For the current local/hackathon prototype:

```conf
listener 1883 0.0.0.0
allow_anonymous true
```

Restart:

```bash
sudo systemctl restart mosquitto
```

Verify:

```bash
ss -ltnp | grep 1883
```

> `allow_anonymous true` is only for a controlled local prototype. Do not expose this configuration to the public internet.

---

## 8. Find the Laptop LAN IP

Run:

```bash
ip route
```

or:

```bash
ip addr
```

Example:

```text
10.36.232.114
```

This is the address the ESP32 must use as the MQTT broker.

Do not use:

```text
127.0.0.1
localhost
```

in the ESP32 MQTT configuration.

---

## 9. Configure Firewall

Check firewalld:

```bash
sudo firewall-cmd --state
```

Allow MQTT:

```bash
sudo firewall-cmd --zone=public --add-port=1883/tcp --permanent
sudo firewall-cmd --reload
```

Verify:

```bash
sudo firewall-cmd --zone=public --list-ports
```

Expected:

```text
1883/tcp
```

---

## 10. Test Mosquitto Locally

Terminal 1:

```bash
mosquitto_sub -h 127.0.0.1 -p 1883 -t nexus/telemetry
```

Terminal 2:

```bash
mosquitto_pub -h 127.0.0.1 -p 1883 -t nexus/telemetry -m '{"test":true}'
```

Terminal 1 should display:

```json
{"test":true}
```

---

## 11. Test MQTT Over LAN

On the laptop:

```bash
mosquitto_sub -h YOUR_LAPTOP_LAN_IP -p 1883 -t nexus/telemetry
```

Example:

```bash
mosquitto_sub -h 10.36.232.114 -p 1883 -t nexus/telemetry
```

The ESP32 and laptop must be on the same Wi-Fi network.

---

## 12. ESP32 MQTT Configuration

In the ESP32 `config.h`:

```cpp
#define MQTT_BROKER "YOUR_LAPTOP_LAN_IP"
#define MQTT_PORT 1883
#define MQTT_TOPIC "nexus/telemetry"
```

Example:

```cpp
#define MQTT_BROKER "10.36.232.114"
#define MQTT_PORT 1883
#define MQTT_TOPIC "nexus/telemetry"
```

The IP must be changed if the laptop gets a different LAN IP.

---

## 13. Test ESP32 → MQTT

Start:

```bash
mosquitto_sub -h YOUR_LAPTOP_LAN_IP -p 1883 -t nexus/telemetry
```

Power/reset the ESP32.

Expected telemetry structure:

```json
{
  "temperature_c": 24.9,
  "humidity_percent": 86,
  "soil_moisture": 0,
  "soil_score": 0,
  "sound_activity": 0.70,
  "sound_score": 99.29,
  "latitude": 25.5788,
  "longitude": 91.8933,
  "gps_source": "FALLBACK"
}
```

Exact values depend on the sensors.

---

## 14. Start FastAPI

From `app`:

```bash
source .venv/bin/activate
uvicorn main:app --reload
```

Expected:

```text
INFO: Uvicorn running on http://127.0.0.1:8000
NEXUS MQTT subscriber started
Connected to MQTT broker
Subscribed to: nexus/telemetry
```

---

## 15. Test FastAPI

In another terminal:

```bash
curl http://127.0.0.1:8000/
```

Expected:

```json
{"message":"NEXUS API is running"}
```

Swagger UI:

```text
http://127.0.0.1:8000/docs
```

Endpoints:

```text
GET  /
POST /readings
GET  /latest
GET  /history
```

---

## 16. Test FastAPI → Neon Manually

This bypasses MQTT and tests the API/database layer:

```bash
curl -X POST http://127.0.0.1:8000/readings   -H "Content-Type: application/json"   -d '{
    "temperature_c": 24.9,
    "humidity_percent": 86,
    "soil_moisture": 0,
    "soil_score": 0,
    "sound_activity": 0.70,
    "sound_score": 99.29,
    "latitude": 25.5788,
    "longitude": 91.8933,
    "gps_source": "FALLBACK"
  }'
```

The response should include database-generated:

```json
"id": 1,
"time": "2026-09-06T..."
```

The ESP32 does not send `id` or `time`.

---

## 17. Test Latest Reading

```bash
curl http://127.0.0.1:8000/latest
```

---

## 18. Test History

```bash
curl http://127.0.0.1:8000/history
```

Returns the latest 10 records.

---

# Full System Test

Run the components in this order.

### Terminal 1 — MQTT monitor

```bash
mosquitto_sub -h YOUR_LAPTOP_LAN_IP -p 1883 -t nexus/telemetry
```

### Terminal 2 — FastAPI

```bash
cd path/to/GreenPlus-backend/app
source .venv/bin/activate
uvicorn main:app --reload
```

### ESP32

Power/reset the ESP32.

FastAPI should show:

```text
Connected to MQTT broker
Subscribed to: nexus/telemetry
MQTT telemetry received:
{...}
Saved telemetry with ID: 2
```

Then:

```bash
curl http://127.0.0.1:8000/latest
```

The response should contain the real ESP32 telemetry.

---

# Current Database Model

Table:

```text
sensor_readings
```

Columns:

```text
id
time
temperature_c
humidity_percent
soil_moisture
soil_score
sound_activity
sound_score
latitude
longitude
gps_source
```

`id` and `time` are generated by PostgreSQL.

They are intentionally absent from ESP32 telemetry.

---

# Troubleshooting

## Port 8000 already in use

Check:

```bash
sudo ss -ltnp | grep :8000
```

Test whether FastAPI is already running:

```bash
curl http://127.0.0.1:8000/
```

If necessary:

```bash
kill PID
```

Then:

```bash
uvicorn main:app --reload
```

## MQTT port 1883 not listening

```bash
sudo systemctl status mosquitto
ss -ltnp | grep 1883
```

Restart:

```bash
sudo systemctl restart mosquitto
```

## ESP32 MQTT connection fails

Check:

1. ESP32 and laptop use the same Wi-Fi.
2. `MQTT_BROKER` is the laptop LAN IP.
3. Mosquitto listens on `0.0.0.0:1883`.
4. Firewall allows `1883/tcp`.
5. Topic is exactly `nexus/telemetry`.

Check:

```bash
sudo firewall-cmd --zone=public --list-ports
```

## MQTT state `-2`

Check:

```bash
ss -ltnp | grep 1883
ip route
```

Make sure the ESP32 uses the laptop's current LAN IP.

## Neon connection fails

Check `.env` and make sure the Neon connection string is correct and includes:

```text
sslmode=require
```

Test:

```bash
python -c "from database import engine; conn = engine.connect(); print('Neon PostgreSQL connection successful'); conn.close()"
```

## FastAPI receives no MQTT telemetry

First check Mosquitto independently:

```bash
mosquitto_sub -h YOUR_LAPTOP_LAN_IP -p 1883 -t nexus/telemetry
```

If ESP32 messages appear there but not in FastAPI, check:

```text
MQTT_BROKER
MQTT_PORT
MQTT_TOPIC
```

The topic must be:

```text
nexus/telemetry
```

---

# Quick Start After Initial Setup

```bash
cd path/to/GreenPlus-backend/app
source .venv/bin/activate
sudo systemctl start mosquitto
uvicorn main:app --reload
```

Then power the ESP32.

Check:

```bash
curl http://127.0.0.1:8000/latest
```

or:

```bash
curl http://127.0.0.1:8000/history
```

---

# Current NEXUS Backend Scope

The current backend handles:

- ESP32 telemetry ingestion
- MQTT subscription
- Pydantic validation
- Neon PostgreSQL storage
- Latest telemetry API
- Historical telemetry API

ML prediction and the environmental risk engine are separate layers and should be added after the telemetry pipeline is stable.
