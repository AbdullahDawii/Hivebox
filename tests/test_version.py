import os
import subprocess

def test_version_output():
    main_path = os.path.join("src", "main.py")
    result = subprocess.run(["python", main_path], capture_output=True, text=True)
    assert "HiveBox App Version: 0.0.1" in result.stdout
