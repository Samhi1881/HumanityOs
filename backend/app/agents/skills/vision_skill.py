from typing import Any, Dict, List

class VisionSkill:
    """Encapsulates image intelligence, sensor feeds inspection, and physical compliance audits."""

    def detect_feed_obstructions(self, road_report: Dict[str, Any]) -> List[str]:
        """Inspects road telemetry reports for physical layout obstructions (mudslides, washouts)."""
        obstructions = []
        details = road_report.get("hazard_details")
        if details:
            if "mudslide" in details.lower() or "slide" in details.lower():
                obstructions.append("Debris slide detected")
            if "water" in details.lower() or "flood" in details.lower():
                obstructions.append("Surface water accumulation")
        
        status = road_report.get("status")
        if status == "Closed" and not obstructions:
            obstructions.append("Unspecified physical blockage")
            
        return obstructions

    def audit_physical_accessibility(self, shelter_details: Dict[str, Any]) -> bool:
        """Inspects shelter physical assets lists to verify standard ADA safety features."""
        shelters = shelter_details.get("shelters", [])
        if not shelters:
            return False
            
        # Verify that at least one active shelter has Wheelchair accessibility features
        for shelter in shelters:
            features = shelter.get("accessibility_features", [])
            if "Wheelchair Restrooms" in features or "ADA Ramp" in features:
                return True
        return False
