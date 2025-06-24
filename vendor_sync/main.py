from fastapi import FastAPI, Request
import random
import time

app = FastAPI()

@app.post("/data")
async def get_data(request: Request):
    payload = await request.json()
    time.sleep(random.uniform(0.1, 0.5))
    return {
        "name": payload.get("name", "John Doe").strip(),
        "email": payload.get("email", "john@example.com").strip(),
        "ssn": "123-45-6789",
        "vendor": "sync"
    }