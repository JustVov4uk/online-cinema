from fastapi.testclient import TestClient
from psycopg import connect

from tests.test_auth_login import get_sync_database_url, unique_email


def get_activation_token_from_database(email: str) -> str:
    with connect(get_sync_database_url()) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT activation_tokens.token
                FROM activation_tokens
                JOIN users ON activation_tokens.user_id = users.id
                WHERE users.email = %s
                """,
                (email,),
            )
            token = cursor.fetchone()[0]

    return str(token)


def get_user_is_active_from_database(email: str) -> bool:
    with connect(get_sync_database_url()) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT is_active
                FROM users
                WHERE email = %s
                """,
                (email,),
            )
            is_active = cursor.fetchone()[0]

    return bool(is_active)


def test_activate_user_success(client: TestClient) -> None:
    email = unique_email()
    password = "StrongPassword123"

    register_response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password},
    )
    assert register_response.status_code == 201

    assert get_user_is_active_from_database(email) is False

    token = get_activation_token_from_database(email)

    activation_response = client.post(
        "/api/v1/auth/activate",
        json={"token": token},
    )

    assert activation_response.status_code == 200
    assert activation_response.json()["email"] == email
    assert activation_response.json()["is_active"] is True
    assert get_user_is_active_from_database(email) is True


def test_activate_user_with_same_token_twice_returns_400(client: TestClient) -> None:
    email = unique_email()
    password = "StrongPassword123"

    register_response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password},
    )
    assert register_response.status_code == 201

    token = get_activation_token_from_database(email)

    first_activation_response = client.post(
        "/api/v1/auth/activate",
        json={"token": token},
    )
    assert first_activation_response.status_code == 200

    second_activation_response = client.post(
        "/api/v1/auth/activate",
        json={"token": token},
    )

    assert second_activation_response.status_code == 400
    assert second_activation_response.json() == {"detail": "Invalid activation token."}


def test_resend_activation_token_for_inactive_user_replaces_old_token(
    client: TestClient,
) -> None:
    email = unique_email()
    password = "StrongPassword123"

    register_response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password},
    )
    assert register_response.status_code == 201

    old_token = get_activation_token_from_database(email)

    resend_response = client.post(
        "/api/v1/auth/activation/resend",
        json={"email": email},
    )

    assert resend_response.status_code == 200
    assert resend_response.json() == {
        "message": "If this email exists and is not active,"
                   " activation instructions were sent."
    }

    new_token = get_activation_token_from_database(email)

    assert new_token != old_token
