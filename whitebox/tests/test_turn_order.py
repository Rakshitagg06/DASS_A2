"""White-box tests for turn sequencing after player elimination."""

from moneypoly.game import Game


def test_bankruptcy_does_not_skip_the_next_player(monkeypatch):
    """If the active player is eliminated, the next player should still get the turn."""
    game = Game(["Alice", "Bob", "Carol"])

    monkeypatch.setattr(game.dice, "roll", lambda: 4)
    monkeypatch.setattr(game.dice, "describe", lambda: "2 + 2 = 4")
    monkeypatch.setattr(game.dice, "is_doubles", lambda: False)
    game.dice.doubles_streak = 0

    def bankrupt_current_player(player, _roll):
        player.balance = 0
        game._check_bankruptcy(player)

    monkeypatch.setattr(game, "_move_and_resolve", bankrupt_current_player)

    game.play_turn()

    assert [player.name for player in game.players] == ["Bob", "Carol"]
    assert game.current_player().name == "Bob"
