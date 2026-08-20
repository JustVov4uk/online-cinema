from fastapi.testclient import TestClient

from tests.test_auth_login import activate_user_in_database, unique_email
from tests.test_movies import (
    make_admin_access_token,
    seed_movie_reference_data,
    valid_movie_payload,
)


def make_user_access_token(client: TestClient) -> str:
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

    return str(login_response.json()["access_token"])


def create_movie_for_cart(client: TestClient) -> int:
    reference_data = seed_movie_reference_data()
    admin_access_token = make_admin_access_token(client)
    payload = valid_movie_payload(
        director_id=reference_data["director_id"],
        certification_id=reference_data["certification_id"],
        genre_ids=reference_data["genre_ids"],
        star_ids=reference_data["star_ids"],
    )

    response = client.post(
        "/api/v1/movies/",
        json=payload,
        headers={"Authorization": f"Bearer {admin_access_token}"},
    )
    assert response.status_code == 201

    return int(response.json()["id"])


def test_get_cart_without_token_returns_401(client: TestClient) -> None:
    response = client.get("/api/v1/cart/")

    assert response.status_code == 401


def test_get_cart_with_user_returns_empty_cart(client: TestClient) -> None:
    access_token = make_user_access_token(client)

    response = client.get(
        "/api/v1/cart/",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 200
    response_data = response.json()
    assert isinstance(response_data["id"], int)
    assert response_data["items"] == []


def test_add_movie_to_cart_returns_updated_cart(client: TestClient) -> None:
    access_token = make_user_access_token(client)
    movie_id = create_movie_for_cart(client)

    response = client.post(
        "/api/v1/cart/items/",
        json={"movie_id": movie_id},
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 201
    response_data = response.json()
    assert len(response_data["items"]) == 1
    assert response_data["items"][0]["movie"]["id"] == movie_id


def test_add_same_movie_to_cart_twice_returns_409(client: TestClient) -> None:
    access_token = make_user_access_token(client)
    movie_id = create_movie_for_cart(client)
    headers = {"Authorization": f"Bearer {access_token}"}

    first_response = client.post(
        "/api/v1/cart/items/",
        json={"movie_id": movie_id},
        headers=headers,
    )
    assert first_response.status_code == 201

    second_response = client.post(
        "/api/v1/cart/items/",
        json={"movie_id": movie_id},
        headers=headers,
    )

    assert second_response.status_code == 409
    assert second_response.json() == {"detail": "Movie is already in cart."}


def test_delete_cart_item_removes_item_from_cart(client: TestClient) -> None:
    access_token = make_user_access_token(client)
    movie_id = create_movie_for_cart(client)
    headers = {"Authorization": f"Bearer {access_token}"}

    add_response = client.post(
        "/api/v1/cart/items/",
        json={"movie_id": movie_id},
        headers=headers,
    )
    assert add_response.status_code == 201
    cart_item_id = add_response.json()["items"][0]["id"]

    delete_response = client.delete(
        f"/api/v1/cart/items/{cart_item_id}",
        headers=headers,
    )

    assert delete_response.status_code == 204

    cart_response = client.get(
        "/api/v1/cart/",
        headers=headers,
    )

    assert cart_response.status_code == 200
    assert cart_response.json()["items"] == []


def test_clear_cart_removes_all_items(client: TestClient) -> None:
    access_token = make_user_access_token(client)
    first_movie_id = create_movie_for_cart(client)
    second_movie_id = create_movie_for_cart(client)
    headers = {"Authorization": f"Bearer {access_token}"}

    first_add_response = client.post(
        "/api/v1/cart/items/",
        json={"movie_id": first_movie_id},
        headers=headers,
    )
    assert first_add_response.status_code == 201

    second_add_response = client.post(
        "/api/v1/cart/items/",
        json={"movie_id": second_movie_id},
        headers=headers,
    )
    assert second_add_response.status_code == 201

    clear_response = client.delete(
        "/api/v1/cart/",
        headers=headers,
    )

    assert clear_response.status_code == 204

    cart_response = client.get(
        "/api/v1/cart/",
        headers=headers,
    )

    assert cart_response.status_code == 200
    assert cart_response.json()["items"] == []
