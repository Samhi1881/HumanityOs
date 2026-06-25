from app.agents.skills import (
    VisionSkill, MedicalSkill, NavigationSkill, WeatherSkill,
    TranslationSkill, CommunicationSkill, ResourceSkill, SearchSkill
)

def test_vision_skill() -> None:
    vision = VisionSkill()
    
    # 1. Test obstruction detection
    road_report = {"status": "Closed", "hazard_details": "Mudslide blocked lanes"}
    obstructions = vision.detect_feed_obstructions(road_report)
    assert "Debris slide detected" in obstructions
    
    # 2. Test physical accessibility audit
    shelter_details = {"shelters": [
        {"name": "Center A", "accessibility_features": ["ADA Ramp", "Wheelchair Restrooms"]}
    ]}
    assert vision.audit_physical_accessibility(shelter_details) is True

def test_medical_skill() -> None:
    medical = MedicalSkill()
    
    # 1. Test triage priority count calculation
    assert medical.prioritize_triage_demand("High") == 120
    assert medical.prioritize_triage_demand("Medium") == 30
    
    # 2. Test compatible facilities filtering
    hospital_list = {"hospitals": [
        {"name": "H1", "specialties": ["Emergency", "Trauma"]},
        {"name": "H2", "specialties": ["Cardiology"]}
    ]}
    filtered = medical.filter_compatible_facilities(hospital_list, "Trauma")
    assert len(filtered) == 1
    assert filtered[0]["name"] == "H1"

def test_navigation_skill() -> None:
    nav = NavigationSkill()
    
    # 1. Test road viability
    open_road = {"status": "Open"}
    closed_road = {"status": "Closed"}
    assert nav.evaluate_road_viability(open_road) is True
    assert nav.evaluate_road_viability(closed_road) is False
    
    # 2. Test detour resolution
    detour_road = {"status": "Closed", "detour_suggested": "Take Highway 9"}
    assert nav.resolve_alternate_path(detour_road) == "Take Highway 9"

def test_weather_skill() -> None:
    weather = WeatherSkill()
    
    # 1. Test storm index calculation
    forecast = {"forecast": [{"precipitation_chance": 0.80, "wind_speed_mph": 30.0}]}
    # score = (0.80 * 5) + (30.0 / 10) = 4.0 + 3.0 = 7.0
    assert weather.calculate_storm_hazard_index(forecast) == 7.0
    
    # 2. Test safety limits
    assert weather.check_wind_safety_limits(wind_speed_mph=25.0) is True
    assert weather.check_wind_safety_limits(wind_speed_mph=45.0) is False

def test_translation_skill() -> None:
    trans = TranslationSkill()
    
    res = {"translated_text": "Hola", "confidence": 0.95}
    assert trans.extract_localized_text(res) == "Hola"
    assert trans.is_translation_reliable(res) is True
    
    unreliable_res = {"translated_text": "Hola", "confidence": 0.50}
    assert trans.is_translation_reliable(unreliable_res) is False

def test_communication_skill() -> None:
    comm = CommunicationSkill()
    
    # 1. Test formatting
    params = {"location": "Sector Alpha", "hazard": "flood"}
    msg = comm.format_alert_broadcast("evacuation", params)
    assert "Sector Alpha" in msg
    assert "flood" in msg
    
    # 2. Test channels
    high_channels = comm.select_distribution_channels("High")
    assert "SMS Broadcast" in high_channels
    assert "Emergency Radio Band" in high_channels

def test_resource_skill() -> None:
    resource = ResourceSkill()
    
    # 1. Test inventory audit
    assert resource.evaluate_stock_level({"reorder_required": True}) is True
    
    # 2. Test supply optimization
    assert resource.optimize_supply_dispatch(available_stock=50, requested_amount=10, priority_level="High") == 10
    # Normal priority capped at 50% = 25
    assert resource.optimize_supply_dispatch(available_stock=50, requested_amount=30, priority_level="Normal") == 25

def test_search_skill() -> None:
    search = SearchSkill()
    
    # 1. Test safe list matching
    missing_result = {"name_queried": "Jane Doe", "found": False, "safe_shelter_id": "S1"}
    family_status = {"family_id": "FAM-10", "members_registered": ["Jane Doe"], "safe_locations": {"Jane Doe": "Civic Hall"}}
    
    reconciled = search.reconcile_safe_status(missing_result, family_status)
    assert reconciled["found"] is True
    assert reconciled["status"] == "Located Safe"
    assert reconciled["location"] == "Civic Hall"
    
    # 2. Test fuzzy match
    roster = ["Sarah Jenkins", "Sarah Torres", "Miguel Torres"]
    matches = search.fuzzy_match_person("Sarah", roster)
    assert len(matches) == 2
    assert "Sarah Jenkins" in matches
