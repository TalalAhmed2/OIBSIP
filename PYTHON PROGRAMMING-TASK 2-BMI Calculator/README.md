# BMI Calculator

A simple, well-tested BMI (Body Mass Index) calculator with both a command-line interface and a graphical (Tkinter) interface. Results can be saved per user to a local SQLite database, with a trend chart showing BMI history over time.

## Features

- Calculate BMI from weight (kg) and height (m)
- Input validation with friendly error messages
- Categorizes results as **Underweight**, **Normal**, **Overweight**, or **Obese**
- Command-line interface for quick calculations
- Desktop GUI (Tkinter) with:
  - Color-coded results
  - Per-user history saved to SQLite
  - History table of past measurements
  - Line chart of BMI trend over time (with reference lines at 18.5 / 25 / 30)
- Unit tests covering the core math and storage logic

## Project Structure

The project is split so each file has a single responsibility:

```
.
├── main.py          # Entry point — routes to CLI or GUI
├── bmi_core.py       # BMI math and validation (no UI, no database)
├── storage.py        # SQLite persistence layer
├── cli.py             # Command-line interface
├── gui.py             # Tkinter desktop interface
└── test_bmi.py        # Unit tests
```

### How the files fit together

- You run `main.py`
  - `--cli` flag → `cli.py` (asks questions in the terminal)
  - no flag → `gui.py` (opens a window)
- Both `cli.py` and `gui.py` use `bmi_core.py` for the BMI math
- Only `gui.py` uses `storage.py` to save results into `bmi_history.db`

## Installation

```bash
git clone <your-repo-url>
cd bmi-calculator
pip install -r requirements.txt
```

The GUI requires `matplotlib` for the trend chart, and `tkinter`, which usually ships with Python but may need to be installed separately on Linux (`sudo apt-get install python3-tk`).

## Usage

**Command line:**

```bash
python main.py --cli
```

You'll be prompted for weight (kg) and height (m), and the program prints your BMI and category, or a friendly error message if the input is invalid.

**GUI:**

```bash
python main.py
```

Opens a window where you can:
1. Enter a name, weight, and height
2. Click **Calculate** to see your BMI and category (color-coded)
3. Click **Save** to store the result for that user
4. Choose a user from the "Show history for" dropdown to view their past measurements in a table and as a trend chart

## Running Tests

```bash
python -m unittest test_bmi.py
```

## Module Reference

### `bmi_core.py` — the brain (math only)

No window, no database — just validation and calculation.

| Name | Purpose |
|---|---|
| `CATEGORIES` | List of category names and ranges (used as documentation; actual sorting is done in `classify_bmi`) |
| `CATEGORY_COLORS` | Color codes for the GUI: blue, green, orange, red |
| `BMIValidationError` | Custom error raised when input is invalid (e.g. weight is `"abc"` or `-5`), so the CLI/GUI can show a friendly message instead of crashing |
| `BMIResult` | A frozen (immutable) result object holding weight, height, bmi, and category |
| `BMIResult.color` | Looks up the category in `CATEGORY_COLORS` so the GUI can paint the result |
| `parse_positive_number(raw, field_name)` | Turns typed text into a number. Blank → "Weight is required"; `"abc"` → "must be a number"; `0` or `-70` → "must be greater than zero"; otherwise returns e.g. `70.0` |
| `classify_bmi(bmi)` | Returns the category label: below 18.5 → Underweight, below 25 → Normal, below 30 → Overweight, otherwise → Obese |
| `calculate_bmi(weight_kg, height_m)` | Computes `BMI = weight / (height × height)`, rounds to 2 decimals, attaches the category, and returns a `BMIResult` |
| `calculate_from_text(weight_raw, height_raw)` | What the CLI and GUI call — parses both input strings, then calculates |

### `storage.py` — the filing cabinet

Handles all persistence to SQLite.

| Name | Purpose |
|---|---|
| `StorageError` | Friendly error if the database file cannot be opened, written, or read |
| `BMIRecord` | One saved row: who, weight, height, BMI, category, date |
| `BMIStorage` | The class that talks to SQLite |
| `BMIStorage.__init__` | If no path is given, defaults to `bmi_history.db` next to the file. Creates tables if they don't already exist |
| `BMIStorage._connect` | Opens the database connection, yields it for use, then commits on success or rolls back on error, and always closes it (`_` prefix means it's an internal helper) |
| `BMIStorage._init_schema` | Runs the SQL to create the `users` and `records` tables. Uses `IF NOT EXISTS`, so it never wipes existing data |
| `BMIStorage.list_users` | Returns all saved names, A–Z |
| `BMIStorage.get_or_create_user` | Reuses an existing user by name (case-insensitive, e.g. "Alex" and "alex" are the same person); creates a new one otherwise. Rejects empty names |
| `BMIStorage.save_record` | Finds or creates the user, then inserts one measurement with the current date/time |
| `BMIStorage.records_for_user` | All measurements for one person, oldest first (used for the trend chart) |
| `BMIStorage.all_records` | Everyone's measurements, newest first (used for the history table) |
| `BMIStorage._row_to_record` | Converts a raw database row into a `BMIRecord` object |
| `BMIStorage.users_with_history` | Alias for `list_users` |

### `cli.py` — beginner terminal app

| Name | Purpose |
|---|---|
| `run_cli` | Prints instructions, reads weight and height via `input()`, calls `calculate_from_text`, then prints the BMI and category — or an `Error: ...` message |

### `gui.py` — the window

| Name | Purpose |
|---|---|
| `BMICalculatorApp` | The whole window; a `tkinter.Tk` app |
| `__init__` | Sets the title and size, opens the database, remembers the last BMI, builds the layout, and populates the user list and table |
| `_build_style` | Sets fonts, colors, and button padding for a cleaner look |
| `_build_layout` | Places every widget: name box, weight, height, Calculate, Save, result text, category legend, history table, chart area |
| `_require_storage` | If the database failed to open, shows an error and blocks save/graph actions |
| `calculate` | Reads the input boxes, computes BMI, and shows it in color. Stores the result in `_last_result` so `save_record` can use it |
| `save_record` | Requires a user name and a valid BMI; writes to SQLite, refreshes the lists, and shows "Saved" |
| `show_trend` | Loads the selected user's history and draws a line chart (date on X, BMI on Y) with dashed reference lines at 18.5, 25, and 30 |
| `_safe_users` | Loads users; shows an error and returns an empty list if the database fails |
| `_refresh_users` | Fills the name dropdown and the "Show history for" dropdown |
| `_refresh_history` | Clears and refills the history table, for all users or one selected user |
| `_parse_date` | Converts the stored date string into a real `date` object for the chart |
| `_display_date` | Formats a date nicely for the table, e.g. `2026-08-25 00:30` |
| `run_gui` | Creates the window and starts `mainloop()`, which waits for clicks until the window is closed |

### `main.py` — the front door

| Name | Purpose |
|---|---|
| `main` | If `--cli` was passed, starts the terminal version; otherwise starts the GUI |
| `if __name__ == "__main__"` | Ensures this only runs when the file is executed directly (`python main.py`), not when imported |

### `test_bmi.py` — automatic checks

**`BMICoreTests`**
- `test_normal_bmi` — 70 kg / 1.75 m should equal 22.86, Normal
- `test_categories` — boundary values land in the correct category
- `test_rejects_non_numeric` — `"abc"` must fail
- `test_rejects_negative_and_zero` — `-70` and a height of `0` must fail

**`StorageTests`**
- `test_save_and_load_multi_user` — "Alex" (saved twice) and "Sam" are stored correctly; "Alex" and "alex" resolve to the same person
- `test_empty_name_rejected` — a blank name must fail

## How a click flows through the code

- **Calculate:** GUI input → `calculate_from_text` → `parse_positive_number` → `calculate_bmi` → `classify_bmi` → colored label
- **Save:** last result + name → `save_record` → `get_or_create_user` → `INSERT` into SQLite → table refreshes
- **Show trend:** selected user → `records_for_user` → matplotlib line drawn on the canvas

## License

Add a license of your choice (e.g. MIT) before publishing.
