"""White-box tests for rent and trade cash transfers."""

from moneypoly.game import Game


def test_pay_rent_transfers_cash_to_owner():
    """Rent should leave the visitor and reach the property owner."""
    game = Game(["Alice", "Bob"])
    visitor, owner = game.players
    prop = game.board.get_property_at(1)
    prop.owner = owner
    owner.add_property(prop)

    game.pay_rent(visitor, prop)

    assert visitor.balance == 1498
    assert owner.balance == 1502


def test_pay_rent_skips_mortgaged_properties():
    """Mortgaged properties should not move any cash."""
    game = Game(["Alice", "Bob"])
    visitor, owner = game.players
    prop = game.board.get_property_at(1)
    prop.owner = owner
    owner.add_property(prop)
    prop.is_mortgaged = True

    game.pay_rent(visitor, prop)

    assert visitor.balance == 1500
    assert owner.balance == 1500


def test_trade_moves_cash_and_property_to_the_right_players():
    """A completed trade should pay the seller and transfer ownership."""
    game = Game(["Alice", "Bob"])
    seller, buyer = game.players
    prop = game.board.get_property_at(3)
    prop.owner = seller
    seller.add_property(prop)

    assert game.trade(seller, buyer, prop, 200) is True
    assert seller.balance == 1700
    assert buyer.balance == 1300
    assert prop.owner is buyer
    assert prop in buyer.properties
    assert prop not in seller.properties


def test_trade_rejects_negative_cash_amounts():
    """Negative trade amounts should be refused before balances change."""
    game = Game(["Alice", "Bob"])
    seller, buyer = game.players
    prop = game.board.get_property_at(3)
    prop.owner = seller
    seller.add_property(prop)

    assert game.trade(seller, buyer, prop, -50) is False
    assert seller.balance == 1500
    assert buyer.balance == 1500
    assert prop.owner is seller
