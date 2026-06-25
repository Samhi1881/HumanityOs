# System Troubleshooting Guide

This guide describes how to diagnose, troubleshoot, and resolve typical operational and environment issues on the HumanityOS platform.

---

## 🔌 1. Database Connection Failures (PostgreSQL)

### Symptoms
* Backend start script fails with `Connecting to database host: postgres:5432...` and eventually times out.
* The dashboard displays the Database status as `offline` or `checking...`.

### Diagnosis & Fix
1. **Check Postgres Container**: If running via Docker Compose, ensure the container is healthy:
   ```bash
   docker ps -a | grep postgres
   ```
2. **Verify Port Availability**: Ensure port `5432` is not blocked by a local native Postgres installation.
3. **Database URL Driver**: Ensure the `DATABASE_URL` in `.env` uses the asynchronous driver:
   * **Correct**: `postgresql+asyncpg://user:password@localhost:5432/db`
   * **Incorrect**: `postgresql://user:password@localhost:5432/db`

---

## ⚡ 2. Redis Connection & Rate Limiting Latencies

### Symptoms
* Requests to `/api/v1/simulation/scenarios` take ~1 second to respond before throwing rate limiting errors or functioning.

### Explanation
By default, the rate limiter attempts to connect to Redis. If Redis is unavailable, a socket timeout (configured to 1 second) can cause request latency.

### Fix
* HumanityOS features a cached `_redis_offline = True` check in [security.py](../backend/app/core/security.py#L217). If the first request experiences a Redis error, the system flags Redis as offline and **instantly switches** to the memory-bound fallback limiter, reducing subsequent request latency to 0ms.
* To restore Redis caching, verify the Redis service is active:
   ```bash
   docker-compose start redis
   ```
   Or check the `REDIS_URL` connection parameters in `.env`.

---

## 🛡️ 3. Firebase Auth & Mock Token Errors

### Symptoms
* API calls return `401 Unauthorized: Authorization credentials missing` or `Invalid authentication token`.

### Diagnosis & Fix
1. **Verify Development Mode**: Offline/local testing uses simulated bearer tokens (`mock-admin`, `mock-responder`). Ensure the backend configuration is running in development mode:
   ```ini
   ENV=development
   DEBUG=True
   ```
2. **Bearer Format**: Verify header payloads are formatted correctly. Headers must contain:
   ```http
   Authorization: Bearer mock-admin
   ```
3. **Production Firebase Configuration**: If `ENV=production`, mock tokens are disabled. You must provide a valid Firebase project ID in `.env`:
   ```ini
   FIREBASE_PROJECT_ID=your-firebase-project-id
   ```
   If client JWTs do not match the expected project issuer (`https://securetoken.google.com/<project_id>`), they are blocked.

---

## 🌐 4. Port Conflicts (8080 or 3000)

### Symptoms
* Uvicorn fails to start with: `[Errno 98] Address already in use` or `[Errno 10048]`.

### Fix
1. Find the active process occupying the port:
   * **Windows**:
     ```powershell
     netstat -ano | findstr :8080
     # Kill the process using the PID found
     taskkill /PID <PID> /F
     ```
   * **macOS / Linux**:
     ```bash
     lsof -i :8080
     kill -9 <PID>
     ```
2. Alternatively, change the target ports inside your `.env` settings.
