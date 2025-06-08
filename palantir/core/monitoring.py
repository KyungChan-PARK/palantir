from .metrics import RequestMetricsMiddleware


def setup_monitoring(app):
    """Attach monitoring middlewares to the FastAPI app."""
    app.add_middleware(RequestMetricsMiddleware)
