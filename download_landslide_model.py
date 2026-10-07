from pathlib import Path
from urllib.request import urlopen

URL = "https://raw.githubusercontent.com/Vivekgupta9181/landslide/main/landslide_model.joblib"
TARGET = Path(__file__).resolve().parent / "models" / "landslide" / "landslide_model.joblib"

TARGET.parent.mkdir(parents=True, exist_ok=True)

print(f"Downloading landslide model to {TARGET}")
with urlopen(URL, timeout=60) as response:
    TARGET.write_bytes(response.read())

print(f"Downloaded {TARGET.stat().st_size} bytes")
