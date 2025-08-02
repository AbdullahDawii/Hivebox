APP_VERSION = "0.0.1"

def get_version() -> str:
    return APP_VERSION

def print_version():
    print(f"HiveBox App Version: {APP_VERSION}")

if __name__ == "__main__":
    print_version()
