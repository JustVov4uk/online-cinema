from fastapi import FastAPI
from src.api.v1.health import router as health_router

app = FastAPI(title="Online Cinema API")

api_version_prefix = "/api/v1"

app.include_router(health_router, prefix=api_version_prefix)