"""Decision-focused tests for helper modules, UI, and the CLI entry point."""

from pathlib import Path
import runpy
from importlib import import_module

import pytest

from moneypoly.bank import Bank
from moneypoly.board import Board
from moneypoly.cards import CardDeck
from moneypoly.dice import Dice
from moneypoly.player import Player
from moneypoly.property import Property, PropertyGroup
from moneypoly import ui


def test_bank_zero_payout_and_insufficient_payout():
    """The bank should ignore zero payouts and reject unaffordable ones."""
    bank = Bank()

    assert bank.pay_out(0) == 0
    with pytest.raises(ValueError):
        bank.pay_out(bank.get_balance() + 1)


def test_bank_give_loan_ignores_non_positive_amounts():
    """Non-positive loans should not change the bank or player state."""
    bank = Bank()
    player = Player("Alice")
    starting_bank_balance = bank.get_balance()

    assert bank.give_loan(player, 0) == 0
    assert player.balance == 1500
    assert bank.get_balance() == starting_bank_balance


def test_bank_summary_and_repr(capsys):
    """The bank summary helpers should render readable state."""
    bank = Bank()
    bank.collect(125)

    bank.summary()

    output = capsys.readouterr().out
    assert "Bank reserves" in output
    assert "Total collected" in output
    assert "Bank(funds=" in repr(bank)


def test_board_reports_blank_and_special_tiles():
    """Board lookup helpers should distinguish blank, special, and missing tiles."""
    board = Board()

    assert board.get_property_at(40) is None
    assert board.get_tile_type(1) == "property"
    assert board.get_tile_type(12) == "blank"
    assert board.get_tile_type(0) == "go"
    assert board.is_special_tile(0) is True
    assert board.is_special_tile(1) is False


def test_board_purchasable_checks_cover_none_owned_and_mortgaged():
    """Purchasable checks should reject missing, owned, and mortgaged spaces."""
    board = Board()
    player = Player("Alice")
    prop = board.get_property_at(1)

    assert board.is_purchasable(12) is False
    assert board.is_purchasable(1) is True

    prop.owner = player
    assert board.is_purchasable(1) is False

    prop.owner = None
    prop.is_mortgaged = True
    assert board.is_purchasable(1) is False


def test_board_repr_reflects_owned_property_count():
    """The board repr should include the number of owned properties."""
    board = Board()
    player = Player("Bob")
    prop = board.get_property_at(1)
    prop.owner = player

    assert "1 owned" in repr(board)


def test_card_deck_peek_len_repr_and_reshuffle(monkeypatch):
    """Deck helpers should support introspection and reset after shuffling."""
    first = {"description": "A", "action": "collect", "value": 1}
    second = {"description": "B", "action": "pay", "value": 1}
    deck = CardDeck([first, second])
    monkeypatch.setattr(
        "random.shuffle", lambda cards: cards.__setitem__(slice(None), list(reversed(cards)))
    )

    assert len(deck) == 2
    assert deck.peek() is first
    deck.draw()
    deck.reshuffle()

    assert deck.index == 0
    assert deck.peek() is second
    assert repr(deck) == "CardDeck(2 cards, next=0)"


def test_dice_reset_describe_and_repr():
    """Dice helpers should describe and reset their internal state."""
    dice = Dice()
    dice.die1 = 3
    dice.die2 = 4
    dice.doubles_streak = 2

    assert dice.describe() == "3 + 4 = 7"
    assert repr(dice) == "Dice(die1=3, die2=4, streak=2)"

    dice.reset()

    assert (dice.die1, dice.die2, dice.doubles_streak) == (0, 0, 0)


def test_dice_roll_increments_the_doubles_streak(monkeypatch):
    """A doubles roll should increment the tracked doubles streak."""
    values = iter([5, 5])
    monkeypatch.setattr("random.randint", lambda _low, _high: next(values))
    dice = Dice()

    total = dice.roll()

    assert total == 10
    assert dice.doubles_streak == 1


def test_player_validation_and_display_helpers():
    """Player helpers should validate balances and expose readable status."""
    player = Player("Carol")
    group = PropertyGroup("Brown", "brown")
    prop = Property("Baltic Avenue", 3, 60, 4, group)
    prop.owner = player
    player.add_property(prop)
    player.in_jail = True

    with pytest.raises(ValueError):
        player.add_money(-1)
    with pytest.raises(ValueError):
        player.deduct_money(-1)

    player.add_property(prop)
    player.remove_property(Property("Ghost", 99, 10, 1))

    assert player.count_properties() == 1
    assert "[JAILED]" in player.status_line()
    assert "Player('Carol'" in repr(player)


def test_property_helpers_cover_mortgage_availability_and_repr():
    """Property helpers should report mortgage and availability state correctly."""
    group = PropertyGroup("Red", "red")
    first = Property("Kentucky Avenue", 21, 220, 18, group)
    second = Property("Indiana Avenue", 23, 220, 18)
    owner = Player("Alice")

    assert first.get_rent() == 18
    assert first.is_available() is True
    assert first.mortgage() == 110
    assert first.mortgage() == 0
    assert first.get_rent() == 0
    assert first.unmortgage_cost() == 121
    assert first.unmortgage() == 121
    assert second.unmortgage_cost() == 0
    assert second.unmortgage() == 0

    first.owner = owner
    assert first.is_available() is False
    assert "owner='Alice'" in repr(first)


def test_property_group_helpers_cover_owner_counts_size_and_repr():
    """Property groups should maintain links and aggregate ownership correctly."""
    group = PropertyGroup("Blue", "blue")
    first = Property("Park Place", 37, 350, 35)
    second = Property("Boardwalk", 39, 400, 50)
    alice = Player("Alice")
    bob = Player("Bob")

    group.add_property(first)
    group.add_property(first)
    group.add_property(second)
    first.owner = alice
    second.owner = bob
    third = Property("Marvin Gardens", 29, 280, 24)
    group.add_property(third)

    counts = group.get_owner_counts()

    assert group.all_owned_by(None) is False
    assert counts[alice] == 1
    assert counts[bob] == 1
    assert group.size() == 3
    assert "3 properties" in repr(group)


def test_ui_print_helpers_cover_player_board_and_standings(capsys):
    """UI helpers should render player cards, standings, and board ownership."""
    board = Board()
    alice = Player("Alice")
    bob = Player("Bob")
    prop = board.get_property_at(1)
    prop.owner = alice
    prop.is_mortgaged = True
    alice.add_property(prop)
    alice.in_jail = True
    alice.jail_turns = 2
    alice.get_out_of_jail_cards = 1
    bob.balance = 2000

    ui.print_banner("MoneyPoly")
    ui.print_player_card(alice)
    ui.print_standings([alice, bob])
    ui.print_board_ownership(board)

    output = capsys.readouterr().out
    assert "MoneyPoly" in output
    assert "IN JAIL" in output
    assert "Jail cards: 1" in output
    assert "[JAILED]" in output
    assert "(* = mortgaged)" in output


def test_ui_print_player_card_handles_players_without_properties(capsys):
    """Player cards should print a friendly placeholder when no property is owned."""
    player = Player("Dana")

    ui.print_player_card(player)

    assert "Properties: none" in capsys.readouterr().out


def test_ui_input_helpers_cover_fallbacks_and_negative_confirmation(monkeypatch):
    """Input helpers should fall back on EOF and reject non-yes answers."""
    monkeypatch.setattr("builtins.input", lambda _prompt: (_ for _ in ()).throw(EOFError))
    assert ui.safe_int_input("Choice: ", default=11) == 11

    monkeypatch.setattr("builtins.input", lambda _prompt: "n")
    assert ui.confirm("Continue? ") is False
    assert ui.format_currency(1500) == "$1,500"


def test_get_player_names_trims_and_filters_empty_entries(monkeypatch):
    """The CLI prompt should return only cleaned player names."""
    entry = import_module("main")
    monkeypatch.setattr("builtins.input", lambda _prompt: " Alice , , Bob ,  Carol ")

    assert entry.get_player_names() == ["Alice", "Bob", "Carol"]


def test_main_runs_the_game_when_setup_succeeds(monkeypatch):
    """The CLI entry point should construct and run the game on success."""
    entry = import_module("main")
    seen = []

    class DummyGame:
        def __init__(self, names):
            seen.append(tuple(names))

        def run(self):
            seen.append("ran")

    monkeypatch.setattr(entry, "get_player_names", lambda: ["Alice", "Bob"])
    monkeypatch.setattr(entry, "Game", DummyGame)

    entry.main()

    assert seen == [("Alice", "Bob"), "ran"]


def test_main_handles_keyboard_interrupt(monkeypatch, capsys):
    """The CLI should print a friendly message when the game is interrupted."""
    entry = import_module("main")

    class DummyGame:
        def __init__(self, _names):
            pass

        def run(self):
            raise KeyboardInterrupt

    monkeypatch.setattr(entry, "get_player_names", lambda: ["Alice", "Bob"])
    monkeypatch.setattr(entry, "Game", DummyGame)

    entry.main()

    assert "Game interrupted" in capsys.readouterr().out


def test_main_handles_setup_value_errors(monkeypatch, capsys):
    """The CLI should surface setup errors without a traceback."""
    entry = import_module("main")

    class DummyGame:
        def __init__(self, _names):
            raise ValueError("bad setup")

    monkeypatch.setattr(entry, "get_player_names", lambda: ["Alice", "Bob"])
    monkeypatch.setattr(entry, "Game", DummyGame)

    entry.main()

    assert "Setup error: bad setup" in capsys.readouterr().out


def test_main_module_runs_from_the_script_entry_point(monkeypatch):
    """Executing the file as __main__ should trigger the CLI entry point."""
    called = []
    main_path = Path(__file__).resolve().parents[2] / "moneypoly" / "moneypoly" / "main.py"

    class DummyGame:
        def __init__(self, _names):
            called.append("init")

        def run(self):
            called.append("run")

    monkeypatch.setattr("builtins.input", lambda _prompt: "Alice,Bob")
    monkeypatch.setattr("moneypoly.game.Game", DummyGame)

    runpy.run_path(str(main_path), run_name="__main__")

    assert called == ["init", "run"]
