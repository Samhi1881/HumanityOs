from typing import Dict, List

class CommunicationSkill:
    """Encapsulates broadcast formatter templates, alert dispatch channels, and routing."""

    def format_alert_broadcast(self, template_name: str, parameters: Dict[str, str]) -> str:
        """Applies parameters to standard emergency template models to generate broadcast messages."""
        templates = {
            "evacuation": "CRITICAL ALERT: Evacuation recommended for {location} due to {hazard}. Seek shelter immediately.",
            "shelter_update": "NOTICE: Shelter '{shelter_name}' has updated space. Occupancy is currently at {occupancy}/{capacity}.",
            "missing_person": "MISSING UPDATE: {name} was located safe at safety center '{shelter_name}'."
        }
        
        template = templates.get(template_name, "NOTICE: {message}")
        try:
            return template.format(**parameters)
        except KeyError as e:
            # Fallback if key missing
            return f"NOTICE: Alert message parameterized template error. Missing field {str(e)}"

    def select_distribution_channels(self, alert_severity: str) -> List[str]:
        """Maps alert severity indices to broadcast output channels (SMS, Radio, email)."""
        if alert_severity.upper() == "HIGH":
            return ["SMS Broadcast", "Emergency Radio Band", "Public Dashboard Alert"]
        return ["Public Dashboard Alert", "Email Digest"]
