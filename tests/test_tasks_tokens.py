from datetime import UTC, datetime, timedelta
from uuid import uuid4

from psycopg import connect

from src.tasks.tokens import delete_expired_auth_tokens_task
from tests.test_auth_login import get_sync_database_url, unique_email


def create_user_with_auth_tokens(
    email: str,
    activation_token: str,
    password_reset_token: str,
    expires_at: datetime,
) -> None:
    with connect(get_sync_database_url()) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO user_groups (name)
                VALUES ('USER')
                ON CONFLICT (name) DO NOTHING
                """
            )
            cursor.execute(
                """
                INSERT INTO users (email, hashed_password, is_active, group_id)
                VALUES (
                    %s,
                    %s,
                    false,
                    (SELECT id FROM user_groups WHERE name = 'USER')
                )
                RETURNING id
                """,
                (email, "hashed-password"),
            )
            user_id = cursor.fetchone()[0]
            cursor.execute(
                """
                INSERT INTO activation_tokens (user_id, token, expires_at)
                VALUES (%s, %s, %s)
                """,
                (user_id, activation_token, expires_at),
            )
            cursor.execute(
                """
                INSERT INTO password_reset_tokens (user_id, token, expires_at)
                VALUES (%s, %s, %s)
                """,
                (user_id, password_reset_token, expires_at),
            )


def token_exists(table_name: str, token: str) -> bool:
    with connect(get_sync_database_url()) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                f"SELECT EXISTS(SELECT 1 FROM {table_name} WHERE token = %s)",
                (token,),
            )
            exists = cursor.fetchone()[0]

    return bool(exists)


def test_delete_expired_auth_tokens_task_removes_only_expired_tokens() -> None:
    yesterday = datetime.now(UTC) - timedelta(days=1)
    tomorrow = datetime.now(UTC) + timedelta(days=1)
    expired_activation_token = f"expired-activation-{uuid4().hex}"
    valid_activation_token = f"valid-activation-{uuid4().hex}"
    expired_reset_token = f"expired-reset-{uuid4().hex}"
    valid_reset_token = f"valid-reset-{uuid4().hex}"

    create_user_with_auth_tokens(
        email=unique_email(),
        activation_token=expired_activation_token,
        password_reset_token=expired_reset_token,
        expires_at=yesterday,
    )
    create_user_with_auth_tokens(
        email=unique_email(),
        activation_token=valid_activation_token,
        password_reset_token=valid_reset_token,
        expires_at=tomorrow,
    )

    result = delete_expired_auth_tokens_task()

    assert result["deleted_activation_tokens"] >= 1
    assert result["deleted_password_reset_tokens"] >= 1
    assert token_exists("activation_tokens", expired_activation_token) is False
    assert token_exists("activation_tokens", valid_activation_token) is True
    assert token_exists("password_reset_tokens", expired_reset_token) is False
    assert token_exists("password_reset_tokens", valid_reset_token) is True
