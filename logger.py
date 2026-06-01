"""
logger.py — Structured Logging Module
======================================
Sets up a dual-handler logger:
  - FileHandler  -> logs/bot.log   (with rotation, 5 MB x 3 backups)
  - StreamHandler -> stdout (colored for readability)

Source: Assignment Doc Section Core Requirements 4 -- logging to file + console.
ISO 25010 Quality: Maintainability -- structured, timestamped, traceable logs.

Note: Uses UTF-8 encoding on StreamHandler to support all platforms.
"""

import logging
import os
import sys
from logging.handlers import RotatingFileHandler

from config import LOG_DIR, LOG_FILE, LOG_MAX_BYTES, LOG_BACKUP_COUNT


# ── ANSI colour codes for console output ─────────────────────────────────────
class _ColourFormatter(logging.Formatter):
    """Add terminal colours to log levels for console readability."""

    COLOURS = {
        logging.DEBUG:    "\033[36m",   # Cyan
        logging.INFO:     "\033[32m",   # Green
        logging.WARNING:  "\033[33m",   # Yellow
        logging.ERROR:    "\033[31m",   # Red
        logging.CRITICAL: "\033[35m",   # Magenta
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        colour = self.COLOURS.get(record.levelno, self.RESET)
        record.levelname = f"{colour}{record.levelname:8s}{self.RESET}"
        return super().format(record)


# ── Public API ────────────────────────────────────────────────────────────────
def setup_logger(name: str = "trading_bot") -> logging.Logger:
    """
    Create and return a configured logger instance.

    Args:
        name: Logger namespace (default: 'trading_bot').

    Returns:
        logging.Logger instance with file + console handlers attached.
    """
    # Create logs directory if needed
    os.makedirs(LOG_DIR, exist_ok=True)

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # Prevent duplicate handlers if called multiple times
    if logger.handlers:
        return logger

    # ── Shared format ─────────────────────────────────────────────────────────
    file_fmt = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console_fmt = _ColourFormatter(
        fmt="%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%H:%M:%S",
    )

    # ── File handler (rotating) ───────────────────────────────────────────────
    file_handler = RotatingFileHandler(
        filename=LOG_FILE,
        maxBytes=LOG_MAX_BYTES,
        backupCount=LOG_BACKUP_COUNT,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(file_fmt)

    # -- Console handler (UTF-8 with fallback for Streamlit / pytest) -----------
    import io
    try:
        # Standard terminal: wrap stdout.buffer for full UTF-8 support
        utf8_stdout = io.TextIOWrapper(
            sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True
        )
        console_handler = logging.StreamHandler(utf8_stdout)
    except AttributeError:
        # Streamlit / pytest capsys: sys.stdout has no .buffer — use as-is
        console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_fmt)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger
