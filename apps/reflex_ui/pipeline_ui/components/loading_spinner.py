"""로딩 스피너 컴포넌트."""

from typing import Optional

import reflex as rx


class LoadingSpinner(rx.Component):
    """로딩 상태를 표시하는 컴포넌트."""

    def __init__(
        self, text: Optional[str] = None, size: str = "md", color: str = "blue"
    ):
        super().__init__()
        self.text = text
        self.size = size
        self.color = color

    def render(self) -> rx.Component:
        return rx.center(
            rx.vstack(
                rx.spinner(size=self.size, color=self.color),
                (
                    rx.text(self.text or "로딩 중...", color="gray.500")
                    if self.text
                    else None
                ),
                spacing="2",
                align="center",
            ),
            width="100%",
            height="100%",
            min_height="200px",
        )
