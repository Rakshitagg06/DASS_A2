"""Tests for the race management module."""

from streetrace_manager import inventory, race_management, registration
from streetrace_manager.models import StreetRaceError


def test_create_race_adds_a_race_and_schedule_entry(state):
    """Creating a race should persist both the race and its schedule."""

    race = race_management.create_race(
        state, "neon-nights", "Industrial Strip", "Friday 22:00", 1200
    )

    assert race.race_id == "neon-nights"
    assert state.schedule["neon-nights"].event_type == "race"


def test_enter_race_allows_only_registered_drivers(state):
    """Only crew members with the driver role may enter races."""

    registration.register_member(state, "Nova", "Mechanic")
    inventory.add_car(state, "Velocity")
    race_management.create_race(
        state, "neon-nights", "Industrial Strip", "Friday 22:00", 1200
    )

    try:
        race_management.enter_race(state, "neon-nights", "Nova", "Velocity")
    except StreetRaceError as error:
        assert "driver role" in str(error)
    else:
        raise AssertionError("Expected non-driver race entry to fail.")


def test_enter_race_reserves_driver_and_car(state):
    """A successful race entry should reserve the chosen driver and car."""

    registration.register_member(state, "Mia", "Driver")
    inventory.add_car(state, "Velocity")
    race = race_management.create_race(
        state, "neon-nights", "Industrial Strip", "Friday 22:00", 1200
    )

    race_management.enter_race(state, "neon-nights", "Mia", "Velocity")

    assert race.entries[0].driver_name == "Mia"
    assert state.schedule["neon-nights"].participants == {"Mia"}
    assert state.schedule["neon-nights"].cars == {"Velocity"}


def test_start_race_requires_at_least_one_entry(state):
    """A race cannot start until someone has entered it."""

    race_management.create_race(
        state, "neon-nights", "Industrial Strip", "Friday 22:00", 1200
    )

    try:
        race_management.start_race(state, "neon-nights")
    except StreetRaceError as error:
        assert "at least one entry" in str(error)
    else:
        raise AssertionError("Expected empty race to fail on start.")
