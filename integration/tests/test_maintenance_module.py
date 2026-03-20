"""Tests for the maintenance module."""

from streetrace_manager import inventory, maintenance, mission_planning, registration
from streetrace_manager.models import StreetRaceError


def _build_damaged_car_with_mechanic(state):
    """Prepare a damaged car and repair resources."""

    registration.register_member(state, "Nova", "Mechanic")
    inventory.add_car(state, "Velocity")
    inventory.mark_car_damaged(state, "Velocity", "major")
    inventory.add_spare_part(state, "belt", 2)
    inventory.add_spare_part(state, "tire", 1)
    inventory.add_tool(state, "wrench", 1)
    inventory.add_tool(state, "jack", 1)
    inventory.update_cash_balance(state, 1000)


def test_assess_damage_creates_repair_mission_from_recipe(state):
    """Damage assessment should translate severity into repair requirements."""

    _build_damaged_car_with_mechanic(state)

    mission = maintenance.assess_damage(
        state, "Velocity", "major", "repair-night-1", "Friday 23:30"
    )

    assert mission.mission_type == "repair"
    assert mission.notes["parts_needed"] == {"belt": 1, "tire": 1}
    assert mission.notes["tools_needed"] == ["wrench", "jack"]


def test_schedule_repair_rejects_missing_parts(state):
    """A repair mission should fail if the required parts are not stocked."""

    registration.register_member(state, "Nova", "Mechanic")
    inventory.add_car(state, "Velocity")
    inventory.mark_car_damaged(state, "Velocity", "minor")
    inventory.add_tool(state, "wrench", 1)

    try:
        maintenance.schedule_repair(
            state,
            "repair-night-1",
            "Velocity",
            "Friday 23:30",
            parts_needed={"belt": 1},
            tools_needed=["wrench"],
            labor_cost=200,
        )
    except StreetRaceError as error:
        assert "requires more belt parts" in str(error)
    else:
        raise AssertionError("Expected repair scheduling to fail without spare parts.")


def test_complete_repair_consumes_resources_and_restores_car(state):
    """Completing a repair should use inventory and ready the car again."""

    _build_damaged_car_with_mechanic(state)
    maintenance.assess_damage(
        state, "Velocity", "major", "repair-night-1", "Friday 23:30"
    )
    mission_planning.start_mission(state, "repair-night-1")

    mission = maintenance.complete_repair(state, "repair-night-1")

    assert mission.status == "completed"
    assert state.cars["Velocity"].condition == "ready"
    assert state.spare_parts["belt"] == 1
    assert state.spare_parts["tire"] == 0
    assert state.cash_balance == 500
