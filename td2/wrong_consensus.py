#!/usr/bin/env python3
"""TD 2, Step 2 (Pair B): the wrong consensus, from the stored TD 1 traces.

No network, no key. Read-only on data/boutique.sqlite.

    python td2/wrong_consensus.py            # every section, run from the repository root
    python td2/wrong_consensus.py --section scan|quorum|panels|cause|check|demo

Sections
  scan    every question where >= 2 of the five TD 1 models return the same WRONG value
  quorum  what the declared quorums return on C09 (fixed 2-of-3 panel, 3-of-5)
  panels  every distinct-family 2-of-3 panel on the twenty questions: wrong consensus count
  cause   C09 root cause: the stored SQL of each agreeing model, decomposed condition by condition
  check   the independent check (population check) on the twenty questions
  demo    supplied synthetic case DEMO-VOTE (toy table, not shop data)

The vote below is a LOCAL copy of the TD 2 contract (Orchestrateur.vote_k_sur_n),
used so this analysis does not depend on Pair A's push. Once Pair A's method is in
skeleton-multi-llm-en.py, `python atelier-vote.py --traces traces-td1.csv --case C09`
must give the same fixed-panel decision as the `quorum` section.
"""
import argparse
import csv
import itertools
import json
import sqlite3
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TRACES = ROOT / "traces-td1.csv"
REFERENCES = ROOT / "reference-td1.csv"
DB = ROOT / "data" / "boutique.sqlite"

# Model -> family. gpt-oss-120b and gpt-oss-20b are the same family (OpenAI gpt-oss):
# a panel holding both is not a panel of distinct families.
FAMILY = {
    "groq:openai/gpt-oss-120b": "openai-gpt-oss",
    "groq:openai/gpt-oss-20b": "openai-gpt-oss",
    "openrouter:cohere/north-mini-code:free": "cohere",
    "groq:qwen/qwen3.8-27b": "qwen",
    "openrouter:dots-studio/dots-3-note-preview:free": "dots",
}
MODELS = list(FAMILY)
FIXED_PANEL = ["groq:openai/gpt-oss-120b", "openrouter:cohere/north-mini-code:free", "groq:qwen/qwen3.8-27b"]


def vote_k_sur_n(proposals, k):
    """Local copy of the TD 2 contract. proposals: dicts with key, value (int|None), verdict."""
    n = len(proposals)
    if not (n // 2 < k <= n):
        raise ValueError(f"k={k} is not a strict majority of n={n}")
    keys = [p["key"] for p in proposals]
    if len(keys) != len(set(keys)):
        raise ValueError("duplicate provider:model in the panel")
    votes = Counter(p["value"] for p in proposals if p["verdict"] == "executed" and p["value"] is not None)
    if votes:
        value, count = votes.most_common(1)[0]
        if count >= k:
            return {"consensus": True, "value": value, "votes": count,
                    "models": [p["key"] for p in proposals if p["verdict"] == "executed" and p["value"] == value]}
    return {"consensus": False, "value": None, "votes": max(votes.values(), default=0), "models": []}


def load_last():
    """Last attempt per (model, case), real nature only, as atelier-vote.py does."""
    last = {}
    with TRACES.open(encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            if r["nature"] == "real":
                last[(f"{r['provider']}:{r['model_requested']}", r["case_id"])] = r
    return last


def load_refs():
    with REFERENCES.open(encoding="utf-8", newline="") as f:
        return {r["case_id"]: (int(r["revenue_cents"]), r["sql"]) for r in csv.DictReader(f)}


def proposal(last, key, case):
    r = last.get((key, case), {})
    ok = r.get("verdict") in {"correct", "incorrect"} and r.get("value") not in {None, ""}
    return {"key": key, "value": int(r["value"]) if ok else None,
            "verdict": "executed" if ok else "error", "cell_id": r.get("cell_id"),
            "trace_verdict": r.get("verdict", "missing")}


def db():
    return sqlite3.connect(f"file:{DB}?mode=ro", uri=True)


def scalar(con, sql):
    return con.execute(sql).fetchone()[0]


# ---------------------------------------------------------------- sections

def section_scan(last, refs):
    out = []
    for case in sorted(refs):
        ref = refs[case][0]
        props = [proposal(last, m, case) for m in MODELS]
        counts = Counter(p["value"] for p in props if p["value"] is not None and p["value"] != ref)
        for value, n in counts.items():
            if n >= 2:
                out.append({"case": case, "wrong_value": value, "reference": ref, "agreeing": n,
                            "models": [p["key"] for p in props if p["value"] == value],
                            "cells": [p["cell_id"] for p in props if p["value"] == value]})
    print(json.dumps({"section": "scan", "nature": "real (TD 1 traces)", "wrong_consensus_cases": out}, indent=1))


def section_quorum(last, refs, case="C09"):
    ref = refs[case][0]
    res = []
    for name, panel, k in [("fixed panel 2-of-3 (atelier-vote.py)", FIXED_PANEL, 2),
                           ("all five TD 1 models, 3-of-5", MODELS, 3),
                           ("counter-example panel 2-of-3 {gpt-oss-120b, qwen, dots}",
                            ["groq:openai/gpt-oss-120b", "groq:qwen/qwen3.8-27b",
                             "openrouter:dots-studio/dots-3-note-preview:free"], 2)]:
        props = [proposal(last, m, case) for m in panel]
        d = vote_k_sur_n(props, k)
        res.append({"quorum": name, "k": k, "n": len(panel),
                    "proposals": {p["key"]: p["value"] if p["verdict"] == "executed" else p["trace_verdict"] for p in props},
                    "decision": d, "reference": ref,
                    "outcome": ("abstention" if not d["consensus"]
                                else "correct consensus" if d["value"] == ref else "WRONG CONSENSUS")})
    print(json.dumps({"section": "quorum", "case": case, "nature": "real (TD 1 traces), vote decided before the reference is read",
                      "results": res}, indent=1))


def section_panels(last, refs):
    rows = []
    for panel in itertools.combinations(MODELS, 3):
        if len({FAMILY[m] for m in panel}) < 3:
            continue  # not three distinct families
        tally = Counter()
        wrong = []
        for case in sorted(refs):
            d = vote_k_sur_n([proposal(last, m, case) for m in panel], 2)
            if not d["consensus"]:
                tally["abstain"] += 1
            elif d["value"] == refs[case][0]:
                tally["correct"] += 1
            else:
                tally["wrong"] += 1
                wrong.append(f"{case}={d['value']}")
        rows.append({"panel": [m.split(":", 1)[1] for m in panel], "correct": tally["correct"],
                     "abstain": tally["abstain"], "wrong_consensus": tally["wrong"], "wrong_cases": wrong})
    print(json.dumps({"section": "panels", "nature": "real (TD 1 traces), 2-of-3, distinct families only",
                      "panels": rows}, indent=1))


C09_REF_WHERE = ("(CAST(strftime('%Y','2026-09-26') AS INTEGER) - CAST(strftime('%Y',c.birth_date) AS INTEGER)"
                 " - (strftime('%m-%d','2026-09-26') < strftime('%m-%d',c.birth_date))) = 25")
FROM = ("FROM orders o JOIN customers c ON o.customer_id = c.customer_id "
        "JOIN product p ON o.product_id = p.product_id")


def section_cause(con):
    def lines(where):
        return scalar(con, f"SELECT COUNT(*) {FROM} WHERE {where}")

    def custs(where):
        return scalar(con, f"SELECT COUNT(DISTINCT c.customer_id) {FROM} WHERE {where}")

    qwen = [  # stored SQL of groq:qwen/qwen3.8-27b:C09, cut into its three conditions
        ("Q1 (o.date year - birth year) = 25", "(strftime('%Y', o.date) - strftime('%Y', c.birth_date)) = 25"),
        ("Q2 order month-day >= birth month-day", "(strftime('%m-%d', o.date) >= strftime('%m-%d', c.birth_date))"),
        ("Q3 order month-day < month-day of birth_date + 26 years",
         "(strftime('%m-%d', o.date) < strftime('%m-%d', date(c.birth_date, '+26 years')))"),
    ]
    dots = [  # stored SQL of openrouter:dots-studio/dots-3-note-preview:free:C09
        ("D1 birth year + 25 = 2026", "CAST(SUBSTR(c.birth_date, 1, 4) AS INTEGER) + 25 = 2026"),
        ("D2 birth month-day = 09-26", "SUBSTR(c.birth_date, 6, 2) = '09' AND SUBSTR(c.birth_date, 9, 2) = '26'"),
        ("D3 order placed on 2026-09-26", "o.date >= '2026-09-26 00:00:00' AND o.date < '2026-09-27 00:00:00'"),
    ]
    out = {"section": "cause", "case": "C09", "nature": "real (TD 1 SQL replayed read-only on boutique.sqlite)",
           "reference": {"where": C09_REF_WHERE, "order_lines": lines(C09_REF_WHERE),
                         "customers": custs(C09_REF_WHERE),
                         "revenue_cents": scalar(con, f"SELECT COALESCE(SUM(o.quantity_product*p.price),0) {FROM} WHERE {C09_REF_WHERE}")}}
    for name, conds in [("qwen3.8-27b", qwen), ("dots-3-note", dots)]:
        steps, acc = [], []
        for label, cond in conds:
            acc.append(cond)
            w = " AND ".join(f"({x})" for x in acc)
            steps.append({"cumulative": label, "order_lines": lines(w), "customers": custs(w),
                          "ref_lines_kept": lines(f"({w}) AND ({C09_REF_WHERE})")})
        out[name] = steps
    # Q2 AND Q3 is a contradiction: the month-day of birth_date + 26 years is the birth month-day.
    out["qwen_proof"] = {
        "customers_where_md(birth+26y) != md(birth)": scalar(
            con, "SELECT COUNT(*) FROM customers WHERE strftime('%m-%d', date(birth_date,'+26 years')) <> strftime('%m-%d', birth_date)"),
        "order_lines_where_Q2_and_Q3": lines(f"({qwen[1][1]}) AND ({qwen[2][1]})"),
    }
    out["dots_proof"] = {
        "customers_born_2001-09-26": scalar(con, "SELECT COUNT(*) FROM customers WHERE birth_date = '2001-09-26'"),
        "orders_on_2026-09-26": scalar(con, "SELECT COUNT(*) FROM orders WHERE o_date >= '2026-09-26' AND o_date < '2026-09-27'"
                                       .replace("o_date", "date")),
        "max_order_date": scalar(con, "SELECT MAX(date) FROM orders"),
    }
    # Delta query: reference lines missed by each wrong query (all of them, since both return 0).
    out["delta_reference_minus_wrong"] = {
        "sql": ("SELECT o.rowid FROM orders o JOIN customers c ON ... WHERE <reference> "
                "EXCEPT SELECT o.rowid ... WHERE <wrong>"),
        "qwen_missing_lines": scalar(con, f"SELECT COUNT(*) FROM (SELECT o.rowid {FROM} WHERE {C09_REF_WHERE} "
                                          f"EXCEPT SELECT o.rowid {FROM} WHERE {' AND '.join(f'({c})' for _, c in qwen)})"),
        "dots_missing_lines": scalar(con, f"SELECT COUNT(*) FROM (SELECT o.rowid {FROM} WHERE {C09_REF_WHERE} "
                                          f"EXCEPT SELECT o.rowid {FROM} WHERE {' AND '.join(f'({c})' for _, c in dots)})"),
    }
    print(json.dumps(out, indent=1))


def section_check(con, last, refs):
    """Independent check: population check, computed without any model output.

    The model returns a SUM. The check recomputes, with a second formulation of
    the age rule (a date() window, not the strftime year difference of the
    reference), the number of customers and order lines the question targets.
    A returned 0 is flagged when that population is not empty. 0 is a legitimate
    answer (C06, C14), so the check tests the population, not the value.
    """
    window = {  # second, independent formulation for the age-at-a-date family
        "C02": "2026-09-25", "C08": "2026-09-24", "C09": "2026-09-26", "C11": "2026-12-01",
    }
    rows = []
    for case in sorted(refs):
        ref, ref_sql = refs[case]
        # population of the reference query: same FROM/WHERE, COUNT(*) instead of SUM
        body = ref_sql.split("FROM", 1)[1].rstrip().rstrip(";")
        pop = scalar(con, f"SELECT COUNT(*) FROM {body}")
        alt = None
        if case in window:
            d = window[case]
            alt = scalar(con, f"SELECT COUNT(*) {FROM} WHERE c.birth_date > date('{d}','-26 years') "
                              f"AND c.birth_date <= date('{d}','-25 years')")
        zeros = [m.split(":", 1)[1] for m in MODELS if proposal(last, m, case)["value"] == 0]
        rows.append({"case": case, "reference": ref, "reference_population_lines": pop,
                     "independent_window_lines": alt, "models_returning_0": zeros,
                     "zero_flagged": bool(zeros) and pop > 0})
    print(json.dumps({"section": "check", "nature": "real (read-only on boutique.sqlite)", "rows": rows}, indent=1))


def section_demo():
    con = sqlite3.connect(":memory:")
    con.execute("CREATE TABLE sales (sale_date TEXT, amount_cents INTEGER)")
    con.execute("INSERT INTO sales VALUES ('2026-01-01', 100)")
    strict = "SELECT COALESCE(SUM(amount_cents), 0) FROM sales WHERE sale_date > '2026-01-01' AND sale_date < '2026-01-02'"
    incl = "SELECT COALESCE(SUM(amount_cents), 0) FROM sales WHERE sale_date >= '2026-01-01' AND sale_date < '2026-01-02'"
    v_strict, v_incl = scalar(con, strict), scalar(con, incl)
    props = [{"key": "demo:A", "value": v_strict, "verdict": "executed"},
             {"key": "demo:B", "value": v_strict, "verdict": "executed"},
             {"key": "demo:C", "value": v_incl, "verdict": "executed"}]
    print(json.dumps({"section": "demo", "case": "DEMO-VOTE", "nature": "synthetic (supplied teaching example, not model output, not shop data)",
                      "toy_table": [["2026-01-01", 100]], "period": "[2026-01-01, 2026-01-02)",
                      "strict_variant": {"sql": strict, "value": v_strict},
                      "inclusive_variant": {"sql": incl, "value": v_incl},
                      "decision_2_of_3": vote_k_sur_n(props, 2), "reference": 100}, indent=1))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--section", choices=["scan", "quorum", "panels", "cause", "check", "demo"])
    a = ap.parse_args()
    last, refs = load_last(), load_refs()
    con = db()
    todo = [a.section] if a.section else ["scan", "quorum", "panels", "cause", "check", "demo"]
    for s in todo:
        {"scan": lambda: section_scan(last, refs), "quorum": lambda: section_quorum(last, refs),
         "panels": lambda: section_panels(last, refs), "cause": lambda: section_cause(con),
         "check": lambda: section_check(con, last, refs), "demo": section_demo}[s]()


if __name__ == "__main__":
    main()
