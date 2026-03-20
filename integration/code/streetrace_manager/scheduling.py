"""Scheduling workflows for races, missions, crew, and cars."""

from __future__ import annotations

from . import inventory, registration
from .models import ScheduledEvent, StreetRaceError, StreetRaceState


def _normalize_slot(slot: str) -> str:
    """Return a normalized schedule slot string."""

    normalized = slot.strip()
    if not normalized:
        raise StreetRaceError("Schedule slot is required.")
    return normalized


def _require_event(state: StreetRaceState, event_id: str) -> ScheduledEvent:
    """Return an existing schedule event or raise an error."""

    normalized_id = event_id.strip()
    if not normalized_id:
        raise StreetRaceError("Event identifier is required.")
    try:
        return state.schedule[normalized_id]
    except KeyError as error:
        raise StreetRaceError(f"Scheduled event {normalized_id} does not exist.") from error


def ensure_no_conflict(
    state: StreetRaceState,
    slot: str,
    participants: list[str] | None = None,
    cars: list[str] | None = None,
    ignore_event_id: str | None = None,
) -> None:
    """Ensure that crew members and cars are free in a schedule slot."""

    normalized_slot = _normalize_slot(slot)
    participant_names = {name.strip() for name in participants or [] if name.strip()}
    car_names = {name.strip() for name in cars or [] if name.strip()}
    for event in state.schedule.values():
        if event.slot != normalized_slot or event.event_id == ignore_event_id:
            continue
        overlapping_members = event.participants & participant_names
        if overlapping_members:
            names = ", ".join(sorted(overlapping_members))
            raise StreetRaceError(f"Scheduling conflict for crew member(s): {names}.")
        overlapping_cars = event.cars & car_names
        if overlapping_cars:
            names = ", ".join(sorted(overlapping_cars))
            raise StreetRaceError(f"Scheduling conflict for car(s): {names}.")


def schedule_event(  # pylint: disable=too-many-arguments,too-many-positional-arguments
    state: StreetRaceState,
    event_id: str,
    event_type: str,
    slot: str,
    participants: list[str] | None = None,
    cars: list[str] | None = None,
) -> ScheduledEvent:
    """Create a schedule entry for a race or mission."""

    normalized_id = event_id.strip()
    normalized_type = event_type.strip().lower()
    if not normalized_id:
        raise StreetRaceError("Event identifier is required.")
    if not normalized_type:
        raise StreetRaceError("Event type is required.")
    if normalized_id in state.schedule:
        raise StreetRaceError(f"Scheduled event {normalized_id} already exists.")
    participant_names = [name.strip() for name in participants or [] if name.strip()]
    car_names = [name.strip() for name in cars or [] if name.strip()]
    ensure_no_conflict(state, slot, participant_names, car_names)
    event = ScheduledEvent(
        event_id=normalized_id,
        event_type=normalized_type,
        slot=_normalize_slot(slot),
        participants=set(participant_names),
        cars=set(car_names),
    )
    state.schedule[normalized_id] = event
    return event


def assign_member_to_event(
    state: StreetRaceState, member_name: str, event_id: str
) -> ScheduledEvent:
    """Reserve a registered crew member for an existing event."""

    member = registration.require_registered_member(state, member_name)
    event = _require_event(state, event_id)
    ensure_no_conflict(
        state, event.slot, participants=[member.name], ignore_event_id=event.event_id
    )
    event.participants.add(member.name)
    return event


def assign_car_to_event(state: StreetRaceState, car_name: str, event_id: str) -> ScheduledEvent:
    """Reserve a tracked car for an existing event."""

    car = inventory.require_car(state, car_name)
    event = _require_event(state, event_id)
    ensure_no_conflict(state, event.slot, cars=[car.name], ignore_event_id=event.event_id)
    event.cars.add(car.name)
    return event
