from __future__ import annotations

import logging
from typing import Any, Callable

from homeassistant.components.sensor import (
    EntityCategory,
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    ERROR_CODES,
    HEAT_DEMAND_STATUS,
    HEAT_PUMP_MODES,
    LOCKOUT_CODES,
    NOTIFICATION_CODES,
    SYSTEM_STATUS,
    WORKING_MODES,
    XTREME_BURNER_STATUS,
    build_device_infos,
)
from .coordinator import XtendDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


class XtendSensorSpec:
    """Static description of a single Xtend/Xtreme sensor entity."""

    def __init__(
        self,
        key: str,
        name: str,
        value_fn: Callable[[dict[str, Any]], Any],
        *,
        translation_key: str,
        unit: str | None = None,
        device_class: str | None = None,
        state_class: str | None = None,
        icon: str | None = None,
        entity_category: str | None = None,
        is_xtreme: bool = False,
    ) -> None:
        self.key = key
        self.name = name
        self.value_fn = value_fn
        self.translation_key = translation_key
        self.unit = unit
        self.device_class = device_class
        self.state_class = state_class
        self.icon = icon
        self.entity_category = entity_category
        self.is_xtreme = is_xtreme


def _stats_dict(data: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(data, dict):
        return {}
    stats = data.get("stats")
    if isinstance(stats, dict):
        return stats
    return data


def _as_raw_value(data: dict[str, Any], key: str, default: Any = None) -> Any:
    stats = _stats_dict(data)
    if not isinstance(stats, dict):
        return default
    value = stats.get(key)
    if value is None:
        return default
    if isinstance(value, str):
        value = value.strip()
        if not value:
            return default
    return value


def _as_int(data: dict[str, Any], key: str, default: int | None = None, divisor: int = 1) -> float | int | None:
    raw = _as_raw_value(data, key)
    if raw is None:
        return default
    try:
        value = int(str(raw))
    except (TypeError, ValueError):
        return default
    return value / divisor if divisor != 1 else value


def _as_float(data: dict[str, Any], key: str, default: float | None = None, divisor: float = 1.0) -> float | None:
    raw = _as_raw_value(data, key)
    if raw is None:
        return default
    try:
        return float(str(raw)) / divisor
    except (TypeError, ValueError):
        return default


def _mode_name(data: dict[str, Any], key: str, lookup: dict[int, str]) -> str | None:
    raw = _as_int(data, key, default=-1)
    if raw is None or raw == -1:
        return None
    return lookup.get(int(raw), f"Unknown ({raw})")


SENSOR_DEFINITIONS: list[XtendSensorSpec] = [
    XtendSensorSpec("4133", "xtend_errorCode", lambda d: _mode_name(d, "4133", ERROR_CODES), icon="mdi:alert-circle-outline", entity_category=EntityCategory.DIAGNOSTIC, translation_key="error_code"),
    XtendSensorSpec("47e0", "xtend_software_version", lambda d: _as_raw_value(d, "47e0"), entity_category=EntityCategory.DIAGNOSTIC, translation_key="software_version"),
    XtendSensorSpec("503e", "xtend_currentHpPowerThermal", lambda d: _as_float(d, "503e", divisor=1000), unit="kW", device_class=None, state_class=SensorStateClass.MEASUREMENT, icon="mdi:thermometer-lines", translation_key="current_heat_pump_power_thermal"),
    XtendSensorSpec("5041", "xtend_currentCop", lambda d: _as_float(d, "5041", divisor=10), unit="thermal/kWh", state_class=SensorStateClass.MEASUREMENT, icon="mdi:gauge", translation_key="current_cop"),
    XtendSensorSpec("5077", "xtend_currentPowerThermal", lambda d: _as_float(d, "5077", divisor=1000), unit="kW", state_class=SensorStateClass.MEASUREMENT, icon="mdi:thermometer-lines", translation_key="current_power_thermal"),
    XtendSensorSpec("5088", "xtend_currentBoilerPowerThermal", lambda d: _as_float(d, "5088", divisor=1000), unit="kW", state_class=SensorStateClass.MEASUREMENT, icon="mdi:thermometer-lines", translation_key="current_boiler_power_thermal"),
    XtendSensorSpec("50f2", "xtend_currentPowerElectric", lambda d: _as_int(d, "50f2"), unit="W", state_class=SensorStateClass.MEASUREMENT, icon="mdi:power-plug-outline", translation_key="current_power_electric"),
    XtendSensorSpec("777d", "xtend_heatpumpMode", lambda d: _mode_name(d, "777d", HEAT_PUMP_MODES), icon="mdi:fire", translation_key="heat_pump_mode"),
    XtendSensorSpec("79b3", "xtend_roomtemperature_1", lambda d: _as_float(d, "79b3", divisor=100), unit="°C", device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT, icon="mdi:home-thermometer-outline", translation_key="room_temperature"),
    XtendSensorSpec("6280", "xtend_tHpReturn", lambda d: _as_float(d, "6280", divisor=100), unit="°C", device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT, icon="mdi:water-thermometer-outline", translation_key="heat_pump_return_temperature"),
    XtendSensorSpec("629c", "xtend_fSystem", lambda d: _as_float(d, "629c", divisor=100), unit="l/min", state_class=SensorStateClass.MEASUREMENT, icon="mdi:waves-arrow-right", translation_key="system_flow"),
    XtendSensorSpec("62d1", "xtend_tOutdoor", lambda d: _as_float(d, "62d1", divisor=100), unit="°C", device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT, icon="mdi:sun-thermometer-outline", translation_key="outdoor_temperature"),
    XtendSensorSpec("62e7", "xtend_tHpSupply", lambda d: _as_float(d, "62e7", divisor=100), unit="°C", device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT, icon="mdi:water-thermometer", translation_key="heat_pump_supply_temperature"),
    XtendSensorSpec("63b3", "xtend_electricEnergyHeating", lambda d: _as_int(d, "63b3"), unit="kWh", device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL_INCREASING, icon="mdi:power-plug-outline", translation_key="electric_energy_heating"),
    XtendSensorSpec("63df", "xtend_thermalEnergyBoiler", lambda d: _as_int(d, "63df"), unit="kWh", state_class=SensorStateClass.TOTAL_INCREASING, icon="mdi:thermometer-lines", translation_key="thermal_energy_boiler"),
    XtendSensorSpec("63f0", "xtend_thermalEnergyHeating", lambda d: _as_int(d, "63f0"), unit="kWh", state_class=SensorStateClass.TOTAL_INCREASING, icon="mdi:thermometer-lines", translation_key="thermal_energy_heating"),
    XtendSensorSpec("6505", "xtend_suctionTemperature", lambda d: _as_float(d, "6505", divisor=100), unit="°C", device_class=SensorDeviceClass.TEMPERATURE, icon="mdi:coolant-temperature", translation_key="suction_temperature"),
    XtendSensorSpec("6578", "xtend_workingMode", lambda d: _mode_name(d, "6578", WORKING_MODES), icon="mdi:fire", translation_key="working_mode"),
    XtendSensorSpec("6579", "xtend_suctionPressure", lambda d: _as_float(d, "6579", divisor=100), unit="bar", state_class=SensorStateClass.MEASUREMENT, icon="mdi:timeline-clock-outline", translation_key="suction_pressure"),
    XtendSensorSpec("65a7", "xtend_actualFrequency", lambda d: _as_float(d, "65a7", divisor=100), unit="hertz", state_class=SensorStateClass.MEASUREMENT, icon="mdi:sine-wave", translation_key="compressor_frequency"),
    XtendSensorSpec("65b0", "xtend_exhaustPressure", lambda d: _as_float(d, "65b0", divisor=100), unit="bar", state_class=SensorStateClass.MEASUREMENT, icon="mdi:timeline-clock-outline", translation_key="exhaust_pressure"),
    XtendSensorSpec("65c1", "xtend_coilTemperature", lambda d: _as_float(d, "65c1", divisor=100), unit="°C", device_class=SensorDeviceClass.TEMPERATURE, icon="mdi:coolant-temperature", translation_key="coil_temperature"),
    XtendSensorSpec("65d9", "xtend_exhaustTemperature", lambda d: _as_float(d, "65d9", divisor=100), unit="°C", device_class=SensorDeviceClass.TEMPERATURE, icon="mdi:coolant-temperature", translation_key="exhaust_temperature"),
    XtendSensorSpec("6a53", "xtend_startDefrostCounter", lambda d: _as_raw_value(d, "6a53"), icon="mdi:counter", entity_category=EntityCategory.DIAGNOSTIC, translation_key="defrost_start_count"),
    XtendSensorSpec("6a8e", "xtend_startHeatingCounter", lambda d: _as_int(d, "6a8e"), icon="mdi:counter", entity_category=EntityCategory.DIAGNOSTIC, translation_key="heating_start_count"),
    XtendSensorSpec("6ac5", "xtend_operationHeatingHours", lambda d: _as_int(d, "6ac5"), unit="h", device_class=SensorDeviceClass.DURATION, state_class=SensorStateClass.TOTAL_INCREASING, icon="mdi:clock-outline", entity_category=EntityCategory.DIAGNOSTIC, translation_key="heating_operation_hours"),
    XtendSensorSpec("6c26", "xtend_temperatureCondensor_refrigrerant_gas", lambda d: _as_float(d, "6c26", divisor=100), unit="°C", device_class=SensorDeviceClass.TEMPERATURE, icon="mdi:coolant-temperature", translation_key="condenser_refrigerant_gas_temperature"),
    XtendSensorSpec("6c33", "xtend_exhaustOverheat", lambda d: _as_float(d, "6c33", divisor=100), unit="°C", device_class=SensorDeviceClass.TEMPERATURE, icon="mdi:coolant-temperature", translation_key="exhaust_overheat"),
    XtendSensorSpec("6c53", "xtend_temperatureSubcooling", lambda d: _as_float(d, "6c53", divisor=100), unit="°C", device_class=SensorDeviceClass.TEMPERATURE, icon="mdi:coolant-temperature", translation_key="subcooling_temperature"),
    XtendSensorSpec("6c66", "xtend_EEVSteps", lambda d: _as_int(d, "6c66"), unit="steps", icon="mdi:numeric", translation_key="eev_steps"),
    XtendSensorSpec("6c8a", "xtend_actualFan1Speed", lambda d: _as_int(d, "6c8a"), unit="rpm", icon="mdi:fan", translation_key="fan_speed"),
    XtendSensorSpec("6ceb", "xtend_temperatureCondensor_refrigrerant_liquid", lambda d: _as_float(d, "6ceb", divisor=100), unit="°C", device_class=SensorDeviceClass.TEMPERATURE, icon="mdi:coolant-temperature", translation_key="condenser_refrigerant_liquid_temperature"),
    XtendSensorSpec("6cfb", "xtend_suctionOverheat", lambda d: _as_float(d, "6cfb", divisor=100), unit="°C", device_class=SensorDeviceClass.TEMPERATURE, icon="mdi:coolant-temperature", translation_key="suction_overheat"),
    XtendSensorSpec("7160", "xtend_poweron_number", lambda d: _as_int(d, "7160"), icon="mdi:counter", entity_category=EntityCategory.DIAGNOSTIC, translation_key="power_on_count"),
    XtendSensorSpec("71a7", "xtend_poweron_hours", lambda d: _as_int(d, "71a7"), unit="h", device_class=SensorDeviceClass.DURATION, state_class=SensorStateClass.TOTAL_INCREASING, icon="mdi:clock-outline", entity_category=EntityCategory.DIAGNOSTIC, translation_key="power_on_hours"),
    XtendSensorSpec("7767", "xtend_RequestedTemperature", lambda d: _as_float(d, "7767", divisor=100), unit="°C", device_class=SensorDeviceClass.TEMPERATURE, icon="mdi:thermometer-auto", translation_key="requested_temperature"),
    XtendSensorSpec("7921", "xtend_roomtemperature_set_1", lambda d: _as_float(d, "7921", divisor=100), unit="°C", device_class=SensorDeviceClass.TEMPERATURE, icon="mdi:home-thermometer", translation_key="room_temperature_setpoint"),
    XtendSensorSpec("7940", "xtend_notification_code", lambda d: _mode_name(d, "7940", NOTIFICATION_CODES), icon="mdi:bell-outline", entity_category=EntityCategory.DIAGNOSTIC, translation_key="notification_code"),
    XtendSensorSpec("7e2c", "xtend_lockout_code", lambda d: _mode_name(d, "7e2c", LOCKOUT_CODES), icon="mdi:alert-outline", entity_category=EntityCategory.DIAGNOSTIC, translation_key="lockout_code"),
    XtendSensorSpec("7e51", "xtend_heatdemand_status", lambda d: _mode_name(d, "7e51", HEAT_DEMAND_STATUS), icon="mdi:message-badge-outline", translation_key="heat_demand_status"),
    XtendSensorSpec("7ed3", "xtend_water_pressure", lambda d: _as_float(d, "7ed3", divisor=100), unit="bar", state_class=SensorStateClass.MEASUREMENT, icon="mdi:timeline-clock-outline", translation_key="water_pressure"),
    XtendSensorSpec("77dd", "xtend_systemStatus", lambda d: _mode_name(d, "77dd", SYSTEM_STATUS), icon="mdi:power", entity_category=EntityCategory.DIAGNOSTIC, translation_key="system_status"),
    XtendSensorSpec("cop_total", "xtend_cop_total", lambda d: _calculate_cop(d), unit="thermal/kWh", state_class=SensorStateClass.MEASUREMENT, icon="mdi:gauge", translation_key="total_cop"),
    XtendSensorSpec("delta_t", "xtend_deltaT", lambda d: _calculate_delta_t(d, "62e7", "6280"), unit="°C", state_class=SensorStateClass.MEASUREMENT, icon="mdi:thermometer-check", translation_key="delta_t"),
    XtendSensorSpec("thermal_total", "xtend_thermal_total", lambda d: _calculate_thermal_total(d), unit="kWh", state_class=SensorStateClass.MEASUREMENT, icon="mdi:thermometer-lines", translation_key="total_thermal_energy"),
    XtendSensorSpec("625b", "xtreme_tBoilerSupply", lambda d: _as_float(d, "625b", divisor=100), unit="°C", device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT, icon="mdi:water-thermometer", is_xtreme=True, translation_key="boiler_supply_temperature"),
    XtendSensorSpec("623c", "xtreme_tBoilerReturn", lambda d: _as_float(d, "623c", divisor=100), unit="°C", device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT, icon="mdi:water-thermometer-outline", is_xtreme=True, translation_key="boiler_return_temperature"),
    XtendSensorSpec("7e7a", "xtreme_burner_status", lambda d: _mode_name(d, "7e7a", XTREME_BURNER_STATUS), icon="mdi:fire", is_xtreme=True, translation_key="burner_status"),
    XtendSensorSpec("7191", "xtreme_gas_meter_ch", lambda d: _as_float(d, "7191", divisor=10000), unit="m³", device_class=SensorDeviceClass.VOLUME, state_class=SensorStateClass.TOTAL_INCREASING, icon="mdi:gauge", is_xtreme=True, translation_key="gas_meter_ch"),
    XtendSensorSpec("8e1e", "xtreme_boiler_ot_slave_version", lambda d: _as_raw_value(d, "8e1e"), icon="mdi:check-decagram", is_xtreme=True, entity_category=EntityCategory.DIAGNOSTIC, translation_key="boiler_ot_slave_version"),
    XtendSensorSpec("8ecc", "xtreme_boiler_ot_slave_opentherm_version", lambda d: _as_raw_value(d, "8ecc"), icon="mdi:check-decagram", is_xtreme=True, entity_category=EntityCategory.DIAGNOSTIC, translation_key="boiler_ot_protocol_version"),
    XtendSensorSpec("8edb", "xtreme_boiler_ot_dhw_temperature", lambda d: _as_float(d, "8edb", divisor=100), unit="°C", device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT, icon="mdi:water-thermometer", is_xtreme=True, translation_key="boiler_dhw_temperature"),
    XtendSensorSpec("8ecb", "xtreme_boiler_ot_dhw_setpoint", lambda d: _as_float(d, "8ecb", divisor=100), unit="°C", device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT, icon="mdi:stop-circle-outline", is_xtreme=True, translation_key="boiler_dhw_setpoint"),
    XtendSensorSpec("8e37", "xtreme_boiler_ot_dhw_hours", lambda d: _as_int(d, "8e37"), unit="h", device_class=SensorDeviceClass.DURATION, state_class=SensorStateClass.TOTAL_INCREASING, icon="mdi:counter", is_xtreme=True, entity_category=EntityCategory.DIAGNOSTIC, translation_key="boiler_dhw_hours"),
    XtendSensorSpec("8e7f", "xtreme_boiler_ot_dhw_flowrate", lambda d: _as_float(d, "8e7f", divisor=100), unit="L/min", device_class=SensorDeviceClass.VOLUME_FLOW_RATE, state_class=SensorStateClass.MEASUREMENT, icon="mdi:waves-arrow-right", is_xtreme=True, translation_key="boiler_dhw_flow_rate"),
    XtendSensorSpec("8e8f", "xtreme_boiler_ot_ch_water_setpoint", lambda d: _as_float(d, "8e8f", divisor=100), unit="°C", device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT, icon="mdi:thermometer-auto", is_xtreme=True, translation_key="boiler_ch_water_setpoint"),
    XtendSensorSpec("8ef9", "xtreme_boiler_ot_ch_hours", lambda d: _as_int(d, "8ef9"), unit="h", device_class=SensorDeviceClass.DURATION, state_class=SensorStateClass.TOTAL_INCREASING, icon="mdi:clock-outline", is_xtreme=True, entity_category=EntityCategory.DIAGNOSTIC, translation_key="boiler_ch_hours"),
    XtendSensorSpec("8e00", "xtreme_boiler_ot_burner_starts", lambda d: _as_raw_value(d, "8e00"), icon="mdi:counter", is_xtreme=True, entity_category=EntityCategory.DIAGNOSTIC, translation_key="boiler_burner_starts"),
    XtendSensorSpec("848e", "xtreme_boiler_ot_modulation_level_set", lambda d: _as_float(d, "848e", divisor=100), unit="%", state_class=SensorStateClass.MEASUREMENT, icon="mdi:percent-box-outline", is_xtreme=True, translation_key="boiler_modulation_setpoint"),
    XtendSensorSpec("8434", "xtreme_boiler_ot_control_setpoint", lambda d: _as_float(d, "8434", divisor=100), unit="°C", device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT, icon="mdi:thermometer", is_xtreme=True, translation_key="boiler_control_setpoint"),
    XtendSensorSpec("84d1", "xtreme_boiler_ot_modulation_level", lambda d: _as_float(d, "84d1", divisor=100), unit="%", state_class=SensorStateClass.MEASUREMENT, icon="mdi:percent", is_xtreme=True, translation_key="boiler_modulation_level"),
    XtendSensorSpec("844c", "xtreme_boiler_ot_ch_pressure", lambda d: _as_float(d, "844c", divisor=100), unit="bar", state_class=SensorStateClass.MEASUREMENT, icon="mdi:timeline-clock", is_xtreme=True, translation_key="boiler_ch_pressure"),
    XtendSensorSpec("8e18", "xtreme_boiler_ot_flame_loss", lambda d: _as_int(d, "8e18"), icon="mdi:counter", is_xtreme=True, entity_category=EntityCategory.DIAGNOSTIC, translation_key="boiler_flame_loss_count"),
    XtendSensorSpec("xtreme_delta_t", "xtreme_deltaT", lambda d: _calculate_delta_t(d, "625b", "623c"), unit="°C", device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT, icon="mdi:thermometer-check", is_xtreme=True, translation_key="xtreme_delta_t"),
]


def _calculate_cop(data: dict[str, Any]) -> float:
    # Use the same helpers as the individual sensors (63b3 and 63f0 use _as_int)
    elec = _as_int(data, "63b3", default=0)
    therm = _as_int(data, "63f0", default=0)
    if elec is None or therm is None:
        return 0
    try:
        elec_f = float(elec)
        therm_f = float(therm)
    except (TypeError, ValueError):
        return 0
    if elec_f > 0.1:
        return round(therm_f / elec_f, 2)
    return 0


def _calculate_delta_t(data: dict[str, Any], supply_key: str, return_key: str) -> float:
    supply = _as_float(data, supply_key, default=None, divisor=100)
    return_value = _as_float(data, return_key, default=None, divisor=100)
    if supply is None or return_value is None:
        return 0.0
    try:
        return round(float(supply) - float(return_value), 1)
    except (TypeError, ValueError):
        return 0.0


def _calculate_thermal_total(data: dict[str, Any]) -> float:
    # Use the same helpers as the individual sensors (63f0 and 63df use _as_int)
    heating = _as_int(data, "63f0", default=0)
    boiler = _as_int(data, "63df", default=0)
    if heating is None or boiler is None:
        return 0.0
    try:
        total = float(heating) + float(boiler)
    except (TypeError, ValueError):
        return 0.0
    return round(total, 0)


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator: XtendDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    host = entry.data.get("host")
    device_info, xtend_device_info, xtreme_device_info = build_device_infos(entry.entry_id, host)

    entities = [
        XtendRawSensor(coordinator, entry.entry_id, "Intergas Local", device_info),
        XtendLastUpdateSensor(coordinator, entry.entry_id, device_info),
    ]
    for spec in SENSOR_DEFINITIONS:
        # Assign Xtend sensors to the Xtend device
        if spec.is_xtreme:
            entities.append(XtendSensorEntity(coordinator, entry.entry_id, spec, xtreme_device_info))
        else:
            entities.append(XtendSensorEntity(coordinator, entry.entry_id, spec, xtend_device_info))

    _LOGGER.info("Adding %s Xtend sensor entities for %s", len(entities), entry.entry_id)
    async_add_entities(entities)

    # Older versions of this integration forced a custom name onto every sensor's
    # registry entry. A custom name takes priority over the translation-based name
    # now used by XtendSensorEntity, so clear that legacy override once to let the
    # translated name show through. This is a no-op for entities without one.
    try:
        from homeassistant.helpers import entity_registry as er

        registry = er.async_get(hass)
        for spec in SENSOR_DEFINITIONS:
            unique_id = f"{entry.entry_id}_{spec.name}"
            entity_id = registry.async_get_entity_id("sensor", DOMAIN, unique_id)
            if entity_id:
                registry_entry = registry.async_get(entity_id)
                if registry_entry is not None and registry_entry.name is not None:
                    registry.async_update_entity(entity_id, name=None)
                    _LOGGER.debug("Cleared legacy custom name for %s", entity_id)
    except Exception:  # pragma: no cover - defensive
        _LOGGER.debug("Could not clear legacy entity names (entity_registry not available)")


class XtendRawSensor(CoordinatorEntity[XtendDataUpdateCoordinator], SensorEntity):
    def __init__(self, coordinator: XtendDataUpdateCoordinator, entry_id: str, name: str, device_info: dict[str, Any] | None = None) -> None:
        super().__init__(coordinator)
        self._attr_name = name
        self._attr_unique_id = f"{entry_id}_raw"
        self._attr_device_info = device_info
        self._entry_id = entry_id

    @property
    def native_value(self) -> Any:
        return "ok" if self.coordinator.data else None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        data = self.coordinator.data or {}
        stats = data.get("stats") if isinstance(data, dict) else None
        return {"stats": stats if isinstance(stats, dict) else data}


class XtendLastUpdateSensor(CoordinatorEntity[XtendDataUpdateCoordinator], SensorEntity):
    """Last successful API update timestamp"""
    
    def __init__(self, coordinator: XtendDataUpdateCoordinator, entry_id: str, device_info: dict[str, Any] | None = None) -> None:
        super().__init__(coordinator)
        self._attr_name = "Last Update"
        self._attr_unique_id = f"{entry_id}_last_update"
        self._attr_device_class = SensorDeviceClass.TIMESTAMP
        self._attr_icon = "mdi:clock-outline"
        self._attr_device_info = device_info

    @property
    def native_value(self) -> Any:
        """Return the timestamp of the last successful update"""
        return self.coordinator.last_update_timestamp


class XtendSensorEntity(CoordinatorEntity[XtendDataUpdateCoordinator], SensorEntity):
    def __init__(self, coordinator: XtendDataUpdateCoordinator, entry_id: str, spec: XtendSensorSpec, device_info: dict[str, Any] | None = None) -> None:
        super().__init__(coordinator)
        self.entity_description = spec
        self._attr_has_entity_name = True
        self._attr_translation_key = spec.translation_key
        self._attr_unique_id = f"{entry_id}_{spec.name}"
        self._attr_device_info = device_info

    @property
    def native_value(self) -> Any:
        data = self.coordinator.data or {}
        if not isinstance(data, dict):
            _LOGGER.debug("Xtend sensor %s received non-dict coordinator data: %s", self.entity_description.key, type(data).__name__)
            return None
        value = self.entity_description.value_fn(data)
        if value is not None:
            _LOGGER.debug("Xtend sensor %s resolved value=%s", self.entity_description.key, value)
        return value

    @property
    def icon(self) -> str | None:
        return self.entity_description.icon

    @property
    def native_unit_of_measurement(self) -> str | None:
        return self.entity_description.unit

    @property
    def device_class(self) -> str | None:
        return self.entity_description.device_class

    @property
    def state_class(self) -> str | None:
        return self.entity_description.state_class

    @property
    def entity_category(self) -> str | None:
        return self.entity_description.entity_category
