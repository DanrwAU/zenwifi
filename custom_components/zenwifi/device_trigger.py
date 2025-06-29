"""Provides device triggers for Zen WiFi Thermostat."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.components.climate import DOMAIN as CLIMATE_DOMAIN
from homeassistant.components.device_automation import DEVICE_TRIGGER_BASE_SCHEMA
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
    CONF_FOR,
    CONF_TYPE,
)
from homeassistant.core import CALLBACK_TYPE, HomeAssistant
from homeassistant.helpers import config_validation as cv, entity_registry as er
from homeassistant.helpers.trigger import TriggerActionType, TriggerInfo
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN

TRIGGER_TYPES = {
    "turned_off",
    "turned_on",
    "changed_to_heat",
    "changed_to_cool",
}

TEMPERATURE_TRIGGER_TYPES = {
    "current_temperature_above",
    "current_temperature_below",
}

TRIGGER_SCHEMA = DEVICE_TRIGGER_BASE_SCHEMA.extend(
    {
        vol.Required(CONF_ENTITY_ID): cv.entity_id,
        vol.Required(CONF_TYPE): vol.In(TRIGGER_TYPES | TEMPERATURE_TRIGGER_TYPES),
        vol.Optional(CONF_FOR): cv.positive_time_period_dict,
        vol.Optional(CONF_ABOVE): vol.Coerce(float),
        vol.Optional(CONF_BELOW): vol.Coerce(float),
    }
)


async def async_get_triggers(
    hass: HomeAssistant, device_id: str
) -> list[dict[str, Any]]:
    """List device triggers for Zen WiFi Thermostat devices."""
    registry = er.async_get(hass)
    triggers = []

    # Get all entities for this device
    entries = [
        entry
        for entry in er.async_entries_for_device(registry, device_id)
        if entry.domain == CLIMATE_DOMAIN
    ]

    # Add triggers for each climate entity
    for entry in entries:
        # State change triggers
        for trigger_type in TRIGGER_TYPES:
            triggers.append(
                {
                    CONF_DEVICE_ID: device_id,
                    CONF_DOMAIN: DOMAIN,
                    CONF_ENTITY_ID: entry.entity_id,
                    CONF_TYPE: trigger_type,
                }
            )

        # Temperature triggers
        for trigger_type in TEMPERATURE_TRIGGER_TYPES:
            triggers.append(
                {
                    CONF_DEVICE_ID: device_id,
                    CONF_DOMAIN: DOMAIN,
                    CONF_ENTITY_ID: entry.entity_id,
                    CONF_TYPE: trigger_type,
                }
            )

    return triggers


async def async_attach_trigger(
    hass: HomeAssistant,
    config: ConfigType,
    action: TriggerActionType,
    trigger_info: TriggerInfo,
) -> CALLBACK_TYPE:
    """Attach a trigger."""
    trigger_type = config[CONF_TYPE]
    entity_id = config[CONF_ENTITY_ID]

    if trigger_type == "turned_off":
        state_config = {
            "platform": "state",
            "entity_id": entity_id,
            "to": "off",
        }
    elif trigger_type == "turned_on":
        state_config = {
            "platform": "state",
            "entity_id": entity_id,
            "from": "off",
        }
    elif trigger_type == "changed_to_heat":
        state_config = {
            "platform": "state",
            "entity_id": entity_id,
            "to": "heat",
        }
    elif trigger_type == "changed_to_cool":
        state_config = {
            "platform": "state",
            "entity_id": entity_id,
            "to": "cool",
        }
    elif trigger_type == "current_temperature_above":
        state_config = {
            "platform": "numeric_state",
            "entity_id": entity_id,
            "attribute": "current_temperature",
            "above": config[CONF_ABOVE],
        }
    elif trigger_type == "current_temperature_below":
        state_config = {
            "platform": "numeric_state",
            "entity_id": entity_id,
            "attribute": "current_temperature",
            "below": config[CONF_BELOW],
        }
    else:
        return lambda: None

    if CONF_FOR in config:
        state_config[CONF_FOR] = config[CONF_FOR]

    if trigger_type in ["current_temperature_above", "current_temperature_below"]:
        state_config = await numeric_state_trigger.async_validate_trigger_config(hass, state_config)
        return await numeric_state_trigger.async_attach_trigger(
            hass, state_config, action, trigger_info, platform_type="device"
        )
    else:
        state_config = await state_trigger.async_validate_trigger_config(hass, state_config)
        return await state_trigger.async_attach_trigger(
            hass, state_config, action, trigger_info, platform_type="device"
        )


async def async_get_trigger_capabilities(
    hass: HomeAssistant, config: ConfigType
) -> dict[str, vol.Schema]:
    """List trigger capabilities."""
    trigger_type = config[CONF_TYPE]

    if trigger_type in TEMPERATURE_TRIGGER_TYPES:
        return {
            "extra_fields": vol.Schema(
                {
                    vol.Required(
                        CONF_ABOVE if "above" in trigger_type else CONF_BELOW
                    ): vol.Coerce(float),
                    vol.Optional(CONF_FOR): cv.positive_time_period_dict,
                }
            )
        }

    if trigger_type in TRIGGER_TYPES:
        return {
            "extra_fields": vol.Schema(
                {vol.Optional(CONF_FOR): cv.positive_time_period_dict}
            )
        }

    return {}