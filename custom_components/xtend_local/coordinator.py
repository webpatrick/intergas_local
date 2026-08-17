from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

import requests

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DEFAULT_SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)


class XtendDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    def __init__(self, hass: HomeAssistant, resource: str, scan_interval: int = DEFAULT_SCAN_INTERVAL) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name="xtend_local",
            update_interval=timedelta(seconds=scan_interval),
        )
        self.resource = resource
        self.last_update_timestamp: datetime | None = None

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            def _fetch() -> dict[str, Any]:
                _LOGGER.debug("Fetching Xtend data from %s", self.resource)
                resp = requests.get(self.resource, timeout=10)
                _LOGGER.debug(
                    "Xtend HTTP status=%s length=%s content-type=%s",
                    resp.status_code,
                    len(resp.text),
                    resp.headers.get("Content-Type"),
                )
                resp.raise_for_status()
                try:
                    payload = resp.json()
                    if isinstance(payload, dict):
                        _LOGGER.debug("Xtend JSON keys total: %s", len(payload.keys()))
                        _LOGGER.debug("Xtend JSON keys: %s", sorted(payload.keys()))
                        # Check for diagnostic fields specifically
                        diagnostic_fields = ['4133', '47e0', '77dd', '6a53', '6a8e', '6ac5', '7160', '71a7', '7940', '7e2c',
                                           '8e1e', '8ecc', '8e00', '8e18', '8e37', '8ef9']
                        missing_diag = [f for f in diagnostic_fields if f not in payload]
                        if missing_diag:
                            _LOGGER.debug("Missing diagnostic fields: %s", missing_diag)
                    else:
                        _LOGGER.debug("Xtend payload type=%s preview=%s", type(payload).__name__, str(payload)[:500])
                    return payload
                except ValueError:
                    preview = resp.text[:500].replace("\n", " ")
                    _LOGGER.debug("Xtend non-JSON response preview: %s", preview)
                    return {"raw": resp.text}

            data = await self.hass.async_add_executor_job(_fetch)
            if not isinstance(data, dict):
                _LOGGER.warning("Xtend coordinator received non-dict payload: %s (%s)", type(data).__name__, data)
            # Update the timestamp on successful fetch
            self.last_update_timestamp = datetime.now(timezone.utc)
            return data
        except Exception as err:
            _LOGGER.exception("Xtend fetch failed for %s", self.resource)
            raise UpdateFailed(f"Unable to fetch Xtend data: {err}") from err
