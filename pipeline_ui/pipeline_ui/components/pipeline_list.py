"""파이프라인 목록 컴포넌트."""

from datetime import datetime
from typing import Any, Dict

import httpx
import reflex as rx


class PipelineList(rx.Component):
    """파이프라인 목록을 표시하는 컴포넌트."""

    def __init__(self):
        super().__init__()
        self.state = {
            "pipelines": [],
            "loading": True,
            "error": None
        }

    def get_initial_state(self) -> Dict[str, Any]:
        return self.state

    async def fetch_pipelines(self):
        """파이프라인 목록을 가져옵니다."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get("http://localhost:8000/pipeline/list")
                if response.status_code == 200:
                    data = response.json()
                    self.state.update({
                        "pipelines": data["pipelines"],
                        "loading": False,
                        "error": None
                    })
                else:
                    self.state.update({
                        "error": "파이프라인 목록을 가져올 수 없습니다.",
                        "loading": False
                    })
        except Exception as e:
            self.state.update({
                "error": str(e),
                "loading": False
            })

    def get_status_color(self, status: str) -> str:
        """상태에 따른 색상을 반환합니다."""
        colors = {
            "running": "blue",
            "completed": "green",
            "failed": "red",
            "pending": "yellow"
        }
        return colors.get(status.lower(), "gray")

    def format_date(self, date_str: str) -> str:
        """날짜를 포맷팅합니다."""
        try:
            dt = datetime.fromisoformat(date_str)
            return dt.strftime("%Y-%m-%d %H:%M")
        except:
            return date_str

    def render(self) -> rx.Component:
        if self.state["loading"]:
            return rx.spinner()
        
        if self.state["error"]:
            return rx.alert(
                self.state["error"],
                status="error"
            )

        return rx.vstack(
            rx.heading("파이프라인 목록", size="6"),
            rx.table(
                rx.thead(
                    rx.tr(
                        rx.th("ID"),
                        rx.th("이름"),
                        rx.th("상태"),
                        rx.th("시작 시간"),
                        rx.th("완료 시간"),
                        rx.th("작업")
                    )
                ),
                rx.tbody(
                    *[
                        rx.tr(
                            rx.td(p["id"]),
                            rx.td(p["name"]),
                            rx.td(
                                rx.badge(
                                    p["status"],
                                    color_scheme=self.get_status_color(p["status"])
                                )
                            ),
                            rx.td(self.format_date(p["start_time"])),
                            rx.td(self.format_date(p["end_time"])),
                            rx.td(
                                rx.hstack(
                                    rx.button(
                                        "상세보기",
                                        size="sm",
                                        on_click=lambda: self.view_details(p["id"])
                                    ),
                                    rx.button(
                                        "로그",
                                        size="sm",
                                        on_click=lambda: self.view_logs(p["id"])
                                    )
                                )
                            )
                        )
                        for p in self.state["pipelines"]
                    ]
                )
            ),
            width="100%",
            padding="4",
            border="1px solid",
            border_color="gray.200",
            border_radius="lg"
        )

    def view_details(self, pipeline_id: str):
        """파이프라인 상세 정보를 봅니다."""
        # TODO: 상세 정보 페이지로 이동
        pass

    def view_logs(self, pipeline_id: str):
        """파이프라인 로그를 봅니다."""
        # TODO: 로그 페이지로 이동
        pass 