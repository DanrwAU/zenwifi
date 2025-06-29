"""Provides device conditions for Zen WiFi Thermostat."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.components.climate import DOMAIN as CLIMATE_DOMAIN
from homeassistant.components.device_automation import DEVICE_CONDITION_BASE_SCHEMA
from homeassistant.components.homeassistant import condition
from homeassistant.components.homeassistant.triggers import (
    numeric_state as numeric_state_trigger,
    state as state_trigger,
)
from homeassistant.const import (
    CONF_ABOVE,
    CONF_BELOW,
    CONF_DEVICE_ID,
    CONF_DOMAIN,
    CONF_ENTITY_ID,
    CONF_TYPE,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import config_validation as cv, entity_registry as er
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN

CONDITION_TYPES = {
    "is_off",
    "is_heating",
    "is_cooling",
}

CONDITION_SCHEMA = DEVICE_CONDITION_BASE_SCHEMA.extend(
    {
        vol.Required(CONF_ENTITY_ID): cv.entity_id,
        vol.Required(CONF_TYPE): vol.In(CONDITION_TYPES),
    }
)

TEMPERATURE_CONDITION_TYPES = {
    "current_temperature_above",
    "current_temperature_below",
}

TEMPERATURE_CONDITION_SCHEMA = DEVICE_CONDITION_BASE_SCHEMA.extend(
    {
        vol.Required(CONF_ENTITY_ID): cv.entity_id,
        vol.Required(CONF_TYPE): vol.In(TEMPERATURE_CONDITION_TYPES),
        vol.Required(vol.Any(CONF_ABOVE, CONF_BELOW)): vol.Coerce(float),
    }
)


async def async_get_conditions(
    hass: HomeAssistant, device_id: str
) -> list[dict[str, Any]]:
    """List device conditions for Zen WiFi Thermostat devices."""
    registry = er.async_get(hass)
    conditions = []

    # Get all entities for this device
    entries = [
        entry
        for entry in er.async_entries_for_device(registry, device_id)
        if entry.domain == CLIMATE_DOMAIN
    ]

    # Add conditions for each climate entity
    for entry in entries:
        # HVAC mode conditions
        for condition_type in CONDITION_TYPES:
            conditions.append(
                {
                    CONF_DEVICE_ID: device_id,
                    CONF_DOMAIN: DOMAIN,
                    CONF_ENTITY_ID: entry.entity_id,
                    CONF_TYPE: condition_type,
                }
            )

        # Temperature conditions
        conditions.extend(
            [
                {
                    CONF_DEVICE_ID: device_id,
                    CONF_DOMAIN: DOMAIN,
                    CONF_ENTITY_ID: entry.entity_id,
                    CONF_TYPE: "current_temperature_above",
                },
                {
                    CONF_DEVICE_ID: device_id,
                    CONF_DOMAIN: DOMAIN,
                    CONF_ENTITY_ID: entry.entity_id,
                    CONF_TYPE: "current_temperature_below",
                },
            ]
        )

    return conditions


@callback
def async_condition_from_config(
    hass: HomeAssistant, config: ConfigType
) -> condition.ConditionCheckerType:
    """Create a function to test a device condition."""
    condition_type = config[CONF_TYPE]
    entity_id = config[CONF_ENTITY_ID]

    if condition_type in CONDITION_TYPES:
        if condition_type == "is_off":
            state = "off"
        elif condition_type == "is_heating":
            state = "heat"
        elif condition_type == "is_cooling":
            state = "cool"

        return condition.state({
            "entity_id": entity_id,
            "state": state,
        })

    if condition_type in TEMPERATURE_CONDITION_TYPES:
        if condition_type == "current_temperature_above":
            return condition.numeric_state({
                "entity_id": entity_id,
                "above": config[CONF_ABOVE],
                "attribute": "current_temperature",
            })
        else:  # current_temperature_below
            return condition.numeric_state({
                "entity_id": entity_id,
                "below": config[CONF_BELOW],
                "attribute": "current_temperature",
            })

    return lambda hass, variables: False


async def async_get_condition_capabilities(
    hass: HomeAssistant, config: ConfigType
) -> dict[str, vol.Schema]:
    """List condition capabilities."""
    condition_type = config[CONF_TYPE]

    if condition_type in TEMPERATURE_CONDITION_TYPES:
        unit = "°C"  # We use Celsius
        return {
            "extra_fields": vol.Schema(
                {
                    vol.Required(
                        CONF_ABOVE if "above" in condition_type else CONF_BELOW
                    ): vol.Coerce(float),
                }
            )
        }

    return {}