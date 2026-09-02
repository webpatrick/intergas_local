from __future__ import annotations

from typing import Any

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, build_device_infos
from .coordinator import XtendDataUpdateCoordinator


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator: XtendDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    host = entry.data.get("host")
    _device_info, xtend_device_info, xtreme_device_info = build_device_infos(entry.entry_id, host)

    async_add_entities([
        DeltaTActiveBinarySensor(
            coordinator,
            entry.entry_id,
            unique_id_suffix="xtend_active_check",
            flow_key="629c",  # fSystem
            supply_key="62e7",  # tHpSupply
            return_key="6280",  # tHpReturn
            source="xtend_deltaT",
            device_info=xtend_device_info,
        ),
        DeltaTActiveBinarySensor(
            coordinator,
            entry.entry_id,
            unique_id_suffix="xtreme_active_check",
            flow_key="8e7f",  # boiler_ot_dhw_flowrate
            supply_key="625b",  # tBoilerSupply
            return_key="623c",  # tBoilerReturn
            source="xtreme_deltaT",
            device_info=xtreme_device_info,
        ),
    ])


def _flow_value(data: dict[str, object], key: str) -> float | None:
    if not isinstance(data, dict):
        return None
    raw = data.get(key)
    if raw is None:
        return None
    try:
        return float(str(raw)) / 100
    except (TypeError, ValueError):
        return None


class DeltaTActiveBinarySensor(CoordinatorEntity[XtendDataUpdateCoordinator], BinarySensorEntity):
    """Generic "is active" check: flow (if known) must be > 0 and supply - return > 0.5°C."""

    def __init__(
        self,
        coordinator: XtendDataUpdateCoordinator,
        entry_id: str,
        *,
        unique_id_suffix: str,
        flow_key: str,
        supply_key: str,
        return_key: str,
        source: str,
        device_info: dict | None = None,
    ) -> None:
        super().__init__(coordinator)
        self._attr_has_entity_name = True
        self._attr_translation_key = "is_active"
        self._attr_unique_id = f"{entry_id}_{unique_id_suffix}"
        self._attr_icon = "mdi:fire-off"
        self._attr_device_info = device_info
        self._flow_key = flow_key
        self._supply_key = supply_key
        self._return_key = return_key
        self._source = source

    @property
    def is_on(self) -> bool:
        data = self.coordinator.data
        if not isinstance(data, dict):
            return False

        flow = _flow_value(data, self._flow_key)
        if flow is not None and flow <= 0:
            return False

        try:
            supply = float(str(data.get(self._supply_key, 0))) / 100
            return_value = float(str(data.get(self._return_key, 0))) / 100
        except (TypeError, ValueError):
            return False

        return (supply - return_value) > 0.5

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        return {"source": self._source}

