# Password Generator

A secure password generator built around a single shared engine (`core.py`), with two interfaces on top of it — a Tkinter GUI and a terminal CLI. Both interfaces call the exact same functions, so the generation rules and validation never diverge between them.

## Features

- **Cryptographically secure generation** using Python's `secrets` module (not `random`)
- **Configurable length** from 8–64 characters
- **Selectable character types** — uppercase, lowercase, numbers, symbols
- **Ambiguous character exclusion** — optionally strips look-alike characters (`0 O o l 1 I`)
- **Guaranteed character coverage** — every selected type is guaranteed to appear at least once
- **Strength scoring** — a simple estimate (Weak / Medium / Strong) based on length and variety
- **Session history** — the last 5 generated passwords (GUI only), kept in memory only — nothing is written to disk
- **Clipboard copy** — automatic copy on generation, with a `pyperclip` fallback to Tkinter's own clipboard
- **Two interfaces, one engine** — GUI (`app.py`) and CLI (`cli.py`) both call `generate_password()` in `core.py`
- **Unit tested** core logic (`test_core.py`)

## Project structure

```
.
├── main.py         # Entry point — routes to GUI or CLI
├── core.py         # Shared password engine (generation, validation, strength scoring)
├── app.py          # Tkinter GUI
├── cli.py          # Terminal CLI
├── test_core.py    # Unit tests for core.py
├── requirements.txt
└── README.md
```

## How it works

### Entry point (`main.py`)

Running `python main.py`:
- checks for a `--cli` flag using `argparse`
- if present → runs `cli.run_cli()`
- otherwise → runs `app.run_gui()`, which opens the Tkinter window and enters the GUI event loop

Both paths eventually call `generate_password()` in `core.py`.

### The engine (`core.py`)

**Settings object** — `PasswordOptions` (a `dataclasses.dataclass`) stores:
- `length` (8–64)
- `uppercase`, `lowercase`, `numbers`, `symbols` (booleans)
- `exclude_ambiguous` (drops `0 O o l 1 I`)

**Character pools** — each selected type becomes a pool of allowed characters:

| Type       | Pool |
|------------|------|
| Uppercase  | `ABCDEFGHIJKLMNOPQRSTUVWXYZ` |
| Lowercase  | `abcdefghijklmnopqrstuvwxyz` |
| Numbers    | `0123456789` |
| Symbols    | `!@#$%^&*()_+-=[]{}|;:,.<>?` |

If "exclude ambiguous" is on, look-alike characters are stripped from every pool.

**Validation** — `validate_options()` rejects:
- length under 8 or over 64
- fewer than two character types selected
- fewer than two non-empty pools after stripping ambiguous characters
- length smaller than the number of selected types (there wouldn't be room for one guaranteed character per type)

**Generation** — for example, length 12 with all four types on:
1. Pick one guaranteed character from each pool with `secrets.choice` (e.g. `A`, `k`, `7`, `#`)
2. Fill the remaining characters (8 more) from the combined alphabet
3. Shuffle using a Fisher–Yates shuffle powered by `secrets.randbelow`, so guaranteed characters aren't always at the start
4. Join into the final password string

This guarantees every selected type appears at least once.

**Strength score** — a simple estimate, not a real entropy audit:
- Length: `+20` at 8, `+20` at 12, `+15` at 16, `+10` at 20
- Variety: `+15` / `+25` / `+35` for 2 / 3 / 4 selected types
- Result: `< 45` → Weak (red), `45–74` → Medium (yellow), `75+` → Strong (green)

### GUI (`app.py`)

Built as a `tk.Tk` subclass, using `IntVar` / `BooleanVar` / `StringVar` to keep widgets in sync with Python values.

- **Length** — a `ttk.Scale` slider and a spinbox share the same variable; moving either updates the strength preview immediately
- **Checkboxes** — uppercase / lowercase / numbers / symbols / exclude ambiguous, also refresh the strength preview live
- **Generate** — reads the widgets into a `PasswordOptions`, calls `generate_password()`, shows an error dialog if invalid, or displays the password, updates the strength bar, pushes it onto history, and copies it to the clipboard
- **Copy to clipboard** — re-copies the current password
- **History** — a `collections.deque(maxlen=5)`, newest at the top, in RAM only; double-click a row to copy that password; clears when the app closes
- **Clipboard helper** — tries `pyperclip.copy()` first, falls back to Tkinter's `clipboard_append()`
- **Look** — a dark theme (`#0f172a` base with cyan accents) via `ttk.Style`; the strength bar is a `Canvas` rectangle sized to `percent / 100` of the bar width

### CLI (`cli.py`)

Follows the same rules with keyboard prompts:
1. Ask for length until a valid integer ≥ 8 is entered
2. Ask y/n for each character type and for ambiguous-character exclusion
3. Try generating; on validation failure, print the error and ask again
4. Print the password and its strength
5. Offer to generate another with the same settings, change settings, or quit

### Tests (`test_core.py`)

Checks that the engine:
- rejects a length of 7
- rejects a single character type
- always includes every selected type
- never emits `0 O o l 1 I` when exclusion is on
- scores a short 2-type password weaker than a long 4-type one
- never uses types that weren't selected

Run with:

```bash
python -m unittest test_core.py
```

## Data flow

```
Widgets (length, checkboxes)
        ↓
PasswordOptions
        ↓
validate_options  →  error dialog if invalid
        ↓
pools (per type)  →  secrets.choice each  →  fill rest  →  shuffle
        ↓
password string
        ↓
display + strength bar + history deque + clipboard
```

## Installation

```bash
git clone https://github.com/<your-username>/<your-repo>.git
cd <your-repo>
pip install -r requirements.txt
```

## Usage

**GUI:**

```bash
python main.py
```

**CLI:**

```bash
python main.py --cli
```

## Libraries used

**Python standard library** (no install required)
- `secrets` — cryptographically strong randomness (`secrets.choice`, `secrets.randbelow`); stronger than `random`, which isn't meant for passwords
- `string` — ready-made alphabets (`ascii_uppercase`, `ascii_lowercase`, `digits`)
- `dataclasses` — `PasswordOptions` holds length and checkbox state in one object
- `argparse` — reads `--cli` from the command line
- `tkinter` / `ttk` — window, slider, spinbox, checkboxes, buttons, listbox
- `collections.deque` — bounded, in-memory history of the last 5 passwords
- `unittest` — tests in `test_core.py`

**Third-party**
- `pyperclip` — copies text to the system clipboard, with a Tkinter fallback if it fails

## License

This project is licensed under the MIT License — see [LICENSE](LICENSE) for details.
