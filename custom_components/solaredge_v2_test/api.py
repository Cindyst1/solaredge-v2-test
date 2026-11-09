"""Read SolarEdge V2 production data."""

from datetime import UTC, datetime, timedelta
import math

from aiohttp import ClientError, ClientTimeout

DOMAIN = "solaredge_v2_test"
BASE = "https://monitoringapi.solaredge.com/v2"
CALLBACK = "http://localhost:8080/oauth/callback"


class ApiError(Exception):
    """The service did not return usable data."""


class AuthError(ApiError):
    """SolarEdge rejected the credentials or grant."""


class PermissionError(ApiError):
    """The grant or plan does not allow a particular endpoint."""


async def request(session, method, path, *, token=None, **kwargs):
    """Make a bounded request without logging credentials or response bodies."""
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    try:
        async with session.request(
            method, BASE + path, headers=headers, allow_redirects=False,
            timeout=ClientTimeout(total=30), **kwargs,
        ) as response:
            if response.status == 401 or (
                path == "/oauth2/token" and response.status == 400
            ):
                raise AuthError(f"SolarEdge returned HTTP {response.status}")
            if response.status == 403:
                raise PermissionError("SolarEdge returned HTTP 403")
            if response.status != 200:
                raise ApiError(f"SolarEdge returned HTTP {response.status}")
            result = await response.json()
    except (ClientError, TimeoutError, ValueError):
        raise ApiError("SolarEdge did not return a usable response") from None
    if not isinstance(result, dict):
        raise ApiError("Unexpected SolarEdge response")
    return result


async def get_tokens(session, credentials, grant_type, **grant):
    """Exchange an authorization code or rotate a refresh token."""
    data = await request(session, "POST", "/oauth2/token", json={
        "grant_type": grant_type, "client_id": credentials["client_id"],
        "client_secret": credentials["client_secret"], **grant,
    })
    access = data.get("access_token")
    refresh = data.get("refresh_token")
    if not isinstance(access, str) or not access or not isinstance(refresh, str) or not refresh:
        raise ApiError("SolarEdge did not return both OAuth tokens")
    try:
        expires_in = int(data["expires_in"])
        if expires_in <= 0:
            raise ValueError
    except (KeyError, TypeError, ValueError, OverflowError):
        raise ApiError("Invalid OAuth token expiry") from None
    return {
        "access_token": access, "refresh_token": refresh,
        "expires_at": datetime.now(UTC).timestamp() + expires_in,
    }


async def get_site_data(session, data, path, **params):
    """Read a site endpoint using the existing grant."""
    return await request(
        session, "GET", f"/sites/{data['site_id']}{path}",
        token=data["access_token"], params=params,
    )


def measurement(value, unit, factors):
    """Normalize a numeric measurement without substituting zero for missing data."""
    if type(value) in (int, float) and math.isfinite(value) and value >= 0:
        if isinstance(unit, str) and unit.upper() in factors:
            return value * factors[unit.upper()]
    return None


async def get_energy(session, data, start=None):
    """Read one production total in Wh."""
    series = await get_site_data(
        session, data, "/energy", **{
            "from": start or data["production_start"],
            "to": datetime.now(UTC).isoformat(), "resolution": "TOTAL", "unit": "WH",
        },
    )
    try:
        if series["unit"].upper() != "WH" or series["resolution"].upper() != "TOTAL":
            raise ValueError
        values = [point["value"] for point in series["values"] if point["value"] is not None]
        value, = values
        if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
            raise ValueError
    except (KeyError, TypeError, ValueError, AttributeError, OverflowError):
        raise ApiError("SolarEdge returned no valid lifetime total in Wh") from None
    return value


async def get_current_power(session, data):
    """Read the latest available quarter-hour sample in W."""
    now = datetime.now(UTC)
    series = await get_site_data(session, data, "/power", **{
        "from": (now - timedelta(hours=2)).isoformat(), "to": now.isoformat(),
        "resolution": "QUARTER_HOUR", "unit": "W",
    })
    samples = {}
    for point in series.get("values") or []:
        try:
            stamp = datetime.fromisoformat(point["timestamp"])
        except (KeyError, TypeError, ValueError):
            continue
        value = measurement(point.get("value"), series.get("unit"), {"W": 1, "KW": 1000})
        if stamp.tzinfo is not None and stamp <= now and value is not None:
            samples[stamp] = value
    return samples[max(samples)] if samples else None


async def get_daily_balance(session, data, start):
    """Read today's optional consumption and export energy in Wh."""
    overview = await get_site_data(session, data, "/overview", **{
        "from": start, "to": datetime.now(UTC).isoformat(),
    })
    production = overview.get("production") or {}
    consumption = overview.get("consumption") or {}
    fields = {
        "exported_energy": (production, "toGrid"),
        "imported_energy": (consumption, "fromGrid"),
        "consumed_energy": (consumption, "total"),
        "self_consumed_energy": (production, "toSelfConsumption"),
    }
    return {
        key: measurement(group.get(field), group.get("unit"), {"WH": 1, "KWH": 1000, "MWH": 1000000})
        for key, (group, field) in fields.items() if isinstance(group, dict)
    }


async def get_site_status(session, data):
    """Read the site's monitoring status."""
    response = await get_site_data(session, data, "")
    site = response.get("site", response)
    status = site.get("status") or site.get("state") if isinstance(site, dict) else None
    return status if isinstance(status, str) and status else None
