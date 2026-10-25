<!-- Shift Zero: paste or merge into your project's AGENTS.md / rules file. -->
# Shift Zero — quality from start

This project runs under Shift Zero: CI in the session. The doctrine lives
at `<SHIFT_ZERO_KIT>/DOCTRINE.md`; read it before your first change.
`szero` means `python3 <SHIFT_ZERO_KIT>/gate/szero.py`.

Before replying to any request that changes behavior:
1. If `.shift-zero/PORT.md` is missing, port the doctrine first
   (`<SHIFT_ZERO_KIT>/protocol/port.md`). No feature work before a walking
   skeleton exists: boots in one command, one passing e2e test.
2. Deliver a thin vertical slice, verified end to end through the real
   interface. Units supplement e2e, never replace it.
3. Prove the new e2e check fails on the old code (revert check).
4. Write `.shift-zero/evidence.json` with `diff_hash` from `szero hash`.
5. Run `szero gate` and fix everything it reports.
6. Start your reply with the verdict line:
   `SHIFT ZERO: <VERIFIED|UNVERIFIED|BLOCKED> | L<n> — <proof or blocker>`

Never weaken a test to get green. Name crappy tests every time.
When tools are missing, say so loudly every turn — missing → why it
blocks quality → smallest ask. Check `szero status` each turn; at L3,
tell the human plainly they don't want Shift Zero quality and should
align or uninstall it.
