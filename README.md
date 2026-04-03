# Statiegeld Tracker

Deposit refund tracker for Lab Digital. Scans cans and bottles via a USB barcode scanner on a Raspberry Pi, keeps count, and provides a printable overview each month.

## Stack

- **FastAPI** + **SQLite** (SQLAlchemy)
- **Jinja2** templates with Lab Digital branding
- **SQLAdmin** panel at `/admin`
- **Open Food Facts** API for automatic product lookup
- **evdev** for USB barcode scanner input (Linux/Pi only)

## Quick start

```bash
task install    # Install dependencies
task dev        # Start dev server at http://localhost:8000
```

## Commands

| Command | Description |
|---|---|
| `task install` | Install dependencies |
| `task dev` | Start development server |
| `task scan -- --barcode <ean>` | Add a single scan |
| `task fake-scan -- --count 10` | Simulate random scans |
| `task seed` | Seed database with known products |
| `task reset` | Delete the database |
| `task install-services` | Install systemd services on Pi |

## How it works

1. **Barcode scanner** (`scanner.py`) runs as a background service, reads the USB device, and POSTs each barcode to the API
2. **Product lookup**: local DB first, then Open Food Facts, then saved as UNKNOWN
3. **Web UI**: overview page with totals, printable for monthly Albert Heijn pickup
4. **Admin** (`/admin`): manage products, sessions, and scans. Fix UNKNOWN product types here

## Security

| Variable | Default | Description |
|---|---|---|
| `ADMIN_USERNAME` | `admin` | Admin panel login |
| `ADMIN_PASSWORD` | `statiegeld` | Admin panel password |
| `API_KEY` | `statiegeld-scanner` | Required header for scan API |
| `SECRET_KEY` | random | Session cookie signing |

The scan API requires an `X-Api-Key` header. Change defaults via environment variables on the Pi.

## Project structure

```
src/statiegeld/
  main.py           # FastAPI app, routes, admin
  models.py         # Product, Session, Scan + ProductType enum
  database.py       # SQLite engine
  config.py         # Environment variable config
  auth.py           # Admin authentication
  seed.py           # Example product data
  openfoodfacts.py  # Product lookup API client
  scanner.py        # USB barcode scanner service
  fake_scanner.py   # Test script to simulate scans
  templates/        # Jinja2 HTML templates
  static/           # CSS + logo
systemd/            # Service files for Raspberry Pi
```

## Raspberry Pi deployment

See [INSTALL.md](INSTALL.md) for full setup instructions.
