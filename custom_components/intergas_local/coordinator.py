from __future__ import annotations

import logging
import time
from datetime import datetime, timedelta, timezone
from typing import Any

import requests

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DEFAULT_SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)

_RETRY_ATTEMPTS = 3
_RETRY_DELAY = 2  # seconds between retries


class XtendDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    def __init__(self, hass: HomeAssistant, resource: str, scan_interval: int = DEFAULT_SCAN_INTERVAL) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name="intergas_local",
            update_interval=timedelta(seconds=scan_interval),
        )
        self.resource = resource
        self.last_update_timestamp: datetime | None = None
        self._consecutive_failures: int = 0

    async def _async_update_data(self) -> dict[str, Any]:
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

        def _fetch_with_retry() -> dict[str, Any]:
            last_err: Exception | None = None
            for attempt in range(1, _RETRY_ATTEMPTS + 1):
                try:
                    return _fetch()
                except Exception as err:
                    last_err = err
                    if attempt < _RETRY_ATTEMPTS:
                        _LOGGER.debug(
                            "Xtend fetch attempt %d/%d failed (%s), retrying in %ds",
                            attempt, _RETRY_ATTEMPTS, err, _RETRY_DELAY,
                        )
                        time.sleep(_RETRY_DELAY)
            raise last_err  # type: ignore[misc]

        try:
            data = await self.hass.async_add_executor_job(_fetch_with_retry)
            if not isinstance(data, dict):
                _LOGGER.warning("Xtend coordinator received non-dict payload: %s (%s)", type(data).__name__, data)
            self._consecutive_failures = 0
            self.last_update_timestamp = datetime.now(timezone.utc)
            return data
        except Exception as err:
            self._consecutive_failures += 1
            # Only log a full traceback on the first failure; subsequent ones use a shorter warning
            # to avoid flooding the log during prolonged connectivity issues.
            if self._consecutive_failures == 1:
                _LOGGER.exception("Xtend fetch failed for %s", self.resource)
            else:
                _LOGGER.warning(
                    "Xtend fetch failed for %s (consecutive failures: %d): %s",
                    self.resource, self._consecutive_failures, err,
                )
            raise UpdateFailed(f"Unable to fetch Xtend data: {err}") from err
