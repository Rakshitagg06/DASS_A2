"""Wallet, loyalty, and order black-box tests for QuickCart."""

import pytest


def _order_user_id(api) -> int:
    return 31


def _cancel_user_id(api) -> int:
    return 33


def _wallet_user_id(api) -> int:
    return api.review_user_id()


def _add_item(api, user_id: int, product_id: int, quantity: int):
    response = api.post(
        "/cart/add",
        user_id=user_id,
        json={"product_id": product_id, "quantity": quantity},
    )
    assert response.status_code == 200


def _create_order(api, user_id: int, product_id: int = 1, quantity: int = 1):
    _add_item(api, user_id, product_id=product_id, quantity=quantity)
    response = api.post(
        "/checkout",
        user_id=user_id,
        json={"payment_method": "CARD"},
    )
    assert response.status_code == 200
    return response.json()["order_id"]


def test_bb84(api):
    user_id = _wallet_user_id(api)
    starting_balance = api.user_json("/wallet", user_id)["wallet_balance"]

    response = api.post("/wallet/add", user_id=user_id, json={"amount": 50})

    assert response.status_code == 200
    assert response.json()["wallet_balance"] == pytest.approx(starting_balance + 50)


def test_bb85(api):
    user_id = _wallet_user_id(api)

    zero_amount = api.post("/wallet/add", user_id=user_id, json={"amount": 0})
    too_large = api.post("/wallet/add", user_id=user_id, json={"amount": 100001})

    assert zero_amount.status_code == 400
    assert too_large.status_code == 400


def test_bb86(api):
    user_id = _wallet_user_id(api)

    response = api.post("/wallet/pay", user_id=user_id, json={"amount": 100})

    assert response.status_code == 400
    assert "Insufficient" in response.json()["error"]


@pytest.mark.xfail(
    strict=False,
    reason="Alternate runtime report: wallet payments greater than balance can incorrectly succeed.",
)
def test_bb87(api):
    user_id = 1
    current_balance = api.user_json("/wallet", user_id)["wallet_balance"]

    response = api.post(
        "/wallet/pay",
        user_id=user_id,
        json={"amount": current_balance + 1},
    )

    assert response.status_code == 400
    assert "Insufficient" in response.json()["error"]


@pytest.mark.xfail(
    strict=True,
    reason="QuickCart over-deducts wallet payments instead of charging the exact amount.",
)
def test_bb88(api):
    user_id = _wallet_user_id(api)
    starting_balance = api.user_json("/wallet", user_id)["wallet_balance"]
    api.post("/wallet/add", user_id=user_id, json={"amount": 50})

    response = api.post("/wallet/pay", user_id=user_id, json={"amount": 25})

    assert response.status_code == 200
    assert response.json()["wallet_balance"] == pytest.approx(starting_balance + 25)


def test_bb89(api):
    user_id = _wallet_user_id(api)
    starting_points = api.user_json("/loyalty", user_id)["loyalty_points"]

    response = api.post("/loyalty/redeem", user_id=user_id, json={"points": 10})

    assert response.status_code == 200
    assert response.json()["loyalty_points"] == starting_points - 10


def test_bb90(api):
    user_id = _wallet_user_id(api)
    current_points = api.user_json("/loyalty", user_id)["loyalty_points"]

    zero_points = api.post("/loyalty/redeem", user_id=user_id, json={"points": 0})
    too_many_points = api.post(
        "/loyalty/redeem",
        user_id=user_id,
        json={"points": current_points + 1},
    )

    assert zero_points.status_code == 400
    assert too_many_points.status_code == 400


@pytest.mark.xfail(
    strict=True,
    reason="QuickCart invoices do not always match the checkout total for fresh orders.",
)
def test_bb91(api):
    user_id = _order_user_id(api)
    order_id = _create_order(api, user_id)

    orders = api.user_json("/orders", user_id)
    detail = api.user_json(f"/orders/{order_id}", user_id)
    invoice = api.user_json(f"/orders/{order_id}/invoice", user_id)

    assert any(order["order_id"] == order_id for order in orders)
    assert detail["order_id"] == order_id
    assert detail["total_amount"] == 126
    assert invoice["order_id"] == str(order_id)
    assert invoice["subtotal"] == 120
    assert invoice["gst_amount"] == 6
    assert invoice["total_amount"] == 126


@pytest.mark.xfail(
    strict=True,
    reason="QuickCart can hang when cancelling a newly placed order.",
)
def test_bb92(api):
    user_id = _cancel_user_id(api)
    stock_before_product_1 = api.user_json("/products/1", user_id)["stock_quantity"]
    stock_before_product_3 = api.user_json("/products/3", user_id)["stock_quantity"]
    _add_item(api, user_id, product_id=1, quantity=6)
    _add_item(api, user_id, product_id=3, quantity=7)
    checkout = api.post(
        "/checkout",
        user_id=user_id,
        json={"payment_method": "CARD"},
    )
    assert checkout.status_code == 200
    order_id = checkout.json()["order_id"]
    stock_after_checkout_product_1 = api.user_json("/products/1", user_id)[
        "stock_quantity"
    ]
    stock_after_checkout_product_3 = api.user_json("/products/3", user_id)[
        "stock_quantity"
    ]

    response = api.post(f"/orders/{order_id}/cancel", user_id=user_id, timeout=10)

    assert response.status_code == 200
    assert response.json()["order_status"] == "CANCELLED"
    assert stock_after_checkout_product_1 == stock_before_product_1 - 6
    assert stock_after_checkout_product_3 == stock_before_product_3 - 7
    assert api.user_json(f"/orders/{order_id}", user_id)["order_status"] == "CANCELLED"
    assert (
        api.user_json("/products/1", user_id)["stock_quantity"]
        == stock_before_product_1
    )
    assert (
        api.user_json("/products/3", user_id)["stock_quantity"]
        == stock_before_product_3
    )


def test_bb93(api):
    user_id = _order_user_id(api)

    response = api.post("/orders/999999/cancel", user_id=user_id)

    assert response.status_code == 404
    assert response.json()["error"] == "Order not found"


def test_bb94(api):
    user_id, order_id = api.delivered_order()

    response = api.post(f"/orders/{order_id}/cancel", user_id=user_id)

    assert response.status_code == 400
    assert response.json()["error"] == "Cannot cancel delivered order"
