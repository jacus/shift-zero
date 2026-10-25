# Porting protocol

Run once per project (and again when the stack changes). The goal: turn
the stack-agnostic doctrine into concrete, **proven** commands for this
repo. The output is `.shift-zero/PORT.md`, committed with the project.

## Steps

1. **Detect.** Identify languages, frameworks, package managers, how the
   app is started, which interfaces it exposes (CLI, HTTP, UI, queue,
   library API) and any existing tests.
2. **Choose the e2e surface.** For each interface, pick the driver:
   - CLI → run the binary/script, assert stdout/stderr/exit code;
   - HTTP → boot the server, send real requests (curl or the stack's
     HTTP client), assert responses;
   - Browser UI → Playwright (works for any web stack);
   - Library → a consumer-style test through the public API only.
3. **Write the commands.** `boot`, `seed`, `e2e`, `teardown`, and a
   `scoped` recipe explaining how to run a subset (by file, tag, route).
4. **Prove them.** Actually run every command. A command that has not
   run successfully must not be written into PORT.md as working.
5. **Record blockers.** Anything that could not be proven goes into a
   *Blockers* section using the doctrine format: missing → why it blocks
   quality → smallest ask.
6. **Install the gate** for the current harness (see `adapters/`).

## PORT.md template

```markdown
# Shift Zero port — <project name>

Ported: <date> by <harness/model>

## Stack
<languages, frameworks, interfaces>

## Commands (all proven)
- boot:     `<cmd>`
- seed:     `<cmd>`
- e2e:      `<cmd>`
- scoped:   `<how to run a subset>`
- teardown: `<cmd>`

## E2E surfaces
- <interface>: <driver and where tests live>

## Blockers
- <missing> → <why it blocks quality> → <smallest ask>

## Testability debt
- <places where the design fights testing (doctrine R7)>
```
