"""White-box tests for absolute-move card destinations."""

from moneypoly.config import INCOME_TAX_AMOUNT
from moneypoly.game import Game


def test_move_to_card_resolves_railroad_purchase(monkeypatch):
    """Move cards should run the same purchase logic on railroads as normal movement."""
    game = Game(["Alice", "Bob"])
    player = game.players[0]
    railroad = game.board.get_property_at(5)
    monkeypatch.setattr("builtins.input", lambda _prompt: "b")

    game._apply_card(
        player,
        {"description": "Advance to Reading Railroad.", "action": "move_to", "value": 5},
    )

    assert player.position == 5
    assert railroad.owner is player


def test_move_to_card_resolves_tax_spaces():
    """Absolute moves should trigger non-property landing effects too."""
    game = Game(["Alice", "Bob"])
    player = game.players[0]
    starting_bank_balance = game.bank.get_balance()

    game._apply_card(
        player,
        {"description": "Move to income tax.", "action": "move_to", "value": 4},
    )

    assert player.position == 4
    assert player.balance == 1500 - INCOME_TAX_AMOUNT
    assert game.bank.get_balance() == starting_bank_balance + INCOME_TAX_AMOUNT


def test_move_to_card_resolves_go_to_jail_spaces():
    """Absolute moves to the jail square should still jail the player."""
    game = Game(["Alice", "Bob"])
    player = game.players[0]

    game._apply_card(
        player,
        {"description": "Move to Go To Jail.", "action": "move_to", "value": 30},
    )

    assert player.in_jail is True
    assert player.position == 10
