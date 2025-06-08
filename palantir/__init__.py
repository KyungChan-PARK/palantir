"""Palantir AIP - AI-based End-to-End Data Pipeline System"""

__all__ = ["core"]

__version__ = "0.1.0"

from .core.settings import settings
from .cli import app as cli_app

__all__ += ["settings", "cli_app"]
