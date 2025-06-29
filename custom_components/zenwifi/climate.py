"""Climate entity for Zen WiFi Thermostat."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
)
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import ZenWifiDataUpdateCoordinator

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

_LOGGER = logging.getLogger(__name__)

# Map Zen WiFi mode integers to Home Assistant HVAC modes
ZEN_MODE_TO_HVAC = {
    0: HVACMode.HEAT,  # heat
    1: HVACMode.HEAT,  # heat (keeping for compatibility)
    2: HVACMode.COOL,  # cool
    3: HVACMode.OFF,  # off
    4: HVACMode.HEAT_COOL,  # auto
    5: HVACMode.OFF,  # eco (map to off)
    6: HVACMode.HEAT,  # emergency_heat (map to heat)
    7: HVACMode.OFF,  # zen (map to off)
}

# Map Home Assistant HVAC modes to Zen WiFi modes
HVAC_TO_ZEN_MODE = {
    HVACMode.OFF: "off",
    HVACMode.HEAT: "heat",
    HVACMode.COOL: "cool",
    HVACMode.HEAT_COOL: "auto",
}

# Define constants for magic numbers
MODE_HEAT = 0
MODE_COOL = 2
MODE_OFF = 3


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Zen WiFi climate entities."""
    coordinator: ZenWifiDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = []
    for device_id, device_data in coordinator.data.items():
        entities.append(ZenWifiClimate(coordinator, device_id, device_data))
        # Create climate entity
    async_add_entities(entities)


class ZenWifiClimate(CoordinatorEntity[ZenWifiDataUpdateCoordinator], ClimateEntity):
    """Representation of a Zen WiFi Thermostat."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.TURN_OFF
        | ClimateEntityFeature.TURN_ON
    )

    def __init__(
        self,
        coordinator: ZenWifiDataUpdateCoordinator,
        device_id: str,
        device_data: dict[str, Any],
    ) -> None:
        """Initialize the climate entity."""
        super().__init__(coordinator)
        self._device_id = device_id
        self._attr_unique_id = f"{device_id}_climate"

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
        )

    @property
    def current_temperature(self) -> float | None:
        """Return the current temperature."""
        return self.device_data.get("currentTemperature")

    @property
    def target_temperature(self) -> float | None:
        """Return the temperature we try to reach."""
        mode = self.device_data.get("mode", 0)
        if mode == MODE_HEAT:  # heat
            return self.device_data.get("heatingSetpoint")
        if mode == MODE_COOL:  # cool
            return self.device_data.get("coolingSetpoint")
        return None

    @property
    def hvac_mode(self) -> HVACMode | None:
        """Return hvac operation ie. heat, cool mode."""
        mode = self.device_data.get("mode", 0)
        return ZEN_MODE_TO_HVAC.get(mode, HVACMode.OFF)

    @property
    def hvac_modes(self) -> list[HVACMode]:
        """Return the list of available hvac operation modes."""
        return [HVACMode.OFF, HVACMode.HEAT, HVACMode.COOL]

    @property
    def hvac_action(self) -> HVACAction | None:
        """Return the current running hvac operation."""
        if not self.device_data.get("isOnline", False):
            return HVACAction.OFF

        relay_states = self.device_data.get("relayStates", {})

        # Check if any heating relays are active
        if relay_states.get("w1") or relay_states.get("w2"):
            return HVACAction.HEATING

        # Check if any cooling relays are active
        if relay_states.get("y1") or relay_states.get("y2"):
            return HVACAction.COOLING

        # Check if fan is running
        if relay_states.get("g"):
            return HVACAction.FAN

        # If online but no relays active, it's idle
        mode = self.device_data.get("mode", 0)
        if mode == MODE_OFF:  # off
            return HVACAction.OFF
        return HVACAction.IDLE

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            return

        # Determine current mode to set appropriate temperature
        current_mode = self.hvac_mode
        if current_mode == HVACMode.HEAT:
            mode = "heat"
        elif current_mode == HVACMode.COOL:
            mode = "cool"
        else:
            # If off, we can't set temperature
            return

        await self.coordinator.client.async_set_mode(
            self._device_id,
            mode,
            temperature,
        )
        await self.coordinator.async_request_refresh()

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set new target hvac mode."""
        if hvac_mode not in HVAC_TO_ZEN_MODE:
            msg = f"Unsupported HVAC mode: {hvac_mode}"
            raise ValueError(msg)

        zen_mode = HVAC_TO_ZEN_MODE[hvac_mode]

        # If setting to heat or cool, use current setpoint
        temperature = None
        if hvac_mode == HVACMode.HEAT:
            temperature = self.device_data.get("heatingSetpoint")
        elif hvac_mode == HVACMode.COOL:
            temperature = self.device_data.get("coolingSetpoint")

        await self.coordinator.client.async_set_mode(
            self._device_id,
            zen_mode,
            temperature,
        )
        await self.coordinator.async_request_refresh()

    async def async_turn_on(self) -> None:
        """Turn the entity on."""
        # Default to heat mode when turning on
        await self.async_set_hvac_mode(HVACMode.HEAT)

    async def async_turn_off(self) -> None:
        """Turn the entity off."""
        await self.async_set_hvac_mode(HVACMode.OFF)

