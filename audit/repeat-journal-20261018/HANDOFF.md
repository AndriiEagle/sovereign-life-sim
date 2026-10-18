# Repeat external audit: actual code, journal recovery and idempotency

Repository: `AndriiEagle/sovereign-life-sim` (GitHub id `1423646041`). Review branch: `codex/journal-audit-530`. Verified starting commit: `5963e7d1dc54057db73f61159171f1bb94f94604`. The immutable review commit is supplied in Andrii's message; do not silently substitute a newer branch head.

Outcome: give a browser-limited auditor the actual implementation, caller/dependency closure, reproducible checks and honest proof limits. This branch is a candidate; it has not been merged into `codex/sovereign-life-sim-530` or applied to the existing running app. Public availability is not a new commercial license; retain [RIGHTS.md](../../RIGHTS.md).

## Reproduced defect and isolated repair

The accepted invariant is: only an incomplete EOF tail may be preserved and truncated. A corrupt complete LF-terminated row must stop recovery without rewriting the journal. Concurrent/restarted replay of one request must not apply its effects twice.

At the starting commit, `Store._recover` iterates `bytes.splitlines(keepends=True)`. That treats a lone CR as a record separator too. Prepending `BROKEN\r` to the final complete LF-terminated record makes recovery treat this corrupt record as an interrupted tail and silently discard that record. This is a data-loss defect under that corruption condition, not a claim that ordinary valid actions always lose data.

The candidate changes only `simulation-core/persistence.py`: import `io` and iterate `io.BytesIO(data)`, whose binary lines end at LF. The corrupt complete record now raises instead of being truncated. This preserves existing JSON/hash/sequence/previous-hash validation and the existing incomplete-tail path. No journal schema, auth, model routing, UI, economics or dependency changes are proposed.

`tests/test_journal_review.py` adds four behavioral tests to the normal Python discovery suite: corrupt complete records (four damage variants), exact preservation of an incomplete Unicode EOF tail, CRLF recovery without rewriting, and real cross-process lease refusal/release. The new corruption test failed on the original algorithm before repair. `run_checks.py` independently restores that algorithm and removes Runtime's duplicate guard in temporary copies; the corresponding tests must fail with assertions.

Important boundaries: `Runtime.execute` and `Game.command` perform deduplication while holding `Store.lock`; `Store.commit` alone does not promise caller-level idempotency. SHA chains provide consistency checks, not authentication against an attacker able to rewrite the whole store. An fsync error means no successful acknowledgement and uncertain durable outcome, not a promise that no bytes reached disk. Review these actual contracts before assigning defects.

## Evidence and reading order

1. [EXTERNAL_PROMPT.md](EXTERNAL_PROMPT.md), [TASKS.md](TASKS.md), this file.
2. [SOURCE_MANIFEST.json](SOURCE_MANIFEST.json): exact source byte hashes, original line counts, base/current status and browser bundles. Bundles are derived, line-numbered reading aids, not original bytes. A single large source file can exceed the target chunk size; detect truncation explicitly.
3. `01-journal-1.md` (Store, real Runtime caller, validation); `02-state-1.md` (state transitions); `03-guards-1.md` (rule/asset/provider/sandbox dependencies).
4. Economics, HTTP/UI/queue, Argon and test bundles listed in the manifest. Cite the original path and numbered source line, never the wrapper's Markdown line.
5. [LOCAL_CHECKS.json](LOCAL_CHECKS.json): actual local outputs, failed mutations and exact fingerprints. [BASELINE_CHECKS.json](BASELINE_CHECKS.json) belongs to starting commit 5963e7d, before the repair. Neither is independent external acceptance.

The existing full Git tree contains original source, required static assets and root context. `CONTEXT_MANIFEST.json` is linked rather than duplicated into the reader; it contains the runtime's 16-project seed plus historical provenance. `sim/params.json`, Argon's world data and package initializers are included in the source reader. The full repository, not the finite reader slice, is required for the entire portable suite and visual review.

## Commands and permitted effects

Prerequisites: Python 3.11+ and Node 20+ already present. No installation is authorized. The documented optional official MCP SDK and rootless OCI paths are separate; missing prerequisites remain HOLD rather than a host-execution fallback.

```sh
git clone --branch codex/journal-audit-530 https://github.com/AndriiEagle/sovereign-life-sim.git
cd sovereign-life-sim
git checkout --detach <exact-review-SHA-from-user>
python -B scripts/verify.py
python -B audit/repeat-journal-20261018/build_reader.py --check
python -B audit/repeat-journal-20261018/run_checks.py
```

The portable suite, local HTTP tests and additional journal checks use disposable synthetic state. The mutation runner edits only temporary copies and writes an ignored `audit/local-journal-focused.json` report. Do not load the operator's `.runtime`, session files, `.env`, credentials, customer data or other checkouts. No hosted model/provider call, paid inference, install, account connection, public upload, remote change or production effect is authorized for the external auditor. Browser-only readers report tests NOT_RUN and can provide a precisely scoped static review.

## Open proof limits and rollback

Rootless generated-Python isolation is BLOCKED_SANDBOX on the checked Windows host. Live providers, Synera, physical devices, real customer outcomes and receiving-model access are not accepted by this package. The optional host governor is outside the public repo; its absence does not prevent the offline simulator/journal tests and must not be invented or bypassed. No new official SDK or visual/browser acceptance is claimed here; earlier receipts stay historical.

Revert the candidate's `persistence.py` hunk to reproduce the defect; use disposable copies for this check. To reject the proposal, leave this branch unmerged. No original source snapshot, live state directory or working primary branch was replaced. A future approved integration must preserve the regression test and verify its exact source again.

The previous returned report was an access/README review, with all implementation areas NOT_READ and executable tests NOT_RUN. Its zero confirmed findings are not a bug-free verdict. See the existing [triage](../returned-audit-triage.uk.md); its private raw attachment is not uploaded.
