from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_client import Counter

# Custom metric: count how many times the agent orchestrator loop runs
agent_loop_total = Counter(
    "agent_loop_total",
    "Total number of orchestrator loops executed",
)


def setup_monitoring(app):
    """Attach Prometheus Instrumentator to FastAPI app."""
    Instrumentator().instrument(app).expose(app)
