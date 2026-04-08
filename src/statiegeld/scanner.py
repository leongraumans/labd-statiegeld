"""Barcode scanner service — reads a USB barcode scanner via evdev.

This script only runs on Linux (Raspberry Pi). It reads keyboard events
from the scanner device and sends each scanned barcode to the API.

Usage:
    uv run python -m statiegeld.scanner
    uv run python -m statiegeld.scanner --device /dev/input/event0
    uv run python -m statiegeld.scanner --list

Requires: pip install evdev (only on the Pi)
"""

import argparse
import os
import sys

import httpx

DEFAULT_URL = "http://localhost:8000/api/scan"
DEFAULT_API_KEY = os.environ.get("API_KEY", "statiegeld-scanner")

# evdev key code to character mapping (digits + Enter)
KEY_MAP = {
    2: "1",
    3: "2",
    4: "3",
    5: "4",
    6: "5",
    7: "6",
    8: "7",
    9: "8",
    10: "9",
    11: "0",
}
KEY_ENTER = 28


def list_devices():
    from evdev import InputDevice, list_devices as evdev_list

    devices = [InputDevice(path) for path in evdev_list()]
    if not devices:
        print("No input devices found.")
        return
    for dev in devices:
        print(f"  {dev.path}: {dev.name} ({dev.phys})")


def scan_loop(device_path: str, api_url: str, api_key: str):
    from evdev import InputDevice, ecodes

    device = InputDevice(device_path)
    device.grab()  # exclusive access, prevents ghost keyboard input
    print(f"Scanner active on {device.path}: {device.name}")
    print(f"Scans will be sent to {api_url}")

    headers = {"X-Api-Key": api_key}
    barcode = ""
    try:
        for event in device.read_loop():
            if event.type != ecodes.EV_KEY or event.value != 1:  # key-down only
                continue

            key = event.code
            if key == KEY_ENTER and barcode:
                response = httpx.post(
                    api_url, json={"barcode": barcode}, headers=headers
                )
                data = response.json()
                if data["status"] == "ok":
                    print(f"  {barcode} -> {data['product']} (+€{data['deposit']:.2f})")
                else:
                    print(f"  {barcode} -> {data['message']}")
                barcode = ""
            elif key in KEY_MAP:
                barcode += KEY_MAP[key]
    except KeyboardInterrupt:
        print("\nScanner stopped.")
    finally:
        device.ungrab()


def main():
    parser = argparse.ArgumentParser(description="USB barcode scanner service")
    parser.add_argument("--device", help="Input device path (e.g. /dev/input/event0)")
    parser.add_argument(
        "--list", action="store_true", help="List available input devices"
    )
    parser.add_argument("--url", default=DEFAULT_URL, help="API URL")
    parser.add_argument("--api-key", default=DEFAULT_API_KEY, help="API key")
    args = parser.parse_args()

    try:
        import evdev  # noqa: F401
    except ImportError:
        print("evdev is not installed. Install with: pip install evdev")
        print("(evdev only works on Linux/Raspberry Pi)")
        sys.exit(1)

    if args.list:
        list_devices()
        return

    if not args.device:
        print("Specify a device with --device, or use --list to see available devices.")
        sys.exit(1)

    scan_loop(args.device, args.url, args.api_key)


if __name__ == "__main__":
    main()
