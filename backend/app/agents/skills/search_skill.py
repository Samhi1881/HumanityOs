from typing import Any, Dict, List

class SearchSkill:
    """Encapsulates safe-list directory reconciliations, missing persons verification, and registry checkups."""

    def reconcile_safe_status(self, missing_result: Dict[str, Any], family_status: Dict[str, Any]) -> Dict[str, Any]:
        """Synthesizes reports from missing registries and family safe structures to return consolidated statuses."""
        name = missing_result.get("name_queried", "Unknown")
        found = missing_result.get("found", False)
        
        shelter_id = missing_result.get("safe_shelter_id")
        
        # Check if the name exists inside the family members safe registry
        family_members = family_status.get("members_registered", [])
        family_safe_zones = family_status.get("safe_locations", {})
        
        member_location = family_safe_zones.get(name)
        if member_location:
            found = True
            
        status = "Located Safe" if found else "Active Search"
        location_resolved = member_location or (f"Shelter {shelter_id}" if shelter_id else "Unknown")

        return {
            "name": name,
            "found": found,
            "status": status,
            "location": location_resolved,
            "family_id": family_status.get("family_id")
        }

    def fuzzy_match_person(self, name_query: str, active_roster: List[str]) -> List[str]:
        """Fuzzy matches sub-strings of names in active shelter list directories."""
        matches = []
        for name in active_roster:
            if name_query.lower() in name.lower():
                matches.append(name)
        return matches
