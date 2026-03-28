from __future__ import annotations

import logging
from typing import Optional


def setup_logging(level: int = logging.INFO) -> logging.Logger:
    """Configure a structured logger for the application."""

    logger = logging.getLogger("rag-platform")
    if logger.handlers:
        return logger
    logger.setLevel(level)
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        fmt="%(asctime)s %(levelname)s %(name)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Return a child logger scoped to the provided name."""

    base_logger = setup_logging()
    return base_logger.getChild(name) if name else base_logger
