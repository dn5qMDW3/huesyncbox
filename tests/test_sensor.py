from unittest.mock import Mock

from homeassistant.core import HomeAssistant
import pytest

from .conftest import setup_integration


@pytest.mark.usefixtures("entity_registry_enabled_by_default")
async def test_sensor(hass: HomeAssistant, mock_api: Mock) -> None:
    """Test the total count of sensor entities after integration setup."""
    await setup_integration(hass, mock_api)
    assert hass.states.async_entity_ids_count("sensor") == 12


async def test_sensor_default_disabled(hass: HomeAssistant, mock_api: Mock) -> None:
    await setup_integration(hass, mock_api)
    # Default-enabled: 4 HDMI inputs + HDMI output status
    assert hass.states.async_entity_ids_count("sensor") == 5


async def test_hdmi_status(hass: HomeAssistant, mock_api: Mock) -> None:
    await setup_integration(hass, mock_api)

    entity = hass.states.get("sensor.name_hdmi1_status")
    assert entity is not None
    assert entity.state == "unplugged"

    entity = hass.states.get("sensor.name_hdmi2_status")
    assert entity is not None
    assert entity.state == "plugged"

    entity = hass.states.get("sensor.name_hdmi3_status")
    assert entity is not None
    assert entity.state == "linked"

    entity = hass.states.get("sensor.name_hdmi4_status")
    assert entity is not None
    assert entity.state == "unknown"


@pytest.mark.usefixtures("entity_registry_enabled_by_default")
async def test_ip_address(hass: HomeAssistant, mock_api: Mock) -> None:
    await setup_integration(hass, mock_api)

    entity = hass.states.get("sensor.name_ip_address")
    assert entity is not None
    assert entity.state == "1.2.3.4"


@pytest.mark.usefixtures("entity_registry_enabled_by_default")
async def test_bridge_id(hass: HomeAssistant, mock_api: Mock) -> None:
    await setup_integration(hass, mock_api)

    entity = hass.states.get("sensor.name_bridge_id")
    assert entity is not None
    assert entity.state == "c42996fffec6c2ca"


@pytest.mark.usefixtures("entity_registry_enabled_by_default")
async def test_bridge_connection_state(hass: HomeAssistant, mock_api: Mock) -> None:
    await setup_integration(hass, mock_api)

    entity = hass.states.get("sensor.name_bridge_connection")
    assert entity is not None
    assert entity.state == "connected"


async def test_wifi_strength_not_supported(hass: HomeAssistant, mock_api: Mock) -> None:
    mock_api.device.wifi = None
    await setup_integration(hass, mock_api)

    entity = hass.states.get("sensor.name_wifi_strength")
    assert entity is None


@pytest.mark.usefixtures("entity_registry_enabled_by_default")
async def test_wifi_strength(hass: HomeAssistant, mock_api: Mock) -> None:
    await setup_integration(hass, mock_api)

    entity = hass.states.get("sensor.name_wifi_quality")
    assert entity is not None
    assert entity.state == "excellent"


@pytest.mark.usefixtures("entity_registry_enabled_by_default")
async def test_content_info(hass: HomeAssistant, mock_api: Mock) -> None:
    await setup_integration(hass, mock_api)

    entity = hass.states.get("sensor.name_content_info")
    assert entity is not None
    assert entity.state == "3840 x 2160 @ 60000 - HDR"


async def test_hdmi_output_status(hass: HomeAssistant, mock_api: Mock) -> None:
    await setup_integration(hass, mock_api)

    entity = hass.states.get("sensor.name_hdmi_output_status")
    assert entity is not None
    assert entity.state == "plugged"


@pytest.mark.usefixtures("entity_registry_enabled_by_default")
async def test_bridge_ip_address(hass: HomeAssistant, mock_api: Mock) -> None:
    await setup_integration(hass, mock_api)

    entity = hass.states.get("sensor.name_bridge_ip_address")
    assert entity is not None
    assert entity.state == "1.2.3.5"


@pytest.mark.usefixtures("entity_registry_enabled_by_default")
async def test_api_level(hass: HomeAssistant, mock_api: Mock) -> None:
    await setup_integration(hass, mock_api)

    entity = hass.states.get("sensor.name_api_level")
    assert entity is not None
    assert entity.state == "10"
