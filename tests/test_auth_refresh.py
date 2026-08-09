from fastapi.testclient import TestClient

from tests.test_auth_login import activate_user_in_database, unique_email


def test_refresh_token_success_returns_new_access_token(client: TestClient) -> None:
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

    refresh_token = login_response.json()["refresh_token"]

    refresh_response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )

    assert refresh_response.status_code == 200
    assert "access_token" in refresh_response.json()
    assert refresh_response.json()["token_type"] == "bearer"


def test_refresh_token_with_invalid_token_returns_401(client: TestClient) -> None:
    refresh_response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": "invalid-token"},
    )

    assert refresh_response.status_code == 401
    assert refresh_response.json() == {"detail": "Invalid refresh token."}