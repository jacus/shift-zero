# TypeScript / Express — "apply a discount code at checkout"

## 1. The crappy test

```ts
jest.mock("../src/checkout");               // mocks the unit under test
import { applyDiscount } from "../src/checkout";

test("applies discount", () => {
  (applyDiscount as jest.Mock).mockReturnValue({ total: 90 });
  expect(applyDiscount({ total: 100 }, "SAVE10").total).toBe(90);
});
```

## 2. The critique

- **R8 — mocks the unit under test.** The test asserts on a value it
  wrote itself. It passes whatever `applyDiscount` does, including nothing.
- **R3 — would pass on the old code.** There is no old behavior it can
  catch, because no real code runs.
- **R2 — no e2e.** The feature is "a customer applies a code at
  checkout". Nothing here touches the route, validation or storage.

> SHIFT ZERO: this test is theater. It tests jest.mock, not your checkout.

## 3. The Shift Zero test

```ts
// e2e/checkout.e2e.test.ts — boots the real app on a random port
import { startApp } from "../src/server";

let app: Awaited<ReturnType<typeof startApp>>;
beforeAll(async () => { app = await startApp({ port: 0, seed: "fixtures/cart.json" }); });
afterAll(() => app.close());

test("SAVE10 takes 10% off the cart total", async () => {
  const res = await fetch(`${app.url}/cart/c1/discount`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ code: "SAVE10" }),
  });
  expect(res.status).toBe(200);
  expect((await res.json()).total).toBe(90);
});

test("unknown codes are rejected and the total is unchanged", async () => {
  const res = await fetch(`${app.url}/cart/c1/discount`, {
    method: "POST", headers: { "content-type": "application/json" },
    body: JSON.stringify({ code: "NOPE" }),
  });
  expect(res.status).toBe(422);
  expect((await (await fetch(`${app.url}/cart/c1`)).json()).total).toBe(100);
});
```

Testability (R7): `startApp({ port: 0, seed })` is the seam. If the app
can't boot on a random port with seeded data, that is the first slice to
build.

## 4. The evidence

```json
{
  "version": 1,
  "diff_hash": "sha256:…",
  "slice": "POST /cart/:id/discount applies SAVE10 end to end",
  "checks": [{
    "name": "discount e2e", "kind": "e2e", "surface": "http",
    "cmd": "npx jest e2e/checkout.e2e.test.ts", "expect_exit": 0,
    "revert_check": { "failed_on_old_code": true, "how": "git stash; route returned 404" }
  }],
  "not_covered": ["discount stacking with gift cards"],
  "verdict": "VERIFIED"
}
```
