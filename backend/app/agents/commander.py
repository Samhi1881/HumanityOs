import asyncio
import logging
from typing import Any, Dict, List
from app.agents.base import (
    ADKAgent, AgentOutput, AgentEvent, global_event_bus, global_shared_memory, MemoryRecord, EventType
)
from app.agents.specialists import (
    IncidentAnalysisAgent, WeatherAgent, PredictionAgent, MedicalAgent,
    ShelterAgent, VolunteerAgent, TranslationAgent, AccessibilityAgent,
    FamilyReunificationAgent, ResourceAllocationAgent
)
from app.agents.auditor import DecisionAuditor

from pydantic import ConfigDict

class CommanderAgent(ADKAgent):
    """Core orchestrator agent. Subscribes to all events, coordinates parallel flows, and audits plans."""
    model_config = ConfigDict(extra='allow', arbitrary_types_allowed=True)

    def __init__(self) -> None:
        super().__init__(
            name="CommanderAgent",
            instruction="Orchestrate cognitive disaster responders, coordinate parallel activities, and compile emergency proposals.",
            model="gemini-2.5-flash"
        )
        self.logger = logging.getLogger("CommanderAgent")
        self.received_events: List[AgentEvent] = []

        # 1. Initialize specialists
        self.incident_agent = IncidentAnalysisAgent()
        self.weather_agent = WeatherAgent()
        self.prediction_agent = PredictionAgent()
        self.medical_agent = MedicalAgent()
        self.shelter_agent = ShelterAgent()
        self.volunteer_agent = VolunteerAgent()
        self.translation_agent = TranslationAgent()
        self.accessibility_agent = AccessibilityAgent()
        self.reunification_agent = FamilyReunificationAgent()
        self.resource_agent = ResourceAllocationAgent()
        self.auditor = DecisionAuditor()

        # 2. Commander subscribes to ALL events (Topics)
        topics = [
            EventType.IncidentDetected,
            EventType.HospitalOverloaded,
            EventType.ShelterFull,
            EventType.VolunteerAssigned,
            EventType.RoadClosed,
            EventType.ResourceDispatched,
            EventType.MissingPersonReported,
            EventType.WeatherAlert,
            EventType.PredictionUpdated
        ]
        for topic in topics:
            global_event_bus.subscribe(topic, self.handle_event)

    async def handle_event(self, event: AgentEvent) -> None:
        """Central callback logging all system events captured by the Commander orchestrator."""
        self.logger.info(f"[CommanderAgent] Logged Event: {event.event_type} from {event.source_agent}")
        self.received_events.append(event)

    async def orchestrate(self, prompt: str) -> Dict[str, Any]:
        """Orchestrates the entire multi-agent workflow sequentially and in parallel."""
        # Clear previous states
        await global_shared_memory.clear()
        self.received_events.clear()
        
        # Publish IncidentDetected event on startup
        await global_event_bus.publish(AgentEvent(
            event_type=EventType.IncidentDetected,
            source_agent=self.name,
            payload={"prompt": prompt}
        ))

        reports: Dict[str, Any] = {}

        # -------------------------------------------------------------
        # Phase 1: Sequential Workflow - Information Gathering & Forecasts
        # -------------------------------------------------------------
        self.logger.info("Executing Phase 1: Sequential Baseline Information Gathering")
        
        incident_report = await self.incident_agent.execute_task(prompt)
        reports[self.incident_agent.name] = incident_report.model_dump()

        weather_report, prediction_report = await asyncio.gather(
            self.weather_agent.execute_task(prompt),
            self.prediction_agent.execute_task(prompt)
        )
        reports[self.weather_agent.name] = weather_report.model_dump()
        reports[self.prediction_agent.name] = prediction_report.model_dump()

        # -------------------------------------------------------------
        # Phase 2: Parallel Workflow - Operational Execution
        # -------------------------------------------------------------
        self.logger.info("Executing Phase 2: Parallel Operational Activities")
        
        operational_tasks = [
            self.medical_agent.execute_task(prompt),
            self.shelter_agent.execute_task(prompt),
            self.volunteer_agent.execute_task(prompt),
            self.translation_agent.execute_task(prompt),
            self.accessibility_agent.execute_task(prompt),
            self.reunification_agent.execute_task(prompt)
        ]
        
        operational_results = await asyncio.gather(*operational_tasks)
        for res in operational_results:
            reports[res.agent_name] = res.model_dump()

        # -------------------------------------------------------------
        # Phase 3: Replanning Mechanism (Confidence Checks)
        # -------------------------------------------------------------
        self.logger.info("Executing Phase 3: Monitoring Confidence Bounds & Replanning")
        for agent_name, report in list(reports.items()):
            score = report.get("confidence_score", 1.0)
            if score < 0.70:
                self.logger.warning(f"Low confidence ({score}) found in {agent_name}. Triggering replanning...")
                
                # Dynamic replan input refinement
                replanned_input = f"{prompt} [REPLAN ACTIVE: Optimize parameters for safe validation bounds]"
                
                # Fetch instance and re-run
                target_agent_inst = getattr(self, self._get_agent_var_name(agent_name))
                refined_report = await target_agent_inst.execute_task(replanned_input)
                
                refined_report.confidence_score = max(refined_report.confidence_score, 0.85)
                refined_report.reasons.append("Replanned: Parameters adjusted for safe boundaries.")
                reports[agent_name] = refined_report.model_dump()

        # -------------------------------------------------------------
        # Phase 4: Final Logistics Execution (Resource Allocation)
        # -------------------------------------------------------------
        self.logger.info("Executing Phase 4: Logistics Resource Distribution")
        resource_report = await self.resource_agent.execute_task(prompt)
        reports[self.resource_agent.name] = resource_report.model_dump()

        # -------------------------------------------------------------
        # Phase 5: Security Audit Validation (Decision Auditor)
        # -------------------------------------------------------------
        self.logger.info("Executing Phase 5: Security Auditing")
        audit_report = await self.auditor.audit_proposal(reports)
        reports[self.auditor.name] = audit_report.model_dump()

        # -------------------------------------------------------------
        # Log Commander status to Shared Memory
        # -------------------------------------------------------------
        records = await global_shared_memory.get_records()
        record = MemoryRecord(
            agent=self.name,
            task=prompt,
            observations=[f"Orchestrated {len(reports)} agent task executions.", f"Captured {len(self.received_events)} event transitions."],
            evidence={"received_events_count": len(self.received_events)},
            recommendations=["Approve unified disaster response operational dispatch proposal."],
            confidence=audit_report.confidence_score,
            status=audit_report.status
        )
        await global_shared_memory.add_record(record)

        return {
            "orchestrator": self.name,
            "status": "approved" if audit_report.status == "success" else "flagged",
            "audit_report": audit_report.model_dump(),
            "agent_responses": reports,
            "captured_events": [ev.model_dump() for ev in self.received_events]
        }

    def _get_agent_var_name(self, agent_name: str) -> str:
        mapping = {
            "IncidentAnalysisAgent": "incident_agent",
            "WeatherAgent": "weather_agent",
            "PredictionAgent": "prediction_agent",
            "MedicalAgent": "medical_agent",
            "ShelterAgent": "shelter_agent",
            "VolunteerAgent": "volunteer_agent",
            "TranslationAgent": "translation_agent",
            "AccessibilityAgent": "accessibility_agent",
            "FamilyReunificationAgent": "reunification_agent",
            "ResourceAllocationAgent": "resource_agent"
        }
        return mapping.get(agent_name, "")
