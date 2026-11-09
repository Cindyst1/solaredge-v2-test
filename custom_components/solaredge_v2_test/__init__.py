"""Set up and poll the SolarEdge V2 test sensor."""

import asyncio
from datetime import UTC, datetime, timedelta
import logging

from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .api import (
    ApiError, AuthError, get_current_power, get_daily_balance,
    get_energy, get_site_status, get_tokens,
)

LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry):
    """Start a coordinator for the test entry."""
    session = async_get_clientsession(hass)
    slow_data = {}
    next_slow_update = datetime.min.replace(tzinfo=UTC)

    async def optional(reading):
        try:
            return await reading
        except AuthError:
            raise
        except ApiError as err:
            LOGGER.debug("Optional SolarEdge reading unavailable: %s", err)
            return None

    async def update():
        nonlocal slow_data, next_slow_update
        data = entry.data
        try:
            if datetime.now(UTC).timestamp() >= data["expires_at"] - 60:
                tokens = await get_tokens(
                    session, data, "refresh_token", refresh_token=data["refresh_token"]
                )
                data = {**data, **tokens}
                hass.config_entries.async_update_entry(entry, data=data)
            lifetime = await get_energy(session, data)
            power = await optional(get_current_power(session, data))
            now = dt_util.now()
            today = now.replace(hour=0, minute=0, second=0, microsecond=0)
            if now >= next_slow_update:
                month = today.replace(day=1)
                year = month.replace(month=1)
                dates = {"energy_today": today, "energy_this_month": month, "energy_this_year": year}
                totals = await asyncio.gather(*(
                    optional(get_energy(session, data, start.isoformat()))
                    for start in dates.values()
                ))
                balance = await optional(get_daily_balance(session, data, today.isoformat()))
                status = await optional(get_site_status(session, data))
                slow_data = {**dict(zip(dates, totals, strict=True)), **(balance or {}), "site_status": status}
                next_slow_update = min(datetime.now(UTC) + timedelta(hours=6), today + timedelta(days=1))
            return {**slow_data, "lifetime_energy": lifetime, "current_power": power}
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
