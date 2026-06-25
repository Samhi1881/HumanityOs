from typing import Annotated
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.services.ai import AIService, GeminiAIService
from app.services.vector import VectorStoreService, ChromaVectorStoreService
from app.services.cache import CacheService, RedisCacheService
from app.services.mcp import MCPService, HttpMCPService

# Import security modules
from app.core.security import User, RoleChecker, check_rate_limit, scan_for_prompt_injection

router = APIRouter()

# Include simulation scenarios
from app.api.v1.simulation import router as simulation_router
router.include_router(simulation_router, prefix="/simulation")

# Input validation model
class PromptRequest(BaseModel):
    prompt: str = Field(..., min_length=5, max_length=500, description="The query/incident prompt message.")

# Dependency providers for services
def get_ai_service() -> AIService:
    return GeminiAIService()

def get_vector_service() -> VectorStoreService:
    return ChromaVectorStoreService()

def get_cache_service() -> CacheService:
    return RedisCacheService()

def get_mcp_service() -> MCPService:
    return HttpMCPService()

# API Routes definitions
@router.get("/status", tags=["System"])
async def get_system_status(
    db: Annotated[AsyncSession, Depends(get_db)],
    cache: Annotated[CacheService, Depends(get_cache_service)],
    _rate_limit: None = Depends(check_rate_limit),
    user: User = Depends(RoleChecker(["Administrator", "Emergency Responder", "Volunteer", "NGO", "Citizen"]))
) -> dict[str, str]:
    """Retrieves operational status of core systems. Open to all authenticated roles."""
    # Check cache status as an example
    cache_ok = "healthy"
    try:
        await cache.set("healthcheck", "ok", expire_seconds=10)
        val = await cache.get("healthcheck")
        if val != "ok":
            cache_ok = "degraded"
    except Exception:
        cache_ok = "offline"

    return {
        "status": "online",
        "database": "connected",
        "cache": cache_ok
    }

@router.post("/query-ai", tags=["AI"])
async def query_ai(
    request_data: PromptRequest,
    request: Request,
    ai_service: Annotated[AIService, Depends(get_ai_service)],
    vector_service: Annotated[VectorStoreService, Depends(get_vector_service)],
    _rate_limit: None = Depends(check_rate_limit),
    user: User = Depends(RoleChecker(["Administrator", "Emergency Responder", "Volunteer", "NGO"]))
) -> dict[str, str]:
    """Simulates query context addition and generation. Restricts direct prompts to responders/NGOs."""
    # Scan for prompt injection attacks
    scan_for_prompt_injection(request_data.prompt, request, user)

    # Mock Chroma query
    query_results = await vector_service.query(
        collection_name="humanity_docs",
        query_texts=[request_data.prompt],
        n_results=1
    )
    
    # Generate text
    ai_response = await ai_service.generate_text(
        prompt=f"Context: {query_results}. Prompt: {request_data.prompt}"
    )

    return {
        "response": ai_response,
        "source": "scaffold_mock"
    }

@router.get("/mcp/tools", tags=["MCP"])
async def list_mcp_tools(
    mcp_service: Annotated[MCPService, Depends(get_mcp_service)],
    server_url: str = "http://localhost:8000/mcp",
    _rate_limit: None = Depends(check_rate_limit),
    user: User = Depends(RoleChecker(["Administrator", "Emergency Responder"]))
) -> dict[str, list]:
    """Retrieve available MCP server tools list. Restricted to Admins and Responders."""
    tools = await mcp_service.list_tools(server_url)
    return {"tools": tools}

@router.post("/agents/orchestrate", tags=["Agents"])
async def orchestrate_agents(
    request_data: PromptRequest,
    request: Request,
    _rate_limit: None = Depends(check_rate_limit),
    user: User = Depends(RoleChecker(["Administrator", "Emergency Responder"]))
) -> dict:
    """Trigger the multi-agent incident response. Restricted to Admins and Responders."""
    # Scan for prompt injection attacks
    scan_for_prompt_injection(request_data.prompt, request, user)

    from app.agents.commander import CommanderAgent
    commander = CommanderAgent()
    result = await commander.orchestrate(request_data.prompt)
    return result
