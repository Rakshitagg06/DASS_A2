"""Tests for the mission planning module."""

from streetrace_manager import inventory, mission_planning, registration
from streetrace_manager.models import StreetRaceError


def test_plan_mission_assigns_required_roles(state):
    """Planning a mission should reserve crew for each requested role."""

    registration.register_member(state, "Mia", "Driver")
    registration.register_member(state, "Zed", "Strategist")
    inventory.add_car(state, "Velocity")

    mission = mission_planning.plan_mission(
        state,
        "dock-delivery",
        "delivery",
        ["driver", "strategist"],
        "Saturday 01:00",
        reward=800,
        car_name="Velocity",
    )

    assert mission.assigned_members == {"driver": ["Mia"], "strategist": ["Zed"]}
    assert state.schedule["dock-delivery"].cars == {"Velocity"}


def test_plan_mission_rejects_unavailable_roles(state):
    """A mission should fail when the needed crew role is unavailable."""

    registration.register_member(state, "Mia", "Driver")
    mission_planning.plan_mission(
        state, "dock-run", "delivery", ["driver"], "Saturday 01:00", reward=400
    )

    try:
        mission_planning.plan_mission(
            state, "rescue-run", "rescue", ["driver"], "Saturday 01:00", reward=600
        )
    except StreetRaceError as error:
        assert "No available crew member" in str(error)
    else:
        raise AssertionError("Expected unavailable role validation to fail.")


def test_plan_mission_rejects_damaged_car_for_non_repair_work(state):
    """Normal missions should require a race-ready vehicle."""

    registration.register_member(state, "Mia", "Driver")
    inventory.add_car(state, "Velocity")
    inventory.mark_car_damaged(state, "Velocity", "minor")

    try:
        mission_planning.plan_mission(
            state,
            "dock-run",
            "delivery",
            ["driver"],
            "Saturday 01:00",
            reward=400,
            car_name="Velocity",
        )
    except StreetRaceError as error:
        assert "not race-ready" in str(error)
    else:
        raise AssertionError("Expected damaged car to block a normal mission.")


def test_start_mission_moves_planned_mission_to_active(state):
    """A planned mission should become active when started once."""

    registration.register_member(state, "Mia", "Driver")
    mission_planning.plan_mission(
        state, "dock-run", "delivery", ["driver"], "Saturday 01:00", reward=400
    )

    mission = mission_planning.start_mission(state, "dock-run")

    assert mission.status == "active"
