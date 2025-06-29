# Zen WiFi Thermostat Integration for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)

This is a custom Home Assistant integration for controlling Zen WiFi Thermostats through their cloud API.

## Features

- Climate entity for controlling thermostat modes (heat, cool, off)
- Temperature sensors for current temperature, heating setpoint, and cooling setpoint
- Binary sensors for online status and C-wire connection status
- Automatic token refresh for maintaining API connection
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

## Entities Created

For each thermostat, the following entities will be created:

### Climate Entity
- Control thermostat mode (heat, cool, off)
- Set target temperature
- View current HVAC action (heating, cooling, idle, off)

### Sensors
- **Current Temperature** - The current room temperature
- **Heating Setpoint** - The target temperature when in heating mode
- **Cooling Setpoint** - The target temperature when in cooling mode

### Binary Sensors
- **Online** - Whether the thermostat is online and connected
- **C-Wire Connected** - Whether a C-wire is connected to the thermostat

## Supported Modes

The integration supports the following HVAC modes:
- Heat
- Cool
- Off

Note: Auto, Eco, Emergency Heat, and Zen modes from the native app are not currently supported.

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

For issues and feature requests, please open an issue on the [GitHub repository](https://github.com/yourusername/zenwifi-hacs).

## Disclaimer

This integration is not affiliated with or endorsed by Zen Ecosystems. Use at your own risk.