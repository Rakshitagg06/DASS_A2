"""Crew registration workflows."""

from __future__ import annotations

from .models import CrewMember, StreetRaceError, StreetRaceState


def _normalize_text(value: str, field_name: str) -> str:
    """Return a stripped text value or raise a validation error."""

    normalized = value.strip()
    if not normalized:
        raise StreetRaceError(f"{field_name} is required.")
    return normalized


def register_member(state: StreetRaceState, name: str, role: str) -> CrewMember:
    """Register a new crew member with an initial role."""

    member_name = _normalize_text(name, "Crew member name")
    member_role = _normalize_text(role, "Crew member role").lower()
    if member_name in state.crew_members:
        raise StreetRaceError(f"{member_name} is already registered.")
    member = CrewMember(name=member_name, roles={member_role})
    state.crew_members[member_name] = member
    state.rankings.setdefault(member_name, 0)
    return member


def require_registered_member(state: StreetRaceState, name: str) -> CrewMember:
    """Return a registered crew member or raise an error."""

    member_name = _normalize_text(name, "Crew member name")
    try:
        return state.crew_members[member_name]
    except KeyError as error:
        raise StreetRaceError(f"{member_name} is not registered.") from error
