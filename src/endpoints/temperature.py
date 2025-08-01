"""This module contains the function to get the average temperature from the OpenSenseMap API."""
from datetime import datetime, timedelta
import requests # type: ignore


async def get_avg_temp() -> float:
    """
    This is the main function that gets the average temperature from the OpenSenseMap API.
    """
    with requests.Session() as session:
        boxes = await get_boxes(session)
        boxes = await check_boxes(boxes)
        boxes_temps = await get_boxes_temp(boxes, session)
        if not boxes_temps:
            return 0.0
        counter = 0.0
        for box in boxes_temps:
            box = float(box)
            counter += box
        avg_temp = counter / len(boxes_temps)
        return round(avg_temp, 2)


async def get_boxes(session) -> list:
    """
    This function gets all the boxes from the OpenSenseMap API.
    """
    url = "https://api.opensensemap.org/boxes/"
    passargs = {"bbox": "13.0884,52.3382,13.7611,52.6755"}
    response = session.get(url, params=passargs, timeout=10)
    if response.status_code == 200:
        return response.json()
    print(f"Error: {response.status_code}")
    return []


async def check_boxes(boxes) -> list:
    """
    checks if the box's sensors last check was at least 3 hours ago and returns a list of box IDs.
    """
    ok_boxs = []
    for box in boxes:
        if "lastMeasurementAt" in box.keys():
            last_measurement = datetime.strptime(
                box["lastMeasurementAt"], "%Y-%m-%dT%H:%M:%S.%fZ"
            )
            now_str = datetime.now().isoformat(timespec="milliseconds") + "Z"
            now = datetime.strptime(now_str, "%Y-%m-%dT%H:%M:%S.%fZ")
            if now - last_measurement <= timedelta(hours=3):
                ok_boxs.append(box["_id"])
    return ok_boxs


async def get_boxes_temp(boxs, session) -> list:
    """
    This function gets the temperature from every box I got so far by using thier IDs."""
    url = "https://api.opensensemap.org/boxes/"
    temps = []
    for box in boxs:
        response = session.get(url + box, timeout=30)
        data = response.json()
        for sensor in data["sensors"]:
            if sensor["title"] == "Temperature":
                temps.append(sensor["lastMeasurement"]["value"])
    return temps