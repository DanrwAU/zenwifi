"""Config flow for Zen WiFi Thermostat."""

from __future__ import annotations

import logging

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_create_clientsession

from .api import (
    ZenWifiApiClient,
    ZenWifiApiClientAuthenticationError,
    ZenWifiApiClientCommunicationError,
    ZenWifiApiClientError,
)
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class ZenWifiFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Zen WiFi Thermostat."""

    VERSION = 1

    async def async_step_user(
        self,
        user_input: dict | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Handle a flow initialized by the user."""
        _errors = {}
        if user_input is not None:
            try:
                await self._test_credentials(
                    username=user_input[CONF_USERNAME],
                    password=user_input[CONF_PASSWORD],
                )
            except ZenWifiApiClientAuthenticationError as exception:
                _LOGGER.warning(exception)
                _errors["base"] = "auth"
            except ZenWifiApiClientCommunicationError as exception:
                _LOGGER.exception("Communication error during authentication")
                _errors["base"] = "connection"
            except ZenWifiApiClientError as exception:
                _LOGGER.exception("Unexpected error during authentication")
                _errors["base"] = "unknown"
            else:
                # Use username as unique_id
                await self.async_set_unique_id(user_input[CONF_USERNAME])
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=f"Zen WiFi - {user_input[CONF_USERNAME]}",
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_USERNAME,
                        default=(user_input or {}).get(CONF_USERNAME, vol.UNDEFINED),
                    ): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.TEXT,
                        ),
                    ),
                    vol.Required(CONF_PASSWORD): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.PASSWORD,
                        ),
                    ),
                },
            ),
            errors=_errors,
        )

    async def _test_credentials(self, username: str, password: str) -> None:
        """Validate credentials."""
        client = ZenWifiApiClient(
            username=username,
            password=password,
            session=async_create_clientsession(self.hass),
        )
        # Test authentication and get user info
        await client.async_authenticate()
        await client.async_get_user_info()
