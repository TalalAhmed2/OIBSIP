"""Checks for generation rules used by both CLI and GUI."""

import string
import unittest

from core import PasswordOptions, generate_password, password_strength, validate_options


class PasswordGeneratorTests(unittest.TestCase):
    def test_rejects_short_length(self) -> None:
        with self.assertRaises(ValueError):
            validate_options(PasswordOptions(length=7, uppercase=True, lowercase=True))

    def test_rejects_fewer_than_two_types(self) -> None:
        with self.assertRaises(ValueError):
            validate_options(
                PasswordOptions(
                    length=12,
                    uppercase=True,
                    lowercase=False,
                    numbers=False,
                    symbols=False,
                )
            )

    def test_includes_each_selected_type(self) -> None:
        options = PasswordOptions(
            length=12,
            uppercase=True,
            lowercase=True,
            numbers=True,
            symbols=True,
        )
        password = generate_password(options)
        self.assertEqual(len(password), 12)
        self.assertTrue(any(c.isupper() for c in password))
        self.assertTrue(any(c.islower() for c in password))
        self.assertTrue(any(c.isdigit() for c in password))
        self.assertTrue(any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password))

    def test_excludes_ambiguous_characters(self) -> None:
        options = PasswordOptions(
            length=32,
            uppercase=True,
            lowercase=True,
            numbers=True,
            symbols=False,
            exclude_ambiguous=True,
        )
        for _ in range(20):
            password = generate_password(options)
            self.assertTrue(set(password).isdisjoint(set("0Ool1I")))

    def test_strength_increases_with_length_and_diversity(self) -> None:
        weak = password_strength(
            PasswordOptions(length=8, uppercase=True, lowercase=True, numbers=False, symbols=False)
        )
        strong = password_strength(
            PasswordOptions(length=20, uppercase=True, lowercase=True, numbers=True, symbols=True)
        )
        self.assertEqual(weak[0], "Weak")
        self.assertEqual(strong[0], "Strong")
        self.assertLess(weak[1], strong[1])

    def test_only_requested_alphabet(self) -> None:
        options = PasswordOptions(
            length=16,
            uppercase=True,
            lowercase=False,
            numbers=True,
            symbols=False,
        )
        password = generate_password(options)
        allowed = set(string.ascii_uppercase + string.digits)
        self.assertTrue(set(password).issubset(allowed))


if __name__ == "__main__":
    unittest.main()
