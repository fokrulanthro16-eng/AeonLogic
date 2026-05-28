from __future__ import annotations

import logging

import structlog


def configure_logging(log_level: str = "WARNING") -> None:
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="%H:%M:%S"),
            structlog.dev.ConsoleRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, log_level.upper())
        ),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def on_startup(log_level: str = "WARNING") -> None:
    configure_logging(log_level)


def on_shutdown() -> None:
    pass
