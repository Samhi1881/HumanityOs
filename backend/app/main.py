from contextlib import asynccontextmanager
from typing import AsyncGenerator, Any
from fastapi import FastAPI, HTTPException, Response, status
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.logging import setup_logging
from app.api.v1 import api_router
from app.services.mcp import HttpMCPService

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Startup tasks
    setup_logging()
    yield
    # Shutdown tasks
    # Cleanup any active HTTP client connections
    mcp_service = HttpMCPService()
    await mcp_service.close()

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Backend API platform for HumanityOS, structured using clean architecture principles.",
    version="0.1.0",
    lifespan=lifespan,
    debug=settings.DEBUG
)

# CORS Middleware Configuration
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Include APIs
app.include_router(api_router, prefix="/api/v1")

# Mount Model Context Protocol (MCP) Server SSE Transport
from app.api.mcp_server import mcp_server
app.mount("/mcp", mcp_server.sse_app())

# Healthcheck routes
@app.get("/health", tags=["System"])
def health_check() -> dict[str, str]:
    """Basic health check endpoint for Cloud Run and Load Balancers."""
    return {"status": "healthy", "service": settings.PROJECT_NAME}

@app.get("/health/live", tags=["System"])
def live_check() -> dict[str, str]:
    """Liveness check to ensure the server process is alive."""
    return {"status": "alive"}

@app.get("/health/ready", tags=["System"])
async def ready_check() -> dict[str, str]:
    """Readiness check to verify DB and Cache connection statuses."""
    from sqlalchemy import text
    from app.db.session import engine
    import redis

    db_status = "healthy"
    redis_status = "healthy"
    details = {}

    # Check Database connection
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception as e:
        db_status = "unhealthy"
        details["database"] = str(e)

    # Check Redis connection
    try:
        r = redis.from_url(settings.REDIS_URL, socket_timeout=1)
        r.ping()
    except Exception as e:
        redis_status = "unhealthy"
        details["redis"] = str(e)

    if db_status == "unhealthy" or redis_status == "unhealthy":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "unhealthy",
                "database": db_status,
                "redis": redis_status,
                "errors": details
            }
        )

    return {
        "status": "healthy",
        "database": db_status,
        "redis": redis_status
    }

@app.get("/metrics", tags=["System"])
def get_metrics() -> Response:
    """Exports application performance metrics in Prometheus format."""
    import psutil
    import os

    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    cpu_percent = process.cpu_percent(interval=None)

    metrics_lines = [
        "# HELP humanityos_cpu_utilization_ratio CPU utilization ratio of the server process.",
        "# TYPE humanityos_cpu_utilization_ratio gauge",
        f"humanityos_cpu_utilization_ratio {cpu_percent / 100.0:.4f}",
        "",
        "# HELP humanityos_memory_bytes Memory usage in bytes.",
        "# TYPE humanityos_memory_bytes gauge",
        f"humanityos_memory_bytes{{type=\"rss\"}} {mem_info.rss}",
        f"humanityos_memory_bytes{{type=\"vms\"}} {mem_info.vms}",
        ""
    ]

    return Response(content="\n".join(metrics_lines), media_type="text/plain")


