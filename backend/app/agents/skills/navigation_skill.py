from typing import Any, Dict, Optional

class NavigationSkill:
    """Encapsulates safe pathfinding, route viability reviews, and detour solvers."""

    def evaluate_road_viability(self, road_report: Dict[str, Any]) -> bool:
        """Determines if a road is safe for emergency vehicle transport routes."""
        status = road_report.get("status", "Open")
        return status.lower() == "open"

    def resolve_alternate_path(self, road_report: Dict[str, Any]) -> Optional[str]:
        """Extracts suggesting detour routes when primary pathways are blocked."""
        if not self.evaluate_road_viability(road_report):
            return road_report.get("detour_suggested", "Take localized bypass route.")
        return None
