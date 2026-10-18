# Sovereign source reader: 04-economics, part 3

Derived reading aid; original file bytes and rights are authoritative. No functions or file sections have been omitted from the listed files. Cite `original/path:line` using the numbered column. Read at the exact review commit supplied in the user message.

## simulation-core/revenue_lab/__init__.py

Original bytes: 108; SHA256: `8a0cb7682b1617b4736b34a362a2884d27f2837a263e07061b40ec87464a9e81`. Original source line numbers follow.

````text
    1 | """Offline decision helpers. No executor, network client, payment proof or ledger."""
    2 | __version__ = "1.0.0"
````

## simulation-core/revenue_lab/core.py

Original bytes: 9957; SHA256: `3ac7b095e6a91de02d0b44b0571f5dbda8cbe81e5a8e72a68497d9c35bd81d5d`. Original source line numbers follow.

````text
    1 | """Pure, bounded economics and planning helpers. All money stays in one currency."""
    2 | from __future__ import annotations
    3 | from dataclasses import dataclass, fields
    4 | from datetime import date
    5 | from decimal import Decimal, InvalidOperation, ROUND_HALF_UP, ROUND_CEILING
    6 | from typing import Any, Mapping
    7 |
    8 | CENT = Decimal("0.01")
    9 | CURRENCIES = frozenset({"CHF", "USD", "EUR", "GBP"})
   10 | MAX_VALUE = Decimal("1000000000")
   11 |
   12 |
   13 | def decimal(value: Any, name: str) -> Decimal:
   14 |     """Accept explicit decimal inputs, rejecting booleans and non-finite values."""
   15 |     if isinstance(value, bool) or not isinstance(value, (str, int, float, Decimal)):
   16 |         raise ValueError(f"{name}: expected a finite non-negative number")
   17 |     try:
   18 |         number = Decimal(str(value))
   19 |     except (InvalidOperation, ValueError):
   20 |         raise ValueError(f"{name}: invalid decimal") from None
   21 |     if not number.is_finite() or number < 0 or number > MAX_VALUE:
   22 |         raise ValueError(f"{name}: outside supported non-negative range")
   23 |     return number
   24 |
   25 |
   26 | def currency(value: Any) -> str:
   27 |     if not isinstance(value, str) or value not in CURRENCIES:
   28 |         raise ValueError("currency: use exact CHF, USD, EUR or GBP; no inferred FX")
   29 |     return value
   30 |
   31 |
   32 | def integer(value: Any, name: str, minimum: int = 0) -> int:
   33 |     if type(value) is not int or value < minimum or value > 1000000:
   34 |         raise ValueError(f"{name}: expected bounded integer >= {minimum}")
   35 |     return value
   36 |
   37 |
   38 | def money(value: Decimal) -> str:
   39 |     return str(value.quantize(CENT, rounding=ROUND_HALF_UP))
   40 |
   41 |
   42 | @dataclass(frozen=True)
   43 | class Quote:
   44 |     currency: str
   45 |     price: Decimal
   46 |     fee_rate: Decimal
   47 |     fee_fixed: Decimal
   48 |     variable_cost: Decimal
   49 |     reserve_rate: Decimal
   50 |     acquisition_hours: Decimal
   51 |     delivery_hours: Decimal
   52 |     support_hours: Decimal
   53 |     hourly_value: Decimal
   54 |
   55 |     @classmethod
   56 |     def from_mapping(cls, data: Mapping[str, Any]) -> "Quote":
   57 |         if not isinstance(data, Mapping):
   58 |             raise ValueError("quote: expected object")
   59 |         required = {f.name for f in fields(cls)}
   60 |         if set(data) != required:
   61 |             missing = sorted(required - set(data))
   62 |             extra = sorted(set(data) - required)
   63 |             raise ValueError(f"quote keys: missing={missing}; extra={extra}")
   64 |         numbers = {key: decimal(data[key], key) for key in required - {"currency"}}
   65 |         result = cls(currency(data["currency"]), **numbers)
   66 |         if result.price <= 0:
   67 |             raise ValueError("price must be positive")
   68 |         if result.fee_rate + result.reserve_rate >= 1:
   69 |             raise ValueError("fee_rate + reserve_rate must be below 1")
   70 |         if result.attention_hours <= 0:
   71 |             raise ValueError("total attention hours must be positive")
   72 |         # Round monetary inputs at the boundary, not arbitrary intermediate hours/rates.
   73 |         for key in ("price", "fee_fixed", "variable_cost"):
   74 |             if numbers[key] != numbers[key].quantize(CENT):
   75 |                 raise ValueError(f"{key}: use at most two decimal places")
   76 |         return result
   77 |
   78 |     @property
   79 |     def attention_hours(self) -> Decimal:
   80 |         return self.acquisition_hours + self.delivery_hours + self.support_hours
   81 |
   82 |     @property
   83 |     def payment_fee(self) -> Decimal:
   84 |         return (self.price * self.fee_rate + self.fee_fixed).quantize(CENT, rounding=ROUND_HALF_UP)
   85 |
   86 |     @property
   87 |     def reserve(self) -> Decimal:
   88 |         return (self.price * self.reserve_rate).quantize(CENT, rounding=ROUND_HALF_UP)
   89 |
   90 |     @property
   91 |     def contribution(self) -> Decimal:
   92 |         return self.price - self.payment_fee - self.variable_cost - self.reserve
   93 |
   94 |
   95 | def evaluate_quote(q: Quote) -> dict[str, Any]:
   96 |     labor = q.attention_hours * q.hourly_value
   97 |     floor = ((q.variable_cost + q.fee_fixed + labor) /
   98 |              (Decimal(1) - q.fee_rate - q.reserve_rate)).quantize(CENT, rounding=ROUND_CEILING)
   99 |     return {
  100 |         "status": "SCENARIO_NOT_ACTUAL", "currency": q.currency,
  101 |         "price": money(q.price), "payment_fee": money(q.payment_fee),
  102 |         "reserve": money(q.reserve), "variable_cost": money(q.variable_cost),
  103 |         "contribution_after_reserve": money(q.contribution),
  104 |         "attention_hours": str(q.attention_hours),
  105 |         "contribution_per_attention_hour": money(q.contribution / q.attention_hours),
  106 |         "imputed_labor": money(labor),
  107 |         "surplus_before_fixed_and_tax": money(q.contribution - labor),
  108 |         "indicative_price_floor_excluding_fixed_and_tax": money(floor),
  109 |         "warnings": [
  110 |             "No tax, AHV, benefits offset, FX, payout verification or SLA estimate.",
  111 |             "Reserve is a scenario cash buffer, not an observed refund probability.",
  112 |             "All acquisition, revision and support time must be supplied by the caller.",
  113 |         ],
  114 |     }
  115 |
  116 |
  117 | def scenario(q: Quote, *, jobs: int, months_billed: int, fixed_monthly: Any,
  118 |              setup_cash: Any, setup_hours: Any, costs_currency: str) -> dict[str, Any]:
  119 |     jobs = integer(jobs, "jobs")
  120 |     months_billed = integer(months_billed, "months_billed", 1)
  121 |     if currency(costs_currency) != q.currency:
  122 |         raise ValueError("currency mismatch: no inferred FX conversion")
  123 |     fixed = decimal(fixed_monthly, "fixed_monthly") * months_billed
  124 |     setup = decimal(setup_cash, "setup_cash")
  125 |     hours = q.attention_hours * jobs + decimal(setup_hours, "setup_hours")
  126 |     operating = q.contribution * jobs - fixed - setup
  127 |     return {
  128 |         "status": "SCENARIO_NOT_FORECAST", "currency": q.currency,
  129 |         "jobs_assumed": jobs, "months_billed": months_billed,
  130 |         "revenue_assumed": money(q.price * jobs),
  131 |         "operating_proxy_after_reserve": money(operating),
  132 |         "attention_hours_including_setup": str(hours),
  133 |         "imputed_labor": money(hours * q.hourly_value),
  134 |         "economic_surplus_before_tax": money(operating - hours * q.hourly_value),
  135 |         "operating_proxy_per_attention_hour": money(operating / hours) if hours else None,
  136 |         "settled_cash": "NOT_VERIFIED", "paid_customer_count": "NOT_VERIFIED",
  137 |     }
  138 |
  139 |
  140 | def freshness(record: Mapping[str, Any], as_of: date) -> dict[str, Any]:
  141 |     """TTL is our review policy, not a publisher guarantee. No online fetch occurs."""
  142 |     if not isinstance(record, Mapping) or not isinstance(as_of, date):
  143 |         raise ValueError("expected evidence object and date")
  144 |     try:
  145 |         checked = date.fromisoformat(record["checked_on"])
  146 |         ttl = integer(record["review_after_days"], "review_after_days")
  147 |         until = date.fromisoformat(record["valid_until"]) if record.get("valid_until") else None
  148 |     except (KeyError, TypeError, ValueError):
  149 |         raise ValueError("evidence: invalid or missing dates/TTL") from None
  150 |     if record.get("access_method") in {"reference_fetch_incomplete", "unverified_navigation_candidate"}:
  151 |         status = "REFERENCE_ONLY"
  152 |     elif checked > as_of:
  153 |         status = "FUTURE_CHECK_REJECTED"
  154 |     elif until and as_of > until:
  155 |         status = "EXPIRED"
  156 |     elif (as_of - checked).days >= ttl:
  157 |         status = "REVIEW_REQUIRED"
  158 |     else:
  159 |         status = "WITHIN_REVIEW_WINDOW_NOT_GUARANTEED"
  160 |     return {"source_id": record.get("id", "UNKNOWN"), "as_of": as_of.isoformat(),
  161 |             "status": status, "age_days": (as_of - checked).days, "network_used": False}
  162 |
  163 |
  164 | LOCAL_ACTIONS = frozenset({"evaluate_quote", "rank_opportunity", "validate_fixture", "draft_local_report"})
  165 | EXTERNAL_ACTIONS = frozenset({"send_email", "submit_proposal", "publish_site", "git_push", "issue_invoice",
  166 |     "charge_customer", "refund", "external_model_call", "create_account", "buy_subscription",
  167 |     "upload_customer_data", "change_production", "post_social", "change_budget"})
  168 | FORBIDDEN_ACTIONS = frozenset({"scrape_upwork", "fake_review", "steal_session_cookie", "bypass_captcha",
  169 |                               "fabricate_payment", "force_push", "auto_raise_budget"})
  170 |
  171 |
  172 | def plan_action(request: Mapping[str, Any]) -> dict[str, Any]:
  173 |     """An advisory report only. It cannot authorize or execute any action."""
  174 |     if not isinstance(request, Mapping):
  175 |         raise ValueError("action request must be an object")
  176 |     action = request.get("action")
  177 |     if not isinstance(action, str):
  178 |         raise ValueError("action must be a string")
  179 |     cost = decimal(request.get("estimated_cost", "0"), "estimated_cost")
  180 |     cur = currency(request.get("currency", "CHF"))
  181 |     if action in FORBIDDEN_ACTIONS:
  182 |         decision = "DENY_POLICY"
  183 |     elif action not in LOCAL_ACTIONS | EXTERNAL_ACTIONS:
  184 |         decision = "DENY_UNKNOWN_ACTION"
  185 |     elif cost > 0:
  186 |         decision = "HOLD_ZERO_BUDGET"
  187 |     elif action in EXTERNAL_ACTIONS:
  188 |         decision = "NEEDS_HUMAN_APPROVAL_AND_TRUSTED_EXECUTOR"
  189 |     else:
  190 |         decision = "ALLOW_LOCAL_DRAFT_ONLY"
  191 |     return {"status": "ADVISORY_ONLY_NOT_AUTHORIZATION", "action": action, "decision": decision,
  192 |             "currency": cur, "estimated_cost": money(cost), "paid_cap": "0.00",
  193 |             "executed": False, "approval_flags_from_payload_ignored": True}
  194 |
  195 |
  196 | DEFAULT_WEIGHTS = {"first_payment_speed": 25, "repeatability": 20, "skill_fit": 20,
  197 |                    "low_risk": 15, "low_attention": 20}
  198 |
  199 |
  200 | def rank_opportunity(scores: Mapping[str, Any], *, hard_gate_clear: bool = False) -> dict[str, Any]:
  201 |     if not isinstance(scores, Mapping) or set(scores) != set(DEFAULT_WEIGHTS):
  202 |         raise ValueError("scores must have exactly the five documented criteria")
  203 |     if type(hard_gate_clear) is not bool:
  204 |         raise ValueError("hard_gate_clear must be a boolean")
  205 |     for key, value in scores.items():
  206 |         if type(value) is not int or not 1 <= value <= 5:
  207 |             raise ValueError(f"{key}: expected integer 1..5")
  208 |     total = sum(scores[k] * weight for k, weight in DEFAULT_WEIGHTS.items()) / 5
  209 |     return {"subjective_score_0_100": total, "status": "SUBJECTIVE_PRIOR_NOT_PROBABILITY",
  210 |             "eligible_for_human_review": hard_gate_clear, "permission_to_execute": False,
  211 |             "warning": "Score never overrides policy, rights, data, cost or payment gates."}
````
