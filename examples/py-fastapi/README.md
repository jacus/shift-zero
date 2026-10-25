# Python / FastAPI — "users can't register twice with the same email"

## 1. The crappy test

```python
def test_duplicate_email(mocker):
    repo = mocker.Mock()
    repo.exists.return_value = True
    service = UserService(repo)
    with pytest.raises(Exception):
        service.register("a@b.c", "pw")
    assert repo.exists.called == repo.exists.called   # tautology
```

## 2. The critique

- **R8 — tautological assert** (`x == x`) and **over-mocking**: the only
  real code path is "raise if a mock says so".
- **R8 — `pytest.raises(Exception)`** passes on *any* crash, including a
  typo.
- **R2/R3 — no e2e, no revert check.** The real bug (two concurrent
  requests both succeed because there is no unique index) is invisible here.

> SHIFT ZERO: a mock told your service the email exists, and your test
> congratulated it for believing the mock. Show me the database saying no.

## 3. The Shift Zero test

```python
# tests/e2e/test_register.py — real app, real (throwaway) database
from fastapi.testclient import TestClient
from app.main import create_app

def test_second_registration_with_same_email_is_rejected(tmp_db_url):
    client = TestClient(create_app(database_url=tmp_db_url))
    first = client.post("/users", json={"email": "a@b.c", "password": "pw12345!"})
    assert first.status_code == 201

    second = client.post("/users", json={"email": "A@b.c", "password": "other999!"})
    assert second.status_code == 409
    assert second.json()["error"] == "email_taken"

    users = client.get("/admin/users").json()
    assert [u["email"] for u in users] == ["a@b.c"]
```

`tmp_db_url` is a fixture that creates and migrates a fresh SQLite or
Postgres database — the seam doctrine R7 asks for. Note the case-variant
email: the e2e test catches the normalization bug the mock never could.

## 4. The evidence

```json
{
  "version": 1,
  "diff_hash": "sha256:…",
  "slice": "POST /users rejects duplicate emails, case-insensitively, via a unique index",
  "checks": [{
    "name": "duplicate registration e2e", "kind": "e2e", "surface": "http",
    "cmd": "pytest tests/e2e/test_register.py -q", "expect_exit": 0,
    "revert_check": { "failed_on_old_code": true, "how": "git stash: second POST returned 201" }
  }],
  "not_covered": ["two truly concurrent requests (needs a load tool)"],
  "blockers": [],
  "verdict": "VERIFIED"
}
```
