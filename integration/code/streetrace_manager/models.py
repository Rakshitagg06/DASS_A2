"""Shared state and domain models for the StreetRace Manager system."""

# pylint: disable=too-many-instance-attributes

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


class StreetRaceError(ValueError):
    """Raised when a business rule or validation rule is violated."""


@dataclass(slots=True)
class CrewMember:
    """A registered crew member."""

    name: str
    roles: set[str] = field(default_factory=set)
    skills: dict[str, int] = field(default_factory=dict)


@dataclass(slots=True)
class Car:
    """A crew vehicle tracked by the inventory module."""

    name: str
    condition: str = "ready"
    damage_severity: str | None = None


@dataclass(slots=True)
class RaceEntry:
    """A race entry pairing a driver with a car."""

    driver_name: str
    car_name: str


@dataclass(slots=True)
class Race:
    """A planned or completed street race."""

    race_id: str
    location: str
    slot: str
    prize_money: int
    status: str = "planned"
    entries: list[RaceEntry] = field(default_factory=list)
    placements: list[str] = field(default_factory=list)


@dataclass(slots=True)
class Mission:
    """A mission assigned to the crew."""

    mission_id: str
    mission_type: str
    slot: str
    required_roles: list[str]
    reward: int = 0
    status: str = "planned"
    assigned_members: dict[str, list[str]] = field(default_factory=dict)
    car_name: str | None = None
    notes: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ScheduledEvent:
    """A scheduled event used for race and mission conflict detection."""

    event_id: str
    event_type: str
    slot: str
    participants: set[str] = field(default_factory=set)
    cars: set[str] = field(default_factory=set)


@dataclass(slots=True)
class StreetRaceState:
    """In-memory state for the StreetRace Manager system."""

    crew_members: dict[str, CrewMember] = field(default_factory=dict)
    cars: dict[str, Car] = field(default_factory=dict)
    spare_parts: dict[str, int] = field(default_factory=dict)
    tools: dict[str, int] = field(default_factory=dict)
    cash_balance: int = 0
    races: dict[str, Race] = field(default_factory=dict)
    missions: dict[str, Mission] = field(default_factory=dict)
    schedule: dict[str, ScheduledEvent] = field(default_factory=dict)
    rankings: dict[str, int] = field(default_factory=dict)
