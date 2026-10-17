"""Usage: python -B -m revenue_lab {demo,quote,gate,freshness,rank}."""
from __future__ import annotations
import argparse
from datetime import date
import json
from pathlib import Path
import sys
from .core import Quote, evaluate_quote, scenario, freshness, plan_action, rank_opportunity

MAX_INPUT_BYTES = 1024 * 1024


def load(path: str) -> dict:
    with Path(path).open("rb") as handle:
        raw = handle.read(MAX_INPUT_BYTES + 1)
    if len(raw) > MAX_INPUT_BYTES:
        raise ValueError("input exceeds 1 MiB safety limit")
    data = json.loads(raw.decode("utf-8-sig"))
    if not isinstance(data, dict):
        raise ValueError("top-level input must be an object")
    return data


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Offline revenue planning; no external actions.")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("demo", help="Print an explicitly simulated economics example")
    for command in ("quote", "gate", "freshness", "rank"):
        child = sub.add_parser(command)
        child.add_argument("input", help="Path to a local JSON object")
        if command == "freshness":
            child.add_argument("--as-of", required=True, help="Explicit ISO date, not hidden current time")
    args = parser.parse_args(argv)
    try:
        if args.command == "demo":
            q = Quote.from_mapping({"currency":"CHF", "price":"750.00", "fee_rate":"0.029",
                "fee_fixed":"0.30", "variable_cost":"25.00", "reserve_rate":"0.05",
                "acquisition_hours":"3", "delivery_hours":"2", "support_hours":"1", "hourly_value":"50"})
            result = {"status":"SIMULATED_NO_CUSTOMERS_NO_PAYMENTS", "quote":evaluate_quote(q),
                "scenarios":[scenario(q,jobs=n,months_billed=m,fixed_monthly="100",setup_cash="100",
                                     setup_hours="16",costs_currency="CHF") for n,m in [(1,1),(3,1),(24,6),(0,6)]]}
        else:
            data = load(args.input)
            if args.command == "quote": result = evaluate_quote(Quote.from_mapping(data))
            elif args.command == "gate": result = plan_action(data)
            elif args.command == "rank": result = rank_opportunity(data)
            else: result = freshness(data, date.fromisoformat(args.as_of))
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, TypeError) as exc:
        print(json.dumps({"status":"INVALID_INPUT", "error":str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
