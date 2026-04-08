"""Fake barcode scanner — simulates scans via the API."""

import argparse
import os
import random
import time

import httpx

from statiegeld.seed import KNOWN_PRODUCTS

DEFAULT_URL = "http://localhost:8000/api/scan"
DEFAULT_API_KEY = os.environ.get("API_KEY", "statiegeld-scanner")


def main():
    parser = argparse.ArgumentParser(description="Simulate barcode scans")
    parser.add_argument("--barcode", help="Specific barcode to scan")
    parser.add_argument(
        "--count", type=int, default=5, help="Number of scans (default: 5)"
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=1.0,
        help="Seconds between scans (default: 1.0)",
    )
    parser.add_argument("--url", default=DEFAULT_URL, help="API URL")
    parser.add_argument("--api-key", default=DEFAULT_API_KEY, help="API key")
    args = parser.parse_args()

    barcodes = [p[0] for p in KNOWN_PRODUCTS]
    headers = {"X-Api-Key": args.api_key}

    print(f"Fake scanner started — {args.count} scans to {args.url}")
    for i in range(args.count):
        barcode = args.barcode or random.choice(barcodes)
        response = httpx.post(args.url, json={"barcode": barcode}, headers=headers)
        data = response.json()

        if data.get("status") == "ok":
            print(
                f"  [{i + 1}/{args.count}] {barcode} -> {data['product']} (+€{data['deposit']:.2f})"
            )
        else:
            print(
                f"  [{i + 1}/{args.count}] {barcode} -> {data.get('detail', data.get('message', 'Error'))}"
            )

        if i < args.count - 1:
            time.sleep(args.interval)

    print("Done!")


if __name__ == "__main__":
    main()
