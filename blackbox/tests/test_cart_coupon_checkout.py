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


def test_cart_add_merges_quantities_for_the_same_product(api):
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
def test_cart_rejects_non_positive_add_quantities(api):
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


def test_cart_rejects_unknown_products(api):
    user_id = _user_id(api)

    response = api.post(
        "/cart/add",
        user_id=user_id,
        json={"product_id": 999999, "quantity": 1},
    )

    assert response.status_code == 404
    assert response.json()["error"] == "Product not found"


def test_cart_update_rejects_non_positive_quantities(api):
    user_id = _user_id(api)
    _add_item(api, user_id, product_id=27, quantity=2)

    response = api.post(
        "/cart/update",
        user_id=user_id,
        json={"product_id": 27, "quantity": 0},
    )

    assert response.status_code == 400


def test_cart_remove_rejects_missing_products(api):
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


def test_cart_clear_removes_all_items(api):
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
def test_cart_subtotals_and_total_follow_quantity_times_price(api):
    user_id = _user_id(api)
    _add_item(api, user_id, product_id=1, quantity=2)
    _add_item(api, user_id, product_id=3, quantity=5)

    cart = _cart(api, user_id)
    item_by_id = {item["product_id"]: item for item in cart["items"]}

    assert item_by_id[1]["subtotal"] == 240
    assert item_by_id[3]["subtotal"] == 200
    assert cart["total"] == 440


def test_coupon_apply_accepts_a_valid_fixed_coupon(api):
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


def test_coupon_apply_rejects_carts_below_the_minimum_value(api):
    user_id = _user_id(api)
    _add_item(api, user_id, product_id=1, quantity=1)

    response = api.post(
        "/coupon/apply",
        user_id=user_id,
        json={"coupon_code": "BONUS75"},
    )

    assert response.status_code == 400
    assert "below minimum" in response.json()["error"]


def test_percent_coupons_respect_their_maximum_discount_cap(api):
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
def test_expired_coupons_are_rejected(api):
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
def test_checkout_rejects_empty_carts(api):
    user_id = _user_id(api)

    response = api.post(
        "/checkout",
        user_id=user_id,
        json={"payment_method": "CARD"},
    )

    assert response.status_code == 400
    assert "Cart is empty" in response.json()["error"]


def test_checkout_rejects_unknown_payment_methods(api):
    user_id = _user_id(api)
    _add_item(api, user_id, product_id=1, quantity=1)

    response = api.post(
        "/checkout",
        user_id=user_id,
        json={"payment_method": "UPI"},
    )

    assert response.status_code == 400
    assert response.json()["error"] == "Invalid payment method"


def test_checkout_with_card_adds_gst_once_and_marks_the_order_paid(api):
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


def test_checkout_rejects_cod_above_the_documented_limit(api):
    user_id = _user_id(api)
    _add_item(api, user_id, product_id=1, quantity=50)

    response = api.post(
        "/checkout",
        user_id=user_id,
        json={"payment_method": "COD"},
    )

    assert response.status_code == 400
    assert "COD not allowed" in response.json()["error"]


def test_checkout_with_wallet_keeps_the_payment_pending(api):
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
