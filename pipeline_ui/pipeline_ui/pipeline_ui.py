"""Welcome to Reflex!."""

from pipeline_ui import styles

# Import all the pages.
from pipeline_ui.pages import dashboard, index, settings  # noqa: F401

import reflex as rx


class State(rx.State):
    """Define empty state to allow access to rx.State.router."""


# Create the app.
app = rx.App(style=styles.base_style)
