"""Tests for the inventory module."""

from streetrace_manager import inventory
from streetrace_manager.models import StreetRaceError


def test_add_car_and_require_available_car(state):
    """Cars should be tracked and retrievable as ready vehicles."""

    car = inventory.add_car(state, "Velocity")

    assert car.name == "Velocity"
    assert inventory.require_available_car(state, "Velocity").name == "Velocity"


def test_add_car_rejects_duplicates(state):
    """Inventory should not allow the same car to be added twice."""

    inventory.add_car(state, "Velocity")

    try:
        inventory.add_car(state, "Velocity")
    except StreetRaceError as error:
        assert "already in the inventory" in str(error)
    else:
        raise AssertionError("Expected duplicate car insert to fail.")


def test_cash_balance_cannot_go_negative(state):
    """Cash updates should reject overspending."""

    inventory.update_cash_balance(state, 500)

    try:
        inventory.update_cash_balance(state, -600, reason="a repair bill")
    except StreetRaceError as error:
        assert "repair bill" in str(error)
    else:
        raise AssertionError("Expected negative cash balance to be rejected.")


def test_spare_parts_and_tools_are_tracked(state):
    """Inventory should manage parts and tools for later repairs."""

    inventory.add_spare_part(state, "belt", 3)
    inventory.add_tool(state, "wrench", 2)
    inventory.consume_spare_part(state, "belt", 1)

    assert state.spare_parts["belt"] == 2
    assert inventory.require_tool(state, "wrench") == 2


def test_damaged_car_is_not_available_until_repaired(state):
    """Damaged cars should be blocked from races until repaired."""

    inventory.add_car(state, "Velocity")
    inventory.mark_car_damaged(state, "Velocity", "major")

    try:
        inventory.require_available_car(state, "Velocity")
    except StreetRaceError as error:
        assert "not race-ready" in str(error)
    else:
        raise AssertionError("Expected damaged car to be unavailable.")

    repaired = inventory.repair_car(state, "Velocity")

    assert repaired.condition == "ready"
    assert repaired.damage_severity is None
