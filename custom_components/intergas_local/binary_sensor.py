from __future__ import annotations

from typing import Any

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import XtendDataUpdateCoordinator


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator: XtendDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    host = entry.data.get("host")
    
    # Parent device - the integration itself (API status)
    device_info = {
        "identifiers": {(DOMAIN, entry.entry_id)},
        "name": "Intergas API",
        "manufacturer": "Intergas",
        "model": "Local",
    }
    if host:
        device_info["connections"] = {("ip", host)}

    # Xtend (heatpump) device
    xtend_device_info = {
        "identifiers": {(DOMAIN, f"{entry.entry_id}_xtend")},
        "name": "Intergas Xtend",
        "manufacturer": "Intergas",
        "model": "Xtend",
        "via_device": (DOMAIN, entry.entry_id),
    }

    # Xtreme (boiler) device
    xtreme_device_info = {
        "identifiers": {(DOMAIN, f"{entry.entry_id}_xtreme")},
        "name": "Intergas Xtreme",
        "manufacturer": "Intergas",
        "model": "Xtreme",
        "via_device": (DOMAIN, entry.entry_id),
    }

    async_add_entities([
        XtendActiveBinarySensor(coordinator, entry.entry_id, xtend_device_info),
        XtremeActiveBinarySensor(coordinator, entry.entry_id, xtreme_device_info)
    ])


class XtendActiveBinarySensor(CoordinatorEntity[XtendDataUpdateCoordinator], BinarySensorEntity):
    """Xtend (Heatpump) active check: supply - return > 0.5°C"""
    
    def __init__(self, coordinator: XtendDataUpdateCoordinator, entry_id: str, device_info: dict | None = None) -> None:
        super().__init__(coordinator)
        self._attr_name = "Is Active"
        self._attr_unique_id = f"{entry_id}_xtend_active_check"
        self._attr_icon = "mdi:fire-off"
        self._attr_device_info = device_info

    @property
    def is_on(self) -> bool:
        if not isinstance(self.coordinator.data, dict):
            return False

        try:
            # 62e7 = tHpSupply, 6280 = tHpReturn
            supply = float(str(self.coordinator.data.get("62e7", 0))) / 100
            return_value = float(str(self.coordinator.data.get("6280", 0))) / 100
        except (TypeError, ValueError):
            return False

        return (supply - return_value) > 0.5

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        return {"source": "xtend_deltaT"}


class XtremeActiveBinarySensor(CoordinatorEntity[XtendDataUpdateCoordinator], BinarySensorEntity):
    """Xtreme (Boiler) active check: supply - return > 0.5°C"""
    
    def __init__(self, coordinator: XtendDataUpdateCoordinator, entry_id: str, device_info: dict | None = None) -> None:
        super().__init__(coordinator)
        self._attr_name = "Is Active"
        self._attr_unique_id = f"{entry_id}_xtreme_active_check"
        self._attr_icon = "mdi:fire-off"
        self._attr_device_info = device_info

    @property
    def is_on(self) -> bool:
        if not isinstance(self.coordinator.data, dict):
            return False

        try:
            # 625b = tBoilerSupply, 623c = tBoilerReturn
            supply = float(str(self.coordinator.data.get("625b", 0))) / 100
            return_value = float(str(self.coordinator.data.get("623c", 0))) / 100
        except (TypeError, ValueError):
            return False

        return (supply - return_value) > 0.5

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        return {"source": "xtreme_deltaT"}


