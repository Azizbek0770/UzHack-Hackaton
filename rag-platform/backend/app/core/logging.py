"""
Structured Logging Configuration — structlog + stdlib
Outputs JSON in production, colored console in development.
"""

import logging
import sys
from typing import Any

import structlog
from structlog.types import EventDict, WrappedLogger


def add_severity(
    logger: WrappedLogger, method: str, event_dict: EventDict
) -> EventDict:
    """Map structlog level names to log severity for GCP/Datadog compatibility."""
    level = event_dict.get("level", method).upper()
    event_dict["severity"] = level
    return event_dict


def configure_logging(debug: bool = False) -> None:
    """
    Configure structlog and stdlib logging.

    In debug mode: human-readable colored console output.
    In production: JSON output for log aggregators.
    """
    log_level = logging.DEBUG if debug else logging.INFO

    # Configure stdlib root logger
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
    )

    # Silence noisy third-party loggers
    for noisy in ("urllib3", "httpx", "httpcore", "faiss", "transformers"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    shared_processors: list[Any] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        add_severity,
    ]

    if debug:
        # Pretty console output for development
        processors = shared_processors + [
            structlog.dev.ConsoleRenderer(colors=True),
        ]
    else:
        # JSON output for production
        processors = shared_processors + [
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ]

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


class TimingLogger:
    """
    Context manager for timing pipeline stages with structured logging.

    Usage:
        async with TimingLogger("embedding", logger) as t:
            result = embed(text)
        # logs: {"stage": "embedding", "elapsed_ms": 42.3}
    """

    def __init__(self, stage: str, logger: Any, **extra: Any):
        self.stage = stage
        self.logger = logger
        self.extra = extra
        self._start: float = 0.0
        self.elapsed_ms: float = 0.0

    def __enter__(self) -> "TimingLogger":
        import time
        self._start = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        import time
        self.elapsed_ms = round((time.perf_counter() - self._start) * 1000, 2)
        if exc_type:
            self.logger.error(
                "Stage failed",
                stage=self.stage,
                elapsed_ms=self.elapsed_ms,
                error=str(exc_val),
                **self.extra,
            )
        else:
            self.logger.debug(
                "Stage completed",
                stage=self.stage,
                elapsed_ms=self.elapsed_ms,
                **self.extra,
            )

    async def __aenter__(self) -> "TimingLogger":
        return self.__enter__()

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        return self.__exit__(exc_type, exc_val, exc_tb)
