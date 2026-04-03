import os
import secrets

ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "statiegeld")
SECRET_KEY = os.environ.get("SECRET_KEY", secrets.token_hex(32))
API_KEY = os.environ.get("API_KEY", "statiegeld-scanner")
