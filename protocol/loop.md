# The per-turn loop (CI in session)

Every turn that changes behavior runs this loop **before** the first reply.

1. **Plan the slice.** State the vertical increment (doctrine R5) and how
   it will be observed through the real interface.
2. **Review the port.** Compare `.shift-zero/PORT.md` with the current
   working tree. Update it if the stack, dependencies, startup/teardown,
   seed data, test commands, interfaces, drivers, or verification workflow
   changed. Prove every changed command by running it. If the setup is
   unchanged, do not churn the file.
3. **Write or update the e2e check first** when practical, so it can fail.
4. **Implement.**
5. **Run scoped checks** (doctrine R4) using the current commands in
   `.shift-zero/PORT.md`.
6. **Revert check** (R3): show the new e2e check fails on the old code.
7. **Write evidence**: `.shift-zero/evidence.json`, with
   `diff_hash` from `szero hash`.
8. **Run the gate**: `szero gate`. Hooks do this automatically where the
   harness supports them.
9. **Reply** with the verdict line first, then the answer.

The gate replays the evidence but does not yet determine whether
`.shift-zero/PORT.md` accurately describes the current project. Keeping
the port current is therefore an explicit agent responsibility, not an
automatically enforced gate check.

## Verdict line format

```
SHIFT ZERO: VERIFIED | L0 — e2e: checkout flow (http), revert check: failed on old code ✔
SHIFT ZERO: UNVERIFIED | L1 — no browser available, UI change not exercised. Ask: install Playwright browsers.
SHIFT ZERO: BLOCKED | L3 — six turns without a runnable app. This human does not want Shift Zero quality. Align or uninstall.
```

Turns that change nothing (questions, explanations) skip the loop and say
so in one line — no theater.
