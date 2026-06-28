"""Climate entity for Zen WiFi Thermostat (heat-only)."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, ClassVar

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
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .data import ZenWifiConfigEntry

_LOGGER = logging.getLogger(__name__)

# This is a heat-only install; cooling is intentionally not supported.
#
# The Zen API reports `mode` using two different enumerations depending on the
# source of the value:
#   * device telemetry (steady state, hasRequestedState == False): 0=heat, 1=cool, 2=off
#   * cloud command    (transient,    hasRequestedState == True):  1=heat, 2=cool, 3=off
# Because cool is never used here, the values we can ever see collapse cleanly to
# four unambiguous states:
MODE_HEATING = 0  # device confirmed in heat
MODE_HEAT_REQUESTED = 1  # heat command sent, not yet confirmed by the device
MODE_OFF = 2  # device confirmed off
MODE_OFF_REQUESTED = 3  # off command sent, not yet confirmed by the device

HEAT_MODES = (MODE_HEATING, MODE_HEAT_REQUESTED)
OFF_MODES = (MODE_OFF, MODE_OFF_REQUESTED)

# Human-friendly status surfaced as a state attribute.
MODE_STATUS_LABELS = {
    MODE_HEATING: "Heating",
    MODE_HEAT_REQUESTED: "Heat Requested",
    MODE_OFF: "Off",
    MODE_OFF_REQUESTED: "Off Requested",
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ZenWifiConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Zen WiFi climate entities."""
    coordinator = entry.runtime_data.coordinator

    async_add_entities(
        ZenWifiClimate(coordinator, device_id, device_data)
        for device_id, device_data in coordinator.data.items()
    )


class ZenWifiClimate(CoordinatorEntity[ZenWifiDataUpdateCoordinator], ClimateEntity):
    """Representation of a Zen WiFi Thermostat (heat-only)."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_hvac_modes: ClassVar[list[HVACMode]] = [HVACMode.OFF, HVACMode.HEAT]
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
        return self.coordinator.last_update_success and self.device_data.get(
            "isOnline", False
        )

    @property
    def current_temperature(self) -> float | None:
        """Return the current temperature."""
        return self.device_data.get("currentTemperature")

    @property
    def hvac_mode(self) -> HVACMode:
        """Return current operation (heat or off)."""
        mode = self.device_data.get("mode")
        if mode in HEAT_MODES:
            return HVACMode.HEAT
        if mode in OFF_MODES:
            return HVACMode.OFF
        _LOGGER.debug("Unexpected Zen mode %s; defaulting to OFF", mode)
        return HVACMode.OFF

    @property
    def target_temperature(self) -> float | None:
        """Return the heat setpoint we try to reach."""
        if self.hvac_mode == HVACMode.HEAT:
            return self.device_data.get("heatingSetpoint")
        return None

    @property
    def hvac_action(self) -> HVACAction:
        """Return the current running hvac operation."""
        if not self.device_data.get("isOnline", False):
            return HVACAction.OFF
        if self.device_data.get("mode") in OFF_MODES:
            return HVACAction.OFF
        relay_states = self.device_data.get("relayStates", {})
        if relay_states.get("w1") or relay_states.get("w2"):
            return HVACAction.HEATING
        return HVACAction.IDLE

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Expose the fine-grained Zen status as a state attribute."""
        mode = self.device_data.get("mode")
        return {
            "status": MODE_STATUS_LABELS.get(mode, f"Unknown ({mode})"),
            "zen_mode_raw": mode,
            "pending": self.device_data.get("hasRequestedState", False),
        }

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature (heat only)."""
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            return
        if self.hvac_mode != HVACMode.HEAT:
            # Setpoint only applies while heating.
            return
        await self.coordinator.client.async_set_mode(
            self._device_id, "heat", temperature
        )
        await self.coordinator.async_request_refresh()

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set new target hvac mode (heat or off)."""
        if hvac_mode == HVACMode.HEAT:
            await self.coordinator.client.async_set_mode(
                self._device_id, "heat", self.device_data.get("heatingSetpoint")
            )
        elif hvac_mode == HVACMode.OFF:
            await self.coordinator.client.async_set_mode(self._device_id, "off")
        else:
            msg = f"Unsupported HVAC mode: {hvac_mode}"
            raise ValueError(msg)
        await self.coordinator.async_request_refresh()

    async def async_turn_on(self) -> None:
        """Turn the entity on (heat)."""
        await self.async_set_hvac_mode(HVACMode.HEAT)

    async def async_turn_off(self) -> None:
        """Turn the entity off."""
        await self.async_set_hvac_mode(HVACMode.OFF)
