# Bounded repairs of the Argon audit findings

The operator explicitly requested these external fixes on 2026-10-18. Canonical
implementations remain in Quantum_Trinity and token-monster, outside this repo.
No global provider route was enabled, no database with real runtime data was
tested, no payment provider/account was connected, and no real payment was made.

- `verify_external.py`: six paired semantic tests, same oracle SHA before/after.
  Baseline reproduced nine failures. Uses temporary SQLite and a loopback mocked
  upstream, never a real inference or payment request.
- `verify_edges.py`: fuzz, framed-packet integrity/expansion bounds, HTTP statuses,
  full SaaS compress/decompress roundtrips, forged payment attempts and native input.
- `verify_checkout_ui.mjs <index.html>`: executes the actual checkout function with
  a simulated DOM/network to verify offline, HTTP error and malformed success.
  The old UI invents a key and fails this test; the repaired UI stays on the form.
- `apply_hardening.py --apply`: historical hash-guarded installation of the initial
  bounded changes. It refuses changed preimages, including already-fixed files.
  Later small corrections are recorded in the private final patch evidence.

`Quantum_Trinity/lossless_codec.py` is a self-contained lossless dictionary codec.
It preserves literals, wording, Unicode and line endings; the packet includes its
dictionary and integrity digest. If header overhead would erase savings it sends
the original text. Native model/CLI traffic remains transparent. Byte reduction
and token estimates are not proof of subscription savings.

The proxy needs an explicit upstream. It preserves payload/model/tools and
returns real HTTP errors rather than fabricated completions; it never selects a
paid fallback from an ambient API key. A request cannot override the upstream URL.

Paid checkout intentionally returns 503 until a verified payment integration is
implemented and authorized. No paid key or completed-payment row is created by
that endpoint. An explicitly requested free demo is separate and marks payment
unverified. Old ledger records are preserved, not retroactively certified or
deleted. This repair does not claim live Stripe/crypto acceptance.

Private reports, preimages and final patches live in `audit/local-*` / `.runtime/`.
