"""Read SolarEdge V2 production data."""

from datetime import UTC, datetime
import math

from aiohttp import ClientError, ClientTimeout

DOMAIN = "solaredge_v2_test"
BASE = "https://monitoringapi.solaredge.com/v2"
CALLBACK = "http://localhost:8080/oauth/callback"


class ApiError(Exception):
    """The service did not return usable data."""


class AuthError(ApiError):
    """SolarEdge rejected the credentials or grant."""


async def request(session, method, path, *, token=None, **kwargs):
    """Make a bounded request without logging credentials or response bodies."""
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    try:
        async with session.request(
            method, BASE + path, headers=headers, allow_redirects=False,
            timeout=ClientTimeout(total=30), **kwargs,
        ) as response:
            if response.status in {401, 403} or (
                path == "/oauth2/token" and response.status == 400
            ):
                raise AuthError(f"SolarEdge returned HTTP {response.status}")
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


async def get_energy(session, data):
    """Read one total in Wh over the site's production lifetime."""
    series = await request(
        session, "GET", f"/sites/{data['site_id']}/energy",
        token=data["access_token"], params={
            "from": data["production_start"],
            "to": datetime.now(UTC).isoformat(),
            "resolution": "TOTAL",
            "unit": "WH",
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
