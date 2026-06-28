"""
Custom integration to integrate Zen WiFi Thermostat with Home Assistant.

For more details about this integration, please refer to
https://github.com/DanrwAU/zenwifi
"""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import TYPE_CHECKING

from homeassistant.const import CONF_PASSWORD, CONF_USERNAME, Platform
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.loader import async_get_loaded_integration

from .api import ZenWifiApiClient
from .const import DOMAIN
from .coordinator import ZenWifiDataUpdateCoordinator
from .data import ZenWifiData

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .data import ZenWifiConfigEntry

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.CLIMATE,
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
]

# The thermostat only pushes telemetry to the cloud about every 5 minutes
# (statusRefreshPeriod=300), so polling faster just refetches identical data.
# User-initiated changes call async_request_refresh() directly and update at once.
SCAN_INTERVAL = timedelta(minutes=2)


# https://developers.home-assistant.io/docs/config_entries_index/#setting-up-an-entry
async def async_setup_entry(hass: HomeAssistant, entry: ZenWifiConfigEntry) -> bool:
    """Set up this integration using UI."""
    client = ZenWifiApiClient(
        username=entry.data[CONF_USERNAME],
        password=entry.data[CONF_PASSWORD],
        session=async_get_clientsession(hass),
    )

    coordinator = ZenWifiDataUpdateCoordinator(
        hass=hass,
        logger=_LOGGER,
        name=DOMAIN,
        update_interval=SCAN_INTERVAL,
        client=client,
    )

    entry.runtime_data = ZenWifiData(
        client=client,
        integration=async_get_loaded_integration(hass, entry.domain),
        coordinator=coordinator,
    )

    await coordinator.async_config_entry_first_refresh()
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ZenWifiConfigEntry) -> bool:
    """Handle removal of an entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_reload_entry(hass: HomeAssistant, entry: ZenWifiConfigEntry) -> None:
    """Reload config entry."""
    await hass.config_entries.async_reload(entry.entry_id)
