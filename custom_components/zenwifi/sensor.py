"""Sensor platform for Zen WiFi Thermostat."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import UnitOfTemperature
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import ZenWifiDataUpdateCoordinator

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .data import ZenWifiConfigEntry

SENSOR_DESCRIPTIONS = [
    SensorEntityDescription(
        key="currentTemperature",
        name="Current Temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        icon="mdi:thermometer",
    ),
    SensorEntityDescription(
        key="heatingSetpoint",
        name="Heating Setpoint",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        icon="mdi:thermometer-chevron-up",
    ),
    SensorEntityDescription(
        key="coolingSetpoint",
        name="Cooling Setpoint",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        icon="mdi:thermometer-chevron-down",
    ),
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ZenWifiConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    coordinator: ZenWifiDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = []
    for device_id, device_data in coordinator.data.items():
        entities.extend(
            ZenWifiSensor(
                coordinator=coordinator,
                device_id=device_id,
                device_data=device_data,
                entity_description=description,
            )
            for description in SENSOR_DESCRIPTIONS
            if description.key in device_data
        )

    async_add_entities(entities)


class ZenWifiSensor(CoordinatorEntity[ZenWifiDataUpdateCoordinator], SensorEntity):
    """Zen WiFi Sensor class."""

    _attr_has_entity_name = True
    _attr_entity_registry_enabled_default = False  # Disabled by default

    def __init__(
        self,
        coordinator: ZenWifiDataUpdateCoordinator,
        device_id: str,
        device_data: dict[str, Any],
        entity_description: SensorEntityDescription,
    ) -> None:
        """Initialize the sensor class."""
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
            and self.device_data.get("isOnline", False)
            and self.entity_description.key in self.device_data
        )

    @property
    def native_value(self) -> float | None:
        """Return the native value of the sensor."""
        return self.device_data.get(self.entity_description.key)

