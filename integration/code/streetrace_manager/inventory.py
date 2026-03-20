"""Inventory workflows for cars, spare parts, tools, and cash."""

from __future__ import annotations

from .models import Car, StreetRaceError, StreetRaceState


VALID_DAMAGE_SEVERITIES = {"minor", "major", "critical"}


def _normalize_text(value: str, field_name: str) -> str:
    """Return a stripped text value or raise a validation error."""

    normalized = value.strip().lower()
    if not normalized:
        raise StreetRaceError(f"{field_name} is required.")
    return normalized


def add_car(state: StreetRaceState, car_name: str) -> Car:
    """Add a car to the inventory."""

    name = car_name.strip()
    if not name:
        raise StreetRaceError("Car name is required.")
    if name in state.cars:
        raise StreetRaceError(f"{name} is already in the inventory.")
    car = Car(name=name)
    state.cars[name] = car
    return car


def require_car(state: StreetRaceState, car_name: str) -> Car:
    """Return an existing car or raise an error."""

    name = car_name.strip()
    if not name:
        raise StreetRaceError("Car name is required.")
    try:
        return state.cars[name]
    except KeyError as error:
        raise StreetRaceError(f"{name} is not in the inventory.") from error


def require_available_car(state: StreetRaceState, car_name: str) -> Car:
    """Return a race-ready car or raise an error."""

    car = require_car(state, car_name)
    if car.condition != "ready":
        raise StreetRaceError(f"{car.name} is not race-ready.")
    return car


def add_spare_part(state: StreetRaceState, part_name: str, quantity: int) -> int:
    """Increase the spare part count for a named part."""

    if quantity < 1:
        raise StreetRaceError("Spare part quantity must be positive.")
    part = _normalize_text(part_name, "Spare part name")
    state.spare_parts[part] = state.spare_parts.get(part, 0) + quantity
    return state.spare_parts[part]


def consume_spare_part(state: StreetRaceState, part_name: str, quantity: int) -> int:
    """Consume spare parts during a repair."""

    if quantity < 1:
        raise StreetRaceError("Consumed spare part quantity must be positive.")
    part = _normalize_text(part_name, "Spare part name")
    current_quantity = state.spare_parts.get(part, 0)
    if current_quantity < quantity:
        raise StreetRaceError(f"Not enough {part} spare parts are available.")
    state.spare_parts[part] = current_quantity - quantity
    return state.spare_parts[part]


def add_tool(state: StreetRaceState, tool_name: str, quantity: int = 1) -> int:
    """Add tools to the inventory."""

    if quantity < 1:
        raise StreetRaceError("Tool quantity must be positive.")
    tool = _normalize_text(tool_name, "Tool name")
    state.tools[tool] = state.tools.get(tool, 0) + quantity
    return state.tools[tool]


def require_tool(state: StreetRaceState, tool_name: str) -> int:
    """Ensure that at least one named tool is available."""

    tool = _normalize_text(tool_name, "Tool name")
    if state.tools.get(tool, 0) < 1:
        raise StreetRaceError(f"{tool} is not available in the inventory.")
    return state.tools[tool]


def update_cash_balance(state: StreetRaceState, amount: int, reason: str = "") -> int:
    """Update the crew cash balance while preventing negative totals."""

    new_balance = state.cash_balance + amount
    if new_balance < 0:
        label = reason or "the requested transaction"
        raise StreetRaceError(f"Cash balance cannot cover {label}.")
    state.cash_balance = new_balance
    return state.cash_balance


def mark_car_damaged(state: StreetRaceState, car_name: str, severity: str) -> Car:
    """Mark a car as damaged after a race or mission."""

    car = require_car(state, car_name)
    damage_severity = _normalize_text(severity, "Damage severity")
    if damage_severity not in VALID_DAMAGE_SEVERITIES:
        raise StreetRaceError("Damage severity must be minor, major, or critical.")
    car.condition = "damaged"
    car.damage_severity = damage_severity
    return car


def repair_car(state: StreetRaceState, car_name: str) -> Car:
    """Restore a damaged car to ready status."""

    car = require_car(state, car_name)
    car.condition = "ready"
    car.damage_severity = None
    return car
