"""Centralized logging setup.

All modules import :func:`get_logger` and log through it so the whole
application shares one consistent, well-formatted logger.
"""
from __future__ import annotations

import logging
import sys

_CONFIGURED = False


def setup_logging(level: int = logging.INFO) -> None:
    """Configure the root logger once (idempotent)."""
    global _CONFIGURED
    if _CONFIGURED:
        return
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    root = logging.getLogger()
    root.setLevel(level)
    # Avoid duplicate handlers on repeated imports.
    for h in root.handlers[:]:
        root.removeHandler(h)
    root.addHandler(handler)
    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    """Return a named logger, ensuring logging is configured once."""
    setup_logging()
    return logging.getLogger(name)
