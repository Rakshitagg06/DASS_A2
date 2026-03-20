"""White-box tests around purchasable board spaces."""

from moneypoly.game import Game


def test_board_exposes_railroads_as_real_properties():
    """Railroad tiles should have backing Property objects."""
    game = Game(["Alice", "Bob"])

    for position in (5, 15, 25, 35):
        prop = game.board.get_property_at(position)
        assert prop is not None
        assert prop.price == 200
        assert game.board.get_tile_type(position) == "railroad"


def test_landing_on_railroad_uses_property_flow(monkeypatch):
    """Players should be able to buy a railroad when they land on one."""
    game = Game(["Alice", "Bob"])
    player = game.players[0]
    player.position = 4
    railroad = game.board.get_property_at(5)
    monkeypatch.setattr("builtins.input", lambda _prompt: "b")

    game._move_and_resolve(player, 1)

    assert railroad.owner is player
    assert railroad in player.properties


def test_buy_property_allows_exact_balance_purchase():
    """Having exactly the asking price should still allow a purchase."""
    game = Game(["Alice", "Bob"])
    player = game.players[0]
    prop = game.board.get_property_at(1)
    player.balance = prop.price

    assert game.buy_property(player, prop) is True
    assert player.balance == 0
    assert prop.owner is player
