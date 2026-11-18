#!/usr/bin/env python3
"""TD 2, Step 3 (Pair C): every 2-of-3 panel evaluated on the stored TD 1 traces.

Offline, standard library only. For each panel of three of the five TD 1
models, takes the final result (last attempt) of each model on each question
and applies the rule of Step 1 with k = 2: only an executed value votes, a
failed model stays in n and casts no vote, a value needs k votes, and no value
is invented when none reaches k. The decision is taken first; the reference
(`reference-td1.csv`) is read only afterwards, to tell a correct consensus from
a wrong one.

    python td2/panels.py
    python td2/panels.py --k 2 --panel groq:openai/gpt-oss-120b groq:openai/gpt-oss-20b groq:qwen/qwen3.8-27b
"""
import argparse
import csv
import itertools
import sys
from collections import Counter
from pathlib import Path

KIT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from rates_by_family import MODELS, final_results, short  # noqa: E402  (same folder)


def decide(panel, question, final, k):
    """Vote of one panel on one question, without the reference."""
    votes = Counter()
    for model in panel:
        row = final[f"{model}:{question}"]
        if row["verdict"] in ("correct", "incorrect") and row["value"] != "":
            votes[row["value"]] += 1
    top = max(votes.values(), default=0)
    if top >= k:
        return max(votes, key=votes.get), top
    return None, top


def evaluate(panel, final, references, k):
    """question -> (status, value): status is correct, abstention or WRONG."""
    outcome = {}
    for question in sorted(references):
        value, _ = decide(panel, question, final, k)
        status = "abstention" if value is None else "correct" if value == references[question] else "WRONG"
        outcome[question] = (status, value)
    return outcome


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--traces", type=Path, default=KIT / "traces-td1.csv")
    parser.add_argument("--reference", type=Path, default=KIT / "reference-td1.csv")
    parser.add_argument("--k", type=int, default=2, help="votes needed (default 2, a strict majority of 3)")
    parser.add_argument("--panel", nargs=3, metavar="PROVIDER:MODEL", help="evaluate one panel instead of the ten")
    args = parser.parse_args()

    final = final_results(args.traces)
    with args.reference.open(newline="", encoding="utf-8") as handle:
        references = {r["case_id"].strip(): r["revenue_cents"].strip() for r in csv.DictReader(handle)}
    panels = [tuple(args.panel)] if args.panel else list(itertools.combinations(MODELS, 3))
    unknown = [m for p in panels for m in p if m not in MODELS]
    if unknown:
        sys.exit(f"unknown model(s): {sorted(set(unknown))}")
    if not 3 // 2 < args.k <= 3:
        sys.exit("k must be a strict majority of 3: 2 or 3")

    print("| Panel | Correct consensus | Abstentions | Wrong consensus | Questions not correct |")
    print("|---|---|---|---|---|")
    for panel in panels:
        outcome = evaluate(panel, final, references, args.k)
        count = Counter(status for status, _ in outcome.values())
        wrong = [f"{q} wrong ({v})" for q, (s, v) in outcome.items() if s == "WRONG"]
        abstain = [q for q, (s, _) in outcome.items() if s == "abstention"]
        notes = wrong + ([", ".join(abstain) + " abstain"] if abstain else [])
        print(f"| {', '.join(short(m) for m in panel)} | {count['correct']} | {count['abstention']} | "
              f"{count['WRONG']} | {'; '.join(notes) or 'none'} |")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
