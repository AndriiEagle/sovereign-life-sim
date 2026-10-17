"""Pure, bounded economics and planning helpers. All money stays in one currency."""
from __future__ import annotations
from dataclasses import dataclass, fields
from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP, ROUND_CEILING
from typing import Any, Mapping

CENT = Decimal("0.01")
CURRENCIES = frozenset({"CHF", "USD", "EUR", "GBP"})
MAX_VALUE = Decimal("1000000000")


def decimal(value: Any, name: str) -> Decimal:
    """Accept explicit decimal inputs, rejecting booleans and non-finite values."""
    if isinstance(value, bool) or not isinstance(value, (str, int, float, Decimal)):
        raise ValueError(f"{name}: expected a finite non-negative number")
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise ValueError(f"{name}: invalid decimal") from None
    if not number.is_finite() or number < 0 or number > MAX_VALUE:
        raise ValueError(f"{name}: outside supported non-negative range")
    return number


def currency(value: Any) -> str:
    if not isinstance(value, str) or value not in CURRENCIES:
        raise ValueError("currency: use exact CHF, USD, EUR or GBP; no inferred FX")
    return value


def integer(value: Any, name: str, minimum: int = 0) -> int:
    if type(value) is not int or value < minimum or value > 1000000:
        raise ValueError(f"{name}: expected bounded integer >= {minimum}")
    return value


def money(value: Decimal) -> str:
    return str(value.quantize(CENT, rounding=ROUND_HALF_UP))


@dataclass(frozen=True)
class Quote:
    currency: str
    price: Decimal
    fee_rate: Decimal
    fee_fixed: Decimal
    variable_cost: Decimal
    reserve_rate: Decimal
    acquisition_hours: Decimal
    delivery_hours: Decimal
    support_hours: Decimal
    hourly_value: Decimal

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "Quote":
        if not isinstance(data, Mapping):
            raise ValueError("quote: expected object")
        required = {f.name for f in fields(cls)}
        if set(data) != required:
            missing = sorted(required - set(data))
            extra = sorted(set(data) - required)
            raise ValueError(f"quote keys: missing={missing}; extra={extra}")
        numbers = {key: decimal(data[key], key) for key in required - {"currency"}}
        result = cls(currency(data["currency"]), **numbers)
        if result.price <= 0:
            raise ValueError("price must be positive")
        if result.fee_rate + result.reserve_rate >= 1:
            raise ValueError("fee_rate + reserve_rate must be below 1")
        if result.attention_hours <= 0:
            raise ValueError("total attention hours must be positive")
        # Round monetary inputs at the boundary, not arbitrary intermediate hours/rates.
        for key in ("price", "fee_fixed", "variable_cost"):
            if numbers[key] != numbers[key].quantize(CENT):
                raise ValueError(f"{key}: use at most two decimal places")
        return result

    @property
    def attention_hours(self) -> Decimal:
        return self.acquisition_hours + self.delivery_hours + self.support_hours

    @property
    def payment_fee(self) -> Decimal:
        return (self.price * self.fee_rate + self.fee_fixed).quantize(CENT, rounding=ROUND_HALF_UP)

    @property
    def reserve(self) -> Decimal:
        return (self.price * self.reserve_rate).quantize(CENT, rounding=ROUND_HALF_UP)

    @property
    def contribution(self) -> Decimal:
        return self.price - self.payment_fee - self.variable_cost - self.reserve


def evaluate_quote(q: Quote) -> dict[str, Any]:
    labor = q.attention_hours * q.hourly_value
    floor = ((q.variable_cost + q.fee_fixed + labor) /
             (Decimal(1) - q.fee_rate - q.reserve_rate)).quantize(CENT, rounding=ROUND_CEILING)
    return {
        "status": "SCENARIO_NOT_ACTUAL", "currency": q.currency,
        "price": money(q.price), "payment_fee": money(q.payment_fee),
        "reserve": money(q.reserve), "variable_cost": money(q.variable_cost),
        "contribution_after_reserve": money(q.contribution),
        "attention_hours": str(q.attention_hours),
        "contribution_per_attention_hour": money(q.contribution / q.attention_hours),
        "imputed_labor": money(labor),
        "surplus_before_fixed_and_tax": money(q.contribution - labor),
        "indicative_price_floor_excluding_fixed_and_tax": money(floor),
        "warnings": [
            "No tax, AHV, benefits offset, FX, payout verification or SLA estimate.",
            "Reserve is a scenario cash buffer, not an observed refund probability.",
            "All acquisition, revision and support time must be supplied by the caller.",
        ],
    }


def scenario(q: Quote, *, jobs: int, months_billed: int, fixed_monthly: Any,
             setup_cash: Any, setup_hours: Any, costs_currency: str) -> dict[str, Any]:
    jobs = integer(jobs, "jobs")
    months_billed = integer(months_billed, "months_billed", 1)
    if currency(costs_currency) != q.currency:
        raise ValueError("currency mismatch: no inferred FX conversion")
    fixed = decimal(fixed_monthly, "fixed_monthly") * months_billed
    setup = decimal(setup_cash, "setup_cash")
    hours = q.attention_hours * jobs + decimal(setup_hours, "setup_hours")
    operating = q.contribution * jobs - fixed - setup
    return {
        "status": "SCENARIO_NOT_FORECAST", "currency": q.currency,
        "jobs_assumed": jobs, "months_billed": months_billed,
        "revenue_assumed": money(q.price * jobs),
        "operating_proxy_after_reserve": money(operating),
        "attention_hours_including_setup": str(hours),
        "imputed_labor": money(hours * q.hourly_value),
        "economic_surplus_before_tax": money(operating - hours * q.hourly_value),
        "operating_proxy_per_attention_hour": money(operating / hours) if hours else None,
        "settled_cash": "NOT_VERIFIED", "paid_customer_count": "NOT_VERIFIED",
    }


def freshness(record: Mapping[str, Any], as_of: date) -> dict[str, Any]:
    """TTL is our review policy, not a publisher guarantee. No online fetch occurs."""
    if not isinstance(record, Mapping) or not isinstance(as_of, date):
        raise ValueError("expected evidence object and date")
    try:
        checked = date.fromisoformat(record["checked_on"])
        ttl = integer(record["review_after_days"], "review_after_days")
        until = date.fromisoformat(record["valid_until"]) if record.get("valid_until") else None
    except (KeyError, TypeError, ValueError):
        raise ValueError("evidence: invalid or missing dates/TTL") from None
    if record.get("access_method") in {"reference_fetch_incomplete", "unverified_navigation_candidate"}:
        status = "REFERENCE_ONLY"
    elif checked > as_of:
        status = "FUTURE_CHECK_REJECTED"
    elif until and as_of > until:
        status = "EXPIRED"
    elif (as_of - checked).days >= ttl:
        status = "REVIEW_REQUIRED"
    else:
        status = "WITHIN_REVIEW_WINDOW_NOT_GUARANTEED"
    return {"source_id": record.get("id", "UNKNOWN"), "as_of": as_of.isoformat(),
            "status": status, "age_days": (as_of - checked).days, "network_used": False}


LOCAL_ACTIONS = frozenset({"evaluate_quote", "rank_opportunity", "validate_fixture", "draft_local_report"})
EXTERNAL_ACTIONS = frozenset({"send_email", "submit_proposal", "publish_site", "git_push", "issue_invoice",
    "charge_customer", "refund", "external_model_call", "create_account", "buy_subscription",
    "upload_customer_data", "change_production", "post_social", "change_budget"})
FORBIDDEN_ACTIONS = frozenset({"scrape_upwork", "fake_review", "steal_session_cookie", "bypass_captcha",
                              "fabricate_payment", "force_push", "auto_raise_budget"})


def plan_action(request: Mapping[str, Any]) -> dict[str, Any]:
    """An advisory report only. It cannot authorize or execute any action."""
    if not isinstance(request, Mapping):
        raise ValueError("action request must be an object")
    action = request.get("action")
    if not isinstance(action, str):
        raise ValueError("action must be a string")
    cost = decimal(request.get("estimated_cost", "0"), "estimated_cost")
    cur = currency(request.get("currency", "CHF"))
    if action in FORBIDDEN_ACTIONS:
        decision = "DENY_POLICY"
    elif action not in LOCAL_ACTIONS | EXTERNAL_ACTIONS:
        decision = "DENY_UNKNOWN_ACTION"
    elif cost > 0:
        decision = "HOLD_ZERO_BUDGET"
    elif action in EXTERNAL_ACTIONS:
        decision = "NEEDS_HUMAN_APPROVAL_AND_TRUSTED_EXECUTOR"
    else:
        decision = "ALLOW_LOCAL_DRAFT_ONLY"
    return {"status": "ADVISORY_ONLY_NOT_AUTHORIZATION", "action": action, "decision": decision,
            "currency": cur, "estimated_cost": money(cost), "paid_cap": "0.00",
            "executed": False, "approval_flags_from_payload_ignored": True}


DEFAULT_WEIGHTS = {"first_payment_speed": 25, "repeatability": 20, "skill_fit": 20,
                   "low_risk": 15, "low_attention": 20}


def rank_opportunity(scores: Mapping[str, Any], *, hard_gate_clear: bool = False) -> dict[str, Any]:
    if not isinstance(scores, Mapping) or set(scores) != set(DEFAULT_WEIGHTS):
        raise ValueError("scores must have exactly the five documented criteria")
    if type(hard_gate_clear) is not bool:
        raise ValueError("hard_gate_clear must be a boolean")
    for key, value in scores.items():
        if type(value) is not int or not 1 <= value <= 5:
            raise ValueError(f"{key}: expected integer 1..5")
    total = sum(scores[k] * weight for k, weight in DEFAULT_WEIGHTS.items()) / 5
    return {"subjective_score_0_100": total, "status": "SUBJECTIVE_PRIOR_NOT_PROBABILITY",
            "eligible_for_human_review": hard_gate_clear, "permission_to_execute": False,
            "warning": "Score never overrides policy, rights, data, cost or payment gates."}
