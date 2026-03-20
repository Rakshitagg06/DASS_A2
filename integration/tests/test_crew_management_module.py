"""Tests for the crew management module."""

from streetrace_manager import crew_management, registration, scheduling
from streetrace_manager.models import StreetRaceError


def test_assign_role_requires_registration(state):
    """Roles can only be assigned after registration."""

    try:
        crew_management.assign_role(state, "Mia", "Driver")
    except StreetRaceError as error:
        assert "not registered" in str(error)
    else:
        raise AssertionError("Expected role assignment to require registration.")


def test_assign_role_and_skill_update_registered_member(state):
    """Role and skill updates should persist on the crew member record."""

    registration.register_member(state, "Mia", "Driver")

    updated_member = crew_management.assign_role(state, "Mia", "Strategist")
    skilled_member = crew_management.set_skill_level(state, "Mia", "Drifting", 9)

    assert updated_member.roles == {"driver", "strategist"}
    assert skilled_member.skills["drifting"] == 9


def test_list_available_members_filters_busy_people_for_the_same_slot(state):
    """Members already reserved in a slot should not appear as available."""

    registration.register_member(state, "Mia", "Driver")
    registration.register_member(state, "Leo", "Driver")
    scheduling.schedule_event(state, "neon-nights", "race", "Friday 22:00")
    scheduling.assign_member_to_event(state, "Mia", "neon-nights")

    available = crew_management.list_available_members(state, "driver", "Friday 22:00")

    assert [member.name for member in available] == ["Leo"]


def test_require_role_members_uses_distinct_people_for_duplicate_roles(state):
    """Repeated role requirements should not reuse the same crew member twice."""

    registration.register_member(state, "Kai", "Mechanic")
    registration.register_member(state, "Rin", "Mechanic")

    assignments = crew_management.require_role_members(
        state, ["mechanic", "mechanic"], "Saturday 01:00"
    )

    assert sorted(assignments["mechanic"]) == ["Kai", "Rin"]


def test_set_skill_level_validates_level_range(state):
    """Skill levels outside the supported range should fail."""

    registration.register_member(state, "Mia", "Driver")

    try:
        crew_management.set_skill_level(state, "Mia", "Drifting", 11)
    except StreetRaceError as error:
        assert "between 0 and 10" in str(error)
    else:
        raise AssertionError("Expected an invalid skill level to fail.")
