import httpx

LOGGING_API = "http://20.244.56.144/evaluation-service/logs"

def log(stack: str, level: str, package: str, message: str):
    payload = {
        "stack": stack,
        "level": level,
        "package": package,
        "message": message
    }
    try:
        with httpx.Client(timeout=5.0) as client:
            client.post(LOGGING_API, json=payload)
    except Exception as e:
        print(f"Logging failed: {e}")
