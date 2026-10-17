# Offline helpers, not an autonomous company
Python 3.10+, standard library only. Run from the package root. No model, browser, payment, messaging, scheduling, credentials or deployment integration is present.

| Command | Function | Boundary |
|---|---|---|
| `python -B -m revenue_lab demo` | Prints four economics scenarios | SIMULATED, no paid customers |
| `python -B -m revenue_lab quote fixtures/quote_chf.json` | Contribution, attention and indicative floor | One currency; no tax/benefits/FX |
| `python -B -m revenue_lab gate fixtures/action_external.json` | Advisory classification of an action | Never executes or grants permission |
| `python -B -m revenue_lab freshness fixtures/source_argon.json --as-of 2026-12-01` | Detects expiry/review age | Does not fetch or confirm the source |
| `python -B -m revenue_lab rank fixtures/rank_rescue.json` | Scores a subjective prior | Not demand, probability or permission |

## Validation
Use `Quote.from_mapping`, not the bare dataclass constructor, for untrusted input. Exact quote keys are required. Monetary transaction inputs support two decimal places; finite non-negative rates/hours are checked, total attention must be positive, fee+reserve must be below one. Values above the documented numeric bound, booleans and mixed currency labels are rejected. The CLI caps a single JSON file at 1 MiB and returns exit 2 on invalid input.

A successful gate command may return exit 0 while its semantic decision is HOLD or DENY. **Exit 0 means a report was generated, not permission to act.** `executed` is always false. An attacker supplying `approved: true` does not change authority.

## Calculation boundaries
Payment fee and reserve use ROUND_HALF_UP to cents. The price floor uses a rounded-up continuous formula and is indicative; actual processor rounding, tax, reserves and refunds can change it. Scenario months are billed months, not days prorated. Income, number of orders, labour value and reserve are user assumptions. Imputed labour is an opportunity-cost scenario, not a bank transfer or accounting deduction.

For production, add authenticated event adapters and isolated execution to the existing KI owners. This package intentionally cannot do that job alone. Unit tests validate only this package in the environment stated in STATUS.json; they do not validate Windows, a browser, a client project or upstream repos.
