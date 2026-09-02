from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv

from .const import DOMAIN, DEFAULT_SCAN_INTERVAL, build_resource_url
from .coordinator import XtendDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    host = entry.data.get("host")
    resource = entry.data.get("resource")
    if not resource and host:
        resource = build_resource_url(host)
    if not resource:
        raise ValueError("No host or resource configured for Xtend Local")

    scan_interval = entry.options.get("scan_interval", entry.data.get("scan_interval", DEFAULT_SCAN_INTERVAL))
    coordinator = XtendDataUpdateCoordinator(hass, resource, scan_interval)

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, ["sensor", "binary_sensor"])

    # Listen for option changes (scan_interval updates)
    entry.async_on_unload(entry.add_update_listener(async_update_listener))

    return True


async def async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    coordinator: XtendDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    scan_interval = entry.options.get("scan_interval", DEFAULT_SCAN_INTERVAL)
    coordinator.update_interval = timedelta(seconds=scan_interval)
    _LOGGER.info("Updated scan_interval to %s seconds", scan_interval)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, ["sensor", "binary_sensor"])
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
