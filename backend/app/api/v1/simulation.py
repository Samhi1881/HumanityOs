from fastapi import APIRouter, Depends
from app.core.security import User, RoleChecker, check_rate_limit
from pydantic import BaseModel
from typing import Any, Dict, List, Optional

router = APIRouter()

class SimulationStep(BaseModel):
    step_number: int
    title: str
    description: str
    event_type: Optional[str] = None
    source_agent: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None
    map_updates: Optional[Dict[str, Any]] = None
    capacity_updates: Optional[Dict[str, Any]] = None
    inventory_updates: Optional[Dict[str, Any]] = None
    orchestrate_prompt: Optional[str] = None

class Scenario(BaseModel):
    id: str
    name: str
    description: str
    center_coords: List[float]
    steps: List[SimulationStep]

SCENARIOS: Dict[str, Scenario] = {
    "cyclone": Scenario(
        id="cyclone",
        name="Cyclone Landfall",
        description="High-velocity winds and coastal storm surge threatening Bay Area shores.",
        center_coords=[37.7749, -122.4194],
        steps=[
            SimulationStep(
                step_number=1,
                title="Weather Warning",
                description="Cyclone Category 1 landfall predicted within 6 hours. High wind advisories active.",
                event_type="WeatherAlert",
                source_agent="WeatherAgent",
                payload={"hazard_index": 8.5, "wind_speed": 75.0},
                map_updates={"heatmap": {"center": [37.7749, -122.4194], "radius": 2500, "color": "#ef4444"}}
            ),
            SimulationStep(
                step_number=2,
                title="Road Blocks",
                description="Coastal storm surge and fallen power lines close Route 101-North.",
                event_type="RoadClosed",
                source_agent="IncidentAnalysisAgent",
                payload={"road_name": "Route 101-North", "detour": "Take Highway 9"},
                map_updates={"markers": [{"type": "hazard", "position": [37.785, -122.410], "label": "Route 101 Blocked"}]}
            ),
            SimulationStep(
                step_number=3,
                title="Shelter Evacuation Influx",
                description="Civic Center Emergency Shelter approaches critical capacity boundaries.",
                event_type="ShelterFull",
                source_agent="ShelterAgent",
                payload={"shelter_name": "Civic Center Hall", "occupancy": 492},
                capacity_updates={"shelters": [{"name": "Civic Center Hall", "occupancy": 492, "capacity": 500}]}
            ),
            SimulationStep(
                step_number=4,
                title="Commander Replanning & Audit",
                description="Commander launches multi-agent replanning. Decision Auditor verifies safety guards.",
                orchestrate_prompt="High precipitation cyclone Category 1 near Sector Alpha, Route 101 closed by downed lines, Civic Center shelter at 98% occupancy, requesting immediate resource mobilization."
            )
        ]
    ),
    "flood": Scenario(
        id="flood",
        name="Atmospheric River Flood",
        description="Severe precipitation leading to watershed flooding and localized mudslides.",
        center_coords=[37.8044, -122.2711],
        steps=[
            SimulationStep(
                step_number=1,
                title="Precipitation Spike",
                description="Heavy downpour triggers flood warnings across watershed zones.",
                event_type="WeatherAlert",
                source_agent="WeatherAgent",
                payload={"hazard_index": 7.0, "wind_speed": 22.0},
                map_updates={"heatmap": {"center": [37.8044, -122.2711], "radius": 2000, "color": "#3b82f6"}}
            ),
            SimulationStep(
                step_number=2,
                title="Mudslide Detours",
                description="Saturated soil results in mudslide, blocking Highway 24 lanes.",
                event_type="RoadClosed",
                source_agent="IncidentAnalysisAgent",
                payload={"road_name": "Highway 24", "detour": "Detour via Tunnel Rd"},
                map_updates={"markers": [{"type": "hazard", "position": [37.810, -122.250], "label": "Highway 24 Mudslide"}]}
            ),
            SimulationStep(
                step_number=3,
                title="Missing Person Alert",
                description="Family registry reports missing hikers in Sector Beta hills.",
                event_type="MissingPersonReported",
                source_agent="FamilyReunificationAgent",
                payload={"name": "Jane Doe"},
                map_updates={"markers": [{"type": "search", "position": [37.795, -122.265], "label": "Search Zone: Hiker"}]}
            ),
            SimulationStep(
                step_number=4,
                title="Logistics Orchestration",
                description="Synthesizing supply corridors and dispatching SAR search operations.",
                orchestrate_prompt="Severe flash flood in Oakland Hills, Highway 24 closed by mudslide, search registry reporting missing persons in Sector Beta, water supply trucks dispatch required."
            )
        ]
    ),
    "earthquake": Scenario(
        id="earthquake",
        name="Urban Seismic Event",
        description="Magnitude 6.8 shock causing structural hazards and high casualty counts.",
        center_coords=[37.3382, -121.8863],
        steps=[
            SimulationStep(
                step_number=1,
                title="Seismic Ingestion",
                description="Magnitude 6.8 earthquake registered in urban Silicon Valley core.",
                event_type="IncidentDetected",
                source_agent="IncidentAnalysisAgent",
                payload={"severity": "CRITICAL", "magnitude": 6.8},
                map_updates={"heatmap": {"center": [37.3382, -121.8863], "radius": 3000, "color": "#f97316"}}
            ),
            SimulationStep(
                step_number=2,
                title="Hospital ICU Strain",
                description="Trauma patients spike. General Memorial Hospital ICU beds drop below safe buffer.",
                event_type="HospitalOverloaded",
                source_agent="MedicalAgent",
                payload={"available_beds": 1},
                capacity_updates={"hospitals": [{"name": "General Memorial Hospital", "available_beds": 1, "capacity": 20}]}
            ),
            SimulationStep(
                step_number=3,
                title="Rescue Triage Dispatch",
                description="Emergency volunteer squad V-105 assigned to collapse hot spots.",
                event_type="VolunteerAssigned",
                source_agent="VolunteerAgent",
                payload={"assigned_count": 15, "skill": "First Aid"},
                map_updates={"markers": [{"type": "volunteer", "position": [37.345, -121.895], "label": "Squad V-105 Site"}]}
            ),
            SimulationStep(
                step_number=4,
                title="Seismic Shock Audit",
                description="Commander reroutes ambulances and auditor checks physical shelter ADA accessibility.",
                orchestrate_prompt="Magnitude 6.8 earthquake in San Jose corridor, structural collapse hazards, General Memorial Hospital beds exhausted, safety auditor verifying ADA accessibility guidelines."
            )
        ]
    ),
    "wildfire": Scenario(
        id="wildfire",
        name="Forest Wildfire Outbreak",
        description="Fast-spreading canopy fire encroaching on suburban hillsides.",
        center_coords=[37.8044, -122.2711],
        steps=[
            SimulationStep(
                step_number=1,
                title="Red Flag Warning",
                description="Extreme heat, low humidity, and high winds activate wildfire warning.",
                event_type="WeatherAlert",
                source_agent="WeatherAgent",
                payload={"hazard_index": 7.8, "wind_speed": 35.0},
                map_updates={"heatmap": {"center": [37.8044, -122.2711], "radius": 2200, "color": "#f43f5e"}}
            ),
            SimulationStep(
                step_number=2,
                title="Corridor Evacuation",
                description="Active wildfire advances. Grizzly Peak Boulevard closed due to heavy smoke.",
                event_type="RoadClosed",
                source_agent="IncidentAnalysisAgent",
                payload={"road_name": "Grizzly Peak Blvd", "detour": "Evacuate Southward"},
                map_updates={"markers": [{"type": "hazard", "position": [37.820, -122.240], "label": "Grizzly Peak Fire Front"}]}
            ),
            SimulationStep(
                step_number=3,
                title="Buffer Lines",
                description="Volunteer groups deployed to establish containment fire lines.",
                event_type="VolunteerAssigned",
                source_agent="VolunteerAgent",
                payload={"assigned_count": 25, "skill": "Fire Safety"},
                map_updates={"markers": [{"type": "volunteer", "position": [37.812, -122.260], "label": "Volunteer Fire Line"}]}
            ),
            SimulationStep(
                step_number=4,
                title="Containment Replanning & Audit",
                description="Commander launches retardant dispatch. Auditor verifies fire line distance bounds.",
                orchestrate_prompt="Oakland Hills corridor wildfire driven by high winds, Grizzly Peak road closed, volunteer fire lines active, requesting emergency retardant supply dispatch."
            )
        ]
    ),
    "heatwave": Scenario(
        id="heatwave",
        name="Extreme Heat Dome",
        description="Sustained high temperatures creating power grid strain and hydration shortages.",
        center_coords=[37.7749, -122.4194],
        steps=[
            SimulationStep(
                step_number=1,
                title="Heat Alert",
                description="Ridge high pressure dome pushes temperatures to record-breaking 105°F.",
                event_type="WeatherAlert",
                source_agent="WeatherAgent",
                payload={"hazard_index": 6.8, "temperature_f": 105.0},
                map_updates={"heatmap": {"center": [37.7749, -122.4194], "radius": 2800, "color": "#f97316"}}
            ),
            SimulationStep(
                step_number=2,
                title="Water depletion",
                description="Hydration reserves drop rapidly across cooling zones.",
                event_type="ResourceDispatched",
                source_agent="ResourceAllocationAgent",
                payload={"delivery_id": "DEL-101", "vehicle": "Truck"},
                inventory_updates={"resources": [{"item_name": "Water Bottles", "quantity_available": 150}]}
            ),
            SimulationStep(
                step_number=3,
                title="Dehydration Triage Influx",
                description="General heat stress incidents fill Valley Health Center emergency space.",
                event_type="HospitalOverloaded",
                source_agent="MedicalAgent",
                payload={"available_beds": 0},
                capacity_updates={"hospitals": [{"name": "Valley Health Center", "available_beds": 0, "capacity": 10}]}
            ),
            SimulationStep(
                step_number=4,
                title="Cooling Dome Replanning",
                description="Commander audits emergency grid resources and launches hydration convoys.",
                orchestrate_prompt="Record heatwave peaking at 105F, water bottle inventory critical, Valley Health Center beds at zero capacity, safety auditor auditing cooling center ADA access."
            )
        ]
    )
}

@router.get("/scenarios", tags=["Simulation"])
async def list_scenarios(
    _rate_limit: None = Depends(check_rate_limit),
    user: User = Depends(RoleChecker(["Administrator", "Emergency Responder", "Volunteer"]))
) -> Dict[str, Scenario]:
    """Retrieves all pre-configured simulation scenarios and steps. Restricted to Admin/Responder/Volunteer."""
    return SCENARIOS

@router.get("/scenarios/{scenario_id}", tags=["Simulation"])
async def get_scenario(
    scenario_id: str,
    _rate_limit: None = Depends(check_rate_limit),
    user: User = Depends(RoleChecker(["Administrator", "Emergency Responder", "Volunteer"]))
) -> Scenario:
    """Retrieves details of a specific simulation scenario. Restricted to Admin/Responder/Volunteer."""
    from fastapi import HTTPException
    scenario = SCENARIOS.get(scenario_id.lower())
    if not scenario:
        raise HTTPException(status_code=404, detail=f"Scenario '{scenario_id}' not found.")
    return scenario
