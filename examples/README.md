# Worked examples

Same doctrine, different stacks. Each example shows one realistic change
and walks through it the Shift Zero way:

1. **The crappy test** an agent typically writes.
2. **The critique** — which doctrine rules it breaks and why.
3. **The Shift Zero test** — end to end through the real interface.
4. **The evidence** the gate replays.

Read them for the *pattern*, not the syntax. A model porting Shift Zero to
a stack that is not here should be able to produce the same four steps.

| Example | Surface | Shows |
|---|---|---|
| [ts-express-api](ts-express-api/README.md) | HTTP | Mocking the unit under test → real server + real requests |
| [py-fastapi](py-fastapi/README.md) | HTTP | Mocked repository + tautology → seeded test DB, revert check |
| [go-cli](go-cli/README.md) | CLI | Testing an internal func → driving the built binary |

Wanted next: Rust library, Java/Spring, PHP/Laravel, React UI with
Playwright, a message-queue consumer, a mobile app.
