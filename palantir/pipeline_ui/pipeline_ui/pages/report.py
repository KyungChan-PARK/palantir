import reflex as rx
import requests


class ReportState(rx.State):
    job_id: str = "1"
    approved: bool = False
    rejected: bool = False
    plot_html: str = ""

    def on_load(self):
        # job_id는 URL에서 추출하거나 기본값 사용
        try:
            url_job_id = rx.router.page_params.get("job_id")
            if url_job_id:
                self.job_id = url_job_id
        except Exception:
            pass
        self.fetch_plot()

    def fetch_plot(self):
        url = f"http://localhost:8000/report/{self.job_id}?format=html"
        resp = requests.get(url)
        if resp.status_code == 200:
            self.plot_html = resp.text
        else:
            self.plot_html = f"<h3>Job {self.job_id} not found</h3>"

    def approve(self):
        resp = requests.post(
            f"http://localhost:8000/report/{self.job_id}/action",
            data={"action": "approve"},
        )
        if resp.status_code == 200 or resp.status_code == 303:
            self.approved = True
            self.rejected = False
        self.fetch_plot()

    def reject(self):
        resp = requests.post(
            f"http://localhost:8000/report/{self.job_id}/action",
            data={"action": "reject"},
        )
        if resp.status_code == 200 or resp.status_code == 303:
            self.rejected = True
            self.approved = False
        self.fetch_plot()


def report():
    state = ReportState()
    return rx.center(
        rx.vstack(
            rx.html(state.plot_html),
            rx.hstack(
                rx.button(
                    "Approve",
                    color_scheme="green",
                    on_click=state.approve,
                    is_disabled=state.approved,
                ),
                rx.button(
                    "Reject",
                    color_scheme="red",
                    on_click=state.reject,
                    is_disabled=state.rejected,
                ),
            ),
            rx.cond(state.approved, rx.text("✅ Approved!", color="green")),
            rx.cond(state.rejected, rx.text("❌ Rejected!", color="red")),
        ),
        height="100vh",
    )


app = rx.App()
app.add_page(report, route="/report/[job_id]")
