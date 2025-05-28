from fastapi import FastAPI

from palantir.api.metrics import router as metrics_router

app = FastAPI()
app.include_router(metrics_router)
