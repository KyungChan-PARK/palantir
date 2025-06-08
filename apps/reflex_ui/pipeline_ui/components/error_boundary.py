"""에러 바운더리 컴포넌트."""

from typing import Optional

import reflex as rx


class ErrorBoundary(rx.Component):
    """자식 컴포넌트의 에러를 처리하는 컴포넌트."""

    def __init__(self, child: rx.Component, fallback: Optional[rx.Component] = None):
        super().__init__()
        self.child = child
        self.fallback = fallback or rx.alert("오류가 발생했습니다.", status="error")
        self.state = {"has_error": False, "error": None}

    def get_initial_state(self) -> dict:
        return self.state

    def on_error(self, error: Exception):
        """에러 발생 시 호출됩니다."""
        self.state.update({"has_error": True, "error": str(error)})

    def render(self) -> rx.Component:
        if self.state["has_error"]:
            return rx.vstack(
                self.fallback,
                rx.text(
                    f"에러 상세: {self.state['error']}",
                    color="gray.500",
                    font_size="sm",
                ),
                width="100%",
                padding="4",
            )
        return self.child
