from fastapi.testclient import TestClient

from tests.test_auth_login import activate_user_in_database, unique_email


def test_get_me_success_returns_current_user(client: TestClient) -> None:
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
        json={"email": email, "password": password},
    )
    assert login_response.status_code == 200

    access_token = login_response.json()["access_token"]

    me_response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert me_response.status_code == 200
    assert me_response.json()["email"] == email
    assert me_response.json()["is_active"] is True
