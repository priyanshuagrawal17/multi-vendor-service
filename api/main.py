from fastapi import FastAPI, Request
from uuid import uuid4
import redis
import os
from pymongo import MongoClient

app = FastAPI()

# Redis setup
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

# MongoDB setup
MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongo:27017/")
mongo_client = MongoClient(MONGO_URI)
db = mongo_client["multivendor"]
jobs_collection = db["jobs"]

@app.post("/jobs")
async def create_job(request: Request):
    payload = await request.json()
    request_id = str(uuid4())
    job = {
        "request_id": request_id,
        "payload": payload,
        "status": "pending"
    }
    # Save to MongoDB
    jobs_collection.insert_one(job)
    # Add to Redis Stream
    r.xadd("jobs_stream", {"request_id": request_id})
    return {"request_id": request_id}

@app.get("/jobs/{request_id}")
def get_job(request_id: str):
    job = jobs_collection.find_one({"request_id": request_id}, {"_id": 0})
    if not job:
        return {"error": "Job not found"}
    if job.get("status") == "complete":
        return {"status": "complete", "result": job.get("result")}
    elif job.get("status") == "failed":
        return {"status": "failed", "error": job.get("error")}
    else:
        return {"status": "processing"}

@app.post("/vendor-webhook/async")
async def vendor_webhook_async(request: Request):
    data = await request.json()
    request_id = data.get("request_id")
    if not request_id:
        return {"error": "Missing request_id"}
    # Clean and store result
    result = {k: v for k, v in data.items() if k != "ssn"}
    jobs_collection.update_one(
        {"request_id": request_id},
        {"$set": {"status": "complete", "result": result}}
    )
    return {"status": "stored"}