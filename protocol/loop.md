# The per-turn loop (CI in session)

Every turn that changes behavior runs this loop **before** the first reply.

1. **Plan the slice.** State the vertical increment (doctrine R5) and how
   it will be observed through the real interface.
2. **Write or update the e2e check first** when practical, so it can fail.
3. **Implement.**
4. **Run scoped checks** (doctrine R4) using the commands in
   `.shift-zero/PORT.md`.
5. **Revert check** (R3): show the new e2e check fails on the old code.
6. **Write evidence**: `.shift-zero/evidence.json`, with
   `diff_hash` from `szero hash`.
7. **Run the gate**: `szero gate`. Hooks do this automatically where the
   harness supports them.
8. **Reply** with the verdict line first, then the answer.

## Verdict line format

```
SHIFT ZERO: VERIFIED | L0 — e2e: checkout flow (http), revert check: failed on old code ✔
SHIFT ZERO: UNVERIFIED | L1 — no browser available, UI change not exercised. Ask: install Playwright browsers.
SHIFT ZERO: BLOCKED | L3 — six turns without a runnable app. This human does not want Shift Zero quality. Align or uninstall.
```

Turns that change nothing (questions, explanations) skip the loop and say
so in one line — no theater.
