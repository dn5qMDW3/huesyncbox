"""Common fixtures  for the Philips Hue Play HDMI Sync Box integration tests."""

from collections.abc import Generator
from dataclasses import dataclass
from unittest.mock import Mock, patch

from homeassistant.const import (
    CONF_ACCESS_TOKEN,
    CONF_HOST,
    CONF_PATH,
    CONF_PORT,
    CONF_UNIQUE_ID,
)
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util
import pytest
from pytest_homeassistant_custom_component.common import (  # type: ignore[import]
    MockConfigEntry,
    async_fire_time_changed,
)

import aiohuesyncbox
from custom_components import huesyncbox

# Test group IDs in the modern v2-API UUID format (the syncbox started returning
# UUIDs after firmware 2.x). The repeating-digit pattern flags these as test data.
GROUP_ID_1 = "11111111-1111-1111-1111-111111111111"
GROUP_ID_2 = "22222222-2222-2222-2222-222222222222"


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations) -> Generator[None]:  # noqa: ANN001, ARG001
    """Enable custom integrations."""
    yield  # noqa: PT022


# Copied from HA tests/components/conftest.py
@pytest.fixture
def entity_registry_enabled_by_default() -> Generator[None]:
    """Test fixture that ensures all entities are enabled in the registry."""
    with patch(
        "homeassistant.helpers.entity.Entity.entity_registry_enabled_default",
        return_value=True,
    ):
        yield


@pytest.fixture
def mock_api() -> Mock:
    """Create a mocked HueSyncBox instance."""
    mock_api = Mock(
        spec=aiohuesyncbox.HueSyncBox,
    )

    mock_api.device = Mock(aiohuesyncbox.device.Device)
    mock_api.device.name = "Name"
    mock_api.device.api_level = 10
    mock_api.device.device_type = "HSB1"
    mock_api.device.firmware_version = "2.5.4"
    mock_api.device.unique_id = "123456ABCDEF"  # Make sure it resembles real value
    mock_api.device.led_mode = 1
    mock_api.device.ip_address = "1.2.3.4"
    mock_api.device.wifi = Mock(aiohuesyncbox.device.Wifi)
    mock_api.device.wifi.strength = 4

    mock_api.execution = Mock(aiohuesyncbox.execution.Execution)
    mock_api.execution.brightness = 120
    mock_api.execution.mode = "music"
    mock_api.execution.last_sync_mode = "game"
    mock_api.execution.sync_active = False
    mock_api.execution.hdmi_source = "input2"
    mock_api.execution.hue_target = GROUP_ID_2
    mock_api.execution.video = Mock(aiohuesyncbox.execution.SyncMode)
    mock_api.execution.video.intensity = "subtle"
    mock_api.execution.music = Mock(aiohuesyncbox.execution.SyncMode)
    mock_api.execution.music.intensity = "moderate"
    mock_api.execution.game = Mock(aiohuesyncbox.execution.SyncMode)
    mock_api.execution.game.intensity = "intense"

    mock_api.hdmi = Mock(aiohuesyncbox.hdmi.Hdmi)
    mock_api.hdmi.input1 = Mock(aiohuesyncbox.hdmi.Input)
    mock_api.hdmi.input1.name = "HDMI 1"
    mock_api.hdmi.input1.type = "generic"
    mock_api.hdmi.input1.status = "unplugged"
    mock_api.hdmi.input2 = Mock(aiohuesyncbox.hdmi.Input)
    mock_api.hdmi.input2.name = "HDMI 2"
    mock_api.hdmi.input2.type = "generic"
    mock_api.hdmi.input2.status = "plugged"
    mock_api.hdmi.input3 = Mock(aiohuesyncbox.hdmi.Input)
    mock_api.hdmi.input3.name = "HDMI 3"
    mock_api.hdmi.input3.type = "generic"
    mock_api.hdmi.input3.status = "linked"
    mock_api.hdmi.input4 = Mock(aiohuesyncbox.hdmi.Input)
    mock_api.hdmi.input4.name = "HDMI 4"
    mock_api.hdmi.input4.type = "generic"
    mock_api.hdmi.input4.status = "unknown"
    mock_api.hdmi.output = Mock(aiohuesyncbox.hdmi.Output)
    mock_api.hdmi.output.name = "HDMI Out"
    mock_api.hdmi.output.type = "generic"
    mock_api.hdmi.output.status = "plugged"
    mock_api.hdmi.content_specs = "3840 x 2160 @ 60000 - HDR"

    mock_api.hue = Mock(aiohuesyncbox.hue.Hue)
    mock_api.hue.bridge_unique_id = "c42996fffec6c2ca"
    mock_api.hue.bridge_ip_address = "1.2.3.5"
    mock_api.hue.connection_state = "connected"
    mock_api.hue.groups = [
        aiohuesyncbox.hue.Group(
            GROUP_ID_1, {"name": "Name 1", "numLights": 1, "active": False}
        ),
        aiohuesyncbox.hue.Group(
            GROUP_ID_2, {"name": "Name 2", "numLights": 2, "active": False}
        ),
    ]

    mock_api.behavior = Mock(aiohuesyncbox.behavior.Behavior)
    mock_api.behavior.force_dovi_native = 1

    return mock_api


@dataclass
class Integration:
    entry: MockConfigEntry
    mock_api: Mock


async def setup_integration(
    hass: HomeAssistant,
    mock_api: Mock,
    mock_config_entry: MockConfigEntry | None = None,
    entry_id: str = "entry_id",
) -> Integration:
    entry = mock_config_entry or MockConfigEntry(
        version=2,
        minor_version=2,
        domain=huesyncbox.DOMAIN,
        entry_id=entry_id,
        unique_id="123456ABCDEF",  # Make sure it resembles the real format
        title="HUESYNCBOX TITLE",
        data={
            CONF_HOST: "host_value",
            CONF_UNIQUE_ID: "unique_id_value",
            CONF_PORT: 1234,
            CONF_PATH: "/path_value",
            CONF_ACCESS_TOKEN: "token_value",
            huesyncbox.const.REGISTRATION_ID: "registration_id_value",
        },
    )
    entry.add_to_hass(hass)

    with patch("aiohuesyncbox.HueSyncBox", return_value=mock_api):
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    return Integration(entry, mock_api)


async def force_coordinator_update(hass: HomeAssistant) -> None:
    async_fire_time_changed(
        hass, dt_util.utcnow() + huesyncbox.const.COORDINATOR_UPDATE_INTERVAL
    )
    await hass.async_block_till_done()
