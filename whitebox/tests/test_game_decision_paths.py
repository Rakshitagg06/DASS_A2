"""Branch-focused tests for the remaining MoneyPoly game paths."""

import pytest

from moneypoly.game import Game


def test_play_turn_advances_after_a_regular_roll(monkeypatch):
    """A normal turn should advance to the next player."""
    game = Game(["Alice", "Bob"])
    monkeypatch.setattr(game, "interactive_menu", lambda _player: None)
    monkeypatch.setattr(game.dice, "roll", lambda: 5)
    monkeypatch.setattr(game.dice, "describe", lambda: "2 + 3 = 5")
    monkeypatch.setattr(game.dice, "is_doubles", lambda: False)
    monkeypatch.setattr(game, "_move_and_resolve", lambda _player, _roll: None)

    game.play_turn()

    assert game.current_player().name == "Bob"
    assert game.turn_number == 1


def test_play_turn_keeps_the_same_player_after_doubles(monkeypatch):
    """Rolling doubles should grant an extra roll instead of advancing the turn."""
    game = Game(["Alice", "Bob"])

    def fake_roll():
        game.dice.die1 = 2
        game.dice.die2 = 2
        game.dice.doubles_streak = 1
        return 4

    monkeypatch.setattr(game, "interactive_menu", lambda _player: None)
    monkeypatch.setattr(game.dice, "roll", fake_roll)
    monkeypatch.setattr(game, "_move_and_resolve", lambda _player, _roll: None)

    game.play_turn()

    assert game.current_player().name == "Alice"
    assert game.turn_number == 0


def test_play_turn_sends_the_player_to_jail_after_three_doubles(monkeypatch):
    """The third doubles in the same turn should send the player to jail."""
    game = Game(["Alice", "Bob"])
    player = game.players[0]
    game.dice.doubles_streak = 2

    def fake_roll():
        game.dice.die1 = 6
        game.dice.die2 = 6
        game.dice.doubles_streak += 1
        return 12

    monkeypatch.setattr(game, "interactive_menu", lambda _player: None)
    monkeypatch.setattr(game.dice, "roll", fake_roll)

    game.play_turn()

    assert player.in_jail is True
    assert player.position == 10
    assert game.current_player().name == "Bob"


def test_play_turn_does_not_grant_an_extra_roll_after_doubles_land_on_go_to_jail(
    monkeypatch,
):
    """Landing on Go To Jail with doubles should still end the turn immediately."""
    game = Game(["Alice", "Bob"])
    player = game.players[0]
    player.position = 24

    def fake_roll():
        game.dice.die1 = 3
        game.dice.die2 = 3
        game.dice.doubles_streak = 1
        return 6

    monkeypatch.setattr(game, "interactive_menu", lambda _player: None)
    monkeypatch.setattr(game.dice, "roll", fake_roll)

    game.play_turn()

    assert player.in_jail is True
    assert player.position == 10
    assert game.current_player().name == "Bob"
    assert game.turn_number == 1


def test_play_turn_does_not_grant_an_extra_roll_after_a_doubles_jail_card(
    monkeypatch,
):
    """A jail card should end the turn even when the triggering roll was doubles."""
    game = Game(["Alice", "Bob"])
    player = game.players[0]
    player.position = 3

    def fake_roll():
        game.dice.die1 = 2
        game.dice.die2 = 2
        game.dice.doubles_streak = 1
        return 4

    monkeypatch.setattr(game, "interactive_menu", lambda _player: None)
    monkeypatch.setattr(game.dice, "roll", fake_roll)
    monkeypatch.setattr(
        game.decks["chance"],
        "draw",
        lambda: {"description": "Go to Jail.", "action": "jail", "value": 0},
    )

    game.play_turn()

    assert player.in_jail is True
    assert player.position == 10
    assert game.current_player().name == "Bob"
    assert game.turn_number == 1


def test_play_turn_processes_jailed_players_and_then_advances(monkeypatch):
    """A jailed player's turn should use the jail flow and then pass the turn on."""
    game = Game(["Alice", "Bob"])
    player = game.players[0]
    player.in_jail = True
    seen = []
    monkeypatch.setattr(game, "interactive_menu", lambda _player: None)
    monkeypatch.setattr(game, "_handle_jail_turn", lambda current_player: seen.append(current_player))

    game.play_turn()

    assert seen == [player]
    assert game.current_player().name == "Bob"


def test_play_turn_handles_jailed_players_removed_during_jail_logic(monkeypatch):
    """If jail handling removes the player, the turn should return cleanly."""
    game = Game(["Alice", "Bob"])
    player = game.players[0]
    player.in_jail = True
    monkeypatch.setattr(game, "interactive_menu", lambda _player: None)

    def remove_player(current_player):
        game.players.remove(current_player)

    monkeypatch.setattr(game, "_handle_jail_turn", remove_player)

    game.play_turn()

    assert [remaining.name for remaining in game.players] == ["Bob"]
    assert game.current_index == 0


@pytest.mark.parametrize("position", [0, 10, 12, 20])
def test_resolve_current_tile_leaves_non_action_tiles_alone(position):
    """Go, jail, blank, and free parking tiles should not trigger side effects."""
    game = Game(["Alice", "Bob"])
    player = game.players[0]
    player.position = position
    starting_balance = player.balance

    game._resolve_current_tile(player)

    assert player.balance == starting_balance
    assert player.position == position


def test_resolve_current_tile_draws_a_chance_card(monkeypatch):
    """Chance tiles should draw from the chance deck and apply the card."""
    game = Game(["Alice", "Bob"])
    player = game.players[0]
    player.position = 7
    seen = []
    card = {"description": "Collect", "action": "collect", "value": 50}
    monkeypatch.setattr(game.decks["chance"], "draw", lambda: card)
    monkeypatch.setattr(game, "_apply_card", lambda current_player, drawn: seen.append((current_player, drawn)))

    game._resolve_current_tile(player)

    assert seen == [(player, card)]


def test_resolve_current_tile_draws_a_community_chest_card(monkeypatch):
    """Community Chest tiles should draw from the matching deck."""
    game = Game(["Alice", "Bob"])
    player = game.players[0]
    player.position = 17
    seen = []
    card = {"description": "Collect", "action": "collect", "value": 50}
    monkeypatch.setattr(game.decks["community_chest"], "draw", lambda: card)
    monkeypatch.setattr(game, "_apply_card", lambda current_player, drawn: seen.append((current_player, drawn)))

    game._resolve_current_tile(player)

    assert seen == [(player, card)]


@pytest.mark.parametrize("tile_name", ["railroad", "property"])
def test_resolve_current_tile_ignores_missing_property_objects(monkeypatch, tile_name):
    """The resolver should safely ignore purchasable tiles with no backing object."""
    game = Game(["Alice", "Bob"])
    player = game.players[0]
    monkeypatch.setattr(game.board, "get_tile_type", lambda _position: tile_name)
    monkeypatch.setattr(game.board, "get_property_at", lambda _position: None)

    game._resolve_current_tile(player)

    assert player in game.players


def test_handle_property_tile_can_start_an_auction(monkeypatch):
    """Choosing auction should delegate to the auction helper."""
    game = Game(["Alice", "Bob"])
    player = game.players[0]
    prop = game.board.get_property_at(1)
    seen = []
    monkeypatch.setattr("builtins.input", lambda _prompt: "a")
    monkeypatch.setattr(game, "auction_property", lambda current_prop: seen.append(current_prop))

    game._handle_property_tile(player, prop)

    assert seen == [prop]


def test_handle_property_tile_skips_when_the_player_passes(monkeypatch, capsys):
    """Unexpected input should fall back to passing on the property."""
    game = Game(["Alice", "Bob"])
    player = game.players[0]
    prop = game.board.get_property_at(1)
    monkeypatch.setattr("builtins.input", lambda _prompt: "x")

    game._handle_property_tile(player, prop)

    assert "passes on" in capsys.readouterr().out


def test_handle_property_tile_notices_when_the_player_already_owns_it(capsys):
    """Landing on your own property should not charge rent."""
    game = Game(["Alice", "Bob"])
    player = game.players[0]
    prop = game.board.get_property_at(1)
    prop.owner = player
    player.add_property(prop)

    game._handle_property_tile(player, prop)

    assert "No rent due" in capsys.readouterr().out


def test_handle_property_tile_charges_rent_when_another_player_owns_it(monkeypatch):
    """Landing on another player's property should delegate to rent collection."""
    game = Game(["Alice", "Bob"])
    visitor, owner = game.players
    prop = game.board.get_property_at(1)
    prop.owner = owner
    owner.add_property(prop)
    seen = []
    monkeypatch.setattr(game, "pay_rent", lambda current_player, current_prop: seen.append((current_player, current_prop)))

    game._handle_property_tile(visitor, prop)

    assert seen == [(visitor, prop)]


def test_buy_property_reports_insufficient_funds():
    """Purchase attempts should fail cleanly when the player is short on cash."""
    game = Game(["Alice", "Bob"])
    player = game.players[0]
    prop = game.board.get_property_at(39)
    player.balance = prop.price - 1

    assert game.buy_property(player, prop) is False
    assert prop.owner is None


def test_resolve_current_tile_handles_standard_properties(monkeypatch):
    """Standard property tiles should delegate to the property handler."""
    game = Game(["Alice", "Bob"])
    player = game.players[0]
    player.position = 1
    seen = []
    monkeypatch.setattr(game, "_handle_property_tile", lambda current_player, prop: seen.append((current_player, prop)))

    game._resolve_current_tile(player)

    assert seen == [(player, game.board.get_property_at(1))]


def test_pay_rent_ignores_unowned_property():
    """Rent should do nothing when a property has no owner."""
    game = Game(["Alice", "Bob"])
    player = game.players[0]
    prop = game.board.get_property_at(1)

    game.pay_rent(player, prop)

    assert player.balance == 1500


def test_mortgage_property_rejects_wrong_owner_and_repeated_mortgages():
    """Mortgage rules should reject invalid ownership and repeated calls."""
    game = Game(["Alice", "Bob"])
    player, owner = game.players
    prop = game.board.get_property_at(1)
    prop.owner = owner
    owner.add_property(prop)

    assert game.mortgage_property(player, prop) is False
    assert game.mortgage_property(owner, prop) is True
    assert game.mortgage_property(owner, prop) is False


def test_unmortgage_property_rejects_wrong_owner_and_non_mortgaged_spaces():
    """Unmortgage rules should validate both ownership and state."""
    game = Game(["Alice", "Bob"])
    player, owner = game.players
    prop = game.board.get_property_at(1)
    prop.owner = owner
    owner.add_property(prop)

    assert game.unmortgage_property(player, prop) is False
    assert game.unmortgage_property(owner, prop) is False


def test_unmortgage_property_succeeds_for_the_owner():
    """A valid unmortgage should restore the property and charge the player."""
    game = Game(["Alice", "Bob"])
    player = game.players[0]
    prop = game.board.get_property_at(1)
    prop.owner = player
    prop.is_mortgaged = True
    player.add_property(prop)
    starting_bank_balance = game.bank.get_balance()

    assert game.unmortgage_property(player, prop) is True
    assert prop.is_mortgaged is False
    assert player.balance == 1500 - 33
    assert game.bank.get_balance() == starting_bank_balance + 33


def test_trade_rejects_wrong_owner_and_insufficient_buyer_balance():
    """Trade failures should leave the property untouched."""
    game = Game(["Alice", "Bob"])
    seller, buyer = game.players
    prop = game.board.get_property_at(1)

    assert game.trade(seller, buyer, prop, 10) is False

    prop.owner = seller
    seller.add_property(prop)
    buyer.balance = 5

    assert game.trade(seller, buyer, prop, 10) is False
    assert prop.owner is seller


def test_auction_property_leaves_it_unowned_when_everyone_passes(monkeypatch):
    """An auction with only passes should not assign the property."""
    game = Game(["Alice", "Bob"])
    prop = game.board.get_property_at(1)
    monkeypatch.setattr("moneypoly.ui.safe_int_input", lambda _prompt, default=0: 0)

    game.auction_property(prop)

    assert prop.owner is None


def test_handle_jail_turn_uses_a_jail_free_card(monkeypatch):
    """Players with a jail-free card should be able to spend it and move."""
    game = Game(["Alice", "Bob"])
    player = game.players[0]
    player.in_jail = True
    player.get_out_of_jail_cards = 1
    moves = []
    confirms = iter([True])
    monkeypatch.setattr("moneypoly.ui.confirm", lambda _prompt: next(confirms))
    monkeypatch.setattr(game.dice, "roll", lambda: 6)
    monkeypatch.setattr(game.dice, "describe", lambda: "3 + 3 = 6")
    monkeypatch.setattr(game, "_move_and_resolve", lambda current_player, roll: moves.append((current_player, roll)))

    game._handle_jail_turn(player)

    assert player.in_jail is False
    assert player.get_out_of_jail_cards == 0
    assert moves == [(player, 6)]


def test_handle_jail_turn_can_decline_the_card_and_pay_instead(monkeypatch):
    """Players should be able to keep the card and pay the fine instead."""
    game = Game(["Alice", "Bob"])
    player = game.players[0]
    player.in_jail = True
    player.get_out_of_jail_cards = 1
    confirms = iter([False, True])
    moves = []
    monkeypatch.setattr("moneypoly.ui.confirm", lambda _prompt: next(confirms))
    monkeypatch.setattr(game.dice, "roll", lambda: 7)
    monkeypatch.setattr(game.dice, "describe", lambda: "3 + 4 = 7")
    monkeypatch.setattr(game, "_move_and_resolve", lambda current_player, roll: moves.append((current_player, roll)))

    game._handle_jail_turn(player)

    assert player.get_out_of_jail_cards == 1
    assert player.in_jail is False
    assert player.balance == 1450
    assert moves == [(player, 7)]


def test_handle_jail_turn_waits_when_the_player_declines_to_leave(monkeypatch):
    """Declining both options should simply consume one jail turn."""
    game = Game(["Alice", "Bob"])
    player = game.players[0]
    player.in_jail = True
    confirms = iter([False, False])
    monkeypatch.setattr("moneypoly.ui.confirm", lambda _prompt: next(confirms))

    game._handle_jail_turn(player)

    assert player.in_jail is True
    assert player.jail_turns == 1


def test_handle_jail_turn_forces_release_after_three_turns(monkeypatch):
    """On the third missed jail turn, the player should be forced out."""
    game = Game(["Alice", "Bob"])
    player = game.players[0]
    player.in_jail = True
    player.jail_turns = 2
    confirms = iter([False, False])
    moves = []
    monkeypatch.setattr("moneypoly.ui.confirm", lambda _prompt: next(confirms))
    monkeypatch.setattr(game.dice, "roll", lambda: 5)
    monkeypatch.setattr(game.dice, "describe", lambda: "2 + 3 = 5")
    monkeypatch.setattr(game, "_move_and_resolve", lambda current_player, roll: moves.append((current_player, roll)))

    game._handle_jail_turn(player)

    assert player.in_jail is False
    assert player.balance == 1450
    assert moves == [(player, 5)]


def test_apply_card_handles_none_and_unknown_actions():
    """Card application should ignore missing cards and reject unknown actions."""
    game = Game(["Alice", "Bob"])
    player = game.players[0]

    assert game._apply_card(player, None) is None
    with pytest.raises(ValueError):
        game._apply_card(player, {"description": "?", "action": "mystery", "value": 0})


def test_apply_card_pay_and_jail_paths():
    """Pay and jail cards should both apply their side effects."""
    game = Game(["Alice", "Bob"])
    player = game.players[0]
    starting_bank_balance = game.bank.get_balance()

    game._apply_card(player, {"description": "Pay", "action": "pay", "value": 30})
    assert player.balance == 1470
    assert game.bank.get_balance() == starting_bank_balance + 30

    game._apply_card(player, {"description": "Jail", "action": "jail", "value": 0})
    assert player.in_jail is True


def test_apply_card_birthday_and_move_to_go_cover_remaining_handlers():
    """Birthday and pass-Go move cards should route through their helper paths."""
    game = Game(["Alice", "Bob"])
    player, other = game.players
    other.balance = 10

    game._apply_card(
        player,
        {"description": "Birthday", "action": "birthday", "value": 10},
    )
    assert player.balance == 1510
    assert other.balance == 0

    player.position = 39
    game._apply_card(
        player,
        {"description": "Advance to Go", "action": "move_to", "value": 0},
    )
    assert player.position == 0
    assert player.balance == 1710


def test_collect_from_other_players_skips_people_who_cannot_afford_it():
    """Collection cards should only charge players who can actually pay."""
    game = Game(["Alice", "Bob", "Carol"])
    player, bob, carol = game.players
    bob.balance = 10
    carol.balance = 100

    game._handle_collect_from_all_card(player, 50)

    assert player.balance == 1550
    assert bob.balance == 10
    assert carol.balance == 50


def test_check_bankruptcy_leaves_solvent_players_in_the_game():
    """The bankruptcy helper should do nothing for solvent players."""
    game = Game(["Alice", "Bob"])
    player = game.players[0]

    game._check_bankruptcy(player)

    assert player in game.players


def test_check_bankruptcy_releases_properties_and_resets_index():
    """Elimination should clear owned properties and clamp the turn index."""
    game = Game(["Alice", "Bob"])
    player = game.players[1]
    prop = game.board.get_property_at(1)
    prop.owner = player
    prop.is_mortgaged = True
    player.add_property(prop)
    player.balance = -100
    game.current_index = 1

    game._check_bankruptcy(player)

    assert prop.owner is None
    assert prop.is_mortgaged is False
    assert game.current_index == 0


def test_check_bankruptcy_tolerates_players_already_removed_from_the_game():
    """A second bankruptcy check should not crash after the player was removed."""
    game = Game(["Alice", "Bob"])
    player = game.players[0]
    game.players.remove(player)
    game.current_index = 1
    player.balance = -100

    game._check_bankruptcy(player)

    assert [remaining.name for remaining in game.players] == ["Bob"]
    assert game.current_index == 0


def test_find_winner_returns_none_for_an_empty_game():
    """Winner selection should gracefully handle an empty player list."""
    game = Game(["Alice", "Bob"])
    game.players = []

    assert game.find_winner() is None


def test_run_prints_a_winner_when_one_player_remains(capsys):
    """The run loop should announce the surviving player."""
    game = Game(["Alice", "Bob"])
    game.players = [game.players[0]]

    game.run()

    assert "wins with a net worth" in capsys.readouterr().out


def test_run_executes_the_loop_and_prints_standings(monkeypatch, capsys):
    """A multi-player run should execute turns until the loop condition stops it."""
    game = Game(["Alice", "Bob"])
    monkeypatch.setattr("moneypoly.game.MAX_TURNS", 1)
    monkeypatch.setattr(game, "play_turn", lambda: setattr(game, "turn_number", 1))

    game.run()

    output = capsys.readouterr().out
    assert "[ Standings ]" in output
    assert "GAME OVER" in output


def test_run_handles_an_empty_player_list(capsys):
    """The run loop should handle a game with no remaining players."""
    game = Game(["Alice", "Bob"])
    game.players = []

    game.run()

    assert "no players remaining" in capsys.readouterr().out


def test_interactive_menu_dispatches_all_visible_options(monkeypatch):
    """The pre-roll menu should route each numbered choice correctly."""
    game = Game(["Alice", "Bob"])
    player = game.players[0]
    choices = iter([1, 2, 3, 4, 5, 6, 0])
    calls = []
    monkeypatch.setattr(
        "moneypoly.ui.safe_int_input",
        lambda prompt, default=0: 150 if "Loan amount" in prompt else next(choices),
    )
    monkeypatch.setattr("moneypoly.ui.print_standings", lambda players: calls.append(("standings", len(players))))
    monkeypatch.setattr("moneypoly.ui.print_board_ownership", lambda board: calls.append(("board", len(board.properties))))
    monkeypatch.setattr(game, "_menu_mortgage", lambda current_player: calls.append(("mortgage", current_player.name)))
    monkeypatch.setattr(game, "_menu_unmortgage", lambda current_player: calls.append(("unmortgage", current_player.name)))
    monkeypatch.setattr(game, "_menu_trade", lambda current_player: calls.append(("trade", current_player.name)))
    monkeypatch.setattr(game.bank, "give_loan", lambda current_player, amount: calls.append(("loan", current_player.name, amount)))

    game.interactive_menu(player)

    assert calls == [
        ("standings", 2),
        ("board", len(game.board.properties)),
        ("mortgage", "Alice"),
        ("unmortgage", "Alice"),
        ("trade", "Alice"),
        ("loan", "Alice", 150),
    ]


def test_interactive_menu_skips_non_positive_loan_requests(monkeypatch):
    """Choosing a loan with zero amount should not call the bank helper."""
    game = Game(["Alice", "Bob"])
    player = game.players[0]
    choices = iter([6, 0, 0])
    called = []
    monkeypatch.setattr(
        "moneypoly.ui.safe_int_input",
        lambda _prompt, default=0: next(choices),
    )
    monkeypatch.setattr(game.bank, "give_loan", lambda _player, _amount: called.append(True))

    game.interactive_menu(player)

    assert called == []


def test_interactive_menu_ignores_invalid_choices_and_loops(monkeypatch):
    """Unknown menu choices should be ignored and the menu should keep running."""
    game = Game(["Alice", "Bob"])
    player = game.players[0]
    choices = iter([9, 0])
    monkeypatch.setattr(
        "moneypoly.ui.safe_int_input",
        lambda _prompt, default=0: next(choices),
    )

    game.interactive_menu(player)


def test_menu_mortgage_covers_empty_and_valid_selection(monkeypatch):
    """Mortgage menu should handle both no-property and valid-selection cases."""
    game = Game(["Alice", "Bob"])
    player = game.players[0]
    game._menu_mortgage(player)

    prop = game.board.get_property_at(1)
    prop.owner = player
    player.add_property(prop)
    seen = []
    monkeypatch.setattr("moneypoly.ui.safe_int_input", lambda _prompt, default=0: 1)
    monkeypatch.setattr(game, "mortgage_property", lambda current_player, current_prop: seen.append((current_player, current_prop)))

    game._menu_mortgage(player)

    assert seen == [(player, prop)]


def test_menu_mortgage_ignores_invalid_selection(monkeypatch):
    """An out-of-range mortgage choice should safely do nothing."""
    game = Game(["Alice", "Bob"])
    player = game.players[0]
    prop = game.board.get_property_at(1)
    prop.owner = player
    player.add_property(prop)
    monkeypatch.setattr("moneypoly.ui.safe_int_input", lambda _prompt, default=0: 5)

    game._menu_mortgage(player)

    assert prop.is_mortgaged is False


def test_menu_unmortgage_covers_empty_and_valid_selection(monkeypatch):
    """Unmortgage menu should handle both empty and valid branches."""
    game = Game(["Alice", "Bob"])
    player = game.players[0]
    game._menu_unmortgage(player)

    prop = game.board.get_property_at(1)
    prop.owner = player
    prop.is_mortgaged = True
    player.add_property(prop)
    seen = []
    monkeypatch.setattr("moneypoly.ui.safe_int_input", lambda _prompt, default=0: 1)
    monkeypatch.setattr(game, "unmortgage_property", lambda current_player, current_prop: seen.append((current_player, current_prop)))

    game._menu_unmortgage(player)

    assert seen == [(player, prop)]


def test_menu_unmortgage_ignores_invalid_selection(monkeypatch):
    """An out-of-range unmortgage choice should safely do nothing."""
    game = Game(["Alice", "Bob"])
    player = game.players[0]
    prop = game.board.get_property_at(1)
    prop.owner = player
    prop.is_mortgaged = True
    player.add_property(prop)
    monkeypatch.setattr("moneypoly.ui.safe_int_input", lambda _prompt, default=0: 5)

    game._menu_unmortgage(player)

    assert prop.is_mortgaged is True


def test_menu_trade_covers_missing_players_invalid_choices_and_success(monkeypatch):
    """Trade menu branches should handle the common early exits and valid flow."""
    solo_game = Game(["Alice", "Bob"])
    solo_player = solo_game.players[0]
    solo_game.players = [solo_player]
    solo_game._menu_trade(solo_player)

    game = Game(["Alice", "Bob"])
    player, partner = game.players
    monkeypatch.setattr("moneypoly.ui.safe_int_input", lambda _prompt, default=0: 3)
    game._menu_trade(player)

    monkeypatch.setattr(
        "moneypoly.ui.safe_int_input",
        lambda _prompt, default=0: 1,
    )
    game._menu_trade(player)

    prop = game.board.get_property_at(1)
    prop.owner = player
    player.add_property(prop)
    invalid_property_prompts = iter([1, 9])
    monkeypatch.setattr(
        "moneypoly.ui.safe_int_input",
        lambda _prompt, default=0: next(invalid_property_prompts),
    )
    game._menu_trade(player)

    prompts = iter([1, 1, 75])
    seen = []
    monkeypatch.setattr("moneypoly.ui.safe_int_input", lambda _prompt, default=0: next(prompts))
    monkeypatch.setattr(game, "trade", lambda seller, buyer, chosen_prop, cash: seen.append((seller, buyer, chosen_prop, cash)))

    game._menu_trade(player)

    assert seen == [(player, partner, prop, 75)]
