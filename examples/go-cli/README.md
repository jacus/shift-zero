# Go CLI — "`todo done <id>` marks a task complete"

## 1. The crappy test

```go
func TestMarkDone(t *testing.T) {
    tasks := []Task{{ID: 1}}
    markDone(tasks, 1)
    // no assertion
}
```

## 2. The critique

- **R8 — asserts nothing.** It passes as long as `markDone` doesn't panic.
- **R2 — tests an internal function**, not the CLI. Argument parsing,
  file persistence and exit codes — where CLI bugs actually live — are
  untouched.
- **R3 — passes on the old code**, so it proves nothing about the change.

> SHIFT ZERO: a test with no assertion is a smoke detector with no
> battery. Drive the binary.

## 3. The Shift Zero test

```go
// e2e/done_test.go — builds and runs the real binary against a temp data dir
func TestDoneMarksTaskComplete(t *testing.T) {
    bin := buildBinary(t)                 // go build -o into t.TempDir()
    data := t.TempDir()
    run := func(args ...string) (string, int) {
        cmd := exec.Command(bin, args...)
        cmd.Env = append(os.Environ(), "TODO_DATA_DIR="+data)
        out, _ := cmd.CombinedOutput()
        return string(out), cmd.ProcessState.ExitCode()
    }

    run("add", "write doctrine")
    out, code := run("done", "1")
    if code != 0 || !strings.Contains(out, "done: write doctrine") {
        t.Fatalf("done failed: code=%d out=%q", code, out)
    }
    list, _ := run("list", "--pending")
    if strings.Contains(list, "write doctrine") {
        t.Fatalf("task still pending after done: %q", list)
    }
    _, code = run("done", "99")
    if code != 2 {
        t.Fatalf("unknown id should exit 2, got %d", code)
    }
}
```

Testability (R7): `TODO_DATA_DIR` is the seam that makes the binary
hermetic. If the CLI hard-codes `~/.todo`, adding that variable is the
first slice.

## 4. The evidence

```json
{
  "version": 1,
  "diff_hash": "sha256:…",
  "slice": "`todo done <id>` completes a task and persists it",
  "checks": [{
    "name": "done e2e", "kind": "e2e", "surface": "cli",
    "cmd": "go test ./e2e -run TestDoneMarksTaskComplete", "expect_exit": 0,
    "revert_check": { "failed_on_old_code": true, "how": "git stash: unknown command \"done\"" }
  }],
  "verdict": "VERIFIED"
}
```
