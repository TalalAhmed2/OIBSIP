"""Cryptographically secure password generation and strength scoring."""

from __future__ import annotations

import secrets
import string
from dataclasses import dataclass

MIN_LENGTH = 8
MAX_LENGTH = 64
MIN_CHAR_TYPES = 2

SYMBOLS = "!@#$%^&*()_+-=[]{}|;:,.<>?"
AMBIGUOUS_CHARS = frozenset("0Ool1I")


@dataclass(frozen=True)
class PasswordOptions:
    length: int
    uppercase: bool = True
    lowercase: bool = True
    numbers: bool = True
    symbols: bool = True
    exclude_ambiguous: bool = False


def _pool(chars: str, exclude_ambiguous: bool) -> str:
    if not exclude_ambiguous:
        return chars
    return "".join(ch for ch in chars if ch not in AMBIGUOUS_CHARS)


def selected_pools(options: PasswordOptions) -> list[str]:
    pools: list[str] = []
    if options.uppercase:
        pools.append(_pool(string.ascii_uppercase, options.exclude_ambiguous))
    if options.lowercase:
        pools.append(_pool(string.ascii_lowercase, options.exclude_ambiguous))
    if options.numbers:
        pools.append(_pool(string.digits, options.exclude_ambiguous))
    if options.symbols:
        pools.append(_pool(SYMBOLS, options.exclude_ambiguous))
    return [pool for pool in pools if pool]


def validate_options(options: PasswordOptions) -> None:
    if options.length < MIN_LENGTH:
        raise ValueError(f"Password length must be at least {MIN_LENGTH} characters.")
    if options.length > MAX_LENGTH:
        raise ValueError(f"Password length cannot exceed {MAX_LENGTH} characters.")

    type_count = sum(
        [options.uppercase, options.lowercase, options.numbers, options.symbols]
    )
    if type_count < MIN_CHAR_TYPES:
        raise ValueError("Select at least two character types.")

    pools = selected_pools(options)
    if len(pools) < MIN_CHAR_TYPES:
        raise ValueError(
            "At least two character types must remain after excluding ambiguous characters."
        )
    if options.length < len(pools):
        raise ValueError(
            "Length must be at least the number of selected character types "
            "so each type can appear at least once."
        )


def generate_password(options: PasswordOptions) -> str:
    validate_options(options)
    pools = selected_pools(options)
    alphabet = "".join(pools)

    chars = [secrets.choice(pool) for pool in pools]
    remaining = options.length - len(chars)
    chars.extend(secrets.choice(alphabet) for _ in range(remaining))

    for i in range(len(chars) - 1, 0, -1):
        j = secrets.randbelow(i + 1)
        chars[i], chars[j] = chars[j], chars[i]

    return "".join(chars)


def password_strength(options: PasswordOptions) -> tuple[str, int]:
    """Return (label, percent 0-100) from length and character-type diversity."""
    validate_options(options)
    type_count = len(selected_pools(options))
    length = options.length

    score = 0
    if length >= 8:
        score += 20
    if length >= 12:
        score += 20
    if length >= 16:
        score += 15
    if length >= 20:
        score += 10

    score += {2: 15, 3: 25, 4: 35}.get(type_count, 0)

    percent = min(100, score)
    if percent < 45:
        label = "Weak"
    elif percent < 75:
        label = "Medium"
    else:
        label = "Strong"
    return label, percent
