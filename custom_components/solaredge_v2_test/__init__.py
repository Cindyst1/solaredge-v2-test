"""Set up and poll the SolarEdge V2 test sensor."""

from datetime import UTC, datetime, timedelta

from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
import logging

from .api import ApiError, AuthError, get_energy, get_tokens

LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry):
    """Start a coordinator for the test entry."""
    session = async_get_clientsession(hass)

    async def update():
        data = entry.data
        try:
            if datetime.now(UTC).timestamp() >= data["expires_at"] - 60:
                tokens = await get_tokens(
                    session, data, "refresh_token", refresh_token=data["refresh_token"]
                )
                data = {**data, **tokens}
                hass.config_entries.async_update_entry(entry, data=data)
            return await get_energy(session, data)
        except AuthError:
            raise ConfigEntryAuthFailed("SolarEdge authorization expired or was rejected") from None
        except ApiError as err:
            raise UpdateFailed(str(err)) from None

    coordinator = DataUpdateCoordinator(
        hass, LOGGER, config_entry=entry, name="SolarEdge V2 Test",
        update_method=update, update_interval=timedelta(hours=1),
    )
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, ["sensor"])
    return True


async def async_unload_entry(hass, entry):
    """Unload the test sensor."""
    return await hass.config_entries.async_unload_platforms(entry, ["sensor"])
