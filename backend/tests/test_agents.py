import pytest
from app.agents.commander import CommanderAgent
from app.agents.base import global_shared_memory, global_event_bus, AgentEvent, EventType, MemoryRecord

@pytest.mark.asyncio
async def test_agent_orchestration_shared_memory_records() -> None:
    """Verifies that all agents write correctly formatted MemoryRecords to shared memory."""
    commander = CommanderAgent()
    prompt = "An emergency flood disaster occurred near Sector Alpha"
    
    result = await commander.orchestrate(prompt)
    
    # 1. Assert structure of result
    assert result["orchestrator"] == "CommanderAgent"
    assert result["status"] == "approved"
    
    # 2. Get records from shared memory
    records = await global_shared_memory.get_records()
    assert len(records) > 0
    
    # Check that Commander's own record exists
    commander_records = await global_shared_memory.get_records(agent="CommanderAgent")
    assert len(commander_records) == 1
    
    # Check that IncidentAnalysisAgent's record exists
    incident_records = await global_shared_memory.get_records(agent="IncidentAnalysisAgent")
    assert len(incident_records) > 0
    
    # 3. Assert strict memory schema layout on a record
    test_record = incident_records[0]
    assert isinstance(test_record, MemoryRecord)
    assert test_record.agent == "IncidentAnalysisAgent"
    assert test_record.timestamp is not None
    assert "flood" in test_record.task or "emergency" in test_record.task.lower()
    assert len(test_record.observations) > 0
    assert isinstance(test_record.evidence, dict)
    assert len(test_record.recommendations) > 0
    assert test_record.confidence > 0.0
    assert test_record.status in ["success", "warning", "failure"]

@pytest.mark.asyncio
async def test_event_bus_subscription_isolation() -> None:
    """Verifies that the Commander receives all events, while specialists only receive relevant ones."""
    commander = CommanderAgent()
    prompt = "A high-wind weather threat detected near the shoreline"
    
    # Clear previous received events
    commander.received_events.clear()
    commander.weather_agent.received_events.clear()
    commander.medical_agent.received_events.clear()
    
    await commander.orchestrate(prompt)
    
    # 1. Commander Agent should have received multiple events (IncidentDetected, WeatherAlert, PredictionUpdated, etc.)
    assert len(commander.received_events) >= 3
    assert any(e.event_type == EventType.IncidentDetected for e in commander.received_events)
    assert any(e.event_type == EventType.WeatherAlert for e in commander.received_events)
    assert any(e.event_type == EventType.PredictionUpdated for e in commander.received_events)
    
    # 2. WeatherAgent should have received IncidentDetected and WeatherAlert events
    assert len(commander.weather_agent.received_events) >= 2
    assert any(e.event_type == EventType.WeatherAlert for e in commander.weather_agent.received_events)
    
    # 3. MedicalAgent should have received IncidentDetected, but NOT WeatherAlert (since it is not in its subscription list!)
    assert any(e.event_type == EventType.IncidentDetected for e in commander.medical_agent.received_events)
    assert not any(e.event_type == EventType.WeatherAlert for e in commander.medical_agent.received_events)

@pytest.mark.asyncio
async def test_adk_workflow_execution() -> None:
    """Verifies that the main ADK workflow runs successfully inside the context."""
    from app.agents.workflow import humanityos_workflow
    from typing import Any
    import asyncio
    
    class MockContext:
        async def run_node(self, node: Any, node_input: Any = None, *args: Any, **kwargs: Any) -> Any:
            func = getattr(node, "_func", node)
            if callable(func):
                if asyncio.iscoroutinefunction(func):
                    return await func(**node_input) if isinstance(node_input, dict) else await func(node_input)
                return func(**node_input) if isinstance(node_input, dict) else func(node_input)
            return node

    ctx = MockContext()
    prompt = "Simulate an earthquake structural assessment drill"
    
    # Run the workflow
    func = getattr(humanityos_workflow, "_func", humanityos_workflow)
    result = await func(ctx, prompt)

    
    # Verify outputs
    assert result is not None
    assert result["orchestrator"] == "CommanderAgent"
    assert result["status"] == "approved"
    assert "IncidentAnalysisAgent" in result["agent_responses"]


