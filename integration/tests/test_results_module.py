"""Tests for the results module."""

from streetrace_manager import inventory, race_management, registration, results
from streetrace_manager.models import StreetRaceError


def _build_active_race(state):
    """Create a simple active race for result tests."""

    registration.register_member(state, "Mia", "Driver")
    inventory.add_car(state, "Velocity")
    race_management.create_race(
        state, "neon-nights", "Industrial Strip", "Friday 22:00", 1200
    )
    race_management.enter_race(state, "neon-nights", "Mia", "Velocity")
    race_management.start_race(state, "neon-nights")


def test_record_race_result_updates_rankings_and_cash(state):
    """Finishing a race should reward cash and leaderboard points."""

    _build_active_race(state)

    race = results.record_race_result(state, "neon-nights", ["Mia"])

    assert race.status == "completed"
    assert state.cash_balance == 1200
    assert results.get_rankings(state)[0] == ("Mia", 5)


def test_record_race_result_requires_matching_placements(state):
    """Result placements should match the entered drivers exactly."""

    _build_active_race(state)

    try:
        results.record_race_result(state, "neon-nights", ["Ghost"])
    except StreetRaceError as error:
        assert "must match" in str(error)
    else:
        raise AssertionError("Expected mismatched placements to fail.")


def test_record_race_result_can_plan_a_follow_up_repair(state):
    """Race damage should be able to trigger a repair mission automatically."""

    registration.register_member(state, "Mia", "Driver")
    registration.register_member(state, "Nova", "Mechanic")
    inventory.add_car(state, "Velocity")
    inventory.add_spare_part(state, "belt", 1)
    inventory.add_tool(state, "wrench", 1)
    race_management.create_race(
        state, "neon-nights", "Industrial Strip", "Friday 22:00", 1200
    )
    race_management.enter_race(state, "neon-nights", "Mia", "Velocity")
    race_management.start_race(state, "neon-nights")

    results.record_race_result(
        state,
        "neon-nights",
        ["Mia"],
        damage_reports={"Velocity": "minor"},
        repair_slot="Friday 23:30",
        auto_schedule_repairs=True,
    )

    repair_mission = state.missions["repair-neon-nights-velocity"]
    assert repair_mission.mission_type == "repair"
    assert repair_mission.assigned_members == {"mechanic": ["Nova"]}
    assert state.cars["Velocity"].condition == "damaged"
