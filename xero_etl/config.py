import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# OAuth credentials
XERO_CLIENT_ID = os.getenv("XERO_CLIENT_ID")
XERO_CLIENT_SECRET = os.getenv("XERO_CLIENT_SECRET")

# Tokens
XERO_ACCESS_TOKEN = os.getenv("XERO_ACCESS_TOKEN")
XERO_REFRESH_TOKEN = os.getenv("XERO_REFRESH_TOKEN")

# Tenant & API
XERO_TENANT_ID = os.getenv("XERO_TENANT_ID")
XERO_BASE_URL = os.getenv("XERO_BASE_URL")

# Rate limits with error handling
try:
    XERO_CALLS_PER_MINUTE = int(os.getenv("XERO_CALLS_PER_MINUTE", 60))
except (ValueError, TypeError):
    XERO_CALLS_PER_MINUTE = 60


def validate_config():
    required = {
        "XERO_CLIENT_ID": XERO_CLIENT_ID,
        "XERO_CLIENT_SECRET": XERO_CLIENT_SECRET,
        "XERO_ACCESS_TOKEN": XERO_ACCESS_TOKEN,
        "XERO_REFRESH_TOKEN": XERO_REFRESH_TOKEN,
        "XERO_TENANT_ID": XERO_TENANT_ID,
        "XERO_BASE_URL": XERO_BASE_URL,
    }

    missing = [k for k, v in required.items() if not v]

    if missing:
        raise OSError(
            f"Missing required environment variables: {', '.join(missing)}"
        )