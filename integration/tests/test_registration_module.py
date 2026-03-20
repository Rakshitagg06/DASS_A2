"""Tests for the registration module."""

from streetrace_manager import registration
from streetrace_manager.models import StreetRaceError


def test_register_member_stores_name_role_and_ranking(state):
    """A new member should be stored with the requested initial role."""

    member = registration.register_member(state, "Mia", "Driver")

    assert member.name == "Mia"
    assert member.roles == {"driver"}
    assert state.rankings["Mia"] == 0


def test_register_member_rejects_duplicates(state):
    """Duplicate registrations should not be accepted."""

    registration.register_member(state, "Mia", "Driver")

    try:
        registration.register_member(state, "Mia", "Mechanic")
    except StreetRaceError as error:
        assert "already registered" in str(error)
    else:
        raise AssertionError("Expected duplicate registration to fail.")


def test_require_registered_member_rejects_unknown_names(state):
    """Looking up an unknown crew member should fail clearly."""

    try:
        registration.require_registered_member(state, "Ghost")
    except StreetRaceError as error:
        assert "not registered" in str(error)
    else:
        raise AssertionError("Expected unknown crew lookup to fail.")
