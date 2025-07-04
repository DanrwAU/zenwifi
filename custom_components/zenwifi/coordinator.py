"""DataUpdateCoordinator for Zen WiFi Thermostat."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import (
    ZenWifiApiClient,
    ZenWifiApiClientAuthenticationError,
    ZenWifiApiClientError,
)

if TYPE_CHECKING:
    from datetime import timedelta

    from homeassistant.core import HomeAssistant

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
            # Process devices from API

            # Filter out devices that are not properly provisioned
            # Provisioned devices have a valid date (not 0001-01-01)
            valid_devices = [
                device for device in devices
                if device.get("provisionedDateTime")
                and not device.get("provisionedDateTime", "").startswith("0001-01-01")
            ]

            # Filtered to valid devices

            # Fetch detailed status for each valid device
            device_data = {}
            for device in valid_devices:
                device_id = device.get("id")
                if device_id:
                    try:
                        status = await self.client.async_get_device_status(device_id)
                        # Merge device info with status
                        device_data[device_id] = {**device, **status}
                    except Exception:
                        _LOGGER.exception(
                            "Failed to get status for device %s", device_id
                        )
                        # Still include basic device info even if status fails
                        device_data[device_id] = device

        except ZenWifiApiClientAuthenticationError as exception:
            raise ConfigEntryAuthFailed(exception) from exception
        except ZenWifiApiClientError as exception:
            raise UpdateFailed(exception) from exception
        else:
            return device_data
