"""Edge-case coverage to prove each StreetRace module stands on its own."""

import pytest

from streetrace_manager import (
    crew_management,
    inventory,
    maintenance,
    mission_planning,
    race_management,
    registration,
    results,
    scheduling,
)
from streetrace_manager.models import StreetRaceError


def assert_error(message, func, *args, **kwargs):
    """Assert that a StreetRaceError includes the expected message fragment."""

    with pytest.raises(StreetRaceError) as error:
        func(*args, **kwargs)
    assert message in str(error.value)


def build_active_race(state, prize_money=1200):
    """Create a single-entry active race for module tests."""

    registration.register_member(state, "Mia", "Driver")
    inventory.add_car(state, "Velocity")
    race_management.create_race(
        state, "neon-nights", "Industrial Strip", "Friday 22:00", prize_money
    )
    race_management.enter_race(state, "neon-nights", "Mia", "Velocity")
    race_management.start_race(state, "neon-nights")


def build_repair_mission(state, labor_cost=200):
    """Create an active repair mission with stocked resources."""

    registration.register_member(state, "Nova", "Mechanic")
    inventory.add_car(state, "Velocity")
    inventory.mark_car_damaged(state, "Velocity", "minor")
    inventory.add_spare_part(state, "belt", 2)
    inventory.add_tool(state, "wrench", 1)
    inventory.update_cash_balance(state, 1000)
    maintenance.schedule_repair(
        state,
        "repair-night-1",
        "Velocity",
        "Friday 23:30",
        parts_needed={"belt": 1},
        tools_needed=["wrench"],
        labor_cost=labor_cost,
    )
    mission_planning.start_mission(state, "repair-night-1")


def test_registration_module_validates_required_text(state):
    """Registration should reject blank crew names and roles."""

    assert_error(
        "Crew member name is required.",
        registration.register_member,
        state,
        "   ",
        "Driver",
    )
    assert_error(
        "Crew member role is required.",
        registration.register_member,
        state,
        "Mia",
        "   ",
    )


def test_crew_management_validates_blank_inputs_and_empty_role_requests(state):
    """Crew management should reject blank roles, skills, and role lists."""

    registration.register_member(state, "Mia", "Driver")

    assert_error("Role is required.", crew_management.assign_role, state, "Mia", "   ")
    assert_error(
        "Skill name is required.",
        crew_management.set_skill_level,
        state,
        "Mia",
        "   ",
        5,
    )
    assert_error(
        "At least one required role must be provided.",
        crew_management.require_role_members,
        state,
        [],
    )


def test_crew_management_handles_optional_and_invalid_schedule_slots(state):
    """Availability lookup should support no slot and reject blank slots."""

    registration.register_member(state, "Mia", "Driver")

    assert [member.name for member in crew_management.list_available_members(state)] == [
        "Mia"
    ]
    assert_error(
        "Schedule slot is required.",
        crew_management.list_available_members,
        state,
        "driver",
        "   ",
    )


def test_inventory_module_covers_validation_branches(state):
    """Inventory should reject blank names, missing items, and bad quantities."""

    assert_error("Car name is required.", inventory.add_car, state, "   ")
    assert_error("Car name is required.", inventory.require_car, state, "   ")
    assert_error("Ghost is not in the inventory.", inventory.require_car, state, "Ghost")
    assert_error(
        "Spare part name is required.",
        inventory.add_spare_part,
        state,
        "   ",
        1,
    )
    assert_error(
        "Spare part quantity must be positive.",
        inventory.add_spare_part,
        state,
        "belt",
        0,
    )
    assert_error(
        "Consumed spare part quantity must be positive.",
        inventory.consume_spare_part,
        state,
        "belt",
        0,
    )
    assert_error(
        "Not enough belt spare parts are available.",
        inventory.consume_spare_part,
        state,
        "belt",
        1,
    )
    assert_error("Tool quantity must be positive.", inventory.add_tool, state, "wrench", 0)
    assert_error(
        "wrench is not available in the inventory.",
        inventory.require_tool,
        state,
        "wrench",
    )

    inventory.add_car(state, "Velocity")
    assert_error(
        "Damage severity must be minor, major, or critical.",
        inventory.mark_car_damaged,
        state,
        "Velocity",
        "wrecked",
    )


def test_scheduling_module_validates_inputs_and_missing_events(state):
    """Scheduling should validate event metadata and referenced resources."""

    assert_error(
        "Schedule slot is required.",
        scheduling.schedule_event,
        state,
        "night-run",
        "race",
        "   ",
    )
    assert_error(
        "Event identifier is required.",
        scheduling.schedule_event,
        state,
        "   ",
        "race",
        "Friday 22:00",
    )
    assert_error(
        "Event type is required.",
        scheduling.schedule_event,
        state,
        "night-run",
        "   ",
        "Friday 22:00",
    )
    scheduling.schedule_event(state, "night-run", "race", "Friday 22:00")
    assert_error(
        "Scheduled event night-run already exists.",
        scheduling.schedule_event,
        state,
        "night-run",
        "race",
        "Saturday 22:00",
    )
    assert_error(
        "Ghost is not registered.",
        scheduling.schedule_event,
        state,
        "crew-check",
        "mission",
        "Saturday 22:00",
        participants=["Ghost"],
    )
    assert_error(
        "Phantom is not in the inventory.",
        scheduling.schedule_event,
        state,
        "car-check",
        "mission",
        "Saturday 23:00",
        cars=["Phantom"],
    )
    registration.register_member(state, "Mia", "Driver")
    inventory.add_car(state, "Velocity")
    assert_error(
        "Scheduled event unknown-event does not exist.",
        scheduling.assign_member_to_event,
        state,
        "Mia",
        "unknown-event",
    )
    assert_error(
        "Event identifier is required.",
        scheduling.assign_member_to_event,
        state,
        "Mia",
        "   ",
    )
    assert_error(
        "Scheduled event unknown-event does not exist.",
        scheduling.assign_car_to_event,
        state,
        "Velocity",
        "unknown-event",
    )


def test_race_management_rejects_invalid_setup_and_duplicate_entries(state):
    """Race management should guard its setup and entry invariants."""

    registration.register_member(state, "Mia", "Driver")
    registration.register_member(state, "Leo", "Driver")
    inventory.add_car(state, "Velocity")
    inventory.add_car(state, "Shadow")

    assert_error(
        "Race identifier is required.",
        race_management.create_race,
        state,
        "   ",
        "Industrial Strip",
        "Friday 22:00",
        1200,
    )
    assert_error(
        "Race prize money cannot be negative.",
        race_management.create_race,
        state,
        "bad-race",
        "Industrial Strip",
        "Friday 22:00",
        -1,
    )

    race_management.create_race(
        state, "neon-nights", "Industrial Strip", "Friday 22:00", 1200
    )
    assert_error(
        "Race neon-nights already exists.",
        race_management.create_race,
        state,
        "neon-nights",
        "Industrial Strip",
        "Saturday 22:00",
        500,
    )

    race_management.enter_race(state, "neon-nights", "Mia", "Velocity")
    assert_error(
        "Mia is already entered in race neon-nights.",
        race_management.enter_race,
        state,
        "neon-nights",
        "Mia",
        "Shadow",
    )
    assert_error(
        "Velocity is already entered in race neon-nights.",
        race_management.enter_race,
        state,
        "neon-nights",
        "Leo",
        "Velocity",
    )


def test_race_management_validates_race_state_before_start_and_entry(state):
    """Race start should validate missing races, readiness, and repeated starts."""

    assert_error(
        "Race ghost-race does not exist.",
        race_management.start_race,
        state,
        "ghost-race",
    )

    registration.register_member(state, "Mia", "Driver")
    inventory.add_car(state, "Velocity")
    race_management.create_race(
        state, "neon-nights", "Industrial Strip", "Friday 22:00", 1200
    )
    race_management.enter_race(state, "neon-nights", "Mia", "Velocity")
    inventory.mark_car_damaged(state, "Velocity", "minor")
    assert_error(
        "Velocity is not race-ready.",
        race_management.start_race,
        state,
        "neon-nights",
    )

    inventory.repair_car(state, "Velocity")
    race_management.start_race(state, "neon-nights")
    assert_error(
        "Race neon-nights cannot be started from active.",
        race_management.start_race,
        state,
        "neon-nights",
    )
    assert_error(
        "Only planned races can accept new entries.",
        race_management.enter_race,
        state,
        "neon-nights",
        "Mia",
        "Velocity",
    )


def test_race_management_rechecks_driver_roles_before_start(state):
    """Race start should fail if an entered member no longer has the driver role."""

    registration.register_member(state, "Mia", "Driver")
    inventory.add_car(state, "Velocity")
    race_management.create_race(
        state, "neon-nights", "Industrial Strip", "Friday 22:00", 1200
    )
    race_management.enter_race(state, "neon-nights", "Mia", "Velocity")

    state.crew_members["Mia"].roles.remove("driver")
    assert_error(
        "Mia does not have the driver role.",
        race_management.start_race,
        state,
        "neon-nights",
    )


def test_results_module_validates_missing_and_inactive_races(state):
    """Results should reject blank, unknown, and inactive race submissions."""

    assert_error(
        "Race identifier is required.",
        results.record_race_result,
        state,
        "   ",
        ["Mia"],
    )
    assert_error(
        "Race ghost-race does not exist.",
        results.record_race_result,
        state,
        "ghost-race",
        ["Mia"],
    )

    registration.register_member(state, "Mia", "Driver")
    inventory.add_car(state, "Velocity")
    race_management.create_race(
        state, "neon-nights", "Industrial Strip", "Friday 22:00", 1200
    )
    race_management.enter_race(state, "neon-nights", "Mia", "Velocity")
    assert_error(
        "Race results can only be recorded for an active race.",
        results.record_race_result,
        state,
        "neon-nights",
        ["Mia"],
    )


def test_results_module_preserves_state_when_result_input_is_invalid(state):
    """Invalid result details should not partially mutate a race state."""

    build_active_race(state)

    assert_error(
        "Race results must include at least one placement.",
        results.record_race_result,
        state,
        "neon-nights",
        ["   "],
    )
    assert state.races["neon-nights"].status == "active"

    assert_error(
        "Damage report for Phantom does not match a race entry.",
        results.record_race_result,
        state,
        "neon-nights",
        ["Mia"],
        damage_reports={"Phantom": "minor"},
    )
    assert state.races["neon-nights"].status == "active"
    assert state.cash_balance == 0

    assert_error(
        "Repair slot is required when auto-scheduling repairs.",
        results.record_race_result,
        state,
        "neon-nights",
        ["Mia"],
        damage_reports={"Velocity": "minor"},
        repair_slot="   ",
        auto_schedule_repairs=True,
    )
    assert state.races["neon-nights"].status == "active"
    assert state.cash_balance == 0


def test_results_module_covers_zero_prize_branch_and_sorted_rankings(state):
    """Zero-prize races should leave cash alone and ties should sort by name."""

    build_active_race(state, prize_money=0)
    registration.register_member(state, "Ava", "Driver")
    state.rankings["Ava"] = 5

    results.record_race_result(state, "neon-nights", ["Mia"])

    assert state.cash_balance == 0
    assert results.get_rankings(state)[:2] == [("Ava", 5), ("Mia", 5)]


def test_mission_planning_validates_setup_and_start_requirements(state):
    """Mission planning should reject invalid setup and broken start preconditions."""

    assert_error(
        "Mission identifier is required.",
        mission_planning.require_mission,
        state,
        "   ",
    )
    assert_error(
        "Mission ghost-mission does not exist.",
        mission_planning.require_mission,
        state,
        "ghost-mission",
    )
    registration.register_member(state, "Mia", "Driver")
    inventory.add_car(state, "Velocity")

    assert_error(
        "Mission reward cannot be negative.",
        mission_planning.plan_mission,
        state,
        "dock-run",
        "delivery",
        ["driver"],
        "Saturday 01:00",
        -1,
    )
    assert_error(
        "At least one required role must be provided.",
        mission_planning.plan_mission,
        state,
        "empty-run",
        "delivery",
        [],
        "Saturday 02:00",
    )

    mission_planning.plan_mission(
        state,
        "dock-run",
        "delivery",
        ["driver"],
        "Saturday 01:00",
        reward=400,
        car_name="Velocity",
    )
    assert_error(
        "Mission dock-run already exists.",
        mission_planning.plan_mission,
        state,
        "dock-run",
        "delivery",
        ["driver"],
        "Saturday 03:00",
    )

    mission = state.missions["dock-run"]
    state.schedule.pop("dock-run")
    assert_error(
        "Mission dock-run is missing its schedule entry.",
        mission_planning.start_mission,
        state,
        "dock-run",
    )
    scheduling.schedule_event(
        state,
        "dock-run",
        "mission",
        "Saturday 04:00",
        participants=["Mia"],
        cars=["Velocity"],
    )

    mission.assigned_members = {}
    assert_error(
        "Mission dock-run is missing an assigned driver.",
        mission_planning.start_mission,
        state,
        "dock-run",
    )


def test_mission_planning_start_and_completion_cover_remaining_branches(state):
    """Mission start and completion should validate roles, cars, and rewards."""

    registration.register_member(state, "Mia", "Driver")
    inventory.add_car(state, "Velocity")
    mission = mission_planning.plan_mission(
        state,
        "dock-run",
        "delivery",
        ["driver"],
        "Saturday 01:00",
        reward=400,
        car_name="Velocity",
    )

    state.crew_members["Mia"].roles.remove("driver")
    assert_error(
        "Mia can no longer satisfy the driver role.",
        mission_planning.start_mission,
        state,
        "dock-run",
    )
    state.crew_members["Mia"].roles.add("driver")
    inventory.mark_car_damaged(state, "Velocity", "minor")
    assert_error(
        "Velocity is not race-ready.",
        mission_planning.start_mission,
        state,
        "dock-run",
    )
    inventory.repair_car(state, "Velocity")

    mission_planning.start_mission(state, "dock-run")
    completed = mission_planning.complete_mission(state, "dock-run")

    assert completed.status == "completed"
    assert state.cash_balance == 400
    assert_error(
        "Mission must be active before completion.",
        mission_planning.complete_mission,
        state,
        "dock-run",
    )

    inventory.mark_car_damaged(state, "Velocity", "minor")
    registration.register_member(state, "Nova", "Mechanic")
    maintenance.schedule_repair(
        state,
        "repair-night-2",
        "Velocity",
        "Saturday 02:00",
        parts_needed={},
        tools_needed=[],
        labor_cost=0,
    )
    mission_planning.start_mission(state, "repair-night-2")
    assert_error(
        "Repair missions must be completed through maintenance.",
        mission_planning.complete_mission,
        state,
        "repair-night-2",
    )


def test_mission_planning_covers_non_planned_and_zero_reward_completion(state):
    """Mission flows should cover repeated starts and no-car zero-reward completion."""

    registration.register_member(state, "Mia", "Driver")
    mission_planning.plan_mission(
        state, "quiet-run", "delivery", ["driver"], "Sunday 01:00", reward=0
    )

    mission_planning.start_mission(state, "quiet-run")
    assert_error(
        "Mission quiet-run cannot be started from active.",
        mission_planning.start_mission,
        state,
        "quiet-run",
    )

    completed = mission_planning.complete_mission(state, "quiet-run")

    assert completed.status == "completed"
    assert completed.car_name is None
    assert state.cash_balance == 0


def test_maintenance_module_validates_assessment_and_repair_planning(state):
    """Maintenance should reject invalid assessments and repair inputs."""

    registration.register_member(state, "Nova", "Mechanic")
    inventory.add_car(state, "Velocity")

    assert_error(
        "Velocity must be damaged before repair planning.",
        maintenance.assess_damage,
        state,
        "Velocity",
        "minor",
        "repair-night-1",
        "Friday 23:30",
    )

    inventory.mark_car_damaged(state, "Velocity", "minor")
    assert_error(
        "Damage severity must be minor, major, or critical.",
        maintenance.assess_damage,
        state,
        "Velocity",
        "wrecked",
        "repair-night-1",
        "Friday 23:30",
    )

    inventory.repair_car(state, "Velocity")
    assert_error(
        "Velocity is not damaged and does not need repairs.",
        maintenance.schedule_repair,
        state,
        "repair-night-1",
        "Velocity",
        "Friday 23:30",
    )


def test_maintenance_module_validates_custom_repair_requirements(state):
    """Maintenance should validate parts, tools, and labor before scheduling."""

    registration.register_member(state, "Nova", "Mechanic")
    inventory.add_car(state, "Velocity")
    inventory.mark_car_damaged(state, "Velocity", "minor")
    inventory.add_spare_part(state, "belt", 1)
    inventory.add_tool(state, "wrench", 1)

    assert_error(
        "Spare part name is required.",
        maintenance.schedule_repair,
        state,
        "repair-blank-part",
        "Velocity",
        "Friday 23:30",
        parts_needed={"   ": 1},
    )
    assert_error(
        "Repair part quantities must be positive.",
        maintenance.schedule_repair,
        state,
        "repair-zero-part",
        "Velocity",
        "Friday 23:30",
        parts_needed={"belt": 0},
    )
    assert_error(
        "Tool name is required.",
        maintenance.schedule_repair,
        state,
        "repair-blank-tool",
        "Velocity",
        "Friday 23:30",
        parts_needed={"belt": 1},
        tools_needed=["   "],
    )
    assert_error(
        "Repair labor cost cannot be negative.",
        maintenance.schedule_repair,
        state,
        "repair-negative-labor",
        "Velocity",
        "Friday 23:30",
        parts_needed={"belt": 1},
        tools_needed=["wrench"],
        labor_cost=-1,
    )

    mission = maintenance.schedule_repair(
        state,
        "repair-no-severity",
        "Velocity",
        "Saturday 00:30",
        parts_needed={},
        tools_needed=[],
        labor_cost=0,
    )
    assert "severity" not in mission.notes


def test_maintenance_completion_validates_mission_shape_and_resources(state):
    """Repair completion should reject broken mission state before mutating inventory."""

    registration.register_member(state, "Mia", "Driver")
    mission_planning.plan_mission(
        state, "dock-run", "delivery", ["driver"], "Saturday 01:00", reward=200
    )
    mission_planning.start_mission(state, "dock-run")
    assert_error(
        "Mission dock-run is not a repair mission.",
        maintenance.complete_repair,
        state,
        "dock-run",
    )

    build_repair_mission(state, labor_cost=200)
    state.missions["repair-night-1"].status = "planned"
    assert_error(
        "Repair mission must be active before completion.",
        maintenance.complete_repair,
        state,
        "repair-night-1",
    )


def test_maintenance_completion_covers_invalid_notes_and_cash_rules(state):
    """Repair completion should validate note shapes, stock, and labor affordability."""

    build_repair_mission(state, labor_cost=200)
    mission = state.missions["repair-night-1"]

    mission.car_name = None
    assert_error(
        "Repair mission is missing a car assignment.",
        maintenance.complete_repair,
        state,
        "repair-night-1",
    )
    mission.car_name = "Velocity"

    mission.notes["parts_needed"] = []
    assert_error(
        "Repair mission part requirements are invalid.",
        maintenance.complete_repair,
        state,
        "repair-night-1",
    )
    mission.notes["parts_needed"] = {"belt": 1}

    state.spare_parts["belt"] = 0
    assert_error(
        "Repair mission is missing required belt spare parts.",
        maintenance.complete_repair,
        state,
        "repair-night-1",
    )
    state.spare_parts["belt"] = 1

    mission.notes["tools_needed"] = "wrench"
    assert_error(
        "Repair mission tool requirements are invalid.",
        maintenance.complete_repair,
        state,
        "repair-night-1",
    )
    mission.notes["tools_needed"] = ["wrench"]

    state.cash_balance = 100
    assert_error(
        "Cash balance cannot cover the repair labor cost.",
        maintenance.complete_repair,
        state,
        "repair-night-1",
    )


def test_maintenance_completion_supports_zero_labor_repairs(state):
    """Zero-labor repairs should complete without reducing cash."""

    build_repair_mission(state, labor_cost=0)

    completed = maintenance.complete_repair(state, "repair-night-1")

    assert completed.status == "completed"
    assert state.cash_balance == 1000
    assert state.cars["Velocity"].condition == "ready"
