"""White-box tests around player movement and Go salary handling."""

from moneypoly.config import GO_SALARY
from moneypoly.player import Player


def test_move_collects_salary_when_passing_go(capsys):
    """Wrapping around the board should award the Go salary once."""
    player = Player("Alice")
    player.position = 39

    new_position = player.move(2)

    assert new_position == 1
    assert player.balance == 1500 + GO_SALARY
    assert "collected" in capsys.readouterr().out


def test_move_collects_salary_when_landing_on_go():
    """Landing exactly on Go should still award the salary."""
    player = Player("Bob")
    player.position = 37

    player.move(3)

    assert player.position == 0
    assert player.balance == 1500 + GO_SALARY


def test_move_without_wrapping_does_not_award_salary():
    """Regular movement on the same lap should not pay the player."""
    player = Player("Carol")

    player.move(6)

    assert player.position == 6
    assert player.balance == 1500
