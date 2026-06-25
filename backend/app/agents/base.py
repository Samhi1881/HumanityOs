import asyncio
from pydantic import BaseModel, Field
from typing import Any, Callable, Dict, List, Optional
import logging

# ==========================================
# Google ADK Primitives Import Fallback
# ==========================================
try:
    from google.adk import Agent as ADKAgent
    from google.adk import Context as ADKContext
    from google.adk.workflow import node as adk_node
    HAS_ADK = True
except ImportError:
    # Robust mock interfaces to prevent dependency errors during local scans / syntax checks
    HAS_ADK = False
    
    class ADKAgent:
        def __init__(self, name: str, instruction: str, model: str = "gemini-2.5-flash", **kwargs: Any) -> None:
            self.name = name
            self.instruction = instruction
            self.model = model
            
    class ADKContext:
        async def run_node(self, node: Any, node_input: Any = None, *args: Any, **kwargs: Any) -> Any:
            func = getattr(node, "_func", node)
            if callable(func):
                import inspect
                sig = inspect.signature(func)

                func_kwargs = {}
                
                # Bind parameters from node_input if it is a dictionary
                if isinstance(node_input, dict):
                    for param_name in sig.parameters:
                        if param_name in node_input:
                            func_kwargs[param_name] = node_input[param_name]
                        elif param_name in ("ctx", "context"):
                            func_kwargs[param_name] = self
                
                # Fallback to positional assignment if binding did not populate kwargs
                if not func_kwargs:
                    params = list(sig.parameters.keys())
                    if params:
                        first_param = params[0]
                        if first_param in ("ctx", "context"):
                            func_kwargs[first_param] = self
                            if len(params) > 1:
                                func_kwargs[params[1]] = node_input
                        else:
                            func_kwargs[first_param] = node_input

                if asyncio.iscoroutinefunction(node):
                    return await node(**func_kwargs)
                return node(**func_kwargs)
            return node


    def adk_node(func: Any) -> Any:
        return func

# ==========================================
# Structured Agent Communication & Models
# ==========================================
from datetime import datetime

class MemoryRecord(BaseModel):
    """Memory log schema for shared information layer."""
    agent: str = Field(..., description="Name of the executing agent")
    timestamp: datetime = Field(default_factory=lambda: datetime.now())
    task: str = Field(..., description="Details of the active task description")
    observations: List[str] = Field(default_factory=list, description="Extracted observation strings")
    evidence: Dict[str, Any] = Field(default_factory=dict, description="Raw supportive evidence records")
    recommendations: List[str] = Field(default_factory=list, description="Proposed actions or outputs")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Agent confidence score")
    status: str = Field(..., description="Outcome status (success, warning, failure)")

class AgentOutput(BaseModel):
    """Standardized output schema for all HumanityOS agents."""
    agent_name: str
    status: str = "success"  # success, failure, warning
    data: Dict[str, Any] = Field(default_factory=dict)
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    reasons: List[str] = Field(default_factory=list)

# Specific Event Types
class EventType:
    IncidentDetected = "IncidentDetected"
    HospitalOverloaded = "HospitalOverloaded"
    ShelterFull = "ShelterFull"
    VolunteerAssigned = "VolunteerAssigned"
    RoadClosed = "RoadClosed"
    ResourceDispatched = "ResourceDispatched"
    MissingPersonReported = "MissingPersonReported"
    WeatherAlert = "WeatherAlert"
    PredictionUpdated = "PredictionUpdated"

class AgentEvent(BaseModel):
    """Payload representing event broadcast across agents."""
    event_type: str  # IncidentDetected, HospitalOverloaded, etc.
    source_agent: str
    target_agent: Optional[str] = None
    payload: Dict[str, Any] = Field(default_factory=dict)

# ==========================================
# Event Bus (Event-Driven Communication)
# ==========================================

class EventBus:
    """Central event broker facilitating asynchronous, event-driven agent interaction."""
    def __init__(self) -> None:
        self.subscribers: Dict[str, List[Callable[[AgentEvent], Any]]] = {}
        self.logger = logging.getLogger("EventBus")

    def subscribe(self, event_type: str, callback: Callable[[AgentEvent], Any]) -> None:
        """Register a handler callback for a specific event type."""
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(callback)

    async def publish(self, event: AgentEvent) -> None:
        """Asynchronously publish an event to all registered subscribers."""
        self.logger.info(f"Event published: {event.event_type} from {event.source_agent}")
        if event.event_type in self.subscribers:
            tasks = []
            for callback in self.subscribers[event.event_type]:
                if asyncio.iscoroutinefunction(callback):
                    tasks.append(callback(event))
                else:
                    callback(event)
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)

# Global Event Bus instance
global_event_bus = EventBus()

# ==========================================
# Shared Memory State
# ==========================================

class SharedMemoryState:
    """Thread-safe global state container accessible by all agents (Shared Memory)."""
    def __init__(self) -> None:
        self._records: List[MemoryRecord] = []
        self._lock = asyncio.Lock()

    async def add_record(self, record: MemoryRecord) -> None:
        """Append a new memory record into the shared layers."""
        async with self._lock:
            self._records.append(record)

    async def get_records(self, agent: Optional[str] = None) -> List[MemoryRecord]:
        """Retrieve all memory records, optionally filtered by agent name."""
        async with self._lock:
            if agent:
                return [r for r in self._records if r.agent == agent]
            return list(self._records)

    async def get_latest_record(self, agent: str) -> Optional[MemoryRecord]:
        """Fetch the most recent memory record logged by a specific agent."""
        async with self._lock:
            filtered = [r for r in self._records if r.agent == agent]
            if filtered:
                # Sort by timestamp ascending, return last
                filtered.sort(key=lambda x: x.timestamp)
                return filtered[-1]
            return None

    async def clear(self) -> None:
        """Clear all memory records."""
        async with self._lock:
            self._records.clear()

# Global Shared Memory instance
global_shared_memory = SharedMemoryState()
