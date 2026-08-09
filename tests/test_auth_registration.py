from uuid import uuid4

from fastapi.testclient import TestClient
from psycopg import connect

from src.core.config import get_settings
from src.core.security import verify_password


def unique_email() -> str:
    return f"user_{uuid4().hex}@example.com"


def get_user_from_database(email: str) -> tuple[bool, int, str] | None:
    database_url = get_settings().ALEMBIC_DATABASE_URL.replace(
        "postgresql+psycopg://",
        "postgresql://",
    )

    with connect(database_url) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT is_active, group_id, hashed_password
                FROM users
                WHERE email = %s
                """,
                (email,),
            )
            return cursor.fetchone()


def test_register_user_success(client: TestClient) -> None:
    email = unique_email()
    password = "StrongPassword123"

    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": password,
        },
    )

    assert response.status_code == 201
    response_data = response.json()
    assert response_data["email"] == email
    assert response_data["is_active"] is False
    assert "hashed_password" not in response_data


def test_register_user_stores_hashed_password(client: TestClient) -> None:
    email = unique_email()
    password = "StrongPassword123"

    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": password,
        },
    )

    assert response.status_code == 201

    user = get_user_from_database(email)

    assert user is not None
    is_active, group_id, hashed_password = user
    assert is_active is False
    assert group_id == 1
    assert hashed_password != password
    assert verify_password(password, hashed_password) is True


def test_register_user_with_duplicate_email_returns_409(client: TestClient) -> None:
    email = unique_email()
    payload = {
        "email": email,
        "password": "StrongPassword123",
    }

    first_response = client.post("/api/v1/auth/register", json=payload)
    second_response = client.post("/api/v1/auth/register", json=payload)

    assert first_response.status_code == 201
    assert second_response.status_code == 409
    assert second_response.json() == {
        "detail": "User with this email already exists.",
    }
