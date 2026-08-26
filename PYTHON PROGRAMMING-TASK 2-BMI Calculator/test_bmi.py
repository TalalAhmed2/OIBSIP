"""Checks for BMI calculation, validation, and SQLite persistence."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from bmi_core import BMIValidationError, calculate_bmi, calculate_from_text, classify_bmi
from storage import BMIStorage, StorageError


class BMICoreTests(unittest.TestCase):
    def test_normal_bmi(self) -> None:
        result = calculate_bmi(70, 1.75)
        self.assertEqual(result.bmi, 22.86)
        self.assertEqual(result.category, "Normal")

    def test_categories(self) -> None:
        self.assertEqual(classify_bmi(18.49), "Underweight")
        self.assertEqual(classify_bmi(18.5), "Normal")
        self.assertEqual(classify_bmi(24.9), "Normal")
        self.assertEqual(classify_bmi(25.0), "Overweight")
        self.assertEqual(classify_bmi(29.9), "Overweight")
        self.assertEqual(classify_bmi(30.0), "Obese")

    def test_rejects_non_numeric(self) -> None:
        with self.assertRaises(BMIValidationError):
            calculate_from_text("abc", "1.75")

    def test_rejects_negative_and_zero(self) -> None:
        with self.assertRaises(BMIValidationError):
            calculate_from_text("-70", "1.75")
        with self.assertRaises(BMIValidationError):
            calculate_from_text("70", "0")


class StorageTests(unittest.TestCase):
    def test_save_and_load_multi_user(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "bmi.db"
            store = BMIStorage(db)
            store.save_record("Alex", 70, 1.75, 22.86, "Normal")
            store.save_record("alex", 72, 1.75, 23.51, "Normal")
            store.save_record("Sam", 90, 1.70, 31.14, "Obese")
            users = store.list_users()
            self.assertEqual(len(users), 2)
            alex_id = next(user_id for user_id, name in users if name.lower() == "alex")
            history = store.records_for_user(alex_id)
            self.assertEqual(len(history), 2)
            self.assertEqual(history[0].user_name, "Alex")

    def test_empty_name_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = BMIStorage(Path(tmp) / "bmi.db")
            with self.assertRaises(StorageError):
                store.get_or_create_user("   ")


if __name__ == "__main__":
    unittest.main()
