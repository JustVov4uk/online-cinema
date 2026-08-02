from uuid import uuid4

from fastapi.testclient import TestClient
from psycopg import connect

from src.core.config import get_settings


def unique_email() -> str:
    return f"login_user_{uuid4().hex}@example.com"


def get_sync_database_url() -> str:
    return get_settings().ALEMBIC_DATABASE_URL.replace(
        "postgresql+psycopg://",
        "postgresql://",
    )


def activate_user_in_database(email: str) -> None:
    with connect(get_sync_database_url()) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE users
                SET is_active = true
                WHERE email = %s
                """,
                (email,),
            )


def test_login_user_success_returns_tokens(client: TestClient) -> None:
    email = unique_email()
    password = "StrongPassword123"

    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": password,
        },
    )
    assert register_response.status_code == 201

    activate_user_in_database(email)

    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )

    assert login_response.status_code == 200
    response_data = login_response.json()
    assert response_data["token_type"] == "bearer"
    assert isinstance(response_data["access_token"], str)
    assert isinstance(response_data["refresh_token"], str)
    assert response_data["access_token"] != ""
    assert response_data["refresh_token"] != ""

def test_login_user_with_wrong_password_returns_401(client: TestClient) -> None:
    email = unique_email()
    password = "StrongPassword123"

    register_response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password},
    )
    assert register_response.status_code == 201

    activate_user_in_database(email)

    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "WrongPassword123"},
    )

    assert login_response.status_code == 401
    assert login_response.json() == {"detail": "Invalid email or password."}

def test_login_inactive_user_returns_403(client: TestClient) -> None:
    email = unique_email()
    password = "StrongPassword123"

    register_response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password},
    )
    assert register_response.status_code == 201

    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )

    assert login_response.status_code == 403
    assert login_response.json() == {"detail": "User account is not active."}
