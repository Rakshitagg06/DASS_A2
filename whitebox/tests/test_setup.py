"""White-box tests around game setup validation."""

import pytest

from moneypoly.game import Game


@pytest.mark.parametrize(
    "names",
    [
        [],
        [""],
        ["Alice"],
        ["Alice", " "],
    ],
)
def test_game_rejects_invalid_player_counts(names):
    """The game should refuse to start unless two real players are supplied."""
    with pytest.raises(ValueError):
        Game(names)


def test_game_keeps_cleaned_player_names():
    """Whitespace-only names should be filtered out during setup."""
    game = Game([" Alice ", "Bob", "  Carol  "])

    assert [player.name for player in game.players] == ["Alice", "Bob", "Carol"]
