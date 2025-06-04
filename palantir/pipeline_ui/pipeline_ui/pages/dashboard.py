"""The dashboard page."""

from datetime import datetime

import reflex as rx

from pipeline_ui.components import ErrorBoundary, PipelineList, SystemStatus
from pipeline_ui.templates import template


@template(route="/dashboard", title="Dashboard")
def dashboard() -> rx.Component:
    """The dashboard page.

    Returns:
        The UI for the dashboard page.
    """
    return rx.vstack(
        rx.heading("시스템 대시보드", size="8"),
        rx.grid(
            ErrorBoundary(
                SystemStatus(), fallback=rx.text("시스템 상태를 불러올 수 없습니다.")
            ),
            ErrorBoundary(
                PipelineList(),
                fallback=rx.text("파이프라인 목록을 불러올 수 없습니다."),
            ),
            columns=[1, 1],
            spacing="4",
            width="100%",
        ),
        rx.box(
            rx.heading("최근 활동", size="6"),
            rx.table(
                rx.thead(
                    rx.tr(
                        rx.th("시간"), rx.th("작업"), rx.th("상태"), rx.th("세부사항")
                    )
                ),
                rx.tbody(
                    rx.tr(
                        rx.td(datetime.now().strftime("%Y-%m-%d %H:%M")),
                        rx.td("파이프라인 실행"),
                        rx.td(rx.badge("완료", color_scheme="green")),
                        rx.td("PIPE-001"),
                    )
                ),
            ),
            width="100%",
            padding="4",
        ),
        width="100%",
        padding="4",
        spacing="4",
    )
