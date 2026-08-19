from main import app

client = app.test_client()

def test_version_output():
    response = client.get("/version")
    assert response.status_code == 200
    assert response.get_json() == {"version": "0.0.1"}
