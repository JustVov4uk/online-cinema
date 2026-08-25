import asyncio
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from src.core.celery_app import celery_app
from src.core.config import get_settings
from src.repositories.accounts import delete_expired_auth_tokens


@celery_app.task(name="tokens.delete_expired_auth_tokens")
def delete_expired_auth_tokens_task() -> dict[str, int]:
    return asyncio.run(_delete_expired_auth_tokens())


async def _delete_expired_auth_tokens() -> dict[str, int]:
    settings = get_settings()
    engine = create_async_engine(settings.DATABASE_URL, poolclass=NullPool)
    session_factory = async_sessionmaker(bind=engine, expire_on_commit=False)

    try:
        async with session_factory() as session:
            deleted_activation_tokens, deleted_password_reset_tokens = (
                await delete_expired_auth_tokens(
                    session=session,
                    now=datetime.now(UTC),
                )
            )
            await session.commit()
    finally:
        await engine.dispose()

    return {
        "deleted_activation_tokens": deleted_activation_tokens,
        "deleted_password_reset_tokens": deleted_password_reset_tokens,
    }
