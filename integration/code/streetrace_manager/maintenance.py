"""Maintenance workflows for damaged race cars."""

from __future__ import annotations

from . import inventory, mission_planning
from .models import Mission, StreetRaceError, StreetRaceState


REPAIR_RECIPES = {
    "minor": ({"belt": 1}, ["wrench"], 200),
    "major": ({"belt": 1, "tire": 1}, ["wrench", "jack"], 500),
    "critical": (
        {"belt": 2, "engine_kit": 1},
        ["wrench", "jack", "diagnostic_scanner"],
        900,
    ),
}


def _require_repair_mission(state: StreetRaceState, mission_id: str) -> Mission:
    """Return a repair mission or raise an error."""

    mission = mission_planning.require_mission(state, mission_id)
    if mission.mission_type != "repair":
        raise StreetRaceError(f"Mission {mission.mission_id} is not a repair mission.")
    return mission


def assess_damage(
    state: StreetRaceState, car_name: str, severity: str, mission_id: str, slot: str
) -> Mission:
    """Translate a damage report into a scheduled repair mission."""

    car = inventory.require_car(state, car_name)
    damage_severity = severity.strip().lower()
    if car.condition != "damaged":
        raise StreetRaceError(f"{car.name} must be damaged before repair planning.")
    if damage_severity not in REPAIR_RECIPES:
        raise StreetRaceError("Damage severity must be minor, major, or critical.")
    parts_needed, tools_needed, labor_cost = REPAIR_RECIPES[damage_severity]
    return schedule_repair(
        state,
        mission_id,
        car.name,
        slot,
        parts_needed=parts_needed,
        tools_needed=tools_needed,
        labor_cost=labor_cost,
        severity=damage_severity,
    )


def schedule_repair(  # pylint: disable=too-many-arguments,too-many-positional-arguments,too-many-locals
    state: StreetRaceState,
    mission_id: str,
    car_name: str,
    slot: str,
    parts_needed: dict[str, int] | None = None,
    tools_needed: list[str] | None = None,
    labor_cost: int = 0,
    severity: str | None = None,
) -> Mission:
    """Plan a repair mission after validating repair resources."""

    car = inventory.require_car(state, car_name)
    if car.condition != "damaged":
        raise StreetRaceError(f"{car.name} is not damaged and does not need repairs.")
    normalized_parts: dict[str, int] = {}
    for part_name, quantity in (parts_needed or {}).items():
        normalized_part = part_name.strip().lower()
        if not normalized_part:
            raise StreetRaceError("Spare part name is required.")
        if quantity < 1:
            raise StreetRaceError("Repair part quantities must be positive.")
        if state.spare_parts.get(normalized_part, 0) < quantity:
            raise StreetRaceError(
                f"Repair mission requires more {normalized_part} parts than are available."
            )
        normalized_parts[normalized_part] = quantity
    normalized_tools: list[str] = []
    for tool_name in tools_needed or []:
        normalized_tool = tool_name.strip().lower()
        if not normalized_tool:
            raise StreetRaceError("Tool name is required.")
        inventory.require_tool(state, normalized_tool)
        normalized_tools.append(normalized_tool)
    if labor_cost < 0:
        raise StreetRaceError("Repair labor cost cannot be negative.")
    mission = mission_planning.plan_mission(
        state,
        mission_id,
        "repair",
        ["mechanic"],
        slot,
        car_name=car.name,
    )
    mission.notes.update(
        {
            "parts_needed": normalized_parts,
            "tools_needed": normalized_tools,
            "labor_cost": labor_cost,
        }
    )
    if severity is not None:
        mission.notes["severity"] = severity
    return mission


def complete_repair(state: StreetRaceState, mission_id: str) -> Mission:
    """Complete an active repair mission and restore the car."""

    mission = _require_repair_mission(state, mission_id)
    if mission.status != "active":
        raise StreetRaceError("Repair mission must be active before completion.")
    if mission.car_name is None:
        raise StreetRaceError("Repair mission is missing a car assignment.")
    parts_needed = mission.notes.get("parts_needed", {})
    if not isinstance(parts_needed, dict):
        raise StreetRaceError("Repair mission part requirements are invalid.")
    for part_name, quantity in parts_needed.items():
        available_quantity = state.spare_parts.get(part_name, 0)
        if available_quantity < quantity:
            raise StreetRaceError(
                f"Repair mission is missing required {part_name} spare parts."
            )
    tools_needed = mission.notes.get("tools_needed", [])
    if not isinstance(tools_needed, list):
        raise StreetRaceError("Repair mission tool requirements are invalid.")
    for tool_name in tools_needed:
        inventory.require_tool(state, tool_name)
    labor_cost = int(mission.notes.get("labor_cost", 0))
    if state.cash_balance < labor_cost:
        raise StreetRaceError("Cash balance cannot cover the repair labor cost.")
    for part_name, quantity in parts_needed.items():
        inventory.consume_spare_part(state, part_name, quantity)
    if labor_cost:
        inventory.update_cash_balance(
            state, -labor_cost, reason=f"repair mission {mission.mission_id}"
        )
    inventory.repair_car(state, mission.car_name)
    mission.status = "completed"
    return mission
