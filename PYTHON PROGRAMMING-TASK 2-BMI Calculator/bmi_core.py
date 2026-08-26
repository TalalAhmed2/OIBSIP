"""BMI calculation, classification, and input validation."""

from __future__ import annotations

from dataclasses import dataclass


CATEGORIES = (
    ("Underweight", 0.0, 18.5),
    ("Normal", 18.5, 25.0),
    ("Overweight", 25.0, 30.0),
    ("Obese", 30.0, float("inf")),
)

CATEGORY_COLORS = {
    "Underweight": "#1565C0",
    "Normal": "#2E7D32",
    "Overweight": "#EF6C00",
    "Obese": "#C62828",
}


class BMIValidationError(ValueError):
    """Raised when weight or height cannot be used for a BMI calculation."""


@dataclass(frozen=True)
class BMIResult:
    weight: float
    height: float
    bmi: float
    category: str

    @property
    def color(self) -> str:
        return CATEGORY_COLORS[self.category]


def parse_positive_number(raw: str, field_name: str) -> float:
    """Parse a numeric value and reject blanks, non-numeric, and non-positive input."""
    text = (raw or "").strip()
    if not text:
        raise BMIValidationError(f"{field_name} is required.")
    try:
        value = float(text)
    except ValueError as exc:
        raise BMIValidationError(
            f"{field_name} must be a number. '{raw}' is not valid."
        ) from exc
    if value != value:  # NaN
        raise BMIValidationError(f"{field_name} must be a valid number.")
    if value <= 0:
        raise BMIValidationError(
            f"{field_name} must be greater than zero. Negative or zero values are not allowed."
        )
    return value


def classify_bmi(bmi: float) -> str:
    if bmi < 18.5:
        return "Underweight"
    if bmi < 25.0:
        return "Normal"
    if bmi < 30.0:
        return "Overweight"
    return "Obese"


def calculate_bmi(weight_kg: float, height_m: float) -> BMIResult:
    if height_m <= 0 or weight_kg <= 0:
        raise BMIValidationError("Weight and height must be greater than zero.")
    bmi = weight_kg / (height_m ** 2)
    return BMIResult(
        weight=weight_kg,
        height=height_m,
        bmi=round(bmi, 2),
        category=classify_bmi(bmi),
    )


def calculate_from_text(weight_raw: str, height_raw: str) -> BMIResult:
    weight = parse_positive_number(weight_raw, "Weight")
    height = parse_positive_number(height_raw, "Height")
    return calculate_bmi(weight, height)
