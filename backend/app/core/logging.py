"""Structured logging setup.

Owner: Member 1. Keeps request/app logs consistently formatted so latency and
data-quality incident counts (System-Design.md 2.10) are easy to grep/aggregate
during the demo, without pulling in a heavyweight logging stack.
"""
import logging
import sys

from app.core.config import get_settings


def configure_logging() -> None:
    settings = get_settings()
    root = logging.getLogger()
    if root.handlers:
        # Already configured (e.g. re-imported under uvicorn --reload); avoid duplicate handlers.
        root.setLevel(settings.LOG_LEVEL)
        return

    handler = logging.StreamHandler(stream=sys.stdout)
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S%z",
        )
    )
    root.addHandler(handler)
    root.setLevel(settings.LOG_LEVEL)

    # Quiet noisy third-party loggers unless we're debugging.
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.INFO if settings.LOG_LEVEL == "DEBUG" else logging.WARNING
    )
