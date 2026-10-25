#!/usr/bin/env python3
"""Shift Zero gate — language-agnostic, stdlib only.

The gate never trusts the agent's prose. It replays the commands listed in
.shift-zero/evidence.json against the current working tree and tracks how
aligned the project is with the doctrine (the escalation ladder).

Commands:
  szero init            create .shift-zero/ in the current git repo
  szero hash            print the diff hash the evidence must reference
  szero gate            replay evidence; exit 0 = reply allowed, 2 = blocked
  szero status          print the current level and open blockers

Options:
  --hook claude-code    read the hook payload from stdin, speak the hook protocol
  --root DIR            project root (default: git toplevel of cwd)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

DIR = ".shift-zero"
EMPTY_TREE = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"
L2_AT, L3_AT = 3, 6
MAX_BLOCKS_PER_TURN = 3

EXIT_OK, EXIT_BLOCK = 0, 2


# ---------------------------------------------------------------- git + state

def git(root: Path, *args: str, check: bool = True) -> str:
    r = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True)
    if check and r.returncode != 0:
        raise RuntimeError(r.stderr.strip() or f"git {' '.join(args)} failed")
    return r.stdout


def find_root(explicit: str | None) -> Path | None:
    start = Path(explicit or ".").resolve()
    r = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=start,
                       capture_output=True, text=True)
    return Path(r.stdout.strip()) if r.returncode == 0 else None


def head(root: Path) -> str:
    r = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root,
                       capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else EMPTY_TREE


def state_path(root: Path) -> Path:
    return root / DIR / "state.json"


def load_state(root: Path) -> dict:
    p = state_path(root)
    if p.exists():
        try:
            return json.loads(p.read_text())
        except json.JSONDecodeError:
            pass
    return {"baseline": head(root), "last_verified_hash": None,
            "unaligned_streak": 0, "blocks_this_turn": 0, "open_blockers": []}


def save_state(root: Path, st: dict) -> None:
    (root / DIR).mkdir(exist_ok=True)
    state_path(root).write_text(json.dumps(st, indent=2) + "\n")


def diff_hash(root: Path, baseline: str) -> str:
    """Hash of everything changed since `baseline`: committed, staged,
    unstaged and untracked — excluding .shift-zero/ itself."""
    h = hashlib.sha256()
    h.update(git(root, "diff", "--binary", baseline, "--", ".",
                 f":(exclude){DIR}").encode())
    untracked = git(root, "ls-files", "--others", "--exclude-standard",
                    "--", ".", f":(exclude){DIR}").splitlines()
    for rel in sorted(untracked):
        h.update(b"\0untracked\0" + rel.encode() + b"\0")
        try:
            h.update((root / rel).read_bytes())
        except OSError:
            pass
    return "sha256:" + h.hexdigest()


def level(streak: int) -> int:
    if streak <= 0:
        return 0
    if streak >= L3_AT:
        return 3
    if streak >= L2_AT:
        return 2
    return 1


# ------------------------------------------------------------------- voice

LOUD = {
    1: "Shift Zero can't vouch for this yet. Fix the gap below and I'll prove it properly.",
    2: ("If you don't give me tools to validate your stuff, how the hell do I provide "
        "quality? Step up, my dear human, and let me offload you."),
    3: ("This human does not want Shift Zero quality. Change the approach and align "
        "— or uninstall Shift Zero."),
}


def banner(lvl: int, blockers: list[dict]) -> str:
    lines = [f"SHIFT ZERO L{lvl}: {LOUD.get(lvl, 'Aligned. Keep slicing vertically.')}"]
    for b in blockers:
        lines.append(f"  - missing: {b.get('missing')} -> why: {b.get('why')} -> ask: {b.get('ask')}")
    if lvl >= 2:
        lines.append("  Open your reply with this. Repeat it every turn until it is fixed.")
    return "\n".join(lines)


# ------------------------------------------------------------------ checks

def validate(ev: dict) -> list[str]:
    errs = []
    for key in ("version", "diff_hash", "slice", "checks", "verdict"):
        if key not in ev:
            errs.append(f"evidence is missing '{key}'")
    if ev.get("verdict") not in (None, "VERIFIED", "UNVERIFIED", "BLOCKED"):
        errs.append("verdict must be VERIFIED, UNVERIFIED or BLOCKED")
    for i, c in enumerate(ev.get("checks") or []):
        for key in ("name", "kind", "cmd", "expect_exit"):
            if key not in c:
                errs.append(f"checks[{i}] is missing '{key}'")
    return errs


def replay(root: Path, check: dict) -> tuple[bool, str]:
    try:
        r = subprocess.run(check["cmd"], shell=True, cwd=root, capture_output=True,
                           text=True, timeout=int(check.get("timeout_s", 300)))
    except subprocess.TimeoutExpired:
        return False, f"timed out after {check.get('timeout_s', 300)}s"
    ok = r.returncode == int(check["expect_exit"])
    tail = (r.stdout + r.stderr).strip().splitlines()[-5:]
    detail = f"exit {r.returncode}, expected {check['expect_exit']}"
    if not ok and tail:
        detail += "\n      " + "\n      ".join(tail)
    return ok, detail


def evaluate(root: Path, st: dict) -> tuple[str, list[str], list[str], list[dict]]:
    """Returns (outcome, problems, warnings, blockers).
    outcome: 'unchanged' | 'pass' | 'honest' | 'fail'"""
    current = diff_hash(root, st["baseline"])
    if current == st.get("last_verified_hash"):
        return "unchanged", [], [], []
    baseline_clean = subprocess.run(
        ["git", "diff", "--quiet", st["baseline"], "--", ".", f":(exclude){DIR}"],
        cwd=root).returncode == 0
    untracked = git(root, "ls-files", "--others", "--exclude-standard", "--", ".",
                    f":(exclude){DIR}").strip()
    if baseline_clean and not untracked:
        return "unchanged", [], [], []

    ev_path = root / DIR / "evidence.json"
    if not ev_path.exists():
        return "fail", ["code changed but there is no .shift-zero/evidence.json — "
                        "no evidence, no reply (R1)"], [], []
    try:
        ev = json.loads(ev_path.read_text())
    except json.JSONDecodeError as e:
        return "fail", [f"evidence.json is not valid JSON: {e}"], [], []

    problems = validate(ev)
    if problems:
        return "fail", problems, [], []
    if ev["diff_hash"] != current:
        return "fail", ["evidence is stale: the code changed after it was written. "
                        "Re-run the checks and `szero hash`."], [], []

    warnings, blockers = [], list(ev.get("blockers") or [])
    checks = ev["checks"]
    for c in checks:
        ok, detail = replay(root, c)
        if not ok:
            problems.append(f"replay failed — {c['name']} ({c['kind']}): {detail}")
    e2e = [c for c in checks if c["kind"] == "e2e"]
    for c in e2e:
        rc = c.get("revert_check") or {}
        if rc.get("failed_on_old_code") is not True:
            warnings.append(f"'{c['name']}' has no revert check — prove it fails on the old code (R3)")
    for t in ev.get("tests_weakened") or []:
        warnings.append(f"test weakened: {t} (R9) — the human must have agreed")

    if ev["verdict"] == "VERIFIED":
        if not e2e:
            problems.append("claimed VERIFIED with no e2e check — units are not proof (R2)")
        return ("fail" if problems else "pass"), problems, warnings, blockers

    # UNVERIFIED / BLOCKED: honest is allowed through, but escalates.
    if ev["verdict"] == "BLOCKED" and not blockers:
        problems.append("BLOCKED without blockers — name what is missing, why, and the ask")
    if problems:
        return "fail", problems, warnings, blockers
    return "honest", [], warnings, blockers


# ---------------------------------------------------------------- commands

def cmd_init(root: Path) -> int:
    d = root / DIR
    d.mkdir(exist_ok=True)
    if not state_path(root).exists():
        save_state(root, load_state(root))
    gi = d / ".gitignore"
    if not gi.exists():
        gi.write_text("state.json\nevidence.json\n")
    print(f"Shift Zero initialised in {d}. Next: port the doctrine (protocol/port.md) "
          "and write .shift-zero/PORT.md with proven commands.")
    return EXIT_OK


def cmd_hash(root: Path) -> int:
    st = load_state(root)
    print(diff_hash(root, st["baseline"]))
    return EXIT_OK


def cmd_status(root: Path, hook: str | None) -> int:
    st = load_state(root)
    lvl = level(st.get("unaligned_streak", 0))
    ported = (root / DIR / "PORT.md").exists()
    if hook and lvl == 0 and ported:
        return EXIT_OK  # aligned: stay quiet in the model's context
    msg = banner(lvl, st.get("open_blockers", []))
    if not ported:
        msg += ("\n  No .shift-zero/PORT.md yet: port the doctrine and build a walking "
                "skeleton before any feature work (R6).")
    print(msg)
    return EXIT_OK


def cmd_gate(root: Path, hook: str | None) -> int:
    st = load_state(root)
    outcome, problems, warnings, blockers = evaluate(root, st)

    if outcome == "unchanged":
        st["blocks_this_turn"] = 0
        save_state(root, st)
        return EXIT_OK

    if outcome == "fail":
        st["blocks_this_turn"] = st.get("blocks_this_turn", 0) + 1
        if st["blocks_this_turn"] <= MAX_BLOCKS_PER_TURN:
            save_state(root, st)
            out = ["SHIFT ZERO GATE: BLOCKED — you may not reply yet."]
            out += [f"  ✗ {p}" for p in problems]
            out += [f"  ! {w}" for w in warnings]
            out.append("  Fix it, rewrite .shift-zero/evidence.json, and finish again.")
            if hook == "claude-code":
                # Documented Stop-hook protocol: JSON decision on stdout, exit 0.
                print(json.dumps({"decision": "block", "reason": "\n".join(out)}))
                return EXIT_OK
            print("\n".join(out), file=sys.stderr)
            return EXIT_BLOCK
        # Loop guard: let the reply through, but it counts as unaligned.
        blockers = blockers or [{"missing": "passing gate",
                                 "why": f"gate failed {MAX_BLOCKS_PER_TURN} times this turn",
                                 "ask": "give the agent what it needs to verify, or align the approach"}]
        problems.append("loop guard released the reply UNVERIFIED")

    st["blocks_this_turn"] = 0
    if outcome == "pass":
        st["unaligned_streak"] = 0
        st["open_blockers"] = []
    else:
        st["unaligned_streak"] = st.get("unaligned_streak", 0) + 1
        st["open_blockers"] = blockers
    st["baseline"] = head(root)
    st["last_verified_hash"] = diff_hash(root, st["baseline"])
    save_state(root, st)

    lvl = level(st["unaligned_streak"])
    if outcome == "pass":
        print("SHIFT ZERO: VERIFIED | L0" + "".join(f"\n  ! {w}" for w in warnings))
    else:
        print(banner(lvl, st["open_blockers"]) +
              "".join(f"\n  ✗ {p}" for p in problems) +
              "".join(f"\n  ! {w}" for w in warnings))
    return EXIT_OK


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="szero", description="Shift Zero gate")
    ap.add_argument("command", choices=["init", "hash", "gate", "status"])
    ap.add_argument("--root")
    ap.add_argument("--hook", choices=["claude-code"])
    a = ap.parse_args(argv)

    if a.hook:
        try:
            payload = json.loads(sys.stdin.read() or "{}")
        except json.JSONDecodeError:
            payload = {}
        a.root = a.root or payload.get("cwd")

    root = find_root(a.root)
    if root is None:
        msg = ("SHIFT ZERO: BLOCKED — this is not a git repository. Without version control "
               "I can't tell what changed, so I can't prove anything. Ask: `git init`.")
        print(msg, file=sys.stderr if a.command == "gate" else sys.stdout)
        return EXIT_OK

    if a.command == "init":
        return cmd_init(root)
    if not (root / DIR).exists():
        if a.command == "gate":
            return EXIT_OK  # not installed in this project; stay out of the way
        print("Shift Zero is not initialised here. Run `szero init`.")
        return EXIT_OK
    if a.command == "hash":
        return cmd_hash(root)
    if a.command == "status":
        return cmd_status(root, a.hook)
    return cmd_gate(root, a.hook)


if __name__ == "__main__":
    sys.exit(main())
