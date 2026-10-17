# AI Architect

Offline-first RuleForge and AssetForge share the server command dispatcher. No provider is called by default.

## Rules and rollback

JSON rule schema: `sovereign.rule.v1`, safe `id`, `format: json`, `origin`, `assumptions`, and up to eight `operations`.
Allowlisted operations: `add_node` (safe ID, title, kind, optional integer-cent daily revenue/cost and ROI base), `expense` (integer cents), and `set_modifier` (explicit confidence/B2B assumptions, 0–100).
Python uses the same schema with `format: python` and `source` defining only `evaluate(state, params, seed)`.
The result is the same allowlisted operation list. No generated module is imported into the host.

Rules are validated and dry-run before staging, then evaluated again on the next tick boundary. Activation is once per version; tower economics continue in the shared core. The UI creates and activates with one 15-minute tick. Provider jobs do the same after successful validation. Failed/conflicting pending rules preserve the last working version and do not stop the clock.

`rollback_rule` cancels a pending version, stages the previous version, or disables a first-version rule's towers. It does not refund historical expenses or erase the journal. Generated artifacts are content-addressed and ignored by Git.

## Real Python isolation

No OCI runtime was found on this host during implementation. Python is **BLOCKED_SANDBOX**, not accepted by a mock executor.
After an owner provisions a rootless Podman/Docker engine with cgroups v2 and a verified official Python image already loaded, create `.runtime/simulator/sandbox.json` with exactly `runtime` (`podman` or `docker`) and `image` (digest-pinned reference). There is no automatic image pull or VM installation.

```powershell
python -B scripts/verify_sandbox.py
```

The worker verifies effective non-root UID, read-only root, no effective capabilities, no-new-privileges, no external network interface, CPU/memory limits, and no GPU device. Limits: one job, 0.5 CPU, 256 MiB, 16 processes, 5-second wall deadline, bounded output. Host files, tokens and sockets are not mounted. AST checks are only an additional filter.

## Paid providers

Optional text adapters: OpenAI and OpenRouter. Image adapter: OpenAI. They are implemented but **not live verified** here. Anthropic and native Codex/Claude model sessions are not claimed connected.

The trusted owner may create `.runtime/simulator/providers.json`; the app has no endpoint that can change it. Required fields: `enabled: true`, `allow_paid: true`, `provider`, `rule_model`, `image_model` when used, positive `task_cap_usd`, `day_cap_usd`, `max_call_usd`, `max_output_tokens` (64–4096), fresh `pricing_verified_on`, and the relevant prices: `input_usd_per_million`, `output_usd_per_million`, `image_usd`. Optional `governor` overrides the existing host launcher path. Enter independently verified pricing; the app does not claim that an operator-entered price is a provider billing guarantee.

Keys remain in environment or ignored `.env`. Every request runs through `gradual_ai_launcher.py --governor`; missing launcher or `harness/power_governor.py` blocks it. Calls are serialized, reserved before launch, and never retried/fail over automatically. Price bounds and remaining task/day reservations are checked first. Unknown charges retain the full reservation pending reconciliation. `reported_cost_usd` is recorded only when the provider returns a cost; missing cost stays unknown. The private local ledger is an adapter receipt, not a replacement for the host's global accounting.

Interrupted paid jobs are marked `INTERRUPTED_NO_RETRY` after restart. Fallback SVGs remain usable. Install `requirements-images.txt` in the chosen environment before validating provider images.

Implementation references: [official MCP SDK v1](https://py.sdk.modelcontextprotocol.io/v1/), [Podman run isolation controls](https://docs.podman.io/en/latest/markdown/podman-run.1.html).
