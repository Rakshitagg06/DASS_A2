"""White-box tests for dice bounds and card deck helpers."""

from moneypoly.cards import CardDeck
from moneypoly.dice import Dice


def test_dice_rolls_use_the_full_six_sided_range(monkeypatch):
    """Each die roll should request a value between 1 and 6 inclusive."""
    calls = []

    def fake_randint(low, high):
        calls.append((low, high))
        return 6 if len(calls) == 1 else 4

    monkeypatch.setattr("random.randint", fake_randint)
    dice = Dice()

    total = dice.roll()

    assert calls == [(1, 6), (1, 6)]
    assert total == 10
    assert dice.die1 == 6
    assert dice.die2 == 4


def test_empty_card_deck_helpers_are_safe():
    """Empty decks should not crash when introspected."""
    deck = CardDeck([])

    assert deck.draw() is None
    assert deck.peek() is None
    assert deck.cards_remaining() == 0
    assert repr(deck) == "CardDeck(0 cards, next=empty)"


def test_cards_remaining_wraps_after_the_deck_cycles():
    """After cycling past the end, the helper should still report a valid count."""
    deck = CardDeck([{"description": "A"}, {"description": "B"}])

    deck.draw()
    deck.draw()
    deck.draw()

    assert deck.cards_remaining() == 1
