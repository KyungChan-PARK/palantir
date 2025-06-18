"""The dashboard page."""

from datetime import datetime

import reflex as rx

from pipeline_ui.components import ErrorBoundary, PipelineList, SystemStatus
from pipeline_ui.templates import template
from ..components.dependency_graph import dependency_graph
from ..components.loading_spinner import loading_spinner
from ..styles import COLORS


@template(route="/dashboard", title="Dashboard")
def dashboard() -> rx.Component:
    """The dashboard page.

    Returns:
        The UI for the dashboard page.
    """
    return rx.vstack(
        rx.heading("에이전트 대시보드", size="xl"),
        rx.tabs(
            rx.tab_list(
                rx.tab("의존성 그래프"),
                rx.tab("성능 메트릭"),
                rx.tab("작업 큐"),
            ),
            rx.tab_panels(
                rx.tab_panel(
                    dependency_graph(),
                ),
                rx.tab_panel(
                    rx.vstack(
                        rx.heading("성능 메트릭", size="lg"),
                        rx.text("준비 중..."),
                        align_items="center",
                    ),
                ),
                rx.tab_panel(
                    rx.vstack(
                        rx.heading("작업 큐", size="lg"),
                        rx.text("준비 중..."),
                        align_items="center",
                    ),
                ),
            ),
        ),
        width="100%",
        padding="4",
        spacing="4",
    )
