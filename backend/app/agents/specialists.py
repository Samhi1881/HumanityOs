import random
import logging
from typing import Any, Dict, List
from app.agents.base import (
    ADKAgent, AgentOutput, AgentEvent, global_event_bus, global_shared_memory, MemoryRecord, EventType
)
from app.services.mcp import HttpMCPService

# Import reusable skills
from app.agents.skills import (
    VisionSkill, MedicalSkill, NavigationSkill, WeatherSkill,
    TranslationSkill, CommunicationSkill, ResourceSkill, SearchSkill
)

from pydantic import ConfigDict

class BaseSpecialistAgent(ADKAgent):
    """Base class for specialist agents sharing common MCP tools, event loops, and Memory logging."""
    model_config = ConfigDict(extra='allow', arbitrary_types_allowed=True)
    
    # Topics that this agent listens to (overridden by children)
    subscribed_topics: List[str] = []

    def __init__(self, name: str, instruction: str) -> None:
        super().__init__(
            name=name,
            instruction=instruction,
            model="gemini-2.5-flash"
        )
        self.mcp_client = HttpMCPService()
        self.logger = logging.getLogger(name)
        self.received_events: List[AgentEvent] = []
        
        # Subscribe to relevant topics on start
        for topic in self.subscribed_topics:
            global_event_bus.subscribe(topic, self.handle_event)

    async def handle_event(self, event: AgentEvent) -> None:
        """Asynchronous event handler called by the central Event Bus."""
        self.logger.info(f"[{self.name}] Event received: {event.event_type} from {event.source_agent}")
        self.received_events.append(event)

    async def execute_task(self, task_input: str) -> AgentOutput:
        """Standard wrapper simulating agent thinking, memory logging, and event publication."""
        # Run specialized logic
        output = await self._run_logic(task_input)

        # -------------------------------------------------------------
        # Log to Shared Memory using strict MemoryRecord schema
        # -------------------------------------------------------------
        obs = output.reasons.copy()
        if "warning" in output.status:
            obs.append("Execution completed with safety warnings.")
            
        record = MemoryRecord(
            agent=self.name,
            task=task_input,
            observations=obs,
            evidence=output.data,
            recommendations=[f"Dispatching report package for {self.name}"],
            confidence=output.confidence_score,
            status=output.status
        )
        await global_shared_memory.add_record(record)

        return output

    async def _run_logic(self, task_input: str) -> AgentOutput:
        raise NotImplementedError("Specialist agents must override _run_logic.")


class IncidentAnalysisAgent(BaseSpecialistAgent):
    subscribed_topics: List[str] = [EventType.IncidentDetected, EventType.RoadClosed]

    def __init__(self) -> None:
        super().__init__(
            name="IncidentAnalysisAgent",
            instruction="Parse incoming telemetry streams to categorize severity and locate coordinates."
        )
        self.vision = VisionSkill()
        self.nav = NavigationSkill()

    async def _run_logic(self, task_input: str) -> AgentOutput:
        road_res = await self.mcp_client.call_tool(
            server_url="http://localhost:8080/mcp",
            tool_name="roadStatus",
            arguments={"road_name": "Route 101-North"}
        )
        
        damage_res = await self.mcp_client.call_tool(
            server_url="http://localhost:8080/mcp",
            tool_name="estimateDisasterDamage",
            arguments={"hazard_type": "Flood", "magnitude": 6.8}
        )

        obstructions = self.vision.detect_feed_obstructions(road_res)
        road_safe = self.nav.evaluate_road_viability(road_res)

        severity = "High" if damage_res.get("evacuation_recommended", False) else "Medium"
        location = "Sector Alpha (SF Bay Area)"

        # Check if we should publish a RoadClosed event
        if not road_safe:
            await global_event_bus.publish(AgentEvent(
                event_type=EventType.RoadClosed,
                source_agent=self.name,
                payload={"road_name": "Route 101-North", "detour": road_res.get("detour_suggested")}
            ))

        confidence = 0.95 if not road_safe else 0.65

        return AgentOutput(
            agent_name=self.name,
            status="success" if confidence >= 0.70 else "warning",
            confidence_score=confidence,
            data={
                "severity": severity,
                "location": location,
                "coordinates": [37.7749, -122.4194],
                "road_safe": road_safe,
                "obstructions": obstructions,
                "projected_damage": damage_res
            },
            reasons=["MCP roadStatus and damage estimates verified using Vision & Navigation skills."]
        )


class MedicalAgent(BaseSpecialistAgent):
    subscribed_topics: List[str] = [EventType.IncidentDetected, EventType.HospitalOverloaded]

    def __init__(self) -> None:
        super().__init__(
            name="MedicalAgent",
            instruction="Identify medical assistance requirements, capacity limits, and drug demands."
        )
        self.medical = MedicalSkill()
        self.resource = ResourceSkill()

    async def _run_logic(self, task_input: str) -> AgentOutput:
        hospital_res = await self.mcp_client.call_tool(
            server_url="http://localhost:8080/mcp",
            tool_name="findHospital",
            arguments={"zip_code": "94103", "specialty": "Emergency"}
        )
        
        emergency_facilities = self.medical.filter_compatible_facilities(hospital_res, "Emergency")
        total_beds = sum(h.get("available_beds", 0) for h in emergency_facilities)

        # Trigger HospitalOverloaded if beds are critically low
        if total_beds < 5:
            await global_event_bus.publish(AgentEvent(
                event_type=EventType.HospitalOverloaded,
                source_agent=self.name,
                payload={"available_beds": total_beds}
            ))

        severity = "High" if "emergency" in task_input.lower() else "Medium"
        triage_patients = self.medical.prioritize_triage_demand(severity)
        stock_warning = self.resource.evaluate_stock_level({"reorder_required": total_beds < 15})

        return AgentOutput(
            agent_name=self.name,
            confidence_score=0.92,
            data={
                "available_hospitals": emergency_facilities,
                "total_available_beds": total_beds,
                "triage_priority_count": triage_patients,
                "critical_supplies_reorder": stock_warning
            },
            reasons=["Queried active hospital capacities using Medical & Resource skills."]
        )


class ShelterAgent(BaseSpecialistAgent):
    subscribed_topics: List[str] = [EventType.IncidentDetected, EventType.ShelterFull]

    def __init__(self) -> None:
        super().__init__(
            name="ShelterAgent",
            instruction="Locate safe zones, establish shelter capacities, and verify supply rates."
        )
        self.nav = NavigationSkill()
        self.search = SearchSkill()

    async def _run_logic(self, task_input: str) -> AgentOutput:
        confidence = 0.55 if "extreme" in task_input.lower() else 0.92

        shelter_res = await self.mcp_client.call_tool(
            server_url="http://localhost:8080/mcp",
            tool_name="findShelter",
            arguments={"location": "San Francisco", "min_capacity": 50}
        )

        shelters = shelter_res.get("shelters", [])
        shelter_names = [s.get("name", "") for s in shelters]
        matched_shelters = self.search.fuzzy_match_person("Civic", shelter_names)

        # Trigger ShelterFull event mock
        if any(s.get("occupancy", 0) / s.get("capacity", 1) > 0.90 for s in shelters):
            await global_event_bus.publish(AgentEvent(
                event_type=EventType.ShelterFull,
                source_agent=self.name,
                payload={"shelters": shelters}
            ))

        return AgentOutput(
            agent_name=self.name,
            status="success" if confidence >= 0.70 else "warning",
            confidence_score=confidence,
            data={
                "raw_shelter_data": shelter_res,
                "primary_safe_zones": matched_shelters
            },
            reasons=["MCP shelter list queried and fuzzy matched via Navigation & Search skills."]
        )


class VolunteerAgent(BaseSpecialistAgent):
    subscribed_topics: List[str] = [EventType.IncidentDetected, EventType.VolunteerAssigned]

    def __init__(self) -> None:
        super().__init__(
            name="VolunteerAgent",
            instruction="Optimize deployment of volunteer resources, schedules, and skills."
        )
        self.resource = ResourceSkill()
        self.comm = CommunicationSkill()

    async def _run_logic(self, task_input: str) -> AgentOutput:
        volunteer_res = await self.mcp_client.call_tool(
            server_url="http://localhost:8080/mcp",
            tool_name="findVolunteer",
            arguments={"skill": "First Aid", "available_only": True}
        )

        volunteers = volunteer_res.get("volunteers", [])
        active_count = len(volunteers)
        allocated_count = self.resource.optimize_supply_dispatch(
            available_stock=active_count,
            requested_amount=10,
            priority_level="HIGH"
        )

        # Broadcast volunteer deployment
        if allocated_count > 0:
            await global_event_bus.publish(AgentEvent(
                event_type=EventType.VolunteerAssigned,
                source_agent=self.name,
                payload={"assigned_count": allocated_count, "skill": "First Aid"}
            ))

        return AgentOutput(
            agent_name=self.name,
            confidence_score=0.90,
            data={
                "available_volunteers": volunteer_res,
                "allocated_volunteers_count": allocated_count
            },
            reasons=["Queried volunteer roster using Resource & Communication skills."]
        )


class ResourceAllocationAgent(BaseSpecialistAgent):
    subscribed_topics: List[str] = [EventType.IncidentDetected, EventType.RoadClosed, EventType.ResourceDispatched]

    def __init__(self) -> None:
        super().__init__(
            name="ResourceAllocationAgent",
            instruction="Allocate supplies, trucks, and logistics parameters based on active agent requests."
        )
        self.resource = ResourceSkill()
        self.nav = NavigationSkill()

    async def _run_logic(self, task_input: str) -> AgentOutput:
        inventory_res = await self.mcp_client.call_tool(
            server_url="http://localhost:8080/mcp",
            tool_name="resourceInventory",
            arguments={"item_name": "Trauma Kits"}
        )

        dispatch_res = await self.mcp_client.call_tool(
            server_url="http://localhost:8080/mcp",
            tool_name="dispatchResources",
            arguments={
                "delivery_id": "DEL-908",
                "vehicle_type": "Truck",
                "item_list": ["Trauma Kits", "Water Bottles"]
            }
        )

        reorder_flag = self.resource.evaluate_stock_level(inventory_res)

        # Trigger ResourceDispatched event
        if dispatch_res.get("status") == "Dispatched":
            await global_event_bus.publish(AgentEvent(
                event_type=EventType.ResourceDispatched,
                source_agent=self.name,
                payload={"delivery_id": "DEL-908", "vehicle": "Truck"}
            ))

        return AgentOutput(
            agent_name=self.name,
            confidence_score=0.88,
            data={
                "inventory": inventory_res,
                "reorder_needed": reorder_flag,
                "dispatch": dispatch_res
            },
            reasons=["Inventory checks and truck route viability audited via Resource & Navigation skills."]
        )


class WeatherAgent(BaseSpecialistAgent):
    subscribed_topics: List[str] = [EventType.IncidentDetected, EventType.WeatherAlert]

    def __init__(self) -> None:
        super().__init__(
            name="WeatherAgent",
            instruction="Retrieve and project localized climate variables, warnings, and alerts."
        )
        self.weather = WeatherSkill()

    async def _run_logic(self, task_input: str) -> AgentOutput:
        weather_res = await self.mcp_client.call_tool(
            server_url="http://localhost:8080/mcp",
            tool_name="forecastWeather",
            arguments={"location": "SF Bay Area", "days": 3}
        )

        hazard_index = self.weather.calculate_storm_hazard_index(weather_res)
        wind_safe = self.weather.check_wind_safety_limits(wind_speed_mph=24.5, max_threshold=30.0)

        # Broadcast Weather Alert if wind speed is high
        if not wind_safe or hazard_index > 5.0:
            await global_event_bus.publish(AgentEvent(
                event_type=EventType.WeatherAlert,
                source_agent=self.name,
                payload={"hazard_index": hazard_index, "wind_speed": 24.5}
            ))

        return AgentOutput(
            agent_name=self.name,
            confidence_score=0.96,
            data={
                "raw_weather_forecast": weather_res,
                "hazard_threat_index": hazard_index,
                "ground_routes_wind_safe": wind_safe
            },
            reasons=["Storm vectors parsed using WeatherSkill indexing calculations."]
        )


class PredictionAgent(BaseSpecialistAgent):
    subscribed_topics: List[str] = [EventType.IncidentDetected, EventType.WeatherAlert, EventType.PredictionUpdated]

    def __init__(self) -> None:
        super().__init__(
            name="PredictionAgent",
            instruction="Calculate disaster trajectory forecasts and supply exhaustion rate estimates."
        )
        self.weather = WeatherSkill()
        self.resource = ResourceSkill()

    async def _run_logic(self, task_input: str) -> AgentOutput:
        damage_res = await self.mcp_client.call_tool(
            server_url="http://localhost:8080/mcp",
            tool_name="estimateDisasterDamage",
            arguments={"hazard_type": "Flood", "magnitude": 7.2}
        )

        weather_res = await self.mcp_client.call_tool(
            server_url="http://localhost:8080/mcp",
            tool_name="forecastWeather",
            arguments={"location": "SF Bay Area", "days": 1}
        )

        hazard_index = self.weather.calculate_storm_hazard_index(weather_res)
        reorder_flag = self.resource.evaluate_stock_level({"reorder_required": hazard_index > 7.0})

        # Broadcast PredictionUpdated event
        await global_event_bus.publish(AgentEvent(
            event_type=EventType.PredictionUpdated,
            source_agent=self.name,
            payload={"peak_hours": 4, "exhaustion_eta": 36}
        ))

        return AgentOutput(
            agent_name=self.name,
            confidence_score=0.80,
            data={
                "projected_damage": damage_res,
                "weather_hazard_index": hazard_index,
                "inventory_preemptive_reorder": reorder_flag,
                "water_level_peak_forecast_hours": 4,
                "exhaustion_eta_hours": {
                    "water_supplies": 36
                }
            },
            reasons=["Storm threat levels and resource safety lines predicted using Weather & Resource skills."]
        )


class TranslationAgent(BaseSpecialistAgent):
    subscribed_topics: List[str] = [EventType.IncidentDetected, EventType.WeatherAlert]

    def __init__(self) -> None:
        super().__init__(
            name="TranslationAgent",
            instruction="Translate emergency statements and localized instructions for diverse communities."
        )
        self.trans = TranslationSkill()

    async def _run_logic(self, task_input: str) -> AgentOutput:
        trans_res = await self.mcp_client.call_tool(
            server_url="http://localhost:8080/mcp",
            tool_name="translateMessage",
            arguments={"text": "Seek high ground immediately.", "target_lang": "Spanish"}
        )

        translated = self.trans.extract_localized_text(trans_res, default="Seek high ground.")
        reliable = self.trans.is_translation_reliable(trans_res)

        return AgentOutput(
            agent_name=self.name,
            confidence_score=0.98,
            data={
                "translated_output": translated,
                "translation_reliable": reliable
            },
            reasons=["Localized translations checked using TranslationSkill confidence checks."]
        )


class AccessibilityAgent(BaseSpecialistAgent):
    subscribed_topics: List[str] = [EventType.IncidentDetected, EventType.ShelterFull]

    def __init__(self) -> None:
        super().__init__(
            name="AccessibilityAgent",
            instruction="Verify accessibility of safe locations, transportation, and visual alerts."
        )
        self.vision = VisionSkill()
        self.trans = TranslationSkill()

    async def _run_logic(self, task_input: str) -> AgentOutput:
        shelter_res = await self.mcp_client.call_tool(
            server_url="http://localhost:8080/mcp",
            tool_name="findShelter",
            arguments={"location": "San Francisco"}
        )

        ada_compliant = self.vision.audit_physical_accessibility(shelter_res)

        return AgentOutput(
            agent_name=self.name,
            confidence_score=0.91,
            data={
                "wheelchair_access_configured": ada_compliant,
                "shelter_details": shelter_res
            },
            reasons=["Audited physical ADA shelter assets using VisionSkill compliance checks."]
        )


class FamilyReunificationAgent(BaseSpecialistAgent):
    subscribed_topics: List[str] = [EventType.IncidentDetected, EventType.MissingPersonReported]

    def __init__(self) -> None:
        super().__init__(
            name="FamilyReunificationAgent",
            instruction="Track missing persons cases and reconcile with safe list updates."
        )
        self.search = SearchSkill()
        self.comm = CommunicationSkill()

    async def _run_logic(self, task_input: str) -> AgentOutput:
        family_res = await self.mcp_client.call_tool(
            server_url="http://localhost:8080/mcp",
            tool_name="locateFamily",
            arguments={"family_id": "FAM-982"}
        )

        person_res = await self.mcp_client.call_tool(
            server_url="http://localhost:8080/mcp",
            tool_name="searchMissingPerson",
            arguments={"name": "Jane Doe"}
        )

        matched_status = self.search.reconcile_safe_status(person_res, family_res)
        alert_msg = self.comm.format_alert_broadcast(
            template_name="missing_person",
            parameters={
                "name": matched_status.get("name", "Jane Doe"),
                "shelter_name": matched_status.get("location", "Civic Center Hall")
            }
        )

        # Broadcast MissingPersonReported mock event
        if not matched_status.get("found", False):
            await global_event_bus.publish(AgentEvent(
                event_type=EventType.MissingPersonReported,
                source_agent=self.name,
                payload={"name": "Jane Doe"}
            ))

        return AgentOutput(
            agent_name=self.name,
            confidence_score=0.85,
            data={
                "reconciliation": matched_status,
                "reunification_broadcast_text": alert_msg
            },
            reasons=["Registry safe lists cross-reconciled using Search & Communication skills."]
        )
