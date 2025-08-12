"""FastAPI application to get temperature data from OpenSenseMap API."""
from datetime import datetime, timedelta
from fastapi import FastAPI
import httpx  # Async HTTP client

# =============================
# App Version
# =============================
APP_VERSION = "0.0.1"

def get_version() -> str:
    """Returns the app version."""
    return APP_VERSION

def print_version():
    """Prints the app version."""
    print(f"HiveBox App Version: {APP_VERSION}")


# =============================
# Temperature Functions
# =============================
async def get_avg_temp() -> float:
    """Gets the average temperature from the OpenSenseMap API."""
    async with httpx.AsyncClient(timeout=10) as client:
        boxes = await get_boxes(client)
        valid_boxes = await check_boxes(boxes)
        boxes_temps = await get_boxes_temp(valid_boxes, client)

    if not boxes_temps:
        return 0.0

    total = sum(float(temp) for temp in boxes_temps)
    avg_temp = total / len(boxes_temps)
    return round(avg_temp, 2)

async def get_boxes(client: httpx.AsyncClient) -> list:
    """Gets all the boxes in the Berlin area."""
    url = "https://api.opensensemap.org/boxes/"
    params = {"bbox": "13.0884,52.3382,13.7611,52.6755"}
    response = await client.get(url, params=params)
    if response.status_code == 200:
        return response.json()
    print(f"Error: {response.status_code}")
    return []

async def check_boxes(boxes: list) -> list:
    """Filters boxes that have measurements in the last 3 hours."""
    valid_ids = []
    now = datetime.utcnow()
    for box in boxes:
        last_measurement_str = box.get("lastMeasurementAt")
        if last_measurement_str:
            last_measurement = datetime.strptime(last_measurement_str, "%Y-%m-%dT%H:%M:%S.%fZ")
            if now - last_measurement <= timedelta(hours=3):
                valid_ids.append(box["_id"])
    return valid_ids

async def get_boxes_temp(box_ids: list, client: httpx.AsyncClient) -> list:
    """Gets temperature readings for the given box IDs."""
    temps = []
    for box_id in box_ids:
        response = await client.get(f"https://api.opensensemap.org/boxes/{box_id}")
        if response.status_code == 200:
            data = response.json()
            for sensor in data.get("sensors", []):
                if sensor.get("title") == "Temperature":
                    temps.append(sensor["lastMeasurement"]["value"])
    return temps


# =============================
# FastAPI Application
# =============================
app = FastAPI()

@app.get("/")
async def root() -> dict:
    """Root endpoint that returns a message."""
    return {"message": "To get the temperature in Berlin, go to /temperature"}

@app.get("/version")
async def version_endpoint() -> dict:
    """Endpoint that returns the version of the application."""
    return {"version": get_version()}

@app.get("/temperature")
async def temperature_endpoint() -> dict:
    """Endpoint that returns the average temperature in Berlin."""
    temp = await get_avg_temp()
    return {"avg_temperature_in_Berlin": temp}


# =============================
# Main Entry Point
# =============================
if __name__ == "__main__":
    print_version()
