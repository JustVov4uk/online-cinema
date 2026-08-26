from fastapi.testclient import TestClient
from psycopg import connect
from pytest import MonkeyPatch

from tests.test_auth_login import (
    activate_user_in_database,
    get_sync_database_url,
    unique_email,
)


def get_authenticated_headers(client: TestClient) -> dict[str, str]:
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
    return {"Authorization": f"Bearer {access_token}"}


def get_profile_avatar_from_database(user_id: int) -> str | None:
    with connect(get_sync_database_url()) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT avatar
                FROM user_profiles
                WHERE user_id = %s
                """,
                (user_id,),
            )
            row = cursor.fetchone()

    if row is None:
        return None

    return str(row[0])


def test_upload_avatar_success_updates_current_user_profile(
    client: TestClient,
    monkeypatch: MonkeyPatch,
) -> None:
    avatar_url = "http://localhost:9000/online-cinema-media/avatars/users/1/avatar.png"

    def fake_upload_avatar_to_storage(
        *,
        user_id: int,
        content: bytes,
        content_type: str,
    ) -> str:
        assert user_id > 0
        assert content == b"fake-png-content"
        assert content_type == "image/png"
        return avatar_url

    monkeypatch.setattr(
        "src.api.v1.profiles.upload_avatar_to_storage",
        fake_upload_avatar_to_storage,
    )

    headers = get_authenticated_headers(client)

    response = client.post(
        "/api/v1/profile/avatar",
        headers=headers,
        files={"file": ("avatar.png", b"fake-png-content", "image/png")},
    )

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["avatar"] == avatar_url
    assert get_profile_avatar_from_database(response_data["user_id"]) == avatar_url


def test_upload_avatar_with_invalid_file_type_returns_400(
    client: TestClient,
) -> None:
    headers = get_authenticated_headers(client)

    response = client.post(
        "/api/v1/profile/avatar",
        headers=headers,
        files={"file": ("avatar.txt", b"text-content", "text/plain")},
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Avatar must be a JPEG, PNG, or WebP image."
    }
