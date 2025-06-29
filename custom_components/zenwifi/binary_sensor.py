"""Binary sensor platform for Zen WiFi Thermostat."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import ZenWifiDataUpdateCoordinator

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .data import ZenWifiConfigEntry

BINARY_SENSOR_DESCRIPTIONS = [
    BinarySensorEntityDescription(
        key="isOnline",
        name="Online",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        icon="mdi:wifi",
    ),
    BinarySensorEntityDescription(
        key="isOnCWire",
        name="C-Wire Connected",
        device_class=BinarySensorDeviceClass.PLUG,
        icon="mdi:power-plug",
    ),
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ZenWifiConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the binary_sensor platform."""
    coordinator: ZenWifiDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = []
    for device_id, device_data in coordinator.data.items():
        entities.extend(
            ZenWifiBinarySensor(
                coordinator=coordinator,
                device_id=device_id,
                device_data=device_data,
                entity_description=description,
            )
            for description in BINARY_SENSOR_DESCRIPTIONS
            if description.key in device_data
        )

    async_add_entities(entities)


class ZenWifiBinarySensor(
    CoordinatorEntity[ZenWifiDataUpdateCoordinator], BinarySensorEntity
):
    """Zen WiFi binary_sensor class."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: ZenWifiDataUpdateCoordinator,
        device_id: str,
        device_data: dict[str, Any],
        entity_description: BinarySensorEntityDescription,
    ) -> None:
        """Initialize the binary_sensor class."""
        super().__init__(coordinator)
        self.entity_description = entity_description
        self._device_id = device_id
        self._attr_unique_id = f"{device_id}_{entity_description.key}"

        # Set device info
        self._attr_device_info = {
            "identifiers": {(DOMAIN, device_id)},
            "name": device_data.get("name", "Zen WiFi Thermostat"),
            "manufacturer": "Zen Ecosystems",
            "model": "Zen Thermostat",
        }

    @property
    def device_data(self) -> dict[str, Any]:
        """Get current device data from coordinator."""
        return self.coordinator.data.get(self._device_id, {})

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            self.coordinator.last_update_success
            and self.entity_description.key in self.device_data
        )

    @property
    def is_on(self) -> bool:
        """Return true if the binary_sensor is on."""
        return bool(self.device_data.get(self.entity_description.key, False))

