from fastapi.testclient import TestClient

from tests.test_cart import make_user_access_token
from tests.test_movies import make_admin_access_token
from tests.test_orders import create_order_with_one_movie


def create_payment_session(
    client: TestClient,
    access_token: str,
    order_id: int,
) -> dict:
    response = client.post(
        "/api/v1/payments/",
        json={"order_id": order_id, "payment_method": "mock_card"},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 201

    return response.json()


def create_successful_payment(client: TestClient) -> tuple[str, dict, dict]:
    access_token, _movie_id, order = create_order_with_one_movie(client)
    payment_session = create_payment_session(
        client=client,
        access_token=access_token,
        order_id=order["id"],
    )

    webhook_response = client.post(
        "/api/v1/payments/webhook",
        json={
            "order_id": order["id"],
            "external_payment_id": payment_session["external_payment_id"],
            "status": "successful",
        },
    )
    assert webhook_response.status_code == 200

    return access_token, order, webhook_response.json()


def test_create_payment_without_token_returns_401(client: TestClient) -> None:
    response = client.post(
        "/api/v1/payments/",
        json={"order_id": 1, "payment_method": "mock_card"},
    )

    assert response.status_code == 401


def test_create_payment_session_for_pending_order_returns_mock_session(
    client: TestClient,
) -> None:
    access_token, _movie_id, order = create_order_with_one_movie(client)

    response = client.post(
        "/api/v1/payments/",
        json={"order_id": order["id"], "payment_method": "mock_card"},
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 201
    response_data = response.json()
    assert response_data["order_id"] == order["id"]
    assert response_data["amount"] == "9.99"
    assert response_data["external_payment_id"].startswith("mock_")
    assert response_data["payment_url"].endswith(response_data["external_payment_id"])


def test_create_payment_session_with_unknown_method_returns_400(
    client: TestClient,
) -> None:
    access_token, _movie_id, order = create_order_with_one_movie(client)

    response = client.post(
        "/api/v1/payments/",
        json={"order_id": order["id"], "payment_method": "cash"},
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Payment method is not available. Use mock_card in test mode."
    }


def test_create_payment_session_for_other_user_order_returns_403(
    client: TestClient,
) -> None:
    _access_token, _movie_id, order = create_order_with_one_movie(client)
    other_access_token = make_user_access_token(client)

    response = client.post(
        "/api/v1/payments/",
        json={"order_id": order["id"], "payment_method": "mock_card"},
        headers={"Authorization": f"Bearer {other_access_token}"},
    )

    assert response.status_code == 403
    assert response.json() == {"detail": "You cannot pay for this order."}


def test_successful_webhook_creates_payment_and_marks_order_paid(
    client: TestClient,
) -> None:
    access_token, order, payment = create_successful_payment(client)

    assert payment["status"] == "successful"
    assert payment["order_id"] == order["id"]
    assert payment["amount"] == "9.99"
    assert len(payment["items"]) == 1
    assert payment["items"][0]["price_at_payment"] == "9.99"

    order_response = client.get(
        f"/api/v1/orders/{order['id']}",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert order_response.status_code == 200
    assert order_response.json()["status"] == "paid"


def test_canceled_webhook_does_not_mark_order_paid(client: TestClient) -> None:
    access_token, _movie_id, order = create_order_with_one_movie(client)
    payment_session = create_payment_session(
        client=client,
        access_token=access_token,
        order_id=order["id"],
    )

    webhook_response = client.post(
        "/api/v1/payments/webhook",
        json={
            "order_id": order["id"],
            "external_payment_id": payment_session["external_payment_id"],
            "status": "canceled",
        },
    )

    assert webhook_response.status_code == 200
    assert webhook_response.json()["status"] == "canceled"

    order_response = client.get(
        f"/api/v1/orders/{order['id']}",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert order_response.status_code == 200
    assert order_response.json()["status"] == "pending"


def test_list_my_payments_returns_only_current_user_payments(
    client: TestClient,
) -> None:
    access_token, _order, payment = create_successful_payment(client)
    other_access_token, _other_order, _other_payment = create_successful_payment(client)

    response = client.get(
        "/api/v1/payments/",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    other_response = client.get(
        "/api/v1/payments/",
        headers={"Authorization": f"Bearer {other_access_token}"},
    )

    assert response.status_code == 200
    assert [item["id"] for item in response.json()] == [payment["id"]]
    assert other_response.status_code == 200
    assert payment["id"] not in [item["id"] for item in other_response.json()]


def test_retrieve_payment_as_owner_returns_payment(client: TestClient) -> None:
    access_token, _order, payment = create_successful_payment(client)

    response = client.get(
        f"/api/v1/payments/{payment['id']}",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 200
    assert response.json()["id"] == payment["id"]


def test_retrieve_payment_as_other_user_returns_403(client: TestClient) -> None:
    _access_token, _order, payment = create_successful_payment(client)
    other_access_token = make_user_access_token(client)

    response = client.get(
        f"/api/v1/payments/{payment['id']}",
        headers={"Authorization": f"Bearer {other_access_token}"},
    )

    assert response.status_code == 403
    assert response.json() == {"detail": "You cannot view this payment."}


def test_admin_can_list_payments_with_status_filter(client: TestClient) -> None:
    _access_token, _order, payment = create_successful_payment(client)
    admin_access_token = make_admin_access_token(client)

    response = client.get(
        "/api/v1/admin/payments/?status=successful",
        headers={"Authorization": f"Bearer {admin_access_token}"},
    )

    assert response.status_code == 200
    assert payment["id"] in [item["id"] for item in response.json()]
