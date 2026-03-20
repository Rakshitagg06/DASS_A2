"""White-box tests for the pre-roll action menu."""

from moneypoly.game import Game


def test_play_turn_opens_the_pre_roll_menu(monkeypatch):
    """Each turn should expose the pre-roll options before the dice are rolled."""
    game = Game(["Alice", "Bob"])
    calls = []
    monkeypatch.setattr(
        game, "interactive_menu", lambda player: calls.append(player.name)
    )
    monkeypatch.setattr(game.dice, "roll", lambda: 1)
    monkeypatch.setattr(game.dice, "describe", lambda: "1 + 0 = 1")
    monkeypatch.setattr(game.dice, "is_doubles", lambda: False)
    game.dice.doubles_streak = 0
    monkeypatch.setattr(game, "_move_and_resolve", lambda _player, _roll: None)

    game.play_turn()

    assert calls == ["Alice"]
