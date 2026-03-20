"""Shared pytest configuration for the white-box MoneyPoly tests."""

from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[2]
PACKAGE_ROOT = REPO_ROOT / "moneypoly" / "moneypoly"

if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))
