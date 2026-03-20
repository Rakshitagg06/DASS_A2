"""Race result recording and leaderboard workflows."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import fields

from . import inventory, maintenance
from .models import Race, StreetRaceError, StreetRaceState


POINTS_BY_POSITION = {1: 5, 2: 3, 3: 1}


def _require_race(state: StreetRaceState, race_id: str) -> Race:
    """Return a race by identifier or raise an error."""

    normalized_id = race_id.strip()
    if not normalized_id:
        raise StreetRaceError("Race identifier is required.")
    try:
        return state.races[normalized_id]
    except KeyError as error:
        raise StreetRaceError(f"Race {normalized_id} does not exist.") from error


def _slugify(value: str) -> str:
    """Return a stable identifier fragment."""

    return "-".join(value.strip().lower().split())


def _restore_state(state: StreetRaceState, snapshot: StreetRaceState) -> None:
    """Restore an in-memory state snapshot after a failed result update."""

    for field in fields(StreetRaceState):
        setattr(state, field.name, getattr(snapshot, field.name))


def _normalize_damage_reports(
    race: Race,
    damage_reports: dict[str, str] | None,
    repair_slot: str | None,
    auto_schedule_repairs: bool,
) -> dict[str, str]:
    """Validate and normalize the reported car damage payload."""

    normalized_damage_reports: dict[str, str] = {}
    if not damage_reports:
        return normalized_damage_reports
    race_cars = {entry.car_name for entry in race.entries}
    for car_name, severity in damage_reports.items():
        normalized_car_name = car_name.strip()
        if normalized_car_name not in race_cars:
            raise StreetRaceError(
                f"Damage report for {normalized_car_name} does not match a race entry."
            )
        normalized_damage_reports[normalized_car_name] = severity
    if auto_schedule_repairs and (repair_slot is None or not repair_slot.strip()):
        raise StreetRaceError("Repair slot is required when auto-scheduling repairs.")
    return normalized_damage_reports


def _apply_result_updates(  # pylint: disable=too-many-arguments,too-many-positional-arguments
    state: StreetRaceState,
    race: Race,
    normalized_placements: list[str],
    normalized_damage_reports: dict[str, str],
    repair_slot: str | None,
    auto_schedule_repairs: bool,
) -> Race:
    """Apply the validated race result updates to the shared state."""

    race.status = "completed"
    race.placements = normalized_placements
    for position, driver_name in enumerate(normalized_placements, start=1):
        state.rankings.setdefault(driver_name, 0)
        state.rankings[driver_name] += POINTS_BY_POSITION.get(position, 0)
    if race.prize_money:
        inventory.update_cash_balance(
            state, race.prize_money, reason=f"prize money for race {race.race_id}"
        )
    for car_name, severity in normalized_damage_reports.items():
        damaged_car = inventory.mark_car_damaged(state, car_name, severity)
        if auto_schedule_repairs:
            repair_id = f"repair-{_slugify(race.race_id)}-{_slugify(damaged_car.name)}"
            maintenance.assess_damage(
                state,
                damaged_car.name,
                damaged_car.damage_severity or severity,
                repair_id,
                repair_slot,
            )
    return race


def record_race_result(  # pylint: disable=too-many-arguments,too-many-positional-arguments,too-many-locals
    state: StreetRaceState,
    race_id: str,
    placements: list[str],
    damage_reports: dict[str, str] | None = None,
    repair_slot: str | None = None,
    auto_schedule_repairs: bool = False,
) -> Race:
    """Record a completed race, update rankings, and optionally plan repairs."""

    snapshot = deepcopy(state)
    race = _require_race(state, race_id)
    if race.status != "active":
        raise StreetRaceError("Race results can only be recorded for an active race.")
    normalized_placements = [name.strip() for name in placements if name.strip()]
    if not normalized_placements:
        raise StreetRaceError("Race results must include at least one placement.")
    entered_drivers = [entry.driver_name for entry in race.entries]
    if sorted(normalized_placements) != sorted(entered_drivers):
        raise StreetRaceError(
            "Race result placements must match the drivers entered in the race."
        )
    normalized_damage_reports = _normalize_damage_reports(
        race, damage_reports, repair_slot, auto_schedule_repairs
    )
    try:
        return _apply_result_updates(
            state,
            race,
            normalized_placements,
            normalized_damage_reports,
            repair_slot,
            auto_schedule_repairs,
        )
    except Exception:
        _restore_state(state, snapshot)
        raise


def get_rankings(state: StreetRaceState) -> list[tuple[str, int]]:
    """Return the driver rankings sorted by score and then name."""

    return sorted(state.rankings.items(), key=lambda item: (-item[1], item[0]))
