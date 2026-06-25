from abc import ABC, abstractmethod
from typing import Any
import httpx

class MCPService(ABC):
    """Abstract Base Class defining Model Context Protocol client interaction requirements."""

    @abstractmethod
    async def list_tools(self, server_url: str) -> list[dict[str, Any]]:
        """List all available tools from a specific MCP Server."""
        pass

    @abstractmethod
    async def call_tool(self, server_url: str, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Execute a tool on an MCP Server."""
        pass


class HttpMCPService(MCPService):
    """HTTP-based client implementation for contacting remote MCP Servers."""
    _client: httpx.AsyncClient | None = None

    def __init__(self) -> None:
        try:
            from app.core.config import settings
            self.server_urls = settings.MCP_SERVER_URLS
        except (ImportError, ModuleNotFoundError):
            self.server_urls = []
        
        if HttpMCPService._client is None or HttpMCPService._client.is_closed:
            HttpMCPService._client = httpx.AsyncClient(timeout=30.0)

    @property
    def client(self) -> httpx.AsyncClient:
        if HttpMCPService._client is None or HttpMCPService._client.is_closed:
            HttpMCPService._client = httpx.AsyncClient(timeout=30.0)
        return HttpMCPService._client

    async def list_tools(self, server_url: str) -> list[dict[str, Any]]:
        """Fetch available tools list from local map or fallback endpoint."""
        # Local tools list details
        local_tools = [
            {"name": "findHospital", "description": "Find hospitals and check beds capacity"},
            {"name": "findShelter", "description": "Search nearby safe zones and shelters"},
            {"name": "findVolunteer", "description": "Query volunteers by skill set"},
            {"name": "forecastWeather", "description": "Get weather reports and advisories"},
            {"name": "roadStatus", "description": "Check street and highway status reports"},
            {"name": "resourceInventory", "description": "Retrieve quantity levels of emergency inventories"},
            {"name": "dispatchResources", "description": "Logistics orders and truck dispatch"},
            {"name": "translateMessage", "description": "Translate texts into target languages"},
            {"name": "estimateDisasterDamage", "description": "Calculate disaster damage estimates"},
            {"name": "locateFamily", "description": "Lookup registered family units"},
            {"name": "searchMissingPerson", "description": "Search contact directories for missing persons"}
        ]
        return local_tools

    async def call_tool(self, server_url: str, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Execute a tool via local dispatch or HTTP POST if remote."""
        # 1. Check local tool registry map
        import app.api.mcp_server as local_mcp
        
        tools_map = {
            "findHospital": local_mcp.findHospital,
            "findShelter": local_mcp.findShelter,
            "findVolunteer": local_mcp.findVolunteer,
            "forecastWeather": local_mcp.forecastWeather,
            "roadStatus": local_mcp.roadStatus,
            "resourceInventory": local_mcp.resourceInventory,
            "dispatchResources": local_mcp.dispatchResources,
            "translateMessage": local_mcp.translateMessage,
            "estimateDisasterDamage": local_mcp.estimateDisasterDamage,
            "locateFamily": local_mcp.locateFamily,
            "searchMissingPerson": local_mcp.searchMissingPerson
        }

        if tool_name in tools_map:
            try:
                func = tools_map[tool_name]
                res = await func(**arguments)
                if hasattr(res, "model_dump"):
                    return res.model_dump()
                return {"result": res}
            except Exception as e:
                return {"status": "error", "message": f"Local tool execution failed: {str(e)}"}

        # 2. Remote HTTP POST Fallback
        try:
            response = await self.client.post(
                f"{server_url}/tools/call",
                json={"name": tool_name, "arguments": arguments}
            )
            if response.status_code == 200:
                return response.json()
        except Exception:
            pass
        return {"status": "error", "message": f"Failed to call MCP tool '{tool_name}'."}

    async def close(self) -> None:
        """Closes internal HTTP client connection pool."""
        if HttpMCPService._client is not None and not HttpMCPService._client.is_closed:
            await HttpMCPService._client.aclose()
            HttpMCPService._client = None


