# Installation Guide

## Requirements

- Raspberry Pi (3/4/5) with Raspberry Pi OS
- USB barcode scanner
- Python 3.14+
- [uv](https://docs.astral.sh/uv/) package manager
- [Task](https://taskfile.dev/) task runner (optional, but recommended)

## Local development (Mac/Linux)

```bash
# Install dependencies
uv sync

# Start the dev server
task dev
# or: uv run python main.py

# In another terminal, simulate some scans
task fake-scan -- --count 10
# or add a specific barcode:
task scan -- --barcode 5449000000996

# Open http://localhost:8000 for the overview
# Open http://localhost:8000/admin for the admin panel
```

## Raspberry Pi setup

### 1. Install system dependencies

```bash
sudo apt update && sudo apt install -y python3 python3-pip git
```

### 2. Install uv

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 3. Clone the project

```bash
cd /home/pi
git clone <your-repo-url> statiegeld
cd statiegeld
```

### 4. Install Python dependencies

```bash
uv sync

# evdev is needed for the barcode scanner (Linux only)
uv pip install evdev
```

### 5. Find your barcode scanner device

Plug in the USB barcode scanner, then:

```bash
uv run python -m statiegeld.scanner --list
```

This will show something like:

```
/dev/input/event0: HID 1234:5678 (usb-0000:01:00.0-1.2/input0)
```

Note the `/dev/input/eventX` path for your scanner.

### 6. Update the scanner service

Edit `systemd/statiegeld-scanner.service` and set the correct device path:

```
ExecStart=/home/pi/statiegeld/.venv/bin/python -m statiegeld.scanner --device /dev/input/event0
```

Also update `User` and `WorkingDirectory` if your username is not `pi`.

### 7. Install and start services

```bash
task install-services
```

Or manually:

```bash
sudo cp systemd/statiegeld-web.service /etc/systemd/system/
sudo cp systemd/statiegeld-scanner.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable statiegeld-web statiegeld-scanner
sudo systemctl start statiegeld-web statiegeld-scanner
```

### 8. Verify

```bash
# Check service status
sudo systemctl status statiegeld-web
sudo systemctl status statiegeld-scanner

# Check logs
sudo journalctl -u statiegeld-web -f
sudo journalctl -u statiegeld-scanner -f
```

The web interface is now available at `http://<pi-ip>:8000`.

## Usage

### Day-to-day

Just scan items with the barcode scanner. Each scan is automatically registered.

### Monthly overview (when Albert Heijn comes by)

1. Open `http://<pi-ip>:8000` in a browser
2. The overview page shows: cans, bottles, and total deposit amount
3. Click **Print** to print the overview
4. Click **Close session** to start a new period

### Managing products

- **Web UI**: go to `/products` to add new products
- **Admin panel**: go to `/admin` to view/edit/delete any record

### Useful commands

```bash
# View service logs
sudo journalctl -u statiegeld-scanner -f

# Restart services after code changes
sudo systemctl restart statiegeld-web statiegeld-scanner

# Add a scan manually (server must be running)
task scan -- --barcode 5449000000996

# Simulate 20 random scans
task fake-scan -- --count 20

# Reset the database
task reset
sudo systemctl restart statiegeld-web
```

## Troubleshooting

### Scanner not working

- Check the device path: `uv run python -m statiegeld.scanner --list`
- The scanner service runs as root (needed for `/dev/input` access)
- Check logs: `sudo journalctl -u statiegeld-scanner -f`

### Unknown barcodes

When a barcode is not in the database, it will be logged but ignored. Add new products via `/products` or `/admin`.

### Database issues

```bash
# Nuclear option: reset everything
task reset
sudo systemctl restart statiegeld-web
```
