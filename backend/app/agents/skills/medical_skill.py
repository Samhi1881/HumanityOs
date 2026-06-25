from typing import Any, Dict, List

class MedicalSkill:
    """Encapsulates emergency triage prioritization and hospital resource compatibility lookups."""

    def prioritize_triage_demand(self, incident_severity: str) -> int:
        """Calculates initial triage patient count projections based on incident severity index."""
        if incident_severity.upper() == "HIGH":
            return 120
        elif incident_severity.upper() == "MEDIUM":
            return 30
        return 5

    def filter_compatible_facilities(self, hospital_list: Dict[str, Any], specialty: str) -> List[Dict[str, Any]]:
        """Filters hospital list to return only facilities matching specific medical specialties."""
        matching = []
        hospitals = hospital_list.get("hospitals", [])
        for hospital in hospitals:
            specialties = hospital.get("specialties", [])
            if any(specialty.lower() in spec.lower() for spec in specialties):
                matching.append(hospital)
        return matching
