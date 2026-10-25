# Shift Zero port — shift-zero (dogfood)

Ported: 2026-10-25 by Claude Opus 5.5

## Stack
Markdown doctrine + one stdlib Python 3 CLI (`gate/szero.py`).

## Commands (all proven)
- boot:     none — the product is a CLI, invoked per check
- seed:     none — each test creates its own temporary git repo
- e2e:      `python3 -m unittest discover -s tests -v`
- scoped:   `python3 -m unittest tests.test_gate_e2e.GateE2E.<test_name>`
- teardown: none — temp dirs are cleaned by the tests

## E2E surfaces
- cli: tests drive `gate/szero.py` as a subprocess against real git repos

## Blockers
- Claude Code itself → the plugin's hooks are not yet exercised in a live
  session → run a real session with the plugin installed and record it

## Testability debt
- none known
