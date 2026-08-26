"""Command-line BMI calculator (beginner tier)."""

from __future__ import annotations

from bmi_core import BMIValidationError, calculate_from_text


def run_cli() -> None:
    print("BMI Calculator")
    print("Enter weight in kilograms and height in metres.")
    print()

    weight_raw = input("Weight (kg): ")
    height_raw = input("Height (m): ")

    try:
        result = calculate_from_text(weight_raw, height_raw)
    except BMIValidationError as exc:
        print(f"Error: {exc}")
        return

    print()
    print(f"BMI: {result.bmi:.2f}")
    print(f"Category: {result.category}")
