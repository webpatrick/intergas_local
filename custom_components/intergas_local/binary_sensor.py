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
            flow_key=None,
            supply_key="625b",  # tBoilerSupply
            return_key="623c",  # tBoilerReturn
            source="xtreme_deltaT",
            device_info=xtreme_device_info,
        ),
    ])


def _stats_dict(data: dict[str, object]) -> dict[str, object]:
    if not isinstance(data, dict):
        return {}
    stats = data.get("stats")
    if isinstance(stats, dict):
        return stats
    return data


def _scaled_float_value(data: dict[str, object], key: str, divisor: float = 100) -> float | None:
    stats = _stats_dict(data)
    raw = stats.get(key)
    if raw is None:
        return None
    if isinstance(raw, str) and not raw.strip():
        return None
    try:
        return float(str(raw)) / divisor
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
        flow_key: str | None,
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

    def _active_debug_values(self) -> dict[str, Any]:
        data = self.coordinator.data
        if not isinstance(data, dict):
            return {
                "source": self._source,
                "has_data": False,
            }

        flow = _scaled_float_value(data, self._flow_key) if self._flow_key else None
        supply = _scaled_float_value(data, self._supply_key)
        return_value = _scaled_float_value(data, self._return_key)
        delta_t = None if supply is None or return_value is None else round(supply - return_value, 2)

        has_temps = supply is not None and return_value is not None
        flow_ok = True if flow is None else flow > 0
        delta_ok = bool(delta_t is not None and delta_t > 0.5)

        return {
            "source": self._source,
            "has_data": True,
            "flow_l_min": flow,
            "supply_c": supply,
            "return_c": return_value,
            "delta_t_c": delta_t,
            "delta_t_threshold_c": 0.5,
            "flow_required": self._flow_key is not None,
            "flow_ok": flow_ok,
            "delta_t_ok": delta_ok,
            "has_temperatures": has_temps,
            "is_active_evaluated": has_temps and flow_ok and delta_ok,
        }

    @property
    def is_on(self) -> bool:
        return bool(self._active_debug_values().get("is_active_evaluated", False))

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        return self._active_debug_values()
