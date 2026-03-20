"""Integration scenarios covering cross-module behavior."""

from streetrace_manager import (
    cli,
    inventory,
    maintenance,
    mission_planning,
    race_management,
    registration,
    results,
)
from streetrace_manager.models import StreetRaceError


def test_register_driver_then_enter_the_driver_into_a_race(state):
    """A registered driver should flow cleanly from signup into race entry."""

    registration.register_member(state, "Mia", "Driver")
    inventory.add_car(state, "Velocity")
    race_management.create_race(
        state, "neon-nights", "Industrial Strip", "Friday 22:00", 1200
    )

    race = race_management.enter_race(state, "neon-nights", "Mia", "Velocity")

    assert race.entries[0].driver_name == "Mia"


def test_attempting_to_enter_a_race_without_a_registered_driver_fails(state):
    """Race entry should fail when the driver was never registered."""

    inventory.add_car(state, "Velocity")
    race_management.create_race(
        state, "neon-nights", "Industrial Strip", "Friday 22:00", 1200
    )

    try:
        race_management.enter_race(state, "neon-nights", "Ghost", "Velocity")
    except StreetRaceError as error:
        assert "not registered" in str(error)
    else:
        raise AssertionError("Expected unregistered driver entry to fail.")


def test_completing_a_race_updates_results_and_inventory_cash(state):
    """Race completion should update both rankings and the crew bankroll."""

    registration.register_member(state, "Mia", "Driver")
    inventory.add_car(state, "Velocity")
    race_management.create_race(
        state, "neon-nights", "Industrial Strip", "Friday 22:00", 1200
    )
    race_management.enter_race(state, "neon-nights", "Mia", "Velocity")
    race_management.start_race(state, "neon-nights")

    results.record_race_result(state, "neon-nights", ["Mia"])

    assert state.cash_balance == 1200
    assert results.get_rankings(state)[0] == ("Mia", 5)


def test_damaged_car_flow_requires_a_mechanic_before_repair_mission_proceeds(state):
    """Damage repair should fail without a mechanic and succeed once one exists."""

    registration.register_member(state, "Mia", "Driver")
    inventory.add_car(state, "Velocity")
    inventory.add_spare_part(state, "belt", 1)
    inventory.add_tool(state, "wrench", 1)
    race_management.create_race(
        state, "neon-nights", "Industrial Strip", "Friday 22:00", 1200
    )
    race_management.enter_race(state, "neon-nights", "Mia", "Velocity")
    race_management.start_race(state, "neon-nights")
    results.record_race_result(
        state, "neon-nights", ["Mia"], damage_reports={"Velocity": "minor"}
    )

    try:
        maintenance.assess_damage(
            state, "Velocity", "minor", "repair-neon-nights-velocity", "Friday 23:30"
        )
    except StreetRaceError as error:
        assert "mechanic role" in str(error)
    else:
        raise AssertionError("Expected repair planning to fail without a mechanic.")

    registration.register_member(state, "Nova", "Mechanic")
    mission = maintenance.assess_damage(
        state, "Velocity", "minor", "repair-neon-nights-velocity", "Friday 23:30"
    )

    assert mission.assigned_members == {"mechanic": ["Nova"]}


def test_missions_cannot_start_if_required_roles_are_unavailable(state):
    """A second mission in the same slot should fail when the driver is busy."""

    registration.register_member(state, "Mia", "Driver")
    mission_planning.plan_mission(
        state, "dock-run", "delivery", ["driver"], "Saturday 01:00", reward=400
    )

    try:
        mission_planning.plan_mission(
            state, "backup-run", "delivery", ["driver"], "Saturday 01:00", reward=250
        )
    except StreetRaceError as error:
        assert "No available crew member" in str(error)
    else:
        raise AssertionError("Expected conflicting mission roles to fail.")


def test_cli_run_executes_the_demo_flow_end_to_end():
    """The packaged demo run should complete without raising errors."""

    state = cli.run()

    assert state.cash_balance == 3500
    assert state.cars["Velocity"].condition == "ready"
    assert state.missions["dock-delivery"].status == "active"
