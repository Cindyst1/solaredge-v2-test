"""Configure one SolarEdge site using a manually pasted OAuth callback."""

from datetime import date, datetime
import secrets
from urllib.parse import parse_qs, urlencode, urlsplit
from uuid import UUID

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import TextSelector, TextSelectorConfig, TextSelectorType
from homeassistant.util import dt as dt_util

from .api import (
    ApiError, AuthError, CALLBACK, DOMAIN, PermissionError, get_devices,
    get_energy, get_tokens,
)


def password_field():
    """Use a masked input for credentials and authorization codes."""
    return TextSelector(TextSelectorConfig(type=TextSelectorType.PASSWORD))


class SolarEdgeV2TestFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Connect a SolarEdge Monitoring API V2 application."""

    VERSION = 1

    async def async_step_reauth(self, entry_data):
        """Request a fresh authorization for the existing site."""
        return await self.async_step_user()

    async def async_step_reconfigure(self, user_input=None):
        """Let an existing installation opt into device inventory."""
        return await self.async_step_user(user_input)

    def _existing_entry(self):
        if self.source == config_entries.SOURCE_REAUTH:
            return self._get_reauth_entry()
        if self.source == config_entries.SOURCE_RECONFIGURE:
            return self._get_reconfigure_entry()
        return None

    async def async_step_user(self, user_input=None):
        """Collect the application's credentials and production start."""
        errors = {}
        entry = self._existing_entry()
        existing = entry.data if entry else {}
        if user_input is not None:
            try:
                client_id = str(UUID(user_input["client_id"].strip()))
                start = date.fromisoformat(user_input["production_start"])
                if start > dt_util.now().date() or not user_input["client_secret"].strip():
                    raise ValueError
            except ValueError:
                errors["base"] = "invalid_input"
            else:
                self.credentials = {
                    "client_id": client_id,
                    "client_secret": user_input["client_secret"].strip(),
                    "production_start": datetime.combine(
                        start, datetime.min.time(), tzinfo=dt_util.get_default_time_zone()
                    ).isoformat(),
                    "start_date": start.isoformat(),
                    "device_inventory": user_input.get("device_inventory", False),
                }
                self.external_id = secrets.token_hex(16)
                params = urlencode({
                    "client_id": client_id,
                    "scope": "SITE_DATA DEVICE_DATA" if self.credentials["device_inventory"] else "SITE_DATA",
                    "redirect_uri": CALLBACK, "access_duration": 1,
                    "external_id": self.external_id,
                })
                self.authorize_url = f"https://connect.solaredge.com/authorize?{params}"
                return await self.async_step_callback()

        return self.async_show_form(step_id="user", errors=errors, data_schema=vol.Schema({
            vol.Required("client_id", default=existing.get("client_id", "")): str,
            vol.Required("client_secret"): password_field(),
            vol.Required("production_start", default=existing.get("start_date", "")): str,
            vol.Optional("device_inventory", default=existing.get("device_inventory", False)): bool,
        }))

    async def async_step_callback(self, user_input=None):
        """Validate the callback, exchange the code and verify the reading."""
        errors = {}
        if user_input is not None:
            try:
                url = urlsplit(user_input["callback"].strip())
                query = parse_qs(url.query)
                site_id, = query["site_id"]
                code, = query["code"]
                if (
                    url._replace(query="", fragment="").geturl() != CALLBACK
                    or url.fragment
                    or query.get("external_id") != [self.external_id]
                    or not site_id.isascii() or not site_id.isdecimal()
                ):
                    raise ValueError
            except (KeyError, ValueError):
                errors["base"] = "invalid_callback"
            else:
                await self.async_set_unique_id(site_id)
                entry = self._existing_entry()
                if entry:
                    self._abort_if_unique_id_mismatch(reason="wrong_site")
                else:
                    self._abort_if_unique_id_configured()
                session = async_get_clientsession(self.hass)
                try:
                    tokens = await get_tokens(
                        session, self.credentials, "authorization_code", code=code
                    )
                    data = {**self.credentials, **tokens, "site_id": site_id}
                    await get_energy(session, data)
                    if data["device_inventory"]:
                        await get_devices(session, data)
                except AuthError:
                    return self.async_abort(reason="authorization_failed")
                except PermissionError:
                    return self.async_abort(reason="insufficient_permissions")
                except ApiError:
                    return self.async_abort(reason="cannot_connect")
                if entry:
                    return self.async_update_reload_and_abort(entry, data=data)
                return self.async_create_entry(title="SolarEdge V2 Test", data=data)

        return self.async_show_form(
            step_id="callback", errors=errors,
            description_placeholders={"authorize_url": self.authorize_url},
            data_schema=vol.Schema({vol.Required("callback"): password_field()}),
        )
