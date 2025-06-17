from apscheduler.schedulers.background import BackgroundScheduler


class DummyScheduler:
    """Fallback scheduler used during testing."""

    def __init__(self):
        self.jobs = []

    def add_job(self, func, *a, **k):
        self.jobs.append((func, a, k))


def add_pipeline_job(dag):
    """Schedule pipeline execution (placeholder)."""
    print(f"[SCHEDULED] DAG: {dag.get('dag_name')}")


try:
    scheduler = BackgroundScheduler()
    scheduler.start()
except Exception:  # pragma: no cover - APScheduler optional
    scheduler = DummyScheduler()
