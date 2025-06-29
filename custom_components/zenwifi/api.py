"""Zen WiFi Thermostat API Client."""

from __future__ import annotations

import logging
import socket
from typing import Any
from urllib.parse import urlencode

import aiohttp
import async_timeout

TIMEOUT = 10
API_HOST = "wifi.zenhq.com"
HTTP_UNAUTHORIZED = 401

_LOGGER = logging.getLogger(__name__)


class ZenWifiApiClientError(Exception):
    """Exception to indicate a general API error."""


class ZenWifiApiClientCommunicationError(ZenWifiApiClientError):
    """Exception to indicate a communication error."""


class ZenWifiApiClientAuthenticationError(ZenWifiApiClientError):
    """Exception to indicate an authentication error."""


def _verify_response_or_raise(response: aiohttp.ClientResponse) -> None:
    """Verify that the response is valid."""
    if response.status in (401, 403):
        msg = "Invalid credentials"
        raise ZenWifiApiClientAuthenticationError(
            msg,
        )
    response.raise_for_status()


class ZenWifiApiClient:
    """Zen WiFi Thermostat API Client."""

    def __init__(
        self,
        username: str,
        password: str,
        session: aiohttp.ClientSession,
    ) -> None:
        """Initialize the API client."""
        self._username = username
        self._password = password
        self._session = session
        self._access_token: str | None = None
        self._refresh_token: str | None = None
        self._consumer_id: str | None = None

    async def async_authenticate(self) -> dict[str, str]:
        """Authenticate with username and password."""
        data = {
            "grant_type": "password",
            "username": self._username,
            "password": self._password,
        }

        response = await self._api_wrapper(
            method="post",
            endpoint="/api/token",
            data=data,
            use_auth=False,
            content_type="application/x-www-form-urlencoded",
        )

        self._access_token = response.get("access_token")
        self._refresh_token = response.get("refresh_token")
        return response

    async def async_refresh_tokens(self) -> dict[str, str]:
        """Refresh the access token using refresh token."""
        if not self._refresh_token:
            msg = "No refresh token available"
            raise ZenWifiApiClientAuthenticationError(msg)

        data = {
            "grant_type": "refresh_token",
            "refresh_token": self._refresh_token,
        }

        response = await self._api_wrapper(
            method="post",
            endpoint="/api/token",
            data=data,
            use_auth=False,
            content_type="application/x-www-form-urlencoded",
        )

        self._access_token = response.get("access_token")
        self._refresh_token = response.get("refresh_token")
        return response

    async def async_get_user_info(self) -> dict[str, Any]:
        """Get user information including consumer ID."""
        response = await self._api_wrapper(
            method="get",
            endpoint="/api/v1/account/userinfo",
        )
        self._consumer_id = response.get("consumerId")
        return response

    async def async_get_devices(self) -> list[dict[str, Any]]:
        """Get list of devices."""
        if not self._consumer_id:
            await self.async_get_user_info()

        response = await self._api_wrapper(
            method="get",
            endpoint=f"/api/v1/consumer/device/getall?consumerId={self._consumer_id}",
        )
        return response.get("devices", [])

    async def async_get_device_status(self, device_id: str) -> dict[str, Any]:
        """Get device status."""
        return await self._api_wrapper(
            method="get",
            endpoint=f"/api/v1/device/status?deviceId={device_id}",
        )

    async def async_set_mode(
        self, device_id: str, mode: str, temperature: float | None = None
    ) -> Any:
        """Set thermostat mode and optionally temperature."""
        endpoint_map = {
            "heat": "/api/v1/device/heat",
            "emergency_heat": "/api/v1/device/emergency/heat",
            "cool": "/api/v1/device/cool",
            "off": "/api/v1/device/off",
        }

        if mode not in endpoint_map:
            msg = f"Invalid mode: {mode}"
            raise ValueError(msg)

        data = {"deviceid": device_id}
        if mode != "off" and temperature is not None:
            data["setpoint"] = temperature

        return await self._api_wrapper(
            method="post",
            endpoint=endpoint_map[mode],
            data=data,
        )

    def get_mode_string(self, mode_int: int) -> str:
        """Convert mode integer to string."""
        mode_map = {
            0: "heat",
            1: "heat",  # keeping for compatibility
            2: "cool",
            3: "off",
            4: "auto",
            5: "eco",
            6: "emergency_heat",
            7: "zen",
        }
        return mode_map.get(mode_int, "unknown")

    async def _api_wrapper(
        self,
        method: str,
        endpoint: str,
        data: dict[str, Any] | None = None,
        *,
        use_auth: bool = True,
        content_type: str = "application/json",
    ) -> Any:
        """Make API request with automatic token refresh on 401."""
        url = f"https://{API_HOST}{endpoint}"
        headers = {"Accept": "application/json"}

        if use_auth:
            if not self._access_token:
                await self.async_authenticate()
            headers["Authorization"] = f"Bearer {self._access_token}"

        if data:
            headers["Content-Type"] = content_type

        # Convert data based on content type
        request_data = None
        json_data = None
        if content_type == "application/x-www-form-urlencoded" and data:
            request_data = urlencode(data)
        elif content_type == "application/json" and data:
            json_data = data

        try:
            async with async_timeout.timeout(TIMEOUT):
                response = await self._session.request(
                    method=method,
                    url=url,
                    headers=headers,
                    data=request_data,
                    json=json_data,
                )

                if response.status == HTTP_UNAUTHORIZED and use_auth:
                    # Try to refresh token
                    await self.async_refresh_tokens()
                    # Retry request with new token
                    headers["Authorization"] = f"Bearer {self._access_token}"
                    response = await self._session.request(
                        method=method,
                        url=url,
                        headers=headers,
                        data=request_data,
                        json=json_data,
                    )

                _verify_response_or_raise(response)
                
                # Check if response has JSON content
                content_type = response.headers.get("content-type", "")
                if "application/json" in content_type:
                    return await response.json()
                else:
                    # For non-JSON responses (like empty success responses)
                    text = await response.text()
                    _LOGGER.debug(
                        "Non-JSON response from %s: content-type=%s, body=%s",
                        endpoint,
                        content_type,
                        text[:200],  # Log first 200 chars
                    )
                    # Return empty dict for successful non-JSON responses
                    return {}

        except TimeoutError as exception:
            msg = f"Timeout error fetching information - {exception}"
            raise ZenWifiApiClientCommunicationError(
                msg,
            ) from exception
        except (aiohttp.ClientError, socket.gaierror) as exception:
            msg = f"Error fetching information - {exception}"
            raise ZenWifiApiClientCommunicationError(
                msg,
            ) from exception
        except ZenWifiApiClientError:
            raise
        except Exception as exception:
            msg = f"Something really wrong happened! - {exception}"
            raise ZenWifiApiClientError(
                msg,
            ) from exception

