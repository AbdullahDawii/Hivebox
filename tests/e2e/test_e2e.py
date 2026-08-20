import os
import requests

BASE_URL = os.getenv("APP_BASE_URL", "http://localhost:5050")


def test_version_endpoint():
    response = requests.get(f"{BASE_URL}/version", timeout=10)
    assert response.status_code == 200
    assert "version" in response.json()


def test_temperature_endpoint():
    response = requests.get(f"{BASE_URL}/temperature", timeout=10)
    assert response.status_code == 200
    data = response.json()
    assert "average_temperature" in data
    assert "status" in data
    assert data["status"] in ["Too Cold", "Good", "Too Hot"]

def test_readyz_endpoint():
    response = requests.get(f"{BASE_URL}/readyz", timeout=30)
    assert response.status_code in [200, 503]
    assert "status" in response.json()


def test_metrics_endpoint():
    response = requests.get(f"{BASE_URL}/metrics", timeout=10)
    assert response.status_code == 200
    assert "hivebox_requests_total" in response.text
