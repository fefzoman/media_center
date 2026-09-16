"""Application entry point."""

from fastapi import FastAPI

from media_center.api.health import router as health_router

app = FastAPI(
    title="My Media",
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url=None,
    openapi_url="/api/openapi.json",
)
app.include_router(health_router, prefix="/api/v1")
