import subprocess

def test_version_output():
    result = subprocess.run(["python", "main.py"], capture_output=True, text=True)
    assert "HiveBox App Version: 0.0.1" in result.stdout
