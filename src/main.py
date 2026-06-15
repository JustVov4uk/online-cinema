from fastapi import FastAPI
from src.core.config import get_settings
from src.api.v1.health import router as health_router

settings = get_settings()

app = FastAPI(title=settings.PROJECT_NAME)

app.include_router(health_router, prefix=settings.API_V1_PREFIX)
