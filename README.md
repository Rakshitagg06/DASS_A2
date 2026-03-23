# DASS_A2

This repository contains all three assignment parts:

- **Part 1 (White-box):** MoneyPoly + white-box tests
- **Part 2 (Integration):** StreetRace Manager modules + integration tests
- **Part 3 (Black-box):** QuickCart API black-box suite

Repository: https://github.com/Rakshitagg06/DASS_A2.git
Drive Folder: https://drive.google.com/drive/u/0/folders/1r6a0YkK4I33zfrAlOja2Ykzmk5FhLwlx

---

## 1) Setup

From repository root:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -U pip pytest requests pylint reportlab
```

---

## 2) Directory Structure (By Part)

### Part 1 — White-box (MoneyPoly)

```text
moneypoly/
  main.py
  moneypoly/
    bank.py
    board.py
    cards.py
    config.py
    dice.py
    game.py
    player.py
    property.py
    ui.py

whitebox/
  diagrams/
    moneypoly_control_flow.mmd
  tests/
    test_*.py
```

### Part 2 — Integration (StreetRace Manager)

```text
integration/
  code/
    main.py
    streetrace_manager/
      cli.py
      crew_management.py
      inventory.py
      maintenance.py
      mission_planning.py
      models.py
      race_management.py
      registration.py
      results.py
      scheduling.py
  diagrams/
    streetrace_call_graph.mmd
  tests/
    test_*.py
```

### Part 3 — Black-box (QuickCart)

```text
blackbox/
  tests/
    test_*.py
  report.md
  bugs_found.txt
```

---

## 3) Run Commands (Each Part)

### Part 1 (MoneyPoly app)

```bash
cd moneypoly
python main.py
```

### Part 1 tests (white-box)

From repository root:

```bash
python -m pytest -q whitebox/tests
```

### Part 1 pylint

```bash
cd moneypoly
python -m pylint main.py moneypoly
```

### Part 2 (StreetRace Manager app)

```bash
cd integration/code
python main.py
```

### Part 2 tests (integration folder)

From repository root:

```bash
python -m pytest -q integration/tests
```

### Part 3 tests (QuickCart black-box)

From repository root:

```bash
python -m pytest -q blackbox/tests
```

Note: Part 3 fixture starts QuickCart from `quickcart_image_x86/` automatically.
Docker is not required for normal black-box test execution in this project setup.

---

## 4) Run All Tests

From repository root:

```bash
python -m pytest -q
```
