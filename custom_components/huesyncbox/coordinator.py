"""Coordinator for the Philips Hue Play HDMI Sync Box integration."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

import aiohuesyncbox

from .const import COORDINATOR_UPDATE_INTERVAL, LOGGER
from .helpers import update_config_entry_title, update_device_registry

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant

MAX_CONSECUTIVE_ERRORS = 5


class HueSyncBoxCoordinator(DataUpdateCoordinator[aiohuesyncbox.HueSyncBox]):
    """Coordinator for polling the Philips Hue Play HDMI Sync Box."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        api: aiohuesyncbox.HueSyncBox,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            LOGGER,
            # Binding the coordinator to the config entry is required since
            # HA 2024.10+; passing it explicitly silences deprecation warnings
            # and will remain required in future releases.
            config_entry=config_entry,
            # Name of the data. For logging purposes.
            name=f"Philips Hue Play HDMI Sync Box ({api.device.name} at {api.device.ip_address})",
            # Polling interval. Will only be polled if there are subscribers.
            # A short (3s) interval keeps UI state responsive to manual changes
            # made on the device itself (e.g., remote, Hue app). The box is a
            # local-network device, so the load is modest.
            update_interval=COORDINATOR_UPDATE_INTERVAL,
        )
        self.api = api
        self._consecutive_errors = 0

    def _is_consecutive_error_reached(self) -> bool:
        self._consecutive_errors += 1
        LOGGER.debug("Consecutive errors = %s", self._consecutive_errors)
        return self._consecutive_errors >= MAX_CONSECUTIVE_ERRORS

    async def _async_update_data(self) -> aiohuesyncbox.HueSyncBox:
        """Fetch data from API endpoint."""
        try:
            async with asyncio.timeout(5):
                old_device = self.api.device
                await self.api.update()
                self._consecutive_errors = 0

                if old_device != self.api.device:
                    await update_device_registry(self.hass, self.config_entry, self.api)
                    update_config_entry_title(
                        self.hass, self.config_entry, self.api.device.name
                    )

        except aiohuesyncbox.Unauthorized as err:
            # Raising ConfigEntryAuthFailed will cancel future updates
            # and start a config flow with SOURCE_REAUTH (async_step_reauth)
            raise ConfigEntryAuthFailed from err
        except aiohuesyncbox.RequestError as err:
            # Transient errors (device temporarily unreachable) are tolerated
            # until MAX_CONSECUTIVE_ERRORS; entities remain available and
            # display the last known values. On the threshold we surface
            # UpdateFailed so HA marks entities as unavailable.
            LOGGER.debug("aiohuesyncbox.RequestError while updating data: %s", err)
            if self._is_consecutive_error_reached():
                raise UpdateFailed(err) from err
        except TimeoutError:
            # Same policy as RequestError: tolerate transient timeouts and
            # only propagate once the consecutive-error threshold is reached.
            LOGGER.debug("asyncio.TimeoutError while updating data")
            if self._is_consecutive_error_reached():
                raise

        return self.api
