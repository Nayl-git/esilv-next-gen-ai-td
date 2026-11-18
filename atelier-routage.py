#!/usr/bin/env python3
"""TD 2 and TD 3: read the decisions of a routing rule, then adapt it to your own.

Synthetic resources, no API call, no key.

Costs are fictional USD excluding tax per request, with a fixed token envelope.
Capability levels 1/2/3 describe eligibility for this exercise, not model IQ.
Quota availability is supplied as a scenario, not measured from a provider.

Adapted by sub-group DIA2-1 (TD 2, Pair C). What changed compared with the kit:
- RESOURCES are the five TD 1 models of our portfolio sheet, plus one paid route.
  Their level is derived from the TD 1 results below (TD1_RATES, TD1_CELLS).
- The request carries a question family and a use (dashboard, customer, payout)
  instead of a bare difficulty and a high_impact flag.
- The check depends on the family, the use and the TD 1 accuracy of the chosen
  model (see checks_for). "none" is only allowed for an internal dashboard and a
  family where the chosen model was 100 % correct in TD 1 and the sample is at
  least four questions.
- Among already included capacity, the cheapest model by reference price comes
  first (see PRICE_ENVELOPE).
- Every reason cites the TD 1 cells that justify the choice.
The four branches of choose (included, defer, paid, abstain) are unchanged.
"""
import argparse
import json

# ---- TD 1 evidence (source: traces-td1.csv, last attempt of each cell) ----
TD1_CELLS = {
    "F1": ["C01", "C04", "C05", "C06", "C07", "C20"],     # period
    "F2": ["C02", "C08", "C09", "C11"],                    # completed age at a date
    "F2b": ["C10"],                                        # completed age at the order
    "F3": ["C03", "C12", "C13", "C14"],                    # product list
    "F4": ["C15", "C16", "C17", "C18", "C19"],             # combinations
}
# Difficulty = capability level a resource needs for the family (derived from TD 1:
# F2 is the only family where a model other than gpt-oss-120b erred on a plain age question).
FAMILY_DIFFICULTY = {"F1": 1, "F3": 1, "F4": 2, "F2b": 2, "F2": 3}
FAMILY_LABEL = {"F1": "period", "F2": "age at a date", "F2b": "age at the order",
                "F3": "product list", "F4": "combinations"}
TD1_RATES = {   # model -> family -> (correct, cases)
    "gpt-oss-120b": {"F1": (6, 6), "F2": (4, 4), "F2b": (1, 1), "F3": (4, 4), "F4": (5, 5)},
    "gpt-oss-20b": {"F1": (6, 6), "F2": (2, 4), "F2b": (1, 1), "F3": (4, 4), "F4": (5, 5)},
    "qwen3.8-27b": {"F1": (6, 6), "F2": (3, 4), "F2b": (0, 1), "F3": (4, 4), "F4": (1, 5)},
    "dots-3-note": {"F1": (6, 6), "F2": (2, 4), "F2b": (0, 1), "F3": (4, 4), "F4": (2, 5)},
    "north-mini-code": {"F1": (6, 6), "F2": (0, 4), "F2b": (0, 1), "F3": (4, 4), "F4": (1, 5)},
}

# Reference prices of the paid route of the same model (USD per million tokens, input, output;
# five-model-summary-en.csv). None = no documented paid route.
PRICES = {
    "gpt-oss-120b": (0.15, 0.60),
    "gpt-oss-20b": (0.075, 0.30),
    "qwen3.8-27b": (0.80, 4.00),
    "dots-3-note": None,
    "north-mini-code": None,
}
PRICE_ENVELOPE = (1000, 300)   # assumed tokens per request: input, output (TD 1 means: about 600 in, 150-260 out)


def request_cost(model):
    price = PRICES[model]
    if price is None:
        return None
    return round((PRICE_ENVELOPE[0] * price[0] + PRICE_ENVELOPE[1] * price[1]) / 1e6, 6)


def resource(rid, model, level, access, cash=0.0, allocation=0.0):
    return {"id": rid, "model": model, "level": level, "access": access, "available": True,
            "cash": cash, "allocation": allocation, "reset_minutes": None}


RESOURCES = [
    resource("groq/gpt-oss-120b:free-plan", "gpt-oss-120b", 3, "free-groq"),
    resource("groq/gpt-oss-20b:free-plan", "gpt-oss-20b", 2, "free-groq"),
    resource("groq/qwen3.8-27b:free-plan", "qwen3.8-27b", 1, "free-groq"),
    resource("openrouter/dots-3-note:free", "dots-3-note", 1, "free-openrouter"),
    resource("openrouter/north-mini-code:free", "north-mini-code", 1, "free-openrouter"),
    resource("openrouter/gpt-oss-120b:paid", "gpt-oss-120b", 3, "tokens",
             cash=request_cost("gpt-oss-120b"), allocation=request_cost("gpt-oss-120b")),
]


def evidence(r, family):
    """The TD 1 cells that justify using resource r for a family."""
    if r is None or family not in TD1_CELLS:
        return "no TD 1 evidence for this family"
    ok, n = TD1_RATES[r["model"]][family]
    return f"{r['model']} {family} {ok}/{n} ({','.join(TD1_CELLS[family])})"


# Declared 2-of-3 panel (k = 2). On the TD 1 traces it gives 20 correct, 0 abstention, 0 wrong
# consensus. The panel never holds qwen3.8-27b and dots-3-note together: both returned 0 on C09
# (reference 487980), so a panel with both and gpt-oss-120b validates that wrong value.
PANEL = "2-of-3 quorum on {gpt-oss-120b, gpt-oss-20b, qwen3.8-27b}"
ZERO_CHECK = "population check before accepting a 0"


def checks_for(request, r):
    """Check required for a family and a use, given the TD 1 accuracy of the chosen model.

    A request that is not run has no check to describe.
    """
    if r is None:
        return "not applicable (request not run)"
    family, use = request["family"], request["use"]
    perfect = False
    if family in TD1_CELLS:
        ok, n = TD1_RATES[r["model"]][family]
        perfect = ok == n and n >= 4
    age = family in ("F2", "F2b")
    if use == "payout":
        # Same control for every family. The lab reference does not exist in production, so the
        # control is a model-free recomputation (a parameterised query per family; implemented
        # for F2 only, see td2/wrong_consensus.py) followed by a human review.
        return "3-of-5 quorum, then deterministic recomputation, then human review"
    if use == "customer":
        return PANEL + ("; " + ZERO_CHECK if age else "")
    if perfect and family in ("F1", "F3"):          # dashboard, 100 % on at least 4 cells
        return "none"
    if family == "F2":
        # read-only execution does not catch a wrong 0 (C09), so the zero check is part of it
        return "read-only execution and " + ZERO_CHECK
    return PANEL + ("; " + ZERO_CHECK if age else "")


def choose(request, resources):
    """A deterministic routing policy, with a reason the user can inspect.

    Already paid capacity is preferred before new spending. A nonurgent request
    can wait for included capacity. At wake-up, availability must be measured
    again: reaching a reset time does not prove that capacity is available.
    """
    family = request["family"]
    difficulty = FAMILY_DIFFICULTY.get(family, 4)   # 4 = capability never measured
    eligible = [r for r in resources if r["level"] >= difficulty]
    included = [r for r in eligible if r["available"] and r["cash"] == 0]
    if included:
        # cheapest reference price first, models without a documented paid route last
        def order(r):
            c = request_cost(r["model"])
            return (r["allocation"], c is None, c or 0.0, r["level"], r["id"])
        chosen = min(included, key=order)
        return {"action": "run", "resource": chosen["id"], "cash": 0,
                "checks": checks_for(request, chosen),
                "reason": "eligible included capacity | " + evidence(chosen, family)}
    waiting = [r for r in eligible if not r["available"] and r["cash"] == 0
               and r["reset_minutes"] is not None
               and 0 < r["reset_minutes"] <= request["deadline_minutes"]]
    if waiting and request["can_wait"]:
        chosen = min(waiting, key=lambda r: r["reset_minutes"])
        return {"action": "defer", "resource": chosen["id"], "cash": 0,
                "checks": checks_for(request, chosen),
                "reason": "recheck availability at wake-up | " + evidence(chosen, family),
                "wake_in_minutes": chosen["reset_minutes"]}
    paid = [r for r in eligible if r["available"] and r["cash"] <= request["budget"]]
    if paid:
        chosen = min(paid, key=lambda r: (r["cash"], r["allocation"], r["id"]))
        return {"action": "run", "resource": chosen["id"], "cash": chosen["cash"],
                "checks": checks_for(request, chosen),
                "reason": "available route within the authorised budget | " + evidence(chosen, family)}
    return {"action": "abstain", "resource": None, "cash": 0,
            "checks": checks_for(request, None),
            "reason": "no eligible resource within deadline and budget | "
                      + ("family never evaluated in TD 1" if family not in TD1_CELLS
                         else f"{family} needs level {difficulty}")}


def scenarios():
    base = {"family": "F1", "use": "dashboard", "can_wait": True,
            "deadline_minutes": 120, "budget": 0.001}
    # Groq free plan exhausted (daily or per-minute limit reached), refills in 60 minutes (assumed)
    exhausted = [dict(r, available=False, reset_minutes=60) if r["access"] == "free-groq" else dict(r)
                 for r in RESOURCES]
    return [
        ("simple", base, RESOURCES),
        ("complex", {**base, "family": "F2"}, RESOURCES),
        ("deferrable", {**base, "family": "F2"}, exhausted),
        ("urgent", {**base, "family": "F2", "can_wait": False, "deadline_minutes": 5}, exhausted),
        ("budget exhausted", {**base, "family": "F2", "can_wait": False, "budget": 0}, exhausted),
        ("high impact", {**base, "family": "F2", "use": "payout"}, RESOURCES),
        ("unknown capability", {**base, "family": "F5"}, RESOURCES),
        ("customer figure", {**base, "use": "customer"}, RESOURCES),
        ("combination dashboard", {**base, "family": "F4"}, RESOURCES),
    ]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", help="show only the named scenario")
    args = parser.parse_args()
    found = False
    for name, request, resources in scenarios():
        if args.scenario and name != args.scenario:
            continue
        found = True
        print(json.dumps({"scenario": name, "nature": "simulation", "request": request,
                          "result": choose(request, resources)}))
    if not found:
        parser.error("unknown scenario")


if __name__ == "__main__":
    main()
