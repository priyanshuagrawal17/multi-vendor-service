import os
import time
import redis
import requests
from pymongo import MongoClient

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongo:27017/")
VENDOR_SYNC_URL = os.getenv("VENDOR_SYNC_URL", "http://vendor_sync:9000/data")
VENDOR_ASYNC_URL = os.getenv("VENDOR_ASYNC_URL", "http://vendor_async:9001/data")

VENDOR_RATE_LIMIT = 1.0

r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
mongo_client = MongoClient(MONGO_URI)
db = mongo_client["multivendor"]
jobs_collection = db["jobs"]

def clean_response(data):
    if isinstance(data, dict):
        data.pop("ssn", None)
        for k, v in data.items():
            if isinstance(v, str):
                data[k] = v.strip()
    return data

def process_job(job_id):
    job = jobs_collection.find_one({"request_id": job_id})
    if not job:
        return
    jobs_collection.update_one({"request_id": job_id}, {"$set": {"status": "processing"}})
    payload = job["payload"]
    vendor = payload.get("vendor", "sync")
    try:
        if vendor == "sync":
            resp = requests.post(VENDOR_SYNC_URL, json=payload, timeout=5)
            resp.raise_for_status()
            result = clean_response(resp.json())
            jobs_collection.update_one({"request_id": job_id}, {"$set": {"status": "complete", "result": result}})
        elif vendor == "async":
            resp = requests.post(VENDOR_ASYNC_URL, json={"request_id": job_id, **payload}, timeout=5)
            resp.raise_for_status()
        else:
            jobs_collection.update_one({"request_id": job_id}, {"$set": {"status": "failed", "error": "Unknown vendor"}})
    except Exception as e:
        jobs_collection.update_one({"request_id": job_id}, {"$set": {"status": "failed", "error": str(e)}})

def main():
    last_sync = 0
    last_async = 0
    print("Worker started, listening for jobs...")
    while True:
        jobs = r.xread({"jobs_stream": "0"}, block=5000, count=1)
        if not jobs:
            continue
        for stream, messages in jobs:
            for msg_id, msg in messages:
                job_id = msg["request_id"]
                job = jobs_collection.find_one({"request_id": job_id})
                if not job or job.get("status") != "pending":
                    continue
                vendor = job["payload"].get("vendor", "sync")
                now = time.time()
                if vendor == "sync" and now - last_sync < VENDOR_RATE_LIMIT:
                    time.sleep(VENDOR_RATE_LIMIT - (now - last_sync))
                if vendor == "async" and now - last_async < VENDOR_RATE_LIMIT:
                    time.sleep(VENDOR_RATE_LIMIT - (now - last_async))
                process_job(job_id)
                if vendor == "sync":
                    last_sync = time.time()
                else:
                    last_async = time.time()

if __name__ == "__main__":
    main()