"""Basic header validation and admin-scope QuickCart tests."""


def test_bb19(api):
    response = api.get("/admin/users", roll_number=None)

    assert response.status_code == 401
    assert "X-Roll-Number" in response.json()["error"]


def test_bb20(api):
    response = api.get("/admin/users", roll_number="abc")

    assert response.status_code == 400
    assert "valid integer" in response.json()["error"]


def test_bb21(api):
    response = api.get("/profile")

    assert response.status_code == 400
    assert "X-User-ID" in response.json()["error"]


def test_bb22(api):
    response = api.get("/profile", headers={"X-User-ID": "not-a-number"})

    assert response.status_code == 400
    assert "valid positive integer" in response.json()["error"]


def test_bb23(api):
    response = api.get("/profile", user_id=999999)

    assert response.status_code == 404
    assert response.json()["error"] == "User not found"


def test_bb24(api):
    admin_users = api.admin_json("/admin/users")
    sample_user = admin_users[0]

    response = api.get(f"/admin/users/{sample_user['user_id']}")

    assert response.status_code == 200
    assert response.json() == sample_user


def test_bb25(api):
    user_id = api.clean_user_id()
    admin_user = api.get(f"/admin/users/{user_id}").json()
    profile = api.get("/profile", user_id=user_id).json()

    assert profile["user_id"] == admin_user["user_id"]
    assert profile["name"] == admin_user["name"]
    assert profile["email"] == admin_user["email"]
    assert profile["phone"] == admin_user["phone"]
    assert profile["wallet_balance"] == admin_user["wallet_balance"]
    assert profile["loyalty_points"] == admin_user["loyalty_points"]
