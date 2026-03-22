"""Additional Part 3 black-box cases focused on PDF BB gap coverage."""

import pytest


def test_bb26(api):
    users = api.admin_json("/admin/users")
    assert isinstance(users, list)
    assert users


def test_bb27(api):
    products = api.admin_json("/admin/products")
    assert any(product["product_id"] == 90 for product in products)


def test_bb28(api):
    profile = api.user_json("/profile", api.clean_user_id())
    for key in ["user_id", "name", "email", "phone", "wallet_balance", "loyalty_points"]:
        assert key in profile


def test_bb29(api):
    addresses = api.user_json("/addresses", api.user_with_addresses_id())
    assert isinstance(addresses, list)


# BB-13 .. BB-16  (Profile PUT: missing/type variants)


def test_bb30(api):
    response = api.put("/profile", user_id=api.clean_user_id(), json={"name": "Only Name"})
    assert response.status_code == 400


def test_bb31(api):
    response = api.put("/profile", user_id=api.clean_user_id(), json={})
    assert response.status_code == 400


def test_bb32(api):
    response = api.put("/profile", user_id=api.clean_user_id(), json={"name": 12345, "phone": "1234567890"})
    assert response.status_code == 400


def test_bb33(api):
    response = api.put("/profile", user_id=api.clean_user_id(), json={"name": "Valid Name", "phone": 1234567890})
    assert response.status_code == 400


# BB-20 .. BB-34 (Addresses POST: enum/boundary/missing/type)


def test_bb34(api):
    response = api.post(
        "/addresses",
        user_id=api.user_with_addresses_id(),
        json={"label": "BAD", "street": "12345 Test Street", "city": "Delhi", "pincode": "123456", "is_default": False},
    )
    assert response.status_code == 400


def test_bb35(api):
    response = api.post(
        "/addresses",
        user_id=api.user_with_addresses_id(),
        json={"label": "HOME", "street": "1234", "city": "Delhi", "pincode": "123456", "is_default": False},
    )
    assert response.status_code == 400


def test_bb36(api):
    response = api.post(
        "/addresses",
        user_id=api.user_with_addresses_id(),
        json={"label": "HOME", "street": "S" * 101, "city": "Delhi", "pincode": "123456", "is_default": False},
    )
    assert response.status_code == 400


def test_bb37(api):
    response = api.post(
        "/addresses",
        user_id=api.user_with_addresses_id(),
        json={"label": "HOME", "street": "12345 Test Street", "city": "D", "pincode": "123456", "is_default": False},
    )
    assert response.status_code == 400


def test_bb38(api):
    response = api.post(
        "/addresses",
        user_id=api.user_with_addresses_id(),
        json={"label": "HOME", "street": "12345 Test Street", "city": "C" * 51, "pincode": "123456", "is_default": False},
    )
    assert response.status_code == 400


def test_bb39(api):
    response = api.post(
        "/addresses",
        user_id=api.user_with_addresses_id(),
        json={"label": "HOME", "street": "12345 Test Street", "city": "Delhi", "pincode": "12345", "is_default": False},
    )
    assert response.status_code == 400


def test_bb40(api):
    response = api.post(
        "/addresses",
        user_id=api.user_with_addresses_id(),
        json={"label": "HOME", "street": "12345 Test Street", "city": "Delhi", "pincode": "1234567", "is_default": False},
    )
    assert response.status_code == 400


def test_bb41(api):
    response = api.post(
        "/addresses",
        user_id=api.user_with_addresses_id(),
        json={"street": "12345 Test Street", "city": "Delhi", "pincode": "123456", "is_default": False},
    )
    assert response.status_code == 400


def test_bb42(api):
    response = api.post(
        "/addresses",
        user_id=api.user_with_addresses_id(),
        json={"label": "HOME", "city": "Delhi", "pincode": "123456", "is_default": False},
    )
    assert response.status_code == 400


def test_bb43(api):
    response = api.post(
        "/addresses",
        user_id=api.user_with_addresses_id(),
        json={"label": "HOME", "street": "12345 Test Street", "pincode": "123456", "is_default": False},
    )
    assert response.status_code == 400


def test_bb44(api):
    response = api.post(
        "/addresses",
        user_id=api.user_with_addresses_id(),
        json={"label": "HOME", "street": "12345 Test Street", "city": "Delhi", "is_default": False},
    )
    assert response.status_code == 400


def test_bb45(api):
    response = api.post(
        "/addresses",
        user_id=api.user_with_addresses_id(),
        json={"label": 123, "street": "12345 Test Street", "city": "Delhi", "pincode": "123456", "is_default": False},
    )
    assert response.status_code == 400


def test_bb46(api):
    response = api.post(
        "/addresses",
        user_id=api.user_with_addresses_id(),
        json={"label": "HOME", "street": 12345, "city": "Delhi", "pincode": "123456", "is_default": False},
    )
    assert response.status_code == 400


def test_bb47(api):
    response = api.post(
        "/addresses",
        user_id=api.user_with_addresses_id(),
        json={"label": "HOME", "street": "12345 Test Street", "city": "Delhi", "pincode": 123456, "is_default": False},
    )
    assert response.status_code == 400


def test_bb48(api):
    response = api.post(
        "/addresses",
        user_id=api.user_with_addresses_id(),
        json={"label": "HOME", "street": "12345 Test Street", "city": "Delhi", "pincode": "123456", "is_default": "true"},
    )
    assert response.status_code == 400


# BB-41, BB-42 (Cart add type variants)


def test_bb49(api):
    response = api.post("/cart/add", user_id=api.clean_user_id(), json={"product_id": "1", "quantity": 1})
    assert response.status_code == 400


def test_bb50(api):
    response = api.post("/cart/add", user_id=api.clean_user_id(), json={"product_id": 1, "quantity": "1"})
    assert response.status_code == 400


# BB-50, BB-54 (Checkout missing/null payment field)


def test_bb51(api):
    response = api.post("/checkout", user_id=api.clean_user_id(), json={})
    assert response.status_code == 400


def test_bb52(api):
    response = api.post("/checkout", user_id=api.clean_user_id(), json={"payment_method": None})
    assert response.status_code == 400


# BB-57, BB-58 (Wallet add boundary/missing)


def test_bb53(api):
    response = api.post("/wallet/add", user_id=api.review_user_id(), json={"amount": 100001})
    assert response.status_code == 400


def test_bb54(api):
    response = api.post("/wallet/add", user_id=api.review_user_id(), json={})
    assert response.status_code == 400


# BB-66, BB-67, BB-69, BB-70 (Reviews)


@pytest.mark.xfail(
    strict=True,
    reason="QuickCart accepts rating 6 instead of rejecting values above 5.",
)
def test_bb55(api):
    response = api.post("/products/250/reviews", user_id=api.review_user_id(), json={"rating": 6, "comment": "too high"})
    assert response.status_code == 400


def test_bb56(api):
    response = api.post("/products/250/reviews", user_id=api.review_user_id(), json={"rating": "5", "comment": "string rating"})
    assert response.status_code == 400


def test_bb57(api):
    response = api.post("/products/250/reviews", user_id=api.review_user_id(), json={"rating": 4, "comment": "x" * 201})
    assert response.status_code == 400


def test_bb58(api):
    response = api.post("/products/250/reviews", user_id=api.review_user_id(), json={"rating": 4})
    assert response.status_code == 400


# BB-77, BB-92 (Support)


def test_bb59(api):
    created = api.post(
        "/support/ticket",
        user_id=api.review_user_id(),
        json={"subject": "Order support", "message": "Need status update"},
    )
    ticket_id = created.json()["ticket_id"]
    response = api.put(
        f"/support/tickets/{ticket_id}",
        user_id=api.review_user_id(),
        json={"status": "REOPENED"},
    )
    assert response.status_code == 400


def test_bb60(api):
    response = api.put(
        "/support/tickets/999999",
        user_id=api.review_user_id(),
        json={"status": "IN_PROGRESS"},
    )
    assert response.status_code == 404
