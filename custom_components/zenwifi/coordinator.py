"""DataUpdateCoordinator for Zen WiFi Thermostat."""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import TYPE_CHECKING, Any

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import (
    ZenWifiApiClient,
    ZenWifiApiClientAuthenticationError,
    ZenWifiApiClientError,
)

if TYPE_CHECKING:
    from .data import ZenWifiConfigEntry

_LOGGER = logging.getLogger(__name__)


# https://developers.home-assistant.io/docs/integration_fetching_data#coordinated-single-api-poll-for-data-for-all-entities
class ZenWifiDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Class to manage fetching data from the API."""

    config_entry: ZenWifiConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        logger: logging.Logger,
        name: str,
        update_interval: timedelta,
        client: ZenWifiApiClient,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            logger,
            name=name,
            update_interval=update_interval,
        )
        self.client = client

    async def _async_update_data(self) -> dict[str, Any]:
        """Update data via library."""
        try:
            # Get all devices
            devices = await self.client.async_get_devices()
            
            # Fetch detailed status for each device
            device_data = {}
            for device in devices:
                device_id = device.get("id")
                if device_id:
                    try:
                        status = await self.client.async_get_device_status(device_id)
                        # Merge device info with status
                        device_data[device_id] = {**device, **status}
                    except Exception as e:
                        _LOGGER.error(f"Failed to get status for device {device_id}: {e}")
                        # Still include basic device info even if status fails
                        device_data[device_id] = device
            
            return device_data
            
        except ZenWifiApiClientAuthenticationError as exception:
            raise ConfigEntryAuthFailed(exception) from exception
        except ZenWifiApiClientError as exception:
            raise UpdateFailed(exception) from exception