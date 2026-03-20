"""Tests for the scheduling module."""

from streetrace_manager import inventory, registration, scheduling
from streetrace_manager.models import StreetRaceError


def test_schedule_event_creates_a_reservation(state):
    """Creating a schedule entry should persist the event details."""

    event = scheduling.schedule_event(state, "neon-nights", "race", "Friday 22:00")

    assert event.event_id == "neon-nights"
    assert state.schedule["neon-nights"].slot == "Friday 22:00"


def test_assign_member_to_event_requires_registration(state):
    """Only registered crew members can be reserved into a schedule."""

    scheduling.schedule_event(state, "neon-nights", "race", "Friday 22:00")

    try:
        scheduling.assign_member_to_event(state, "Mia", "neon-nights")
    except StreetRaceError as error:
        assert "not registered" in str(error)
    else:
        raise AssertionError("Expected scheduling to require registered members.")


def test_assign_member_to_event_blocks_same_slot_conflicts(state):
    """A member should not be double-booked into overlapping events."""

    registration.register_member(state, "Mia", "Driver")
    scheduling.schedule_event(state, "neon-nights", "race", "Friday 22:00")
    scheduling.schedule_event(state, "dock-run", "mission", "Friday 22:00")
    scheduling.assign_member_to_event(state, "Mia", "neon-nights")

    try:
        scheduling.assign_member_to_event(state, "Mia", "dock-run")
    except StreetRaceError as error:
        assert "Scheduling conflict" in str(error)
    else:
        raise AssertionError("Expected same-slot scheduling conflict.")


def test_assign_car_to_event_blocks_same_slot_conflicts(state):
    """Cars should also be protected from overlapping schedule reservations."""

    inventory.add_car(state, "Velocity")
    scheduling.schedule_event(state, "neon-nights", "race", "Friday 22:00")
    scheduling.schedule_event(state, "dock-run", "mission", "Friday 22:00")
    scheduling.assign_car_to_event(state, "Velocity", "neon-nights")

    try:
        scheduling.assign_car_to_event(state, "Velocity", "dock-run")
    except StreetRaceError as error:
        assert "Scheduling conflict" in str(error)
    else:
        raise AssertionError("Expected same-slot car conflict.")
