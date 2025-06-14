"""시스템 상태 컴포넌트."""

from typing import Any, Dict

import httpx
import reflex as rx


class SystemStatus(rx.Component):
    """시스템 상태를 표시하는 컴포넌트."""

    def __init__(self):
        super().__init__()
        self.state = {
            "cpu": 0,
            "memory": 0,
            "disk": 0,
            "network": 0,
            "loading": True,
            "error": None,
        }

    def get_initial_state(self) -> Dict[str, Any]:
        return self.state

    async def fetch_metrics(self):
        """시스템 메트릭을 가져옵니다."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get("http://localhost:8000/metrics")
                if response.status_code == 200:
                    metrics = response.json()
                    self.state.update(
                        {
                            "cpu": metrics["system"]["cpu"],
                            "memory": metrics["system"]["memory"]["percent"],
                            "disk": metrics["system"]["disk"]["percent"],
                            "network": metrics["system"]["network"]["bytes_sent"],
                            "loading": False,
                            "error": None,
                        }
                    )
                else:
                    self.state.update(
                        {"error": "메트릭을 가져올 수 없습니다.", "loading": False}
                    )
        except Exception as e:
            self.state.update({"error": str(e), "loading": False})

    def render(self) -> rx.Component:
        if self.state["loading"]:
            return rx.spinner()

        if self.state["error"]:
            return rx.alert(self.state["error"], status="error")

        return rx.vstack(
            rx.heading("시스템 상태", size="6"),
            rx.grid(
                rx.box(
                    rx.text("CPU 사용량"),
                    rx.progress(value=self.state["cpu"], max=100, color_scheme="blue"),
                    rx.text(f"{self.state['cpu']}%"),
                ),
                rx.box(
                    rx.text("메모리 사용량"),
                    rx.progress(
                        value=self.state["memory"], max=100, color_scheme="green"
                    ),
                    rx.text(f"{self.state['memory']}%"),
                ),
                rx.box(
                    rx.text("디스크 사용량"),
                    rx.progress(
                        value=self.state["disk"], max=100, color_scheme="purple"
                    ),
                    rx.text(f"{self.state['disk']}%"),
                ),
                columns=[1],
                spacing="4",
                width="100%",
            ),
            width="100%",
            padding="4",
            border="1px solid",
            border_color="gray.200",
            border_radius="lg",
        )
