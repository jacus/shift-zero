# Porting protocol

Run on first setup and revisit whenever the project stack or verification
setup changes. The goal is to turn the stack-agnostic doctrine into
concrete, **proven** commands for this repo. The output is
`.shift-zero/PORT.md`, committed with the project and maintained as the
project evolves.

## When to refresh PORT.md

Review the port on every behavior-changing turn. Update it whenever a
change affects any of the following:
- languages, frameworks, package managers, or runtime/dependency versions;
- how the app is started, seeded, or torn down;
- test commands, test locations, test drivers, or scoped-test recipes;
- interfaces available for end-to-end checks (CLI, HTTP, browser, queue,
  library API, and so on);
- environment requirements, fixtures, services, or other prerequisites for
  reproducing verification.

Do not rewrite it for ordinary feature work when these details are
unchanged. If a relevant change is made, prove each changed command by
running it and update the documented blockers/testability debt as needed.
If a command cannot be proven because the environment is missing something,
mark it unproven and record the blocker; never present it as working.

## Initial porting steps

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
