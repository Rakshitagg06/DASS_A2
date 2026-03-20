"""White-box tests for jail payments and mortgage handling."""

from moneypoly.config import JAIL_FINE
from moneypoly.game import Game


def test_jail_fine_is_deducted_before_release(monkeypatch):
    """Paying to leave jail should reduce the player's balance and move them."""
    game = Game(["Alice", "Bob"])
    player = game.players[0]
    player.in_jail = True
    starting_bank_balance = game.bank.get_balance()
    moves = []
    monkeypatch.setattr("moneypoly.ui.confirm", lambda _prompt: True)
    monkeypatch.setattr(game.dice, "roll", lambda: 4)
    monkeypatch.setattr(game.dice, "describe", lambda: "2 + 2 = 4")
    monkeypatch.setattr(
        game,
        "_move_and_resolve",
        lambda current_player, roll: moves.append((current_player.name, roll)),
    )

    game._handle_jail_turn(player)

    assert player.balance == 1500 - JAIL_FINE
    assert game.bank.get_balance() == starting_bank_balance + JAIL_FINE
    assert player.in_jail is False
    assert player.jail_turns == 0
    assert moves == [("Alice", 4)]


def test_cannot_pay_voluntary_jail_fine_without_cash(monkeypatch):
    """Players without enough money should stay jailed for the turn."""
    game = Game(["Alice", "Bob"])
    player = game.players[0]
    player.in_jail = True
    player.balance = 40
    monkeypatch.setattr("moneypoly.ui.confirm", lambda _prompt: True)

    game._handle_jail_turn(player)

    assert player.in_jail is True
    assert player.jail_turns == 1
    assert player.balance == 40


def test_unmortgage_fails_without_changing_state_when_cash_is_short():
    """A failed unmortgage should leave the property mortgaged."""
    game = Game(["Alice", "Bob"])
    player = game.players[0]
    prop = game.board.get_property_at(1)
    prop.owner = player
    player.add_property(prop)
    prop.is_mortgaged = True
    player.balance = 10

    assert game.unmortgage_property(player, prop) is False
    assert prop.is_mortgaged is True
    assert player.balance == 10
