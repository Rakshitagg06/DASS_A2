"""Shared pytest configuration for the StreetRace Manager tests."""

from pathlib import Path
import sys

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
PACKAGE_ROOT = REPO_ROOT / "integration" / "code"

if str(PACKAGE_ROOT) not in sys.path:
    sys.path.append(str(PACKAGE_ROOT))


from streetrace_manager.models import StreetRaceState


@pytest.fixture
def state() -> StreetRaceState:
    """Return a fresh StreetRace Manager state object."""

    return StreetRaceState()
