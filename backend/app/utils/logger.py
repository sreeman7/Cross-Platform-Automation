"""Application logger configuration."""

import logging


def configure_logging() -> None:
    """Configure root logging once for the application."""

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
