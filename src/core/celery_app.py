from celery import Celery

from src.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "online_cinema",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["src.tasks.email", "src.tasks.tokens"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_always_eager=settings.CELERY_TASK_ALWAYS_EAGER,
    task_eager_propagates=True,
    beat_schedule={
        "delete-expired-auth-tokens": {
            "task": "tokens.delete_expired_auth_tokens",
            "schedule": settings.CELERY_DELETE_EXPIRED_TOKENS_INTERVAL_SECONDS,
        },
    },
)
