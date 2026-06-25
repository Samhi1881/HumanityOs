from typing import Any, Dict, List
from app.agents.base import ADKAgent, AgentOutput, AgentEvent, global_event_bus

from pydantic import ConfigDict

class DecisionAuditor(ADKAgent):
    """The security validator. Evaluates proposed plans and checks guardrails."""
    model_config = ConfigDict(extra='allow', arbitrary_types_allowed=True)

    def __init__(self) -> None:
        super().__init__(
            name="DecisionAuditor",
            instruction="Audit final aggregated proposals to verify safety, resource limits, and confidence bounds.",
            model="gemini-2.5-flash"
        )

    async def audit_proposal(self, proposal: Dict[str, Any]) -> AgentOutput:
        """Audits the compiled plan for resource safety, accessibility, and confidence."""
        await global_event_bus.publish(AgentEvent(
            event_type="audit_request",
            source_agent=self.name,
            payload={"proposal": proposal}
        ))

        warnings: List[str] = []
        violations: List[str] = []

        # 1. Audit Agent Confidence Scores
        for agent_name, agent_data in proposal.items():
            if isinstance(agent_data, dict):
                score = agent_data.get("confidence_score", 1.0)
                if score < 0.60:
                    violations.append(f"Agent {agent_name} reports critically low confidence score ({score:.2f}).")
                elif score < 0.75:
                    warnings.append(f"Agent {agent_name} reports marginal confidence score ({score:.2f}).")

        # 2. Audit Shelter Capacity Bounds (Resource constraint checks)
        shelter_data = proposal.get("ShelterAgent", {}).get("data", {})
        shelters = shelter_data.get("shelters", [])
        for shelter in shelters:
            capacity = shelter.get("capacity", 0)
            occupancy = shelter.get("occupancy", 0)
            if occupancy > capacity:
                violations.append(f"Shelter {shelter.get('name')} exceeds maximum capacity bounds ({occupancy}/{capacity}).")

        # 3. Audit Accessibility Compliance
        accessibility_data = proposal.get("AccessibilityAgent", {}).get("data", {})
        if not accessibility_data.get("wheelchair_access_configured", True):
            violations.append("Accessibility standard violation: Safe zone lacks wheelchair layout support.")

        # Determine overall safety status
        status = "success"
        if violations:
            status = "failure"
        elif warnings:
            status = "warning"

        audit_results = {
            "is_safe": len(violations) == 0,
            "violations": violations,
            "warnings": warnings,
            "audited_count": len(proposal)
        }

        output = AgentOutput(
            agent_name=self.name,
            status=status,
            confidence_score=0.99 if status == "success" else 0.80,
            data=audit_results,
            reasons=violations + warnings if (violations or warnings) else ["Proposal satisfies all safety metrics and resource constraints."]
        )

        # Publish validation completed event
        await global_event_bus.publish(AgentEvent(
            event_type="task_completed",
            source_agent=self.name,
            payload={"audit_report": output.model_dump()}
        ))

        return output
