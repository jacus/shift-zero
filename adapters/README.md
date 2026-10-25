# Adapters

Shift Zero enforces in tiers. Be honest with users about which one they get.

| Harness | Doctrine | Gate | Enforcement |
|---|---|---|---|
| Claude Code | skill (plugin) | Stop hook | **Hard** — reply blocked until evidence replays |
| Any harness with an AGENTS.md / rules file | `agents-md/AGENTS.md` | agent runs `szero gate` itself | **Soft** — the model can skip it |
| OpenCode | planned | planned (plugin events) | — |
| Codex CLI | planned | planned | — |

## Claude Code

The repository root is the plugin (`.claude-plugin/plugin.json`,
`skills/`, `hooks/hooks.json`) and also a one-plugin marketplace:

```
/plugin marketplace add jacus/shift-zero
/plugin install shift-zero@shift-zero
```

Then in a project: ask the agent to port Shift Zero. It runs
`szero init`, writes `.shift-zero/PORT.md` with proven commands, and from
then on the Stop hook replays evidence before every reply.

Hooks installed:
- `SessionStart`, `UserPromptSubmit` → `szero status`: injects the current
  escalation level and open blockers (silent when aligned).
- `Stop` → `szero gate`: blocks the reply when evidence is missing, stale,
  fails on replay, or claims VERIFIED without e2e.

## Any other harness

Copy `agents-md/AGENTS.md` into the project (or merge it into the
existing rules file) and keep the kit checked out somewhere the agent can
reach. Enforcement is soft until a native adapter exists.
