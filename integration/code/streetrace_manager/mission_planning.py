"""Mission planning workflows."""

from __future__ import annotations

from . import crew_management, inventory, scheduling
from .models import Mission, StreetRaceError, StreetRaceState


def _normalize_text(value: str, field_name: str) -> str:
    """Return a stripped text value or raise a validation error."""

    normalized = value.strip()
    if not normalized:
        raise StreetRaceError(f"{field_name} is required.")
    return normalized


def require_mission(state: StreetRaceState, mission_id: str) -> Mission:
    """Return a mission by identifier or raise an error."""

    normalized_id = _normalize_text(mission_id, "Mission identifier")
    try:
        return state.missions[normalized_id]
    except KeyError as error:
        raise StreetRaceError(f"Mission {normalized_id} does not exist.") from error


def plan_mission(  # pylint: disable=too-many-arguments,too-many-positional-arguments,too-many-locals
    state: StreetRaceState,
    mission_id: str,
    mission_type: str,
    required_roles: list[str],
    slot: str,
    reward: int = 0,
    car_name: str | None = None,
) -> Mission:
    """Plan a mission after validating required crew roles and optional car access."""

    normalized_id = _normalize_text(mission_id, "Mission identifier")
    normalized_type = _normalize_text(mission_type, "Mission type").lower()
    normalized_slot = _normalize_text(slot, "Mission slot")
    if reward < 0:
        raise StreetRaceError("Mission reward cannot be negative.")
    if normalized_id in state.missions:
        raise StreetRaceError(f"Mission {normalized_id} already exists.")
    if not required_roles:
        raise StreetRaceError("At least one required role must be provided.")
    assignments = crew_management.require_role_members(
        state, required_roles, normalized_slot
    )
    reserved_cars: list[str] = []
    assigned_car: str | None = None
    if car_name is not None:
        if normalized_type == "repair":
            assigned_car = inventory.require_car(state, car_name).name
        else:
            assigned_car = inventory.require_available_car(state, car_name).name
        reserved_cars = [assigned_car]
    scheduling.schedule_event(
        state, normalized_id, "mission", normalized_slot, cars=reserved_cars
    )
    for member_names in assignments.values():
        for member_name in member_names:
            scheduling.assign_member_to_event(state, member_name, normalized_id)
    mission = Mission(
        mission_id=normalized_id,
        mission_type=normalized_type,
        slot=normalized_slot,
        required_roles=[role.strip().lower() for role in required_roles],
        reward=reward,
        assigned_members=assignments,
        car_name=assigned_car,
    )
    state.missions[normalized_id] = mission
    return mission


def start_mission(state: StreetRaceState, mission_id: str) -> Mission:
    """Move a planned mission into the active state."""

    mission = require_mission(state, mission_id)
    if mission.status != "planned":
        raise StreetRaceError(
            f"Mission {mission.mission_id} cannot be started from {mission.status}."
        )
    mission.status = "active"
    return mission
