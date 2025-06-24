# Multi-Vendor Data Fetch Service

## Quick Start

```sh
git clone <your-repo-url>
cd multi-vendor-service
docker-compose up --build
```

## Architecture Overview

```
+--------+      +-----------+      +--------+      +--------+
|        |      |           |      |        |      |        |
|  API   +----->+  Redis    +----->+ Worker +----->+ Vendor |
|        |      |  Stream   |      |        |      |  Mock  |
+---+----+      +-----+-----+      +---+----+      +---+----+
    |                  |               |               |
    |                  |               |               |
    v                  v               v               v
+--------+        +--------+      +--------+      +--------+
|  Mongo |        | Vendor |      | Vendor |      |Webhook |
|  DB    |        | Sync   |      | Async  |      |Service |
+--------+        +--------+      +--------+      +--------+
```

## Key Design Decisions
- **FastAPI** for async, fast API endpoints.
- **Redis Streams** for reliable job queueing.
- **MongoDB** for job persistence and status tracking.
- **Rate-limiting** handled in worker per vendor.
- **Vendor mocks** simulate both sync and async behaviors.
- **Docker Compose** for easy local orchestration.

## Sample cURL Commands

### Submit a Job (Sync Vendor)
```sh
curl -X POST http://localhost:8000/jobs \
  -H 'Content-Type: application/json' \
  -d '{"vendor": "sync", "name": "Alice", "email": "alice@example.com"}'
```

### Submit a Job (Async Vendor)
```sh
curl -X POST http://localhost:8000/jobs \
  -H 'Content-Type: application/json' \
  -d '{"vendor": "async", "name": "Bob", "email": "bob@example.com"}'
```

### Check Job Status
```sh
curl http://localhost:8000/jobs/<request_id>
```