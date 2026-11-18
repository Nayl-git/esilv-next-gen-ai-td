#!/usr/bin/env python3
"""TD 2, Step 3 (Pair C): TD 1 rates by question family, from the stored traces.

Offline, standard library only. For each model and each family, counts the
questions whose final result (last attempt of the cell) is correct. The
families partition the twenty questions:

    F1  period                     C01 C04 C05 C06 C07 C20
    F2  completed age at a date    C02 C08 C09 C11
    F2b completed age at the order C10
    F3  product list               C03 C12 C13 C14
    F4  combinations               C15 C16 C17 C18 C19

    python td2/rates_by_family.py
    python td2/rates_by_family.py --traces traces-td1.csv --failures
"""
import argparse
import csv
import sys
from pathlib import Path

KIT = Path(__file__).resolve().parent.parent
FAMILIES = {
    "F1 period": ["C01", "C04", "C05", "C06", "C07", "C20"],
    "F2 completed age at a date": ["C02", "C08", "C09", "C11"],
    "F2b completed age at the order": ["C10"],
    "F3 product list": ["C03", "C12", "C13", "C14"],
    "F4 combinations": ["C15", "C16", "C17", "C18", "C19"],
}
MODELS = [
    "groq:openai/gpt-oss-120b",
    "groq:openai/gpt-oss-20b",
    "groq:qwen/qwen3.8-27b",
    "openrouter:dots-studio/dots-3-note-preview:free",
    "openrouter:cohere/north-mini-code:free",
]


def short(model: str) -> str:
    """Name used in the report: no provider, no ':free', no '-preview'."""
    return model.split("/")[-1].replace(":free", "").replace("-preview", "")


def final_results(traces: Path) -> dict:
    """cell_id -> row of the last attempt (highest attempt number, then latest date)."""
    final = {}
    with traces.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            key = (int(row["attempts"] or 0), row["date_utc"])
            if row["cell_id"] not in final or key >= final[row["cell_id"]][0]:
                final[row["cell_id"]] = (key, row)
    return {cell: row for cell, (_, row) in final.items()}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--traces", type=Path, default=KIT / "traces-td1.csv")
    parser.add_argument("--failures", action="store_true", help="also list the failing cells of each family")
    args = parser.parse_args()

    final = final_results(args.traces)
    questions = [q for qs in FAMILIES.values() for q in qs]
    assert sorted(questions) == [f"C{i:02d}" for i in range(1, 21)], "the families must partition C01 to C20"
    missing = [f"{m}:{q}" for m in MODELS for q in questions if f"{m}:{q}" not in final]
    if missing:
        sys.exit(f"missing cells in the traces: {missing[:5]}")

    print("| Family | Questions | " + " | ".join(f"`{short(m)}`" for m in MODELS) + " |")
    print("|---|---|" + "---|" * len(MODELS))
    for family, qs in FAMILIES.items():
        counts = [sum(final[f"{m}:{q}"]["verdict"] == "correct" for q in qs) for m in MODELS]
        print(f"| {family} | {', '.join(qs)} | " + " | ".join(f"{c}/{len(qs)}" for c in counts) + " |")
    totals = [sum(final[f"{m}:{q}"]["verdict"] == "correct" for q in questions) for m in MODELS]
    print("| **Total** | C01 to C20 | " + " | ".join(f"{t}/20" for t in totals) + " |")

    if args.failures:
        print("\nFailing cells (final result)")
        for family, qs in FAMILIES.items():
            for m in MODELS:
                bad = [(q, final[f"{m}:{q}"]["verdict"]) for q in qs if final[f"{m}:{q}"]["verdict"] != "correct"]
                if bad:
                    print(f"  {family} | {short(m)}: {bad}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
