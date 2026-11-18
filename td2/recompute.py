#!/usr/bin/env python3
"""TD 2, Step 3 (Pair C): deterministic recomputation of a revenue figure, without any model.

A payout needs a control that exists in production, so it cannot lean on the
lab reference. This script is that control: a parameterised SQL query, written
once and shared by every question family, run read-only on the same database
with the parameters of the question. A figure given by a model is accepted only
if it equals the recomputed one.

The query is built from three optional filters, which give the five families:

    period    date >= start AND date < end        (closed on the left, open on the right)
    products  product_id IN (...)
    age       completed age 25, as a birth-date window: a customer is 25 on a day D
              when born in ]D - 26 years, D - 25 years]. The day D is the reference
              date of the question, or the date of each order ("at the time of the order").

    F1 period only            F3 products (with or without a period)
    F2 age at a date only     F2b age at the order only
    F4 any other combination

Where the values come from, and what this control is not:
- The parameters are written by hand below from the text of the twenty questions, and a
  consistency check compares them with `questions-td1.json`. In a service, the parameters must
  come from the structured request. If a model reads the question and produces them, the
  control is no longer model-free.
- The age window is a different formulation from the reference queries (strftime year
  difference). A third path, plain Python on the CSV files, recomputes every figure too.
- A free-text question outside the known families cannot be recomputed.
- Edge case not handled: a reference date or an order date of 29 February, where `date()`
  rolls a missing 29 February over to 1 March. No such date exists in the base.
- On the TD 1 traces (`--traces`), the recomputed value equals the lab reference, so the
  verdicts it gives are the verdicts of the lab: the point is that the same control works
  without the reference, on a parameterised query.

    python td2/recompute.py                      # the twenty questions: SQL, CSV path, reference
    python td2/recompute.py --verify C09 0       # accept or reject a model figure
    python td2/recompute.py --traces             # control applied to the 100 TD 1 cells
"""
import argparse
import csv
import json
import re
import sqlite3
import sys
from datetime import date
from pathlib import Path

KIT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from rates_by_family import FAMILIES, MODELS, final_results, short  # noqa: E402  (same folder)

AGE = 25
FROM = ("FROM orders o JOIN product p ON p.product_id = o.product_id "
        "JOIN customers c ON c.customer_id = o.customer_id")
MIDNIGHT = " 00:00:00"


def period(start, end):
    return (start + MIDNIGHT, end + MIDNIGHT)


# Parameters of the twenty questions, written from questions-td1.json.
# age: ("date", D) completed age on the day D, ("order", None) completed age on each order date.
PARAMS = {
    "C01": dict(period=period("2026-03-01", "2026-06-01")),
    "C02": dict(age=("date", "2026-09-25")),
    "C03": dict(period=period("2026-01-01", "2026-07-01"), products=("a", "b", "c")),
    "C04": dict(period=period("2026-01-01", "2026-10-01")),
    "C05": dict(period=period("2026-06-01", "2026-06-02")),
    "C06": dict(period=period("2025-01-01", "2026-01-01")),
    "C07": dict(period=period("2026-05-31", "2026-06-01")),
    "C08": dict(age=("date", "2026-09-24")),
    "C09": dict(age=("date", "2026-09-26")),
    "C10": dict(age=("order", None)),
    "C11": dict(age=("date", "2026-12-01")),
    "C12": dict(products=("a", "b", "c")),
    "C13": dict(period=period("2026-04-01", "2026-05-01"), products=("a", "c")),
    "C14": dict(period=period("2026-10-01", "2026-12-01"), products=("a", "b", "c")),
    "C15": dict(period=period("2026-03-01", "2026-06-01"), age=("date", "2026-09-25")),
    "C16": dict(products=("a", "b", "c"), age=("date", "2026-09-25")),
    "C17": dict(period=period("2026-01-01", "2026-07-01"), products=("a", "b", "c"), age=("date", "2026-09-25")),
    "C18": dict(period=period("2026-05-01", "2026-06-01"), age=("order", None)),
    "C19": dict(period=period("2026-09-01", "2026-10-01"), products=("d",), age=("date", "2026-09-25")),
    "C20": dict(period=period("2026-06-01", "2026-09-01")),
}


def family_of(params: dict) -> str:
    """Family of a question, from the filters it carries."""
    has_period, has_products, age = params.get("period"), params.get("products"), params.get("age")
    if age and not has_period and not has_products:
        return "F2" if age[0] == "date" else "F2b"
    if age:
        return "F4"
    return "F3" if has_products else "F1"


def build_query(period=None, products=None, age=None):
    """Parameterised SQL and its arguments. The values never enter the SQL text."""
    where, args = [], []
    if period:
        where += ["o.date >= ?", "o.date < ?"]
        args += list(period)
    if products:
        where.append("o.product_id IN (" + ",".join("?" * len(products)) + ")")
        args += list(products)
    if age:
        kind, day = age
        ref = "?" if kind == "date" else "o.date"
        where += [f"c.birth_date > date({ref}, '-{AGE + 1} years')", f"c.birth_date <= date({ref}, '-{AGE} years')"]
        if kind == "date":
            args += [day, day]
    sql = "SELECT COALESCE(SUM(o.quantity_product * p.price), 0) " + FROM
    if where:
        sql += " WHERE " + " AND ".join(where)
    return sql, args


def connect():
    connection = sqlite3.connect((KIT / "data" / "boutique.sqlite").as_uri() + "?mode=ro", uri=True)
    connection.execute("PRAGMA query_only = 1")
    return connection


def recompute(question_id: str, connection=None) -> int:
    """Revenue in cents, recomputed from the parameters of the question."""
    own = connection is None
    connection = connection or connect()
    try:
        sql, args = build_query(**PARAMS[question_id])
        return connection.execute(sql, args).fetchone()[0]
    finally:
        if own:
            connection.close()


def completed_age(born: date, on: date) -> int:
    return on.year - born.year - ((on.month, on.day) < (born.month, born.day))


def recompute_csv(question_id: str) -> int:
    """Third path: plain Python on the CSV files, with an explicit completed-age function."""
    def read(name):
        with (KIT / "data" / name).open(newline="", encoding="utf-8") as handle:
            return list(csv.DictReader(handle))
    price = {r["product_id"]: int(r["price"]) for r in read("product.csv")}
    born = {r["customer_id"]: date.fromisoformat(r["birth_date"]) for r in read("customers.csv")}
    p = PARAMS[question_id]
    total = 0
    for row in read("orders.csv"):
        if p.get("period") and not (p["period"][0] <= row["date"] < p["period"][1]):
            continue
        if p.get("products") and row["product_id"] not in p["products"]:
            continue
        if p.get("age"):
            kind, day = p["age"]
            on = date.fromisoformat(day) if kind == "date" else date.fromisoformat(row["date"][:10])
            if completed_age(born[row["customer_id"]], on) != AGE:
                continue
        total += int(row["quantity_product"]) * price[row["product_id"]]
    return total


def check_against_questions() -> list:
    """Every date, every product letter and the age mode of PARAMS must match the question text."""
    questions = {q["id"]: q["question"] for q in json.loads(
        (KIT / "questions-td1.json").read_text(encoding="utf-8"))["questions"]}
    problems = []
    for qid, p in PARAMS.items():
        text = questions[qid]
        dates = set(re.findall(r"\d{4}-\d{2}-\d{2}", text))
        mine = set()
        if p.get("period"):
            mine |= {d[:10] for d in p["period"]}
        if p.get("age") and p["age"][0] == "date":
            mine.add(p["age"][1])
        if dates != mine:
            problems.append(f"{qid}: dates in the question {sorted(dates)} differ from the parameters {sorted(mine)}")
        found = re.search(r"products? ([a-e](?:, [a-e])*(?: and [a-e])?)", text)
        letters = tuple(re.findall(r"\b[a-e]\b", found.group(1))) if found else None
        if letters != p.get("products"):
            problems.append(f"{qid}: products in the question {letters} differ from the parameters {p.get('products')}")
        if ("at the time of the order" in text) != bool(p.get("age") and p["age"][0] == "order"):
            problems.append(f"{qid}: age mode differs from the question")
        if ("25 years old" in text) != bool(p.get("age")):
            problems.append(f"{qid}: age filter differs from the question")
    return problems


def load_references() -> dict:
    with (KIT / "reference-td1.csv").open(newline="", encoding="utf-8") as handle:
        return {r["case_id"].strip(): int(r["revenue_cents"].strip()) for r in csv.DictReader(handle)}


def table(references: dict) -> int:
    expected = {q: f for f, qs in FAMILIES.items() for q in qs}
    problems = check_against_questions()
    connection = connect()
    bad = 0
    print("| Question | Family | Recomputed (SQL) | CSV path | Reference | Equal |")
    print("|---|---|---|---|---|---|")
    for qid in sorted(PARAMS):
        family = family_of(PARAMS[qid])
        value, via_csv = recompute(qid, connection), recompute_csv(qid)
        same = value == via_csv == references[qid]
        bad += not same
        label = next(name for name in FAMILIES if name.split()[0] == family)
        if label != next(name for name in FAMILIES if qid in FAMILIES[name]):
            problems.append(f"{qid}: family {family} differs from rates_by_family.py")
        print(f"| {qid} | {family} | {value} | {via_csv} | {references[qid]} | {'yes' if same else 'NO'} |")
    connection.close()
    print(f"\nparameters consistent with the questions: {'yes' if not problems else 'NO'}")
    for line in problems:
        print("  ", line)
    print(f"questions where the three paths are not equal: {bad}")
    return 0 if not problems and not bad else 1


def verify(question_id: str, value: str) -> int:
    if question_id not in PARAMS:
        sys.exit(f"unknown question {question_id}")
    try:
        figure = int(value)
    except ValueError:
        sys.exit("the figure must be an integer number of cents")
    expected = recompute(question_id)
    accepted = figure == expected
    print(json.dumps({"question": question_id, "family": family_of(PARAMS[question_id]), "model_value": figure,
                      "recomputed": expected, "decision": "accept" if accepted else "reject"}))
    return 0 if accepted else 2


def traces(path: Path) -> int:
    final = final_results(path)
    connection = connect()
    expected = {q: recompute(q, connection) for q in PARAMS}
    connection.close()
    print("| Model | Accepted | Rejected | No figure | Rejected: zeros | Rejected: other values |")
    print("|---|---|---|---|---|---|")
    mismatch = 0
    for model in MODELS:
        accepted = rejected = none = zeros = others = 0
        for qid in sorted(PARAMS):
            row = final[f"{model}:{qid}"]
            if row["verdict"] not in ("correct", "incorrect") or row["value"] == "":
                none += 1
                continue
            if int(row["value"]) == expected[qid]:
                accepted += 1
                mismatch += row["verdict"] != "correct"
            else:
                rejected += 1
                zeros += int(row["value"]) == 0
                others += int(row["value"]) != 0
                mismatch += row["verdict"] != "incorrect"
        print(f"| {short(model)} | {accepted} | {rejected} | {none} | {zeros} | {others} |")
    print(f"\ncells where the control and the lab verdict disagree: {mismatch}")
    return 0 if not mismatch else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--verify", nargs=2, metavar=("QUESTION", "CENTS"), help="accept or reject a model figure")
    parser.add_argument("--traces", action="store_true", help="apply the control to the TD 1 traces")
    parser.add_argument("--traces-file", type=Path, default=KIT / "traces-td1.csv")
    args = parser.parse_args()
    if args.verify:
        return verify(*args.verify)
    if args.traces:
        return traces(args.traces_file)
    return table(load_references())


if __name__ == "__main__":
    raise SystemExit(main())
