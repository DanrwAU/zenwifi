"""Custom types for Zen WiFi Thermostat."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.loader import Integration

    from .api import ZenWifiApiClient
    from .coordinator import ZenWifiDataUpdateCoordinator


type ZenWifiConfigEntry = ConfigEntry[ZenWifiData]


@dataclass
class ZenWifiData:
    """Data for the Zen WiFi integration."""

    client: ZenWifiApiClient
    coordinator: ZenWifiDataUpdateCoordinator
    integration: Integration

