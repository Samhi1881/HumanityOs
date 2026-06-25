# HumanityOS Environment Configuration Guide

This document defines and documents the environment variables used by the HumanityOS backend.

## Production Configuration

Create a `.env` file in the `backend/` directory or inject these variables in your deployment environments (e.g. Google Cloud Run Settings / Kubernetes ConfigMaps).

| Variable Name | Type | Default Value | Description / Security Considerations |
| :--- | :--- | :--- | :--- |
| **PROJECT_NAME** | `str` | `"HumanityOS"` | Logical name of the application service. |
| **ENV** | `str` | `"development"` | Application environment. Set to `production` in live deployments. |
| **DEBUG** | `bool` | `True` | Toggle verbose debug logs and stacktraces. Set to `False` in production. |
| **PORT** | `int` | `8080` | Port the FastAPI application binds to. |
| **SECRET_KEY** | `str` | *None* | **CRITICAL SECURITY**: Encryption key for signing state tokens. **Never** use default values in production. |
| **ACCESS_TOKEN_EXPIRE_MINUTES** | `int` | `60` | Lifespan of generated system authorization tokens. |
| **BACKEND_CORS_ORIGINS** | `list` | `[]` | Comma-separated or JSON array of CORS origins allowed. e.g. `https://humanityos.web.app`. |
| **DATABASE_URL** | `str` | *None* | Connection URI. Production requires PostgreSQL asyncpg drivers: `postgresql+asyncpg://user:pass@host:5432/dbname`. |
| **REDIS_URL** | `str` | *None* | Connection URI. Used for Rate Limiter and Cache service. e.g. `redis://localhost:6379/0`. |
| **CHROMADB_HOST** | `str` | `"localhost"` | Host address of Chroma vector store. |
| **CHROMADB_PORT** | `int` | `8001` | Port of Chroma vector store. |
| **GEMINI_API_KEY** | `str` | *None* | **SECRET**: Google AI Studio API Key to enable the specialists' response generators. |
| **GEMINI_MODEL** | `str` | `"gemini-2.5-flash"` | Specialist LLM generator model version. |
| **MCP_SERVER_URLS** | `list` | `[]` | List of secondary Model Context Protocol server endpoints. |
| **LOG_LEVEL** | `str` | `"INFO"` | Logging verbosity filter: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`. |
| **STRUCTURED_LOGGING** | `bool` | `False` | Toggles JSON-formatted console logging. Must be `true` in production (e.g., Cloud Logging aggregation). |
| **FIREBASE_PROJECT_ID** | `str` | `"humanityos-prod"` | Google Firebase Project ID used to verify client JWT claims. |
| **RATE_LIMIT_PER_MINUTE** | `int` | `60` | Sliding window rate limits threshold protecting protected API endpoints. |

## Production Security Best Practices

1. **Secret Management**: Do **not** commit actual keys to source control. In GCP Cloud Run, reference secrets directly from **Secret Manager** as mounted environment variables.
2. **CORS Configuration**: Restrict `BACKEND_CORS_ORIGINS` to the exact domain serving the static assets (e.g. `https://humanityos.web.app`) instead of using wildcards (`*`).
3. **Database Security**: Enforce SSL connections for Postgres in production by appending `?ssl=require` or parsing connection certifications.
4. **Structured Logging**: Enable `STRUCTURED_LOGGING=true` so that log lines are emitted as JSON. Cloud Log Viewer automatically parses these fields (such as `user_id`, `role`, `status_code`, etc.) to trigger alerts.
