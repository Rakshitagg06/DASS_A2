"""Small command-line demo flow for the StreetRace Manager package."""

from __future__ import annotations

from . import (
    crew_management,
    inventory,
    maintenance,
    mission_planning,
    race_management,
    registration,
    results,
)
from .models import StreetRaceState


def seed_demo_data(state: StreetRaceState) -> StreetRaceState:
    """Load a compact demo crew, inventory, and bankroll."""

    registration.register_member(state, "Mia", "Driver")
    registration.register_member(state, "Nova", "Mechanic")
    registration.register_member(state, "Zed", "Strategist")
    crew_management.assign_role(state, "Mia", "Scout")
    crew_management.set_skill_level(state, "Mia", "Drifting", 9)
    crew_management.set_skill_level(state, "Nova", "Repairs", 10)
    crew_management.set_skill_level(state, "Zed", "Planning", 8)
    inventory.add_car(state, "Velocity")
    inventory.add_spare_part(state, "belt", 3)
    inventory.add_spare_part(state, "tire", 2)
    inventory.add_spare_part(state, "engine_kit", 1)
    inventory.add_tool(state, "wrench", 2)
    inventory.add_tool(state, "jack", 1)
    inventory.add_tool(state, "diagnostic_scanner", 1)
    inventory.update_cash_balance(state, 2500, reason="starting bankroll")
    return state


def _print_summary(state: StreetRaceState) -> None:
    """Print a short system summary for the demo run."""

    rankings = ", ".join(f"{name}:{points}" for name, points in results.get_rankings(state))
    print("StreetRace Manager demo complete.")
    print(f"Cash balance: {state.cash_balance}")
    print(f"Cars: {', '.join(sorted(state.cars))}")
    print(f"Rankings: {rankings}")
    print(f"Missions: {', '.join(sorted(state.missions))}")


def run() -> StreetRaceState:
    """Run a short end-to-end demo flow from registration to repair."""

    state = seed_demo_data(StreetRaceState())
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
        "dock-delivery",
        "delivery",
        ["driver", "strategist"],
        "Saturday 01:00",
        reward=800,
        car_name="Velocity",
    )
    mission_planning.start_mission(state, "dock-delivery")
    _print_summary(state)
    return state
