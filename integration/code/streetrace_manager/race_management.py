"""Race planning and entry workflows."""

from __future__ import annotations

from . import inventory, registration, scheduling
from .models import Race, RaceEntry, StreetRaceError, StreetRaceState


def _normalize_text(value: str, field_name: str) -> str:
    """Return a stripped text value or raise a validation error."""

    normalized = value.strip()
    if not normalized:
        raise StreetRaceError(f"{field_name} is required.")
    return normalized


def _require_race(state: StreetRaceState, race_id: str) -> Race:
    """Return a race by identifier or raise an error."""

    normalized_id = _normalize_text(race_id, "Race identifier")
    try:
        return state.races[normalized_id]
    except KeyError as error:
        raise StreetRaceError(f"Race {normalized_id} does not exist.") from error


def create_race(
    state: StreetRaceState, race_id: str, location: str, slot: str, prize_money: int
) -> Race:
    """Create a scheduled race with an associated prize pool."""

    normalized_id = _normalize_text(race_id, "Race identifier")
    normalized_location = _normalize_text(location, "Race location")
    normalized_slot = _normalize_text(slot, "Race slot")
    if prize_money < 0:
        raise StreetRaceError("Race prize money cannot be negative.")
    if normalized_id in state.races:
        raise StreetRaceError(f"Race {normalized_id} already exists.")
    scheduling.schedule_event(state, normalized_id, "race", normalized_slot)
    race = Race(
        race_id=normalized_id,
        location=normalized_location,
        slot=normalized_slot,
        prize_money=prize_money,
    )
    state.races[normalized_id] = race
    return race


def enter_race(
    state: StreetRaceState, race_id: str, driver_name: str, car_name: str
) -> Race:
    """Enter a registered driver and race-ready car into a planned race."""

    race = _require_race(state, race_id)
    if race.status != "planned":
        raise StreetRaceError("Only planned races can accept new entries.")
    driver = registration.require_registered_member(state, driver_name)
    if "driver" not in driver.roles:
        raise StreetRaceError(f"{driver.name} does not have the driver role.")
    car = inventory.require_available_car(state, car_name)
    if any(entry.driver_name == driver.name for entry in race.entries):
        raise StreetRaceError(f"{driver.name} is already entered in race {race.race_id}.")
    if any(entry.car_name == car.name for entry in race.entries):
        raise StreetRaceError(f"{car.name} is already entered in race {race.race_id}.")
    event = state.schedule[race.race_id]
    scheduling.ensure_no_conflict(
        state,
        event.slot,
        participants=[driver.name],
        cars=[car.name],
        ignore_event_id=race.race_id,
    )
    scheduling.assign_member_to_event(state, driver.name, race.race_id)
    scheduling.assign_car_to_event(state, car.name, race.race_id)
    race.entries.append(RaceEntry(driver_name=driver.name, car_name=car.name))
    return race


def start_race(state: StreetRaceState, race_id: str) -> Race:
    """Move a planned race into the active state."""

    race = _require_race(state, race_id)
    if race.status != "planned":
        raise StreetRaceError(f"Race {race.race_id} cannot be started from {race.status}.")
    if not race.entries:
        raise StreetRaceError("A race needs at least one entry before it can start.")
    race.status = "active"
    return race
