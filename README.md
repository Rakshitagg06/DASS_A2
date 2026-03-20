# DASS_A2

Part 1 of the assignment is implemented around the MoneyPoly codebase in
`moneypoly/moneypoly`, with white-box tests and diagram assets under `whitebox/`.

Part 2 is implemented under `integration/` as a command-line StreetRace Manager
system with the required six modules plus two additional relevant modules:
`Scheduling` and `Maintenance`.

## Repository Link

`https://github.com/Rakshitagg06/DASS_A2.git`

## How To Run MoneyPoly

```bash
cd moneypoly/moneypoly
python main.py
```

## How To Run StreetRace Manager

```bash
cd integration/code
python main.py
```

## How To Run The Tests

From the repository root:

```bash
python -m pytest
```

## Part 2 Layout

```text
integration/
  code/
  diagrams/
  tests/
```

The Part 2 Mermaid call graph source is stored in
`integration/diagrams/streetrace_call_graph.mmd`.

## How To Run pylint For Part 1

```bash
cd moneypoly/moneypoly
python -m pylint main.py moneypoly
```
