"""Cart, coupon, and checkout black-box tests for QuickCart."""

import pytest


def _user_id(api) -> int:
    return api.clean_user_id()


def _cart(api, user_id: int):
    response = api.get("/cart", user_id=user_id)
    assert response.status_code == 200
    return response.json()


def _add_item(api, user_id: int, product_id: int, quantity: int):
    response = api.post(
        "/cart/add",
        user_id=user_id,
        json={"product_id": product_id, "quantity": quantity},
    )
    assert response.status_code == 200
    return response


def test_bb01(api):
    user_id = _user_id(api)

    _add_item(api, user_id, product_id=27, quantity=2)
    _add_item(api, user_id, product_id=27, quantity=3)
    cart = _cart(api, user_id)

    assert len(cart["items"]) == 1
    assert cart["items"][0]["product_id"] == 27
    assert cart["items"][0]["quantity"] == 5


@pytest.mark.xfail(
    strict=True,
    reason="QuickCart currently accepts zero and negative add-to-cart quantities.",
)
def test_bb02(api):
    user_id = _user_id(api)

    zero_quantity = api.post(
        "/cart/add",
        user_id=user_id,
        json={"product_id": 1, "quantity": 0},
    )
    negative_quantity = api.post(
        "/cart/add",
        user_id=user_id,
        json={"product_id": 1, "quantity": -1},
    )

    assert zero_quantity.status_code == 400
    assert negative_quantity.status_code == 400


def test_bb03(api):
    user_id = _user_id(api)

    response = api.post(
        "/cart/add",
        user_id=user_id,
        json={"product_id": 999999, "quantity": 1},
    )

    assert response.status_code == 404
    assert response.json()["error"] == "Product not found"


@pytest.mark.xfail(
    strict=True,
    reason="QuickCart returns 404 Product not found when product_id is missing instead of 400 validation error.",
)
def test_bb04(api):
    user_id = _user_id(api)

    response = api.post(
        "/cart/add",
        user_id=user_id,
        json={"quantity": 1},
    )

    assert response.status_code == 400


def test_bb05(api):
    user_id = _user_id(api)
    _add_item(api, user_id, product_id=27, quantity=2)

    response = api.post(
        "/cart/update",
        user_id=user_id,
        json={"product_id": 27, "quantity": 0},
    )

    assert response.status_code == 400


def test_bb06(api):
    user_id = _user_id(api)
    _cart(api, user_id)

    response = api.post(
        "/cart/remove",
        user_id=user_id,
        json={"product_id": 27},
    )

    assert response.status_code == 404
    assert "Product" in response.json()["error"]
    assert "cart" in response.json()["error"]


def test_bb07(api):
    user_id = _user_id(api)
    _add_item(api, user_id, product_id=27, quantity=2)

    response = api.delete("/cart/clear", user_id=user_id)

    assert response.status_code == 200
    assert _cart(api, user_id)["items"] == []
    assert _cart(api, user_id)["total"] == 0


@pytest.mark.xfail(
    strict=True,
    reason="QuickCart overflows cart subtotals and drops items from the cart total.",
)
def test_bb08(api):
    user_id = _user_id(api)
    _add_item(api, user_id, product_id=1, quantity=2)
    _add_item(api, user_id, product_id=3, quantity=5)

    cart = _cart(api, user_id)
    item_by_id = {item["product_id"]: item for item in cart["items"]}

    assert item_by_id[1]["subtotal"] == 240
    assert item_by_id[3]["subtotal"] == 200
    assert cart["total"] == 440


def test_bb09(api):
    user_id = _user_id(api)
    _add_item(api, user_id, product_id=1, quantity=1)

    response = api.post(
        "/coupon/apply",
        user_id=user_id,
        json={"coupon_code": "WELCOME50"},
    )

    assert response.status_code == 200
    assert response.json()["coupon_code"] == "WELCOME50"
    assert response.json()["discount"] == 50
    assert response.json()["new_total"] == 70


@pytest.mark.xfail(
    strict=True,
    reason="QuickCart applies coupon response totals but ignores the applied coupon during checkout total calculation.",
)
def test_bb10(api):
    user_id = _user_id(api)
    _add_item(api, user_id, product_id=1, quantity=1)

    apply_response = api.post(
        "/coupon/apply",
        user_id=user_id,
        json={"coupon_code": "WELCOME50"},
    )
    checkout_response = api.post(
        "/checkout",
        user_id=user_id,
        json={"payment_method": "CARD"},
    )

    assert apply_response.status_code == 200
    assert checkout_response.status_code == 200

    discounted_subtotal = 120 - 50
    expected_total = discounted_subtotal + (discounted_subtotal * 0.05)
    assert checkout_response.json()["total_amount"] == expected_total


def test_bb11(api):
    user_id = _user_id(api)
    _add_item(api, user_id, product_id=1, quantity=1)

    response = api.post(
        "/coupon/apply",
        user_id=user_id,
        json={"coupon_code": "BONUS75"},
    )

    assert response.status_code == 400
    assert "below minimum" in response.json()["error"]


def test_bb12(api):
    user_id = _user_id(api)
    _add_item(api, user_id, product_id=1, quantity=10)

    response = api.post(
        "/coupon/apply",
        user_id=user_id,
        json={"coupon_code": "SUPER10"},
    )

    assert response.status_code == 200
    assert response.json()["discount"] == 80
    assert response.json()["new_total"] == 1120


@pytest.mark.xfail(
    strict=True,
    reason="QuickCart currently accepts expired coupons when the cart value qualifies.",
)
def test_bb13(api):
    user_id = _user_id(api)
    _add_item(api, user_id, product_id=1, quantity=10)

    response = api.post(
        "/coupon/apply",
        user_id=user_id,
        json={"coupon_code": "EXPIRED100"},
    )

    assert response.status_code == 400
    assert "expired" in response.json()["error"].lower()


@pytest.mark.xfail(
    strict=True,
    reason="QuickCart currently allows checkout to proceed even when the cart is empty.",
)
def test_bb14(api):
    user_id = _user_id(api)

    response = api.post(
        "/checkout",
        user_id=user_id,
        json={"payment_method": "CARD"},
    )

    assert response.status_code == 400
    assert "Cart is empty" in response.json()["error"]


def test_bb15(api):
    user_id = _user_id(api)
    _add_item(api, user_id, product_id=1, quantity=1)

    response = api.post(
        "/checkout",
        user_id=user_id,
        json={"payment_method": "UPI"},
    )

    assert response.status_code == 400
    assert response.json()["error"] == "Invalid payment method"


def test_bb16(api):
    user_id = _user_id(api)
    _add_item(api, user_id, product_id=1, quantity=1)

    response = api.post(
        "/checkout",
        user_id=user_id,
        json={"payment_method": "CARD"},
    )

    assert response.status_code == 200
    assert response.json()["gst_amount"] == 6
    assert response.json()["total_amount"] == 126
    assert response.json()["payment_status"] == "PAID"
    assert response.json()["order_status"] == "PLACED"


def test_bb17(api):
    user_id = _user_id(api)
    _add_item(api, user_id, product_id=1, quantity=50)

    response = api.post(
        "/checkout",
        user_id=user_id,
        json={"payment_method": "COD"},
    )

    assert response.status_code == 400
    assert "COD not allowed" in response.json()["error"]


def test_bb18(api):
    user_id = _user_id(api)
    _add_item(api, user_id, product_id=1, quantity=1)

    response = api.post(
        "/checkout",
        user_id=user_id,
        json={"payment_method": "WALLET"},
    )

    assert response.status_code == 200
    assert response.json()["gst_amount"] == 6
    assert response.json()["total_amount"] == 126
    assert response.json()["payment_status"] == "PENDING"
