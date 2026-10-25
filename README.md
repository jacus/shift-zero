# Shift Zero

![Shift left, all the way to zero: from "test last" through CI, dev and TDD to testability designed in before the first line, built as thin vertical end-to-end slices.](assets/shift-zero-hero.gif)

**Quality from start.** Shift-left pushed to its limit: CI runs *inside the
agent's session*, before its first answer — not in a pipeline an hour later.

Shift Zero is a portable doctrine plus a tiny gate that you install into
any coding agent harness. It makes the agent:

- **prove every behavior change end to end** before replying, through the
  system's real interface (CLI, HTTP, browser, messages);
- **prove its tests can fail** — a test that passes on the old code tests
  nothing;
- **build in thin, vertical, testable slices**, starting from a walking
  skeleton;
- **name crappy tests** — mocking the unit under test, empty asserts,
  sleeps, skipped tests — every single time;
- **loudly call out the human** when the environment makes quality
  impossible, every turn, until it's fixed.

> "If you don't give me tools to validate your stuff, how the hell do I
> provide quality? Step up, my dear human, and let me offload you."

It costs tokens and time on purpose. If you don't want that, Shift Zero
will tell you — and suggest you uninstall it.

## How it works

1. **Port once.** The model reads [`DOCTRINE.md`](DOCTRINE.md) and the
   [`examples/`](examples/), then writes `.shift-zero/PORT.md` for *your*
   stack — every command in it proven by actually running it.
2. **Verify every turn.** Before replying, the agent runs scoped e2e
   checks and writes `.shift-zero/evidence.json` ([schema](protocol/evidence.schema.json)).
3. **Gate.** [`gate/szero.py`](gate/szero.py) doesn't trust prose. It
   *replays* the evidence against the current working tree and blocks the
   reply if evidence is missing, stale, failing, or claims VERIFIED without
   an e2e check.
4. **Escalate.** The gate tracks alignment: L1 nag → L2 loud → L3
   *"this human does not want Shift Zero quality — align or uninstall."*

The model knows your stack. Shift Zero only supplies the definition of
quality and refuses to let it slide.

## Install

**Claude Code** (hard enforcement via hooks):

```
/plugin marketplace add jacus/shift-zero
/plugin install shift-zero@shift-zero
```

**Any other harness** (soft enforcement): merge
[`adapters/agents-md/AGENTS.md`](adapters/agents-md/AGENTS.md) into your
project's rules file. See [`adapters/`](adapters/README.md).

The gate is a single stdlib Python 3 file — no dependencies, any project
language.

## Repo map

```
DOCTRINE.md                 the product: rules, voice, escalation
skills/shift-zero/SKILL.md  operational summary for agents
protocol/                   port.md, loop.md, evidence.schema.json
gate/szero.py               replay gate + escalation ladder
hooks/hooks.json            Claude Code hooks
.claude-plugin/             Claude Code plugin + marketplace manifest
adapters/                   per-harness install notes, AGENTS.md fallback
examples/                   crappy test → critique → e2e test → evidence
tests/                      e2e tests for the gate (Shift Zero dogfoods itself)
```

## Status

v0.1 — doctrine draft, working gate, Claude Code plugin. See
[ROADMAP.md](ROADMAP.md).

## License

MIT
