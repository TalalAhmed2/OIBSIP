"""Command-line password generator (Beginner tier + secure generation)."""

from __future__ import annotations

from core import MIN_LENGTH, PasswordOptions, generate_password, password_strength


def _yes_no(prompt: str) -> bool:
    while True:
        answer = input(prompt).strip().lower()
        if answer in {"y", "yes"}:
            return True
        if answer in {"n", "no"}:
            return False
        print("Please enter y or n.")


def _ask_length() -> int:
    while True:
        raw = input(f"Password length (minimum {MIN_LENGTH}): ").strip()
        try:
            length = int(raw)
        except ValueError:
            print("Please enter a whole number.")
            continue
        if length < MIN_LENGTH:
            print(f"Length must be at least {MIN_LENGTH}.")
            continue
        return length


def _ask_options() -> PasswordOptions:
    while True:
        length = _ask_length()
        print("Include character types (y/n). At least two are required.")
        uppercase = _yes_no("  Uppercase letters (A-Z)? ")
        lowercase = _yes_no("  Lowercase letters (a-z)? ")
        numbers = _yes_no("  Numbers (0-9)? ")
        symbols = _yes_no("  Symbols (!@#$...)? ")
        exclude_ambiguous = _yes_no("  Exclude ambiguous characters (0, O, o, l, 1, I)? ")

        options = PasswordOptions(
            length=length,
            uppercase=uppercase,
            lowercase=lowercase,
            numbers=numbers,
            symbols=symbols,
            exclude_ambiguous=exclude_ambiguous,
        )
        try:
            generate_password(options)
        except ValueError as exc:
            print(f"Invalid choices: {exc}")
            continue
        return options


def run_cli() -> None:
    print("Random Password Generator")
    print("-" * 28)
    options = _ask_options()

    while True:
        password = generate_password(options)
        label, percent = password_strength(options)
        print(f"\nGenerated password: {password}")
        print(f"Strength: {label} ({percent}%)")

        if not _yes_no("Generate another password with the same settings? "):
            if _yes_no("Change settings and generate again? "):
                options = _ask_options()
                continue
            print("Goodbye.")
            return


if __name__ == "__main__":
    run_cli()
