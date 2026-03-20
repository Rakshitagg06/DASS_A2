"""Regression tests for direct purchase guard rails."""

from moneypoly.game import Game


def test_buy_property_rejects_already_owned_property():
    """Direct purchase calls should not steal a property from its owner."""
    game = Game(["Alice", "Bob"])
    buyer, owner = game.players
    prop = game.board.get_property_at(1)
    prop.owner = owner
    owner.add_property(prop)

    assert game.buy_property(buyer, prop) is False
    assert prop.owner is owner
    assert prop in owner.properties
    assert prop not in buyer.properties


def test_buy_property_rejects_mortgaged_unowned_property():
    """Mortgaged spaces should not be directly buyable."""
    game = Game(["Alice", "Bob"])
    buyer = game.players[0]
    prop = game.board.get_property_at(1)
    prop.is_mortgaged = True

    assert game.buy_property(buyer, prop) is False
    assert prop.owner is None
    assert buyer.properties == []
