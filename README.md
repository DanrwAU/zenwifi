# Zen WiFi Thermostat Integration for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)

This is a custom Home Assistant integration for controlling Zen WiFi Thermostats through their cloud API.

## Features

- Climate entity for controlling the thermostat (heat / off — heat-only)
- Temperature sensors for current temperature and heating setpoint
- Binary sensors for online status and C-wire connection status
- Automatic token refresh, with re-authentication if credentials change
- Support for multiple thermostats on one account

## Installation

### HACS Installation (Recommended)

1. Ensure [HACS](https://hacs.xyz/) is installed
2. Add this repository as a custom repository in HACS:
   - Navigate to HACS → Integrations
   - Click the three dots menu → Custom repositories
   - Add the repository URL and select "Integration" as the category
3. Search for "Zen WiFi Thermostat" in HACS
4. Click Install
5. Restart Home Assistant

### Manual Installation

1. Copy the `custom_components/zenwifi` folder to your Home Assistant's `custom_components` directory
2. Restart Home Assistant

## Configuration

1. Go to Settings → Devices & Services
2. Click "Add Integration"
3. Search for "Zen WiFi Thermostat"
4. Enter your Zen WiFi account credentials (username and password)
5. Click Submit

The integration will automatically discover all thermostats associated with your account.

**Note**: The climate entity plus temperature and binary sensors are all created and enabled by default.

## Entities Created

For each thermostat, the following entities will be created:

### Climate Entity
- Control thermostat mode (heat, off)
- Set target (heating) temperature
- View current HVAC action (heating, idle, off)
- `status` attribute exposing the raw device state (Heating / Heat Requested / Off / Off Requested)

### Sensors
- **Current Temperature** - The current room temperature
- **Heating Setpoint** - The target temperature when heating

### Binary Sensors
- **Online** - Whether the thermostat is online and connected
- **C-Wire Connected** - Whether a C-wire is connected to the thermostat

## Supported Modes

This is a **heat-only** integration. The supported HVAC modes are:
- Heat
- Off

Cooling, Auto, Eco, Emergency Heat, and Zen modes are intentionally not supported.

## Entity Management

All entities (climate, temperature sensors, binary sensors) are enabled by default.
You can disable any you don't need from the device page in Settings → Devices & Services.

## Update Interval

The integration polls the Zen WiFi API every minute to update device states.

## Troubleshooting

### Authentication Issues
If you experience authentication errors:
1. Verify your username and password are correct
2. Check if you can log into the Zen WiFi mobile app
3. Remove and re-add the integration

### Device Not Responding
If your thermostat appears offline:
1. Check your thermostat's WiFi connection
2. Verify the thermostat is powered on
3. Check if you can control it through the Zen WiFi mobile app

## Support

For issues and feature requests, please open an issue on the [GitHub repository](https://github.com/DanrwAU/zenwifi).

## Disclaimer

This integration is not affiliated with or endorsed by Zen Ecosystems. Use at your own risk.

It talks to the legacy `wifi.zenhq.com` cloud API, which is **undocumented and unmaintained**:
Zen Ecosystems' assets were acquired by Mysa in 2023 and the original Zen consumer app no
longer works. The API still responds today, but could be shut down at any time — there is no
local-control fallback for the WiFi edition.