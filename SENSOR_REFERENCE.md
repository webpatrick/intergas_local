# Sensor reference

This page gives a quick overview of the main sensors exposed by the Intergas Local integration and what they roughly represent.

The exact sensor names in Home Assistant can vary slightly depending on the entity registry and the friendly-name cleanup, but the list below reflects the meanings of the underlying values.

## Heat pump / Xtend sensors

| Sensor | Meaning |
| --- | --- |
| Current Heat pump Power Thermal | Current thermal output of the heat pump in kW |
| Current COP | Instantaneous COP / efficiency ratio |
| Current Power Thermal | Current thermal power in kW |
| Current Boiler Power Thermal | Thermal power from the boiler part in kW |
| Current Power Electric | Instant electric power consumption in W |
| Heat pump Mode | Operating mode such as DHW, Heating, Cooling, Off, etc. |
| Room temperature | Indoor room temperature reading |
| Heat pump Return Temperature | Return temperature of the heat pump loop |
| System Flow | Water flow in the system |
| Outdoor Temperature | Ambient outdoor temperature |
| Heat pump Supply Temperature | Supply temperature of the heat pump loop |
| Electric Energy Heating | Total electrical energy used for heating |
| Thermal Energy Boiler | Total thermal energy associated with the boiler |
| Thermal Energy Heating | Total thermal energy for heating |
| Suction Temperature | Refrigerant suction temperature |
| Working Mode | Current working state such as Cooling, Heating, Defrosting, Pumpdown |
| Suction Pressure | Suction pressure |
| Actual Frequency | Compressor frequency |
| Exhaust Pressure | Exhaust pressure |
| Coil Temperature | Coil temperature |
| Exhaust Temperature | Exhaust temperature |
| Start Defrost Counter | Number of defrost cycles initiated |
| Start Heating Counter | Number of heating starts |
| Heating Operation Hours | Total heating runtime |
| Condenser Refrigerant Gas Temperature | Condenser gas-side temperature |
| Exhaust Overheat | Overheat indication on the exhaust side |
| Subcooling Temperature | Subcooling value |
| EEV Steps | Electronic expansion valve position / steps |
| Actual Fan 1 Speed | Fan speed |
| Condenser Refrigerant Liquid Temperature | Condenser liquid-side temperature |
| Suction Overheat | Suction-side overheating |
| Power On Number | Number of power cycles or starts |
| Power On Hours | Total power-on / operating hours |
| Requested Temperature | Requested target temperature |
| Room temperature Set | Room temperature setpoint |
| Notification Code | Current notification / alarm code |
| Lockout Code | Current lockout code |
| Heat Demand Status | Current heat demand state |
| Water Pressure | Central heating water pressure |
| System Status | Overall controller / system status |
| Total COP | Total averaged COP |
| Delta T | Temperature difference between supply and return |
| Total Thermal Energy | Combined thermal energy total |
| Error Code | Current error / alarm code |

## Xtreme / boiler sensors

| Sensor | Meaning |
| --- | --- |
| Boiler Supply Temperature | Boiler supply water temperature |
| Boiler Return Temperature | Boiler return water temperature |
| Burner Status | Burner state (startup, ignition, running, lockout, etc.) |
| Gas Meter CH | Central-heating gas consumption meter |
| Boiler OT Slave Version | OpenTherm slave version on the boiler |
| Boiler OT Slave OpenTherm Version | OpenTherm protocol version details |
| Boiler OT DHW Temperature | DHW temperature as reported via OpenTherm |
| Boiler OT DHW Setpoint | DHW temperature setpoint |
| Boiler OT DHW Hours | DHW runtime hours |
| Boiler OT DHW Flowrate | DHW flow rate |
| Boiler OT CH Water Setpoint | Central heating water setpoint |
| Boiler OT CH Hours | Central-heating runtime hours |
| Boiler OT Burner Starts | Burner starts counter |
| Boiler OT Modulation Level Set | Target modulation level |
| Boiler OT Control Setpoint | Boiler control setpoint |
| Boiler OT Modulation Level | Actual modulation level |
| Boiler OT CH Pressure | Central heating pressure |
| Boiler OT Flame Loss | Flame-loss counter / diagnostic |
| Xtreme Delta T | Boiler supply-return temperature difference |

## Binary sensors

These are available as active checks for the heat pump and boiler systems:

- Xtend active check: compares supply and return temperature difference; true when the heat pump is actively transferring heat
- Xtreme active check: compares boiler supply and return temperature difference; true when the boiler is active

## Diagnostic sensors

A number of sensors are marked as diagnostic and are mostly meant for service or troubleshooting, for example:

- Error code
- Notification code
- Lockout code
- System status
- Heat demand status
- Power-on counters and runtime counters
- OpenTherm version and boiler service data

## Notes

- Some sensor names are intentionally kept generic to match the raw API values, while the friendly display name is cleaned up in Home Assistant.
- The actual values can vary depending on the exact Intergas hardware model and firmware revision.
- If a sensor does not apply to your installation, it may simply remain unavailable or stay at a default value.

For installation and setup details, see the main [README.md](README.md).
