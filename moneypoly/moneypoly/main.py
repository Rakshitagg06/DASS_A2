"""Command-line entry point for the MoneyPoly game."""

from moneypoly.game import Game


def get_player_names():
    """Prompt for player names and return the cleaned list."""
    print("Enter player names separated by commas (minimum 2 players):")
    raw = input("> ").strip()
    names = [n.strip() for n in raw.split(",") if n.strip()]
    return names


def main():
    """Start an interactive MoneyPoly session."""
    try:
        names = get_player_names()
        game = Game(names)
        game.run()
    except (KeyboardInterrupt, EOFError):
        print("\n\n  Game interrupted. Goodbye!")
    except ValueError as exc:
        print(f"Setup error: {exc}")


if __name__ == "__main__":
    main()
