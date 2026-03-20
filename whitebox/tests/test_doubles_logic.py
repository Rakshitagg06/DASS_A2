"""Regression tests for doubles streak handling."""

from moneypoly.game import Game


def test_doubles_streak_resets_when_turn_passes_to_the_next_player(monkeypatch):
    """A new player's first double should not count against the previous player."""
    game = Game(["Alice", "Bob"])
    bob = game.players[1]
    game.dice.doubles_streak = 2
    game.advance_turn()

    def fake_roll():
        game.dice.die1 = 4
        game.dice.die2 = 4
        game.dice.doubles_streak += 1
        return 8

    monkeypatch.setattr(game, "interactive_menu", lambda _player: None)
    monkeypatch.setattr(game.dice, "roll", fake_roll)
    monkeypatch.setattr(game, "_move_and_resolve", lambda _player, _roll: None)

    game.play_turn()

    assert bob.in_jail is False
    assert game.current_player() is bob
    assert game.dice.doubles_streak == 1
