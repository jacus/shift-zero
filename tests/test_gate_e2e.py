"""End-to-end tests for the Shift Zero gate.

Shift Zero eats its own cooking: every test drives the real CLI as a
subprocess against a real temporary git repository. No mocks.
"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SZERO = Path(__file__).resolve().parent.parent / "gate" / "szero.py"


def sh(cwd, *args):
    return subprocess.run(list(args), cwd=cwd, capture_output=True, text=True)


class Project:
    """A throwaway git project with a tiny CLI 'app' to verify."""

    def __init__(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        sh(self.root, "git", "init", "-q", "-b", "main")
        sh(self.root, "git", "config", "user.email", "t@example.com")
        sh(self.root, "git", "config", "user.name", "t")
        self.write("app.sh", 'echo "hello"\n')
        sh(self.root, "git", "add", ".")
        sh(self.root, "git", "commit", "-qm", "skeleton")
        self.szero("init")

    def write(self, rel, text):
        (self.root / rel).write_text(text)

    def szero(self, *args, stdin=None):
        return subprocess.run([sys.executable, str(SZERO), *args], cwd=self.root,
                              input=stdin, capture_output=True, text=True)

    def evidence(self, verdict="VERIFIED", checks=None, **extra):
        ev = {
            "version": 1,
            "diff_hash": self.szero("hash").stdout.strip(),
            "slice": "greet in the new way",
            "checks": checks if checks is not None else [{
                "name": "greets", "kind": "e2e", "surface": "cli",
                "cmd": "sh app.sh | grep -q howdy", "expect_exit": 0,
                "revert_check": {"failed_on_old_code": True, "how": "git stash"},
            }],
            "verdict": verdict,
            **extra,
        }
        (self.root / ".shift-zero" / "evidence.json").write_text(json.dumps(ev))

    def state(self):
        return json.loads((self.root / ".shift-zero" / "state.json").read_text())

    def close(self):
        self.tmp.cleanup()


class GateE2E(unittest.TestCase):
    def setUp(self):
        self.p = Project()

    def tearDown(self):
        self.p.close()

    def test_no_change_lets_reply_through(self):
        r = self.p.szero("gate")
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_change_without_evidence_is_blocked(self):
        self.p.write("app.sh", 'echo "howdy"\n')
        r = self.p.szero("gate")
        self.assertEqual(r.returncode, 2)
        self.assertIn("no evidence, no reply", r.stderr)

    def test_new_untracked_file_counts_as_change(self):
        self.p.write("feature.sh", "echo new\n")
        self.assertEqual(self.p.szero("gate").returncode, 2)

    def test_valid_e2e_evidence_is_verified_and_replayed(self):
        self.p.write("app.sh", 'echo "howdy"\n')
        self.p.evidence()
        r = self.p.szero("gate")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("VERIFIED | L0", r.stdout)
        # Same tree again: nothing to re-verify.
        self.assertEqual(self.p.szero("gate").returncode, 0)

    def test_stale_evidence_is_blocked(self):
        self.p.write("app.sh", 'echo "howdy"\n')
        self.p.evidence()
        self.p.write("app.sh", 'echo "howdy partner"\n')
        r = self.p.szero("gate")
        self.assertEqual(r.returncode, 2)
        self.assertIn("stale", r.stderr)

    def test_editing_a_new_file_after_evidence_makes_it_stale(self):
        self.p.write("app.sh", 'echo "howdy"\n')
        self.p.write("feature.sh", "echo v1\n")
        self.p.evidence()
        self.p.write("feature.sh", "echo v2\n")
        r = self.p.szero("gate")
        self.assertEqual(r.returncode, 2)
        self.assertIn("stale", r.stderr)

    def test_lying_evidence_fails_on_replay(self):
        self.p.write("app.sh", 'echo "hello again"\n')  # does not say howdy
        self.p.evidence()
        r = self.p.szero("gate")
        self.assertEqual(r.returncode, 2)
        self.assertIn("replay failed", r.stderr)

    def test_verified_without_e2e_is_rejected(self):
        self.p.write("app.sh", 'echo "howdy"\n')
        self.p.evidence(checks=[{"name": "lint", "kind": "static",
                                 "cmd": "true", "expect_exit": 0}])
        r = self.p.szero("gate")
        self.assertEqual(r.returncode, 2)
        self.assertIn("no e2e check", r.stderr)

    def test_missing_revert_check_warns(self):
        self.p.write("app.sh", 'echo "howdy"\n')
        self.p.evidence(checks=[{"name": "greets", "kind": "e2e",
                                 "cmd": "sh app.sh | grep -q howdy", "expect_exit": 0}])
        r = self.p.szero("gate")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("no revert check", r.stdout)

    def test_honest_blocked_escalates_to_align_or_uninstall(self):
        blocker = {"missing": "a browser", "why": "UI changes can't be exercised",
                   "ask": "npx playwright install"}
        for turn in range(1, 7):
            self.p.write("app.sh", f'echo "turn {turn}"\n')
            self.p.evidence(verdict="BLOCKED", checks=[], blockers=[blocker])
            r = self.p.szero("gate")
            self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("L3", r.stdout)
        self.assertIn("uninstall Shift Zero", r.stdout)
        status = self.p.szero("status").stdout
        self.assertIn("npx playwright install", status)
        self.assertIn("uninstall Shift Zero", status)

    def test_level_two_uses_the_loud_voice(self):
        for turn in range(3):
            self.p.write("app.sh", f'echo "turn {turn}"\n')
            self.p.evidence(verdict="UNVERIFIED", checks=[])
            r = self.p.szero("gate")
        self.assertIn("L2", r.stdout)
        self.assertIn("how the hell", r.stdout)

    def test_verified_turn_resets_the_ladder(self):
        for turn in range(4):
            self.p.write("app.sh", f'echo "turn {turn}"\n')
            self.p.evidence(verdict="UNVERIFIED", checks=[])
            self.p.szero("gate")
        self.assertEqual(self.p.state()["unaligned_streak"], 4)
        self.p.write("app.sh", 'echo "howdy"\n')
        self.p.evidence()
        self.assertEqual(self.p.szero("gate").returncode, 0)
        self.assertEqual(self.p.state()["unaligned_streak"], 0)

    def test_loop_guard_releases_after_three_blocks(self):
        self.p.write("app.sh", 'echo "howdy"\n')
        codes = [self.p.szero("gate").returncode for _ in range(4)]
        self.assertEqual(codes, [2, 2, 2, 0])
        self.assertEqual(self.p.state()["unaligned_streak"], 1)

    def test_claude_code_hook_reads_cwd_from_payload(self):
        self.p.write("app.sh", 'echo "howdy"\n')
        payload = json.dumps({"cwd": str(self.p.root), "stop_hook_active": False})
        r = subprocess.run([sys.executable, str(SZERO), "gate", "--hook", "claude-code"],
                           cwd=tempfile.gettempdir(), input=payload,
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        decision = json.loads(r.stdout)
        self.assertEqual(decision["decision"], "block")
        self.assertIn("no evidence", decision["reason"])

    def test_status_hook_is_quiet_when_aligned_and_loud_when_not(self):
        (self.p.root / ".shift-zero" / "PORT.md").write_text("# port\n")
        quiet = self.p.szero("status", "--hook", "claude-code",
                             stdin=json.dumps({"cwd": str(self.p.root)}))
        self.assertEqual(quiet.stdout, "")
        for turn in range(3):
            self.p.write("app.sh", f'echo "turn {turn}"\n')
            self.p.evidence(verdict="UNVERIFIED", checks=[])
            self.p.szero("gate")
        loud = self.p.szero("status", "--hook", "claude-code",
                            stdin=json.dumps({"cwd": str(self.p.root)}))
        self.assertIn("L2", loud.stdout)
        self.assertIn("Open your reply with this", loud.stdout)

    def test_committed_change_still_needs_evidence(self):
        self.p.write("app.sh", 'echo "howdy"\n')
        sh(self.p.root, "git", "commit", "-qam", "sneaky")
        self.assertEqual(self.p.szero("gate").returncode, 2)

    def test_gate_stays_out_of_projects_without_shift_zero(self):
        with tempfile.TemporaryDirectory() as d:
            sh(d, "git", "init", "-q")
            Path(d, "x.txt").write_text("x")
            r = subprocess.run([sys.executable, str(SZERO), "gate"], cwd=d,
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, 0)


if __name__ == "__main__":
    unittest.main()
