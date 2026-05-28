from __future__ import annotations

import structlog


def configure_logging(log_level: str = "WARNING") -> None:
    import logging

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="%H:%M:%S"),
            structlog.dev.ConsoleRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, log_level.upper(), logging.WARNING)
        ),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def on_startup(log_level: str | None = None) -> None:
    """Configure logging using the provided level or the value from settings."""
    from aeonlogic.config.settings import get_settings

    effective = (log_level or get_settings().log_level).upper()
    configure_logging(effective)


def on_shutdown() -> None:
    pass
