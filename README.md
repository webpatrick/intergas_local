# Intergas Local

A Home Assistant custom integration for the Intergas Xtend / Xtreme local API.

This integration is based on the same local-access approach described in [HA_connection_Xtend](https://github.com/DSchoutsen/HA_connection_Xtend): the Home Assistant instance connects directly to the Xtend unit over its local HTTP API instead of using a cloud service.

It is designed for setups where the heat pump is only reachable on its own local network, which means Home Assistant usually needs a dedicated Wi‑Fi adapter or a separate Wi‑Fi network path to the Xtend controller.

## Why this integration exists

The Intergas Xtend system exposes operational data through a local API on the unit. This integration polls that API directly and exposes the most relevant system values in Home Assistant as entities.

This is a local-only integration:

- no cloud dependency
- no vendor app required
- no external API token needed
- no polling through a remote service

## Important: dedicated Wi‑Fi requirement

For Xtend installations, Home Assistant often needs to be connected to a separate Wi‑Fi network or use a dedicated USB Wi‑Fi adapter.

This is important because the Xtend controller is typically reachable only through a dedicated local network, not through the normal home network. In practice that means:

- HA should have access to the Xtend controller via a second Wi‑Fi interface or a dedicated SSID / subnet
- the main home network and the Xtend network should not be competing for the same interface
- the unit IP should be reachable from Home Assistant directly on its local API

This is the same principle used in the original HA_connection_Xtend setup.

## Features

- Local polling of Intergas Xtend and Xtreme values over HTTP
- Heat pump temperature, flow, pressure, power and operating state sensors
- Boiler / Xtreme status and operating diagnostics
- Error, lockout and notification code mapping
- Energy, thermal and efficiency related values
- Active binary sensors for Xtend and Xtreme presence/activity
- Configurable polling interval
- Home Assistant UI config flow
- Works without third-party cloud services

## Supported data

The integration reads and exposes values such as:

- heat pump supply / return temperatures
- outdoor temperature
- flow rate
- suction and exhaust pressure
- current electrical power
- thermal power and COP
- operation mode and system status
- notification and lockout codes
- Xtreme boiler supply / return temperatures
- burner status and boiler diagnostics

## Entities

The integration creates a set of sensors and binary sensors in Home Assistant.

### Heat pump / Xtend sensors

Examples include:

- current electrical power
- thermal power
- COP
- heat pump supply and return temperature
- outdoor temperature
- flow rate
- operation mode
- working mode
- system status
- error / lockout / notification codes
- energy totals and runtime counters

### Xtreme / boiler sensors

Examples include:

- boiler supply and return temperature
- burner status
- boiler gas meter data
- DHW and CH related values
- boiler operating hours and setpoints

### Binary sensors

- Xtend active check
- Xtreme active check

These are based on the delta between supply and return temperatures and indicate whether the unit is actively running.

## Installation

### HACS (recommended)

1. Open Home Assistant
2. Go to HACS
3. Open Integrations
4. Click the menu button and choose Custom repositories
5. Add this repository URL
6. Search for Xtend Local
7. Install the integration
8. Restart Home Assistant

### Manual installation

1. Download or clone this repository
2. Copy the `custom_components/xtend_local` directory into your Home Assistant `custom_components` folder
3. Restart Home Assistant

## Configuration

1. Go to Settings > Devices & Services > Add Integration
2. Search for Xtend Local
3. Enter the Xtend host or local IP address
4. Optionally adjust the polling interval
5. Save the configuration

The integration will build the local API URL automatically, for example:

http://<xtend_ip>/api/stats/values?fields=...

## Network setup example

A common setup is:

- Home Assistant main LAN: normal home Wi‑Fi or Ethernet
- HA dedicated Wi‑Fi adapter: connected to the Xtend access point or local Xtend subnet
- Xtend controller: reachable at a local IP such as `10.20.30.1`

This allows Home Assistant to talk to the unit locally without exposing the system to the internet or needing the cloud.

## Troubleshooting

### Integration does not load

- verify the Xtend host IP is correct
- check whether Home Assistant can reach the unit on the local network
- confirm the Xtend controller is online and connected to the local Wi‑Fi or AP
- check Home Assistant logs for HTTP or parsing errors

### No data appears

- confirm the API endpoint is reachable from HA
- verify the device is on the correct dedicated Wi‑Fi network
- check whether the heat pump is actually active or reporting values
- try increasing the polling interval if the controller is slow to respond

### Separate Wi‑Fi not available

This integration expects direct local connectivity. If HA cannot reach the controller on a separate local network, the integration will not be able to poll the statistics reliably.

## Notes

This project is a local, derived implementation based on the original Xtend / Intergas work by DSchoutsen and related community efforts. It is tailored for the common Xtend/Xtreme local API access pattern and the dedicated Wi‑Fi setup required by these systems.

## License

This project does not currently declare a license in its metadata. Please check the repository contents and downstream usage requirements before distributing or reusing the code outside your own Home Assistant setup.
