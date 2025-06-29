"""Debug script to help diagnose multiple device instances issue."""

import asyncio
import json
import logging
import os
from getpass import getpass

import aiohttp

# Add parent directory to path
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from custom_components.zenwifi.api import ZenWifiApiClient

logging.basicConfig(level=logging.DEBUG)
_LOGGER = logging.getLogger(__name__)


async def main():
    """Main debug function."""
    print("Zen WiFi Debug Tool")
    print("=" * 50)
    
    username = input("Enter username: ")
    password = getpass("Enter password: ")
    
    async with aiohttp.ClientSession() as session:
        client = ZenWifiApiClient(username, password, session)
        
        try:
            # Authenticate
            print("\n1. Authenticating...")
            await client.async_authenticate()
            print("✓ Authentication successful")
            
            # Get user info
            print("\n2. Getting user info...")
            user_info = await client.async_get_user_info()
            print(f"✓ Consumer ID: {client._consumer_id}")
            
            # Get devices
            print("\n3. Getting devices...")
            devices = await client.async_get_devices()
            print(f"✓ Found {len(devices)} device(s)")
            
            # Print device details
            print("\n4. Device Details:")
            print("=" * 50)
            for i, device in enumerate(devices):
                print(f"\nDevice {i + 1}:")
                print(f"  ID: {device.get('id')}")
                print(f"  Name: {device.get('name')}")
                print(f"  Location ID: {device.get('locationId')}")
                print(f"  Hub MAC: {device.get('hubMacAddress')}")
                
                # Get device status
                device_id = device.get('id')
                if device_id:
                    try:
                        status = await client.async_get_device_status(device_id)
                        print(f"\n  Status:")
                        print(f"    Online: {status.get('isOnline')}")
                        print(f"    Mode: {status.get('mode')} ({client.get_mode_string(status.get('mode', 0))})")
                        print(f"    Current Temp: {status.get('currentTemperature')}°C")
                        print(f"    Heating Setpoint: {status.get('heatingSetpoint')}°C")
                        print(f"    Cooling Setpoint: {status.get('coolingSetpoint')}°C")
                    except Exception as e:
                        print(f"  ERROR getting status: {e}")
            
            # Save raw data for analysis
            print("\n5. Saving raw data to debug_output.json...")
            debug_data = {
                "devices": devices,
                "device_count": len(devices),
                "device_ids": [d.get('id') for d in devices],
                "device_names": [d.get('name') for d in devices],
            }
            
            with open("debug_output.json", "w") as f:
                json.dump(debug_data, f, indent=2)
            print("✓ Data saved to debug_output.json")
            
        except Exception as e:
            print(f"\nERROR: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())