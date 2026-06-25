import pytest
from app.api import mcp_server as server

@pytest.mark.asyncio
async def test_findHospital_tool() -> None:
    res = await server.findHospital(zip_code="94103", specialty="Emergency")
    assert isinstance(res, server.HospitalList)
    assert len(res.hospitals) > 0
    assert res.hospitals[0].name == "General Memorial Hospital"

@pytest.mark.asyncio
async def test_findShelter_tool() -> None:
    res = await server.findShelter(location="San Francisco")
    assert isinstance(res, server.ShelterList)
    assert len(res.shelters) > 0
    assert any(s.name == "Civic Center Hall" for s in res.shelters)

@pytest.mark.asyncio
async def test_findVolunteer_tool() -> None:
    res = await server.findVolunteer(skill="First Aid")
    assert isinstance(res, server.VolunteerList)
    assert len(res.volunteers) > 0
    assert res.volunteers[0].skills[0] == "First Aid"

@pytest.mark.asyncio
async def test_forecastWeather_tool() -> None:
    res = await server.forecastWeather(location="SF Bay Area", days=2)
    assert isinstance(res, server.WeatherForecast)
    assert len(res.forecast) == 2

@pytest.mark.asyncio
async def test_roadStatus_tool() -> None:
    res = await server.roadStatus(road_name="Route 101-North")
    assert isinstance(res, server.RoadReport)
    assert res.status == "Closed"

@pytest.mark.asyncio
async def test_resourceInventory_tool() -> None:
    res = await server.resourceInventory(item_name="Trauma Kits")
    assert isinstance(res, server.InventoryStatus)
    assert res.quantity_available == 250
    assert res.unit == "kits"

@pytest.mark.asyncio
async def test_dispatchResources_tool() -> None:
    res = await server.dispatchResources(delivery_id="DEL-10", vehicle_type="Truck", item_list=["Trauma Kits"])
    assert isinstance(res, server.DispatchConfirmation)
    assert res.status == "Dispatched"
    assert res.vehicle_assigned == "Truck"

@pytest.mark.asyncio
async def test_translateMessage_tool() -> None:
    res = await server.translateMessage(text="Seek high ground immediately.", target_lang="es")
    assert isinstance(res, server.TranslationResult)
    assert res.target_language == "es"
    assert "terreno elevado" in res.translated_text

@pytest.mark.asyncio
async def test_estimateDisasterDamage_tool() -> None:
    res = await server.estimateDisasterDamage(hazard_type="Flood", magnitude=6.0)
    assert isinstance(res, server.DamageProjection)
    assert res.projected_loss_usd == 900000.0
    assert res.evacuation_recommended is True

@pytest.mark.asyncio
async def test_locateFamily_tool() -> None:
    res = await server.locateFamily(family_id="FAM-1")
    assert isinstance(res, server.FamilyStatus)
    assert "Jane Doe" in res.members_registered

@pytest.mark.asyncio
async def test_searchMissingPerson_tool() -> None:
    res = await server.searchMissingPerson(name="Sarah Jenkins")
    assert isinstance(res, server.MissingPersonResult)
    assert res.found is True
    assert res.safe_shelter_id == "S1"
