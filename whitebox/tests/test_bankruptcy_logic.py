"""Regression tests for bankruptcy edge cases."""

from moneypoly.game import Game


def test_player_with_zero_cash_and_assets_is_not_eliminated():
    """Owning assets should keep a zero-cash player alive in the game."""
    game = Game(["Alice", "Bob"])
    player = game.players[0]
    prop = game.board.get_property_at(1)
    prop.owner = player
    player.add_property(prop)
    player.balance = 0

    game._check_bankruptcy(player)

    assert player in game.players
    assert prop.owner is player


def test_player_with_negative_cash_and_assets_is_not_eliminated():
    """A player who can recover through assets should not be removed immediately."""
    game = Game(["Alice", "Bob"])
    player = game.players[0]
    prop = game.board.get_property_at(1)
    prop.owner = player
    player.add_property(prop)
    player.balance = -10

    game._check_bankruptcy(player)

    assert player in game.players


def test_player_with_negative_total_net_worth_is_eliminated():
    """Truly insolvent players should still be eliminated."""
    game = Game(["Alice", "Bob"])
    player = game.players[0]
    player.balance = -1

    game._check_bankruptcy(player)

    assert player not in game.players
