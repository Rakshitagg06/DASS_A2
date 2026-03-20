"""Integration scenarios covering cross-module behavior."""

from streetrace_manager import (
    cli,
    crew_management,
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


def test_assigning_driver_role_after_registration_unlocks_race_entry(state):
    """A registered member should be able to race after gaining the driver role."""

    registration.register_member(state, "Mia", "Mechanic")
    crew_management.assign_role(state, "Mia", "Driver")
    inventory.add_car(state, "Velocity")
    race_management.create_race(
        state, "neon-nights", "Industrial Strip", "Friday 22:00", 1200
    )

    race = race_management.enter_race(state, "neon-nights", "Mia", "Velocity")

    assert race.entries[0].driver_name == "Mia"
    assert state.schedule["neon-nights"].participants == {"Mia"}


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


def test_race_reservation_blocks_same_slot_delivery_with_the_same_car(state):
    """A car already reserved for a race should be blocked from a same-slot mission."""

    registration.register_member(state, "Mia", "Driver")
    registration.register_member(state, "Leo", "Driver")
    registration.register_member(state, "Zed", "Strategist")
    inventory.add_car(state, "Velocity")
    race_management.create_race(
        state, "neon-nights", "Industrial Strip", "Friday 22:00", 1200
    )
    race_management.enter_race(state, "neon-nights", "Mia", "Velocity")

    try:
        mission_planning.plan_mission(
            state,
            "dock-run",
            "delivery",
            ["driver", "strategist"],
            "Friday 22:00",
            reward=500,
            car_name="Velocity",
        )
    except StreetRaceError as error:
        assert "Scheduling conflict for car" in str(error)
    else:
        raise AssertionError("Expected the reserved race car to block the mission.")


def test_active_mission_blocks_same_slot_race_entry_for_the_busy_driver(state):
    """A driver already assigned to a mission should not be double-booked into a race."""

    registration.register_member(state, "Mia", "Driver")
    inventory.add_car(state, "Velocity")
    mission_planning.plan_mission(
        state, "dock-run", "delivery", ["driver"], "Friday 22:00", reward=300
    )
    race_management.create_race(
        state, "neon-nights", "Industrial Strip", "Friday 22:00", 1200
    )

    try:
        race_management.enter_race(state, "neon-nights", "Mia", "Velocity")
    except StreetRaceError as error:
        assert "Scheduling conflict for crew member" in str(error)
    else:
        raise AssertionError("Expected the busy mission driver to be blocked.")


def test_race_workflows_fail_cleanly_if_the_schedule_entry_is_missing(state):
    """Race flows should raise a domain error when the schedule linkage is broken."""

    registration.register_member(state, "Mia", "Driver")
    inventory.add_car(state, "Velocity")
    race_management.create_race(
        state, "neon-nights", "Industrial Strip", "Friday 22:00", 1200
    )

    state.schedule.pop("neon-nights")
    try:
        race_management.enter_race(state, "neon-nights", "Mia", "Velocity")
    except StreetRaceError as error:
        assert "missing its schedule entry" in str(error)
    else:
        raise AssertionError("Expected the broken race schedule to block entry.")


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


def test_completed_race_and_repair_flow_updates_inventory_resources(state):
    """A completed race and its repair mission should update cash, parts, and car state."""

    registration.register_member(state, "Mia", "Driver")
    registration.register_member(state, "Nova", "Mechanic")
    inventory.add_car(state, "Velocity")
    inventory.add_spare_part(state, "belt", 2)
    inventory.add_tool(state, "wrench", 1)
    inventory.update_cash_balance(state, 1000)
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
    mission_planning.start_mission(state, "repair-neon-nights-velocity")
    maintenance.complete_repair(state, "repair-neon-nights-velocity")

    assert state.missions["repair-neon-nights-velocity"].status == "completed"
    assert state.cash_balance == 2000
    assert state.spare_parts["belt"] == 1
    assert state.cars["Velocity"].condition == "ready"


def test_damaged_car_cannot_receive_a_second_unfinished_repair_mission(state):
    """A damaged car should not accumulate overlapping repair missions."""

    registration.register_member(state, "Mia", "Driver")
    registration.register_member(state, "Nova", "Mechanic")
    inventory.add_car(state, "Velocity")
    inventory.add_spare_part(state, "belt", 2)
    inventory.add_tool(state, "wrench", 1)
    race_management.create_race(
        state, "neon-nights", "Industrial Strip", "Friday 22:00", 1200
    )
    race_management.enter_race(state, "neon-nights", "Mia", "Velocity")
    race_management.start_race(state, "neon-nights")
    results.record_race_result(
        state, "neon-nights", ["Mia"], damage_reports={"Velocity": "minor"}
    )
    maintenance.assess_damage(
        state, "Velocity", "minor", "repair-neon-nights-velocity", "Friday 23:30"
    )

    try:
        maintenance.schedule_repair(
            state,
            "repair-neon-nights-velocity-backup",
            "Velocity",
            "Saturday 00:30",
            parts_needed={"belt": 1},
            tools_needed=["wrench"],
            labor_cost=200,
        )
    except StreetRaceError as error:
        assert "unfinished repair mission" in str(error)
    else:
        raise AssertionError("Expected the duplicate repair mission to be rejected.")


def test_repair_mission_cannot_start_after_the_car_was_already_fixed(state):
    """A stale repair mission should not start once the car is ready again."""

    registration.register_member(state, "Nova", "Mechanic")
    inventory.add_car(state, "Velocity")
    inventory.mark_car_damaged(state, "Velocity", "minor")
    maintenance.schedule_repair(
        state,
        "repair-night-1",
        "Velocity",
        "Friday 23:30",
        parts_needed={},
        tools_needed=[],
        labor_cost=0,
    )
    inventory.repair_car(state, "Velocity")

    try:
        mission_planning.start_mission(state, "repair-night-1")
    except StreetRaceError as error:
        assert "cannot start a repair mission" in str(error)
    else:
        raise AssertionError("Expected a ready car to block the stale repair mission.")


def test_failed_auto_repair_planning_rolls_back_the_race_result(state):
    """A repair-planning failure should leave the race and inventory state untouched."""

    registration.register_member(state, "Mia", "Driver")
    inventory.add_car(state, "Velocity")
    inventory.add_spare_part(state, "belt", 1)
    inventory.add_tool(state, "wrench", 1)
    race_management.create_race(
        state, "neon-nights", "Industrial Strip", "Friday 22:00", 1200
    )
    race_management.enter_race(state, "neon-nights", "Mia", "Velocity")
    race_management.start_race(state, "neon-nights")

    try:
        results.record_race_result(
            state,
            "neon-nights",
            ["Mia"],
            damage_reports={"Velocity": "minor"},
            repair_slot="Friday 23:30",
            auto_schedule_repairs=True,
        )
    except StreetRaceError as error:
        assert "mechanic role" in str(error)
    else:
        raise AssertionError("Expected the repair planning failure to bubble up.")

    assert state.races["neon-nights"].status == "active"
    assert state.cash_balance == 0
    assert state.rankings["Mia"] == 0
    assert state.cars["Velocity"].condition == "ready"
    assert state.missions == {}


def test_repaired_car_can_complete_a_later_delivery_mission_for_extra_reward(state):
    """A repaired car should be reusable in a later mission that pays out a reward."""

    registration.register_member(state, "Mia", "Driver")
    registration.register_member(state, "Nova", "Mechanic")
    registration.register_member(state, "Zed", "Strategist")
    inventory.add_car(state, "Velocity")
    inventory.add_spare_part(state, "belt", 2)
    inventory.add_tool(state, "wrench", 1)
    inventory.update_cash_balance(state, 1000)
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
    mission_planning.start_mission(state, "repair-neon-nights-velocity")
    maintenance.complete_repair(state, "repair-neon-nights-velocity")

    mission_planning.plan_mission(
        state,
        "dock-run",
        "delivery",
        ["driver", "strategist"],
        "Saturday 01:00",
        reward=500,
        car_name="Velocity",
    )
    mission_planning.start_mission(state, "dock-run")
    mission_planning.complete_mission(state, "dock-run")

    assert state.missions["dock-run"].status == "completed"
    assert state.cash_balance == 2500
    assert state.cars["Velocity"].condition == "ready"


def test_repaired_car_and_driver_can_reenter_a_later_race_and_stack_rewards(state):
    """A repaired race setup should remain reusable for a later race workflow."""

    registration.register_member(state, "Mia", "Driver")
    registration.register_member(state, "Nova", "Mechanic")
    inventory.add_car(state, "Velocity")
    inventory.add_spare_part(state, "belt", 2)
    inventory.add_tool(state, "wrench", 1)
    inventory.update_cash_balance(state, 1000)
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
    mission_planning.start_mission(state, "repair-neon-nights-velocity")
    maintenance.complete_repair(state, "repair-neon-nights-velocity")

    race_management.create_race(
        state, "harbor-sprint", "Harbor District", "Saturday 01:00", 700
    )
    race_management.enter_race(state, "harbor-sprint", "Mia", "Velocity")
    race_management.start_race(state, "harbor-sprint")
    results.record_race_result(state, "harbor-sprint", ["Mia"])

    assert state.races["harbor-sprint"].status == "completed"
    assert state.cash_balance == 2700
    assert results.get_rankings(state)[0] == ("Mia", 10)
    assert state.cars["Velocity"].condition == "ready"


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
