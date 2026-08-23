from fastapi.testclient import TestClient
from psycopg import connect

from tests.test_auth_login import get_sync_database_url
from tests.test_cart import create_movie_for_cart
from tests.test_orders import add_movie_to_cart, create_order_with_one_movie
from tests.test_payments import create_payment_session, create_successful_payment


def test_successful_payment_creates_purchased_movie(client: TestClient) -> None:
    _access_token, order, _payment = create_successful_payment(client)
    order_item = order["items"][0]

    with connect(get_sync_database_url()) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT movie_id, order_item_id
                FROM purchased_movies
                WHERE order_item_id = %s
                """,
                (order_item["id"],),
            )
            purchased_movie = cursor.fetchone()

    assert purchased_movie == (order_item["movie"]["id"], order_item["id"])


def test_user_cannot_add_purchased_movie_to_cart(client: TestClient) -> None:
    access_token, order, _payment = create_successful_payment(client)
    movie_id = order["items"][0]["movie"]["id"]

    response = client.post(
        "/api/v1/cart/items/",
        json={"movie_id": movie_id},
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 409
    assert response.json() == {"detail": "Movie is already purchased."}


def test_create_order_excludes_purchased_movies_from_cart(client: TestClient) -> None:
    access_token, paid_order, _payment = create_successful_payment(client)
    purchased_movie_id = paid_order["items"][0]["movie"]["id"]
    new_movie_id = create_movie_for_cart(client)

    with connect(get_sync_database_url()) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id
                FROM carts
                WHERE user_id = %s
                """,
                (paid_order["user_id"],),
            )
            cart_id = cursor.fetchone()[0]
            cursor.execute(
                """
                INSERT INTO cart_items (cart_id, movie_id)
                VALUES (%s, %s)
                """,
                (cart_id, purchased_movie_id),
            )

    add_movie_to_cart(
        client=client,
        access_token=access_token,
        movie_id=new_movie_id,
    )

    response = client.post(
        "/api/v1/orders/",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 201
    response_data = response.json()
    assert response_data["excluded_movie_ids"] == [purchased_movie_id]
    assert len(response_data["order"]["items"]) == 1
    assert response_data["order"]["items"][0]["movie"]["id"] == new_movie_id


def test_repeated_successful_webhook_does_not_duplicate_purchased_movie(
    client: TestClient,
) -> None:
    access_token, _movie_id, order = create_order_with_one_movie(client)
    payment_session = create_payment_session(
        client=client,
        access_token=access_token,
        order_id=order["id"],
    )
    payload = {
        "order_id": order["id"],
        "external_payment_id": payment_session["external_payment_id"],
        "status": "successful",
    }

    first_response = client.post("/api/v1/payments/webhook", json=payload)
    second_response = client.post("/api/v1/payments/webhook", json=payload)

    assert first_response.status_code == 200
    assert second_response.status_code == 200

    with connect(get_sync_database_url()) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT COUNT(*)
                FROM purchased_movies
                WHERE user_id = %s
                  AND movie_id = %s
                """,
                (order["user_id"], order["items"][0]["movie"]["id"]),
            )
            purchased_count = cursor.fetchone()[0]

    assert purchased_count == 1
