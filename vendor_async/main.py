from fastapi import FastAPI, Request
import random
import time
import threading
import requests
import os

WEBHOOK_URL = os.getenv("WEBHOOK_URL", "http://api:8000/vendor-webhook/async")

app = FastAPI()

def send_result_later(request_id, payload):
    def task():
        time.sleep(random.uniform(1, 3))  # Simulate async delay
        data = {
            "request_id": request_id,
            "name": payload.get("name", "Jane Doe").strip(),
            "email": payload.get("email", "jane@example.com").strip(),
            "ssn": "987-65-4321",
            "vendor": "async"
        }
        try:
            requests.post(WEBHOOK_URL, json=data, timeout=5)
        except Exception as e:
            print(f"Failed to send webhook: {e}")
    threading.Thread(target=task).start()

@app.post("/data")
async def get_data(request: Request):
    payload = await request.json()
    request_id = payload.get("request_id")
    send_result_later(request_id, payload)
    return {"status": "accepted"}