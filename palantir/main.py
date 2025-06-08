from fastapi import FastAPI
from palantir.api.ask import router as ask_router
from palantir.api.metrics import router as metrics_router
from palantir.api.ontology import router as ontology_router
from palantir.api.pipeline import router as pipeline_router
from palantir.api.report import router as report_router
from palantir.api.status import router as status_router
from palantir.api.upload import router as upload_router
from palantir.api.registry import router as registry_router
from palantir.api.actions import router as actions_router
from palantir.core.logging_config import setup_logger
from asgi_correlation_id import CorrelationIdMiddleware
from loguru import logger

app = FastAPI()

setup_logger()

app.add_middleware(CorrelationIdMiddleware)

app.include_router(ask_router)
app.include_router(metrics_router)
app.include_router(ontology_router)
app.include_router(pipeline_router)
app.include_router(report_router)
app.include_router(status_router)
app.include_router(upload_router)
app.include_router(registry_router)
app.include_router(actions_router)
