"""White-box tests for bank cash-flow behavior."""

import pytest

from moneypoly.bank import Bank
from moneypoly.game import Game


def test_bank_collect_rejects_negative_amounts():
    """Negative collections should fail fast instead of silently mutating funds."""
    bank = Bank()

    with pytest.raises(ValueError):
        bank.collect(-10)


def test_give_loan_reduces_bank_reserves_and_tracks_it():
    """Emergency loans should leave the bank and be recorded."""
    bank = Bank()
    game = Game(["Alice", "Bob"])
    player = game.players[0]
    starting_balance = bank.get_balance()

    paid = bank.give_loan(player, 300)

    assert paid == 300
    assert player.balance == 1800
    assert bank.get_balance() == starting_balance - 300
    assert bank.loan_count() == 1
    assert bank.total_loans_issued() == 300


def test_mortgage_property_uses_bank_funds_for_the_payout():
    """Mortgaging should pay the player from bank reserves."""
    game = Game(["Alice", "Bob"])
    player = game.players[0]
    prop = game.board.get_property_at(1)
    prop.owner = player
    player.add_property(prop)
    starting_bank_balance = game.bank.get_balance()

    assert game.mortgage_property(player, prop) is True
    assert player.balance == 1500 + prop.mortgage_value
    assert game.bank.get_balance() == starting_bank_balance - prop.mortgage_value
