"""Profile, address, and product black-box tests for QuickCart."""

import pytest


def test_bb61(api):
    user_id = api.clean_user_id()

    response = api.put(
        "/profile",
        user_id=user_id,
        json={"name": "QA User", "phone": "1234567890"},
    )

    assert response.status_code == 200
    profile = api.user_json("/profile", user_id)
    assert profile["name"] == "QA User"
    assert profile["phone"] == "1234567890"


def test_bb62(api):
    user_id = api.clean_user_id()

    response = api.put(
        "/profile",
        user_id=user_id,
        json={"name": "Q", "phone": "1234567890"},
    )

    assert response.status_code == 400
    assert "Name must be between 2 and 50 characters" in response.json()["error"]


def test_bb63(api):
    user_id = api.clean_user_id()

    response = api.put(
        "/profile",
        user_id=user_id,
        json={"name": "Valid User", "phone": "12345"},
    )

    assert response.status_code == 400
    assert "Phone must be exactly 10 digits" in response.json()["error"]


@pytest.mark.xfail(
    strict=True,
    reason="QuickCart accepts non-digit phone values when the length is 10 characters.",
)
def test_bb64(api):
    user_id = api.clean_user_id()

    response = api.put(
        "/profile",
        user_id=user_id,
        json={"name": "Valid Name", "phone": "98A654321B"},
    )

    assert response.status_code == 400
    assert "Phone must be exactly 10 digits" in response.json()["error"]


def test_bb65(api):
    user_id = api.user_with_addresses_id()
    payload = {
        "label": "OFFICE",
        "street": "12345 Test Street",
        "city": "Delhi",
        "pincode": "123456",
        "is_default": False,
    }

    response = api.post("/addresses", user_id=user_id, json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["message"] == "Address added successfully"
    assert body["address"]["address_id"] > 0
    assert body["address"]["label"] == payload["label"]
    assert body["address"]["street"] == payload["street"]
    assert body["address"]["city"] == payload["city"]
    assert body["address"]["pincode"] == payload["pincode"]
    assert body["address"]["is_default"] is False


@pytest.mark.xfail(
    strict=False,
    reason="Alternate runtime report: valid 6-digit pincode 500001 can be rejected with Invalid pincode.",
)
def test_bb66(api):
    user_id = api.user_with_addresses_id()

    response = api.post(
        "/addresses",
        user_id=user_id,
        json={
            "label": "OTHER",
            "street": "Main Street 12",
            "city": "Hyderabad",
            "pincode": "500001",
            "is_default": False,
        },
    )

    assert response.status_code == 200
    assert response.json()["address"]["pincode"] == "500001"


@pytest.mark.xfail(
    strict=False,
    reason="Alternate runtime report: non-digit pincode values can be accepted instead of rejected.",
)
def test_bb67(api):
    user_id = api.user_with_addresses_id()

    response = api.post(
        "/addresses",
        user_id=user_id,
        json={
            "label": "HOME",
            "street": "Main Street 12",
            "city": "Hyderabad",
            "pincode": "ABCDE",
            "is_default": False,
        },
    )

    assert response.status_code == 400
    assert "Pincode" in response.json()["error"]


def test_bb68(api):
    user_id = api.user_with_addresses_id()
    original = api.user_json("/addresses", user_id)[0]

    response = api.put(
        f"/addresses/{original['address_id']}",
        user_id=user_id,
        json={
            "street": "54321 Updated Avenue",
            "label": "OTHER",
            "city": "Mumbai",
            "pincode": "654321",
            "is_default": False,
        },
    )

    assert response.status_code == 200
    updated = response.json()["address"]
    assert updated["street"] == "54321 Updated Avenue"
    assert updated["is_default"] is False
    assert updated["label"] == original["label"]
    assert updated["city"] == original["city"]
    assert updated["pincode"] == original["pincode"]


def test_bb69(api):
    user_id = api.clean_user_id()

    response = api.delete("/addresses/999999", user_id=user_id)

    assert response.status_code == 404
    assert response.json()["error"] == "Address not found"


@pytest.mark.xfail(
    strict=True,
    reason="QuickCart allows multiple default addresses after creating a new default.",
)
def test_bb70(api):
    user_id = api.user_with_addresses_id()

    response = api.post(
        "/addresses",
        user_id=user_id,
        json={
            "label": "OTHER",
            "street": "98765 Default Switch Road",
            "city": "Pune",
            "pincode": "654321",
            "is_default": True,
        },
    )

    assert response.status_code == 200
    addresses = api.user_json("/addresses", user_id)
    default_addresses = [address for address in addresses if address["is_default"]]
    assert len(default_addresses) == 1
    assert default_addresses[0]["address_id"] == response.json()["address"]["address_id"]


def test_bb71(api):
    user_id = api.clean_user_id()
    active_products = api.user_json("/products", user_id)

    assert active_products
    assert all(product["is_active"] is True for product in active_products)
    assert 90 not in {product["product_id"] for product in active_products}


def test_bb72(api):
    user_id = api.clean_user_id()

    response = api.get("/products/999999", user_id=user_id)

    assert response.status_code == 404
    assert response.json()["error"] == "Product not found"


def test_bb73(api):
    user_id = api.clean_user_id()

    search_results = api.user_json("/products?search=Apple", user_id)
    category_results = api.user_json("/products?category=Vegetables", user_id)

    assert any("Apple" in product["name"] for product in search_results)
    assert category_results
    assert all(product["category"] == "Vegetables" for product in category_results)


@pytest.mark.xfail(
    strict=True,
    reason="QuickCart rounds several product prices away from the seeded admin values.",
)
def test_bb74(api):
    user_id = api.clean_user_id()
    listed_products = api.user_json("/products", user_id)
    admin_products = api.admin_products_by_id()

    for product in listed_products:
        assert product["price"] == admin_products[product["product_id"]]["price"]


@pytest.mark.xfail(
    strict=True,
    reason="QuickCart ignores the requested product price sort order.",
)
def test_bb75(api):
    user_id = api.clean_user_id()

    ascending_prices = [
        product["price"] for product in api.user_json("/products?sort=asc", user_id)
    ]
    descending_prices = [
        product["price"] for product in api.user_json("/products?sort=desc", user_id)
    ]

    assert ascending_prices == sorted(ascending_prices)
    assert descending_prices == sorted(descending_prices, reverse=True)
