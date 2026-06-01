"""
config.py — Configuration Loader
=================================
Loads environment variables from .env file and Streamlit Secrets.

Works in:
1. Local development (.env)
2. Streamlit Cloud (Secrets)

Source: Assignment Doc §Setup — API key configuration requirement.
"""

import os
from dotenv import load_dotenv

# Load local .env if present
load_dotenv()

# ------------------------------------------------------------------------------
# Binance API Credentials
# ------------------------------------------------------------------------------

API_KEY = ""
API_SECRET = ""

# Try Streamlit Secrets first
try:
    import streamlit as st

    API_KEY = st.secrets.get("BINANCE_API_KEY", "")
    API_SECRET = st.secrets.get("BINANCE_API_SECRET", "")

except Exception:
    pass

# Fallback to local .env
if not API_KEY:
    API_KEY = os.getenv("BINANCE_API_KEY", "")

if not API_SECRET:
    API_SECRET = os.getenv("BINANCE_API_SECRET", "")

# Always use testnet for this assignment
TESTNET: bool = True

# ------------------------------------------------------------------------------
# Logging Configuration
# ------------------------------------------------------------------------------
LOG_DIR: str = "logs"
LOG_FILE: str = os.path.join(LOG_DIR, "bot.log")
LOG_MAX_BYTES: int = 5 * 1024 * 1024  # 5 MB
LOG_BACKUP_COUNT: int = 3

# ------------------------------------------------------------------------------
# Validation Constants
# ------------------------------------------------------------------------------

VALID_SIDES = {"BUY", "SELL"}
VALID_ORDER_TYPES = {"MARKET", "LIMIT"}
VALID_TIME_IN_FORCE = {"GTC", "IOC", "FOK"}

# ------------------------------------------------------------------------------
# Startup Validation
# ------------------------------------------------------------------------------


def validate_config() -> None:
    """
    Raise RuntimeError if credentials are missing.

    Supports:
    - Local .env
    - Streamlit Cloud Secrets
    """

    if not API_KEY:
        raise RuntimeError(
            "BINANCE_API_KEY not found. "
            "Use .env locally or Streamlit Secrets when deployed."
        )

    if not API_SECRET:
        raise RuntimeError(
            "BINANCE_API_SECRET not found. "
            "Use .env locally or Streamlit Secrets when deployed."
        )
