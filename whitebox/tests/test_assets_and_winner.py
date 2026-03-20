"""White-box tests for asset valuation, group ownership, and winners."""

from moneypoly.game import Game
from moneypoly.player import Player
from moneypoly.property import Property, PropertyGroup


def test_full_group_ownership_requires_every_property():
    """Owning only part of a colour group must not trigger double rent."""
    group = PropertyGroup("Brown", "brown")
    first = Property("Mediterranean Avenue", 1, 60, 2, group)
    second = Property("Baltic Avenue", 3, 60, 4, group)
    owner = Player("Owner")

    first.owner = owner

    assert not group.all_owned_by(owner)
    assert first.get_rent() == 2

    second.owner = owner

    assert group.all_owned_by(owner)
    assert first.get_rent() == 4


def test_net_worth_counts_owned_property_value():
    """Standings should reflect property assets, not only liquid cash."""
    player = Player("Alice", balance=1200)
    property_group = PropertyGroup("Pink", "pink")
    prop = Property("States Avenue", 13, 140, 10, property_group)
    prop.owner = player
    player.add_property(prop)

    assert player.net_worth() == 1340


def test_mortgaged_property_counts_at_mortgage_value():
    """Mortgaged properties should contribute their recoverable value."""
    player = Player("Bob", balance=700)
    prop = Property("Park Place", 37, 350, 35)
    prop.owner = player
    prop.is_mortgaged = True
    player.add_property(prop)

    assert player.net_worth() == 875


def test_find_winner_uses_highest_net_worth():
    """The winner should be the richest surviving player."""
    game = Game(["Alice", "Bob"])
    alice, bob = game.players
    prop = Property("Boardwalk", 39, 400, 50)
    prop.owner = alice
    alice.add_property(prop)
    bob.balance = 1600

    assert game.find_winner() is alice
