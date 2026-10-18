# Argon audit follow-up — 2026-10-18

Input: SOURCE_ONLY audit of `08555703a19f85aacbf3497012e3c1b910d74d88`.
The source chat/report is private and is not included in this package.

| Finding | Resolution / acceptance boundary |
|---|---|
| Setup amount is only an ROI basis | Opt-in `auto_deduct_setup` debits the synthetic balance once per tower. Rule-created towers debit on rule activation; manually configured towers on cashflow activation (or configuration if already active). Paid setup survives rule edits, rollback and restart. ROI subtracts actual scenario setup debits. |
| Expense has no explicit KPI effects | Optional `kpi_modifiers` sets an absolute global `revenue_multiplier` (0–5), `Bio_RAM` (0–100), or confidence/B2B hypothesis (0–100). UI exposes expense, multiplier and Bio_RAM. Cashflow/Conductor and runway use effective rounded revenue. Plain text expense infers no effects. |
| MCP restart/permanent registration | Startup and server-token rotation perform a real HTTP command → SSE → ack exchange. `configure_mcp.py` creates ignored project-only Codex configuration; no global account config is changed or uploaded. Registration and SDK acceptance do not prove a model has used the tools in an existing chat. |
| Contradictory Phase 1 status | Current README/HANDOFF/TASKS describe current runtime. Earlier text is preserved in `audit/phase1-*-snapshot.md` and `audit/phase1-mcp-notes.md`. |
| Generated Python isolation | Still `BLOCKED_SANDBOX` unless a real rootless OCI probe succeeds. No runtime/VM installed, no host execution fallback. |
| Synera live rollout/customer acceptance | Still NOT_RUN/BLOCKED. Requires the separate project's approved environment, accounts, recovery procedure, physical devices and explicit customer decision. No customer message sent. |

Semantic baseline: the seven follow-up regression cases produced six errors before
the code changes (unsupported new contracts and missing reconnect). They pass
afterward. Invalid/over-budget operations leave state unchanged; financial effects
are journaled atomically. UI requests reuse durable IDs after ambiguous responses.
The existing Argon queue is reused through `mcp-bridge/command-queue.mjs`.

Portable acceptance: `python -B scripts/verify.py`. SDK/browser/environment evidence
is separate and recorded in `audit/argon-followup-acceptance.json`; historical
`audit/phase2-acceptance.json` remains evidence for its earlier source slice.
