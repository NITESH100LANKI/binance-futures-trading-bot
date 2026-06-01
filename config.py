"""
config.py — Configuration Loader
=================================
Loads environment variables from .env file and exposes
typed constants used throughout the trading bot.

Source: Assignment Doc §Setup — API key configuration requirement.
"""

import os
from dotenv import load_dotenv

# Load .env from project root
load_dotenv()

# ── Binance API Credentials (Futures Testnet) ─────────────────────────────────
API_KEY: str = os.getenv("BINANCE_API_KEY", "")
API_SECRET: str = os.getenv("BINANCE_API_SECRET", "")

# Always use testnet for this assignment
TESTNET: bool = True

# ── Logging Configuration ─────────────────────────────────────────────────────
LOG_DIR: str = "logs"
LOG_FILE: str = os.path.join(LOG_DIR, "bot.log")
LOG_MAX_BYTES: int = 5 * 1024 * 1024   # 5 MB per file
LOG_BACKUP_COUNT: int = 3               # Keep 3 rotated files

# ── Validation Constants ──────────────────────────────────────────────────────
VALID_SIDES = {"BUY", "SELL"}
VALID_ORDER_TYPES = {"MARKET", "LIMIT"}
VALID_TIME_IN_FORCE = {"GTC", "IOC", "FOK"}

# ── Sanity check on startup ───────────────────────────────────────────────────


def validate_config() -> None:
    """Raise RuntimeError if critical config values are missing."""
    if not API_KEY:
        raise RuntimeError(
            "BINANCE_API_KEY is not set. "
            "Create a .env file from .env.example and add your testnet API key."
        )
    if not API_SECRET:
        raise RuntimeError(
            "BINANCE_API_SECRET is not set. "
            "Create a .env file from .env.example and add your testnet API secret."
        )
