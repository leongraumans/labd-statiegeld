# Agents

## Project context

This is a deposit refund (statiegeld) tracking app for Lab Digital, built with FastAPI + SQLite. It runs on a Raspberry Pi with a USB barcode scanner. The web UI is only used once a month to print an overview.

## Architecture decisions

- **No async SQLAlchemy** — single user app on a Pi, sync is simpler
- **No Alembic** — delete DB + re-seed on schema changes
- **No Docker** — runs directly with uv on the Pi
- **ProductType enum** — CAN (0.15), BOTTLE (0.25), UNKNOWN (0.00). Deposit is derived from type, not stored separately
- **Open Food Facts** — free API for product lookup. Falls back to UNKNOWN if product can't be classified
- **SQLAdmin** — Django-style admin panel with authentication

## Key files

- `src/statiegeld/main.py` — all routes, admin config, core logic
- `src/statiegeld/models.py` — SQLAlchemy models with ProductType enum
- `src/statiegeld/openfoodfacts.py` — product lookup + can/bottle classification
- `src/statiegeld/config.py` — all env vars with defaults

## Conventions

- Code and comments in English
- Frontend UI text in Dutch (session overview page) and English (other pages)
- Lab Digital branding: black background, #02ff5d green accent, Archivo font
- All timestamps stored as UTC, displayed in Europe/Amsterdam timezone
- Templates use `render()` helper which injects unknown product count on every page

## Running

```bash
task install    # install deps
task dev        # start server
task fake-scan  # simulate scans
```

## Testing changes

1. `rm -f statiegeld.db` to reset
2. `task dev` starts server with auto-reload
3. `task scan -- --barcode <ean>` to test individual barcodes
4. Check `/admin` for data inspection (login: admin/statiegeld)
