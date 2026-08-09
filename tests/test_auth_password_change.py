from fastapi.testclient import TestClient

from tests.test_auth_login import activate_user_in_database, unique_email


def test_password_change_success_changes_password_for_authenticated_user(
    client: TestClient,
) -> None:
    email = unique_email()
    old_password = "StrongPassword123"
    new_password = "NewStrongPassword123"

    register_response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": old_password},
    )
    assert register_response.status_code == 201

    activate_user_in_database(email)

    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": old_password},
    )
    assert login_response.status_code == 200

    access_token = login_response.json()["access_token"]

    password_change_response = client.post(
        "/api/v1/auth/password-change",
        json={
            "old_password": old_password,
            "new_password": new_password,
        },
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert password_change_response.status_code == 200
    assert password_change_response.json() == {
        "message": "Password has been changed successfully."
    }

    old_password_login_response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": old_password},
    )
    assert old_password_login_response.status_code == 401

    new_password_login_response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": new_password},
    )
    assert new_password_login_response.status_code == 200


def test_password_change_with_wrong_old_password_returns_400(
    client: TestClient,
) -> None:
    email = unique_email()
    old_password = "StrongPassword123"

    register_response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": old_password},
    )
    assert register_response.status_code == 201

    activate_user_in_database(email)

    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": old_password},
    )
    assert login_response.status_code == 200

    access_token = login_response.json()["access_token"]

    password_change_response = client.post(
        "/api/v1/auth/password-change",
        json={
            "old_password": "WrongPassword123",
            "new_password": "NewStrongPassword123",
        },
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert password_change_response.status_code == 400
    assert password_change_response.json() == {"detail": "Old password is incorrect."}
