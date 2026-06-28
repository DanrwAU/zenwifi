"""DataUpdateCoordinator for Zen WiFi Thermostat."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import (
    ZenWifiApiClient,
    ZenWifiApiClientAuthenticationError,
    ZenWifiApiClientCommunicationError,
    ZenWifiApiClientError,
)

if TYPE_CHECKING:
    from datetime import timedelta

    from homeassistant.core import HomeAssistant

    from .data import ZenWifiConfigEntry

_LOGGER = logging.getLogger(__name__)

# Devices that were never provisioned report this placeholder date.
UNPROVISIONED_DATE_PREFIX = "0001-01-01"


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
        """Fetch provisioned devices and merge in their current status."""
        try:
            devices = await self.client.async_get_devices()

            # Skip devices that were never provisioned (placeholder date).
            valid_devices = [
                device
                for device in devices
                if device.get("provisionedDateTime")
                and not device["provisionedDateTime"].startswith(
                    UNPROVISIONED_DATE_PREFIX
                )
            ]

            device_data: dict[str, Any] = {}
            for device in valid_devices:
                device_id = device.get("id")
                if not device_id:
                    continue
                try:
                    status = await self.client.async_get_device_status(device_id)
                    device_data[device_id] = {**device, **status}
                except ZenWifiApiClientCommunicationError:
                    # Transient per-device failure: keep the basic list info.
                    _LOGGER.warning(
                        "Status fetch failed for device %s; using basic info",
                        device_id,
                    )
                    device_data[device_id] = device
        except ZenWifiApiClientAuthenticationError as exception:
            raise ConfigEntryAuthFailed(exception) from exception
        except ZenWifiApiClientError as exception:
            raise UpdateFailed(exception) from exception
        else:
            return device_data
