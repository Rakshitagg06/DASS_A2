"""Role and skill management for registered crew members."""

from __future__ import annotations

from . import registration
from .models import CrewMember, StreetRaceError, StreetRaceState


def _normalize_role(role: str) -> str:
    """Return a normalized role name."""

    normalized = role.strip().lower()
    if not normalized:
        raise StreetRaceError("Role is required.")
    return normalized


def _members_busy_in_slot(state: StreetRaceState, slot: str | None) -> set[str]:
    """Return the set of members already reserved in a schedule slot."""

    if slot is None:
        return set()
    normalized_slot = slot.strip()
    if not normalized_slot:
        raise StreetRaceError("Schedule slot is required.")
    busy_members: set[str] = set()
    for event in state.schedule.values():
        if event.slot == normalized_slot:
            busy_members.update(event.participants)
    return busy_members


def assign_role(state: StreetRaceState, member_name: str, role: str) -> CrewMember:
    """Assign an additional role to a registered crew member."""

    member = registration.require_registered_member(state, member_name)
    member.roles.add(_normalize_role(role))
    return member


def set_skill_level(
    state: StreetRaceState, member_name: str, skill_name: str, level: int
) -> CrewMember:
    """Record or update a crew member skill level."""

    member = registration.require_registered_member(state, member_name)
    skill = skill_name.strip().lower()
    if not skill:
        raise StreetRaceError("Skill name is required.")
    if level < 0 or level > 10:
        raise StreetRaceError("Skill level must be between 0 and 10.")
    member.skills[skill] = level
    return member


def list_available_members(
    state: StreetRaceState, role: str | None = None, slot: str | None = None
) -> list[CrewMember]:
    """List crew members available for a role and optional schedule slot."""

    required_role = _normalize_role(role) if role is not None else None
    busy_members = _members_busy_in_slot(state, slot)
    available = [
        member
        for member in state.crew_members.values()
        if member.name not in busy_members
        and (required_role is None or required_role in member.roles)
    ]
    return sorted(available, key=lambda member: member.name)


def require_role_members(
    state: StreetRaceState, required_roles: list[str], slot: str | None = None
) -> dict[str, list[str]]:
    """Reserve distinct crew members for each required role."""

    if not required_roles:
        raise StreetRaceError("At least one required role must be provided.")
    assignments: dict[str, list[str]] = {}
    selected_names: set[str] = set()
    for role in required_roles:
        normalized_role = _normalize_role(role)
        candidates = [
            member
            for member in list_available_members(state, normalized_role, slot)
            if member.name not in selected_names
        ]
        if not candidates:
            raise StreetRaceError(
                f"No available crew member can satisfy the {normalized_role} role."
            )
        chosen_member = candidates[0]
        selected_names.add(chosen_member.name)
        assignments.setdefault(normalized_role, []).append(chosen_member.name)
    return assignments
