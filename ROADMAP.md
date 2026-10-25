# Roadmap

## v0.1 — skeleton (this commit)
- [x] Doctrine draft: 10 rules, demands on the human, voice, escalation
- [x] Evidence schema and per-turn loop
- [x] Gate: diff hash, evidence replay, e2e requirement, revert-check
      warnings, escalation ladder, loop guard, Claude Code hook protocol
- [x] Gate e2e tests, mutation-checked
- [x] Claude Code plugin (skill + hooks) and AGENTS.md fallback
- [x] Three worked examples (TS/HTTP, Python/HTTP, Go/CLI)

## v0.2 — prove it on real projects
- [ ] Port Shift Zero onto 3 real repos in different stacks; fix the doctrine where it breaks
- [ ] `claude plugin validate` in CI; real Claude Code session test of the hooks
- [ ] PreToolUse hook: block edits that weaken existing tests without consent (R9)
- [ ] Gate verifies revert checks itself (stash, replay, expect failure) instead of trusting the flag

## v0.3 — more harnesses, more stacks
- [ ] OpenCode adapter (plugin events)
- [ ] Codex CLI adapter
- [ ] Examples: Rust lib, Java/Spring, PHP/Laravel, React + Playwright, queue consumer, mobile

## v0.4 — measure
- [ ] Eval set of ~50 tasks with hidden tests, mixed stacks
- [ ] Report: first-reply hidden-test pass rate vs tokens/time, with and without Shift Zero
