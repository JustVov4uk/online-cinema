from fastapi.testclient import TestClient
from psycopg import connect

from tests.test_auth_login import get_sync_database_url, unique_email


def get_password_reset_token_from_database(email: str) -> str:
    with connect(get_sync_database_url()) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT password_reset_tokens.token
                FROM password_reset_tokens
                JOIN users ON password_reset_tokens.user_id = users.id
                WHERE users.email = %s
                """,
                (email,),
            )
            token = cursor.fetchone()[0]

    return str(token)


def test_password_reset_request_for_existing_user_creates_token(
    client: TestClient,
) -> None:
    email = unique_email()
    password = "StrongPassword123"
    expected_response = {
        "message": "If this email exists, password reset instructions were sent."
    }

    register_response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password},
    )
    assert register_response.status_code == 201

    reset_response = client.post(
        "/api/v1/auth/password-reset/request",
        json={"email": email},
    )

    assert reset_response.status_code == 200
    assert reset_response.json() == expected_response

    reset_token = get_password_reset_token_from_database(email)

    assert reset_token != ""


def test_password_reset_request_for_unknown_email_returns_generic_response(
    client: TestClient,
) -> None:
    expected_response = {
        "message": "If this email exists, password reset instructions were sent."
    }

    reset_response = client.post(
        "/api/v1/auth/password-reset/request",
        json={"email": unique_email()},
    )

    assert reset_response.status_code == 200
    assert reset_response.json() == expected_response
