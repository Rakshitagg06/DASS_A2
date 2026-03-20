"""Additional white-box tests for branch-heavy gameplay paths."""

from moneypoly.config import INCOME_TAX_AMOUNT, LUXURY_TAX_AMOUNT
from moneypoly.game import Game
from moneypoly import ui


def test_move_and_resolve_income_tax_collects_for_the_bank():
    """Landing on income tax should deduct the fixed amount and credit the bank."""
    game = Game(["Alice", "Bob"])
    player = game.players[0]
    player.position = 3
    starting_bank_balance = game.bank.get_balance()

    game._move_and_resolve(player, 1)

    assert player.position == 4
    assert player.balance == 1500 - INCOME_TAX_AMOUNT
    assert game.bank.get_balance() == starting_bank_balance + INCOME_TAX_AMOUNT


def test_move_and_resolve_luxury_tax_collects_for_the_bank():
    """Landing on luxury tax should deduct the fixed amount and credit the bank."""
    game = Game(["Alice", "Bob"])
    player = game.players[0]
    player.position = 37
    starting_bank_balance = game.bank.get_balance()

    game._move_and_resolve(player, 1)

    assert player.position == 38
    assert player.balance == 1500 - LUXURY_TAX_AMOUNT
    assert game.bank.get_balance() == starting_bank_balance + LUXURY_TAX_AMOUNT


def test_move_and_resolve_go_to_jail_square():
    """Landing on the Go To Jail tile should send the player to jail."""
    game = Game(["Alice", "Bob"])
    player = game.players[0]
    player.position = 29

    game._move_and_resolve(player, 1)

    assert player.in_jail is True
    assert player.position == 10


def test_collect_card_pays_out_from_the_bank():
    """Collect cards should increase the player balance and lower bank reserves."""
    game = Game(["Alice", "Bob"])
    player = game.players[0]
    starting_bank_balance = game.bank.get_balance()

    game._apply_card(
        player,
        {"description": "Collect $150.", "action": "collect", "value": 150},
    )

    assert player.balance == 1650
    assert game.bank.get_balance() == starting_bank_balance - 150


def test_jail_free_card_increases_the_player_inventory():
    """Jail-free cards should be stored on the player."""
    game = Game(["Alice", "Bob"])
    player = game.players[0]

    game._apply_card(
        player,
        {"description": "Get out of jail free.", "action": "jail_free", "value": 0},
    )

    assert player.get_out_of_jail_cards == 1


def test_auction_property_accepts_the_highest_valid_bid(monkeypatch):
    """Auctions should skip invalid bids and award the highest affordable one."""
    game = Game(["Alice", "Bob", "Carol"])
    prop = game.board.get_property_at(1)
    bids = iter([5, 2_000, 200])
    starting_bank_balance = game.bank.get_balance()
    monkeypatch.setattr(ui, "safe_int_input", lambda _prompt, default=0: next(bids))

    game.auction_property(prop)

    winner = game.players[2]
    assert prop.owner is winner
    assert winner.balance == 1300
    assert game.bank.get_balance() == starting_bank_balance + 200


def test_board_helpers_track_owned_and_unowned_properties():
    """Board helper methods should reflect the latest ownership state."""
    game = Game(["Alice", "Bob"])
    player = game.players[0]
    prop = game.board.get_property_at(1)
    prop.owner = player
    player.add_property(prop)

    assert game.board.properties_owned_by(player) == [prop]
    assert prop not in game.board.unowned_properties()
    assert game.board.is_purchasable(3) is True
    assert game.board.is_purchasable(1) is False


def test_safe_int_input_returns_the_default_on_invalid_text(monkeypatch):
    """Invalid integer input should fall back to the provided default."""
    monkeypatch.setattr("builtins.input", lambda _prompt: "oops")

    assert ui.safe_int_input("Choice: ", default=7) == 7


def test_confirm_treats_lowercase_y_as_yes(monkeypatch):
    """The yes/no helper should accept a standard affirmative answer."""
    monkeypatch.setattr("builtins.input", lambda _prompt: "y")

    assert ui.confirm("Continue? ") is True
