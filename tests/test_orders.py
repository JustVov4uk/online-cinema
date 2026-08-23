from fastapi.testclient import TestClient
from psycopg import connect

from tests.test_auth_login import get_sync_database_url
from tests.test_cart import create_movie_for_cart, make_user_access_token
from tests.test_movies import make_admin_access_token


def add_movie_to_cart(
    client: TestClient,
    access_token: str,
    movie_id: int,
) -> None:
    response = client.post(
        "/api/v1/cart/items/",
        json={"movie_id": movie_id},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 201


def create_order_with_one_movie(client: TestClient) -> tuple[str, int, dict]:
    access_token = make_user_access_token(client)
    movie_id = create_movie_for_cart(client)
    add_movie_to_cart(
        client=client,
        access_token=access_token,
        movie_id=movie_id,
    )

    response = client.post(
        "/api/v1/orders/",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 201

    return access_token, movie_id, response.json()["order"]


def test_create_order_without_token_returns_401(client: TestClient) -> None:
    response = client.post("/api/v1/orders/")

    assert response.status_code == 401


def test_create_order_with_empty_cart_returns_400(client: TestClient) -> None:
    access_token = make_user_access_token(client)

    response = client.post(
        "/api/v1/orders/",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Cart is empty."}


def test_create_order_from_cart_returns_order_and_clears_cart(
    client: TestClient,
) -> None:
    access_token, movie_id, order = create_order_with_one_movie(client)

    assert order["status"] == "pending"
    assert order["total_amount"] == "9.99"
    assert len(order["items"]) == 1
    assert order["items"][0]["movie"]["id"] == movie_id
    assert order["items"][0]["price_at_order"] == "9.99"

    cart_response = client.get(
        "/api/v1/cart/",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert cart_response.status_code == 200
    assert cart_response.json()["items"] == []


def test_create_duplicate_pending_order_returns_409(client: TestClient) -> None:
    access_token, movie_id, _order = create_order_with_one_movie(client)
    add_movie_to_cart(
        client=client,
        access_token=access_token,
        movie_id=movie_id,
    )

    response = client.post(
        "/api/v1/orders/",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 409
    assert response.json() == {
        "detail": "Pending order with the same movies already exists."
    }


def test_list_my_orders_returns_only_current_user_orders(client: TestClient) -> None:
    access_token, _movie_id, created_order = create_order_with_one_movie(client)
    other_access_token, _other_movie_id, _other_order = create_order_with_one_movie(
        client
    )

    response = client.get(
        "/api/v1/orders/",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    other_response = client.get(
        "/api/v1/orders/",
        headers={"Authorization": f"Bearer {other_access_token}"},
    )

    assert response.status_code == 200
    assert [order["id"] for order in response.json()] == [created_order["id"]]
    assert other_response.status_code == 200
    assert created_order["id"] not in [
        order["id"] for order in other_response.json()
    ]


def test_retrieve_order_as_owner_returns_order(client: TestClient) -> None:
    access_token, _movie_id, created_order = create_order_with_one_movie(client)

    response = client.get(
        f"/api/v1/orders/{created_order['id']}",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 200
    assert response.json()["id"] == created_order["id"]


def test_retrieve_order_as_other_user_returns_403(client: TestClient) -> None:
    _access_token, _movie_id, created_order = create_order_with_one_movie(client)
    other_access_token = make_user_access_token(client)

    response = client.get(
        f"/api/v1/orders/{created_order['id']}",
        headers={"Authorization": f"Bearer {other_access_token}"},
    )

    assert response.status_code == 403
    assert response.json() == {"detail": "You cannot view this order."}


def test_cancel_pending_order_returns_canceled_order(client: TestClient) -> None:
    access_token, _movie_id, created_order = create_order_with_one_movie(client)

    response = client.post(
        f"/api/v1/orders/{created_order['id']}/cancel",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "canceled"


def test_cancel_paid_order_returns_400(client: TestClient) -> None:
    access_token, _movie_id, created_order = create_order_with_one_movie(client)

    with connect(get_sync_database_url()) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE orders
                SET status = 'paid'
                WHERE id = %s
                """,
                (created_order["id"],),
            )

    response = client.post(
        f"/api/v1/orders/{created_order['id']}/cancel",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Only pending orders can be canceled."}


def test_admin_can_list_orders_with_status_filter(client: TestClient) -> None:
    _access_token, _movie_id, created_order = create_order_with_one_movie(client)
    admin_access_token = make_admin_access_token(client)

    response = client.get(
        "/api/v1/admin/orders/?status=pending",
        headers={"Authorization": f"Bearer {admin_access_token}"},
    )

    assert response.status_code == 200
    assert created_order["id"] in [order["id"] for order in response.json()]
