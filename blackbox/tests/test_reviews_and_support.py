"""Review and support-ticket black-box tests for QuickCart."""

import pytest


PRODUCT_WITHOUT_SEEDED_REVIEWS = 250


def test_bb76(api):
    user_id = api.review_user_id()

    response = api.get(
        f"/products/{PRODUCT_WITHOUT_SEEDED_REVIEWS}/reviews",
        user_id=user_id,
    )

    assert response.status_code == 200
    assert response.json()["average_rating"] == 0
    assert response.json()["reviews"] == []


def test_bb77(api):
    first_user = api.review_user_id()
    second_user = api.second_review_user_id()

    first_review = api.post(
        f"/products/{PRODUCT_WITHOUT_SEEDED_REVIEWS}/reviews",
        user_id=first_user,
        json={"rating": 4, "comment": "good"},
    )
    second_review = api.post(
        f"/products/{PRODUCT_WITHOUT_SEEDED_REVIEWS}/reviews",
        user_id=second_user,
        json={"rating": 5, "comment": "great"},
    )
    summary = api.user_json(
        f"/products/{PRODUCT_WITHOUT_SEEDED_REVIEWS}/reviews",
        first_user,
    )

    assert first_review.status_code == 200
    assert second_review.status_code == 200
    assert summary["average_rating"] == 4.5
    assert len(summary["reviews"]) == 2


@pytest.mark.xfail(
    strict=True,
    reason="QuickCart accepts rating 0 instead of rejecting values outside 1-5.",
)
def test_bb78(api):
    user_id = api.review_user_id()

    response = api.post(
        f"/products/{PRODUCT_WITHOUT_SEEDED_REVIEWS}/reviews",
        user_id=user_id,
        json={"rating": 0, "comment": "bad"},
    )

    assert response.status_code == 400
    assert "between 1 and 5" in response.json()["error"]


def test_bb79(api):
    user_id = api.review_user_id()

    response = api.post(
        f"/products/{PRODUCT_WITHOUT_SEEDED_REVIEWS}/reviews",
        user_id=user_id,
        json={"rating": 4, "comment": ""},
    )

    assert response.status_code == 400
    assert "between 1 and 200 characters" in response.json()["error"]


@pytest.mark.xfail(
    strict=True,
    reason="QuickCart truncates support-ticket messages instead of saving them exactly.",
)
def test_bb80(api):
    user_id = api.review_user_id()
    message = "Need a refund because the delivered apples were bruised."

    response = api.post(
        "/support/ticket",
        user_id=user_id,
        json={"subject": "Refund help", "message": message},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "OPEN"
    assert body["message"] == message

    admin_tickets = api.admin_json("/admin/tickets")
    saved_ticket = next(ticket for ticket in admin_tickets if ticket["ticket_id"] == body["ticket_id"])
    assert saved_ticket["message"] == message


def test_bb81(api):
    user_id = api.review_user_id()
    created = api.post(
        "/support/ticket",
        user_id=user_id,
        json={"subject": "Order help", "message": "Please check my order status."},
    )
    ticket_id = created.json()["ticket_id"]

    in_progress = api.put(
        f"/support/tickets/{ticket_id}",
        user_id=user_id,
        json={"status": "IN_PROGRESS"},
    )
    closed = api.put(
        f"/support/tickets/{ticket_id}",
        user_id=user_id,
        json={"status": "CLOSED"},
    )
    reopened = api.put(
        f"/support/tickets/{ticket_id}",
        user_id=user_id,
        json={"status": "OPEN"},
    )

    assert in_progress.status_code == 200
    assert closed.status_code == 200
    assert reopened.status_code == 400
    assert "Invalid status transition" in reopened.json()["error"]


@pytest.mark.xfail(
    strict=False,
    reason="Alternate runtime report: support tickets can incorrectly allow direct OPEN->CLOSED transition.",
)
def test_bb82(api):
    user_id = api.review_user_id()
    created = api.post(
        "/support/ticket",
        user_id=user_id,
        json={"subject": "Direct close check", "message": "transition guard"},
    )
    ticket_id = created.json()["ticket_id"]

    closed = api.put(
        f"/support/tickets/{ticket_id}",
        user_id=user_id,
        json={"status": "CLOSED"},
    )

    assert closed.status_code == 400
    assert "Invalid status transition" in closed.json()["error"]


def test_bb83(api):
    user_id = api.review_user_id()

    response = api.post(
        "/support/ticket",
        user_id=user_id,
        json={"subject": "Shrt", "message": "x"},
    )

    assert response.status_code == 400
    assert "between 5 and 100 characters" in response.json()["error"]
