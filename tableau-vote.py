#!/usr/bin/env python3
"""TD 2, Step 1: compare the fixed 2-of-3 panel with the 3-of-5 quorum on stored TD 1 traces.

No network. Uses your Orchestrateur.vote_k_sur_n from skeleton-multi-llm-en.py.
The reference is compared AFTER each decision, never given to the vote.

    python3 tableau-vote.py                            # markdown table on stdout
    python3 tableau-vote.py --out reports/td2-table.md # also write it to a file
"""
import argparse
import csv
import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace

PANEL_3 = [
    ("groq", "openai/gpt-oss-120b"),
    ("openrouter", "cohere/north-mini-code:free"),
    ("groq", "qwen/qwen3.8-27b"),
]
PANEL_5 = PANEL_3 + [
    ("groq", "openai/gpt-oss-20b"),
    ("openrouter", "dots-studio/dots-3-note-preview:free"),
]


def load_vote():
    spec = importlib.util.spec_from_file_location("student_skeleton", Path(__file__).with_name("skeleton-multi-llm-en.py"))
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return lambda proposals, k: module.Orchestrateur.vote_k_sur_n(None, proposals, k)


def last_rows(rows, case, nature):
    """Last attempt per (provider, model) for one question: the highest `attempts` number,
    whatever the order of the rows in the file (a tie keeps the later row)."""
    selected = {}
    for row in rows:
        if row["case_id"] == case and row["nature"] == nature:
            key = (row["provider"], row["model_requested"])
            if key not in selected or int(row["attempts"] or 0) >= int(selected[key]["attempts"] or 0):
                selected[key] = row
    return selected


def proposals_for(selected, panel):
    proposals = []
    for provider, model in panel:
        row = selected.get((provider, model), {})
        value = row.get("value", "")
        valid = row.get("verdict") in {"correct", "incorrect"} and value not in {None, ""}
        proposals.append(SimpleNamespace(provider=provider, model_requested=model,
                                         value=int(value) if valid else None,
                                         verdict="executed" if valid else "error"))
    return proposals


def cell(decision, reference):
    if not decision["consensus"]:
        return f"abstention ({decision['votes']} voix max)"
    ok = "OK" if reference is not None and decision["value"] == reference else "FAUX"
    return f"{decision['value']} ({decision['votes']} voix) {ok}"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--traces", type=Path, default=Path("traces-td1.csv"))
    parser.add_argument("--nature", default="real", choices=["real", "replay", "simulation"])
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    vote = load_vote()
    with args.traces.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))

    cases = sorted({r["case_id"] for r in rows if r["nature"] == args.nature})
    lines = ["| Question | Référence | 2-sur-3 (k=2) | 3-sur-5 (k=3) | Change ? |",
             "|---|---|---|---|---|"]
    details = []
    for case in cases:
        selected = last_rows(rows, case, args.nature)
        refs = {int(r["reference"]) for r in selected.values() if r.get("reference") not in {None, ""}}
        reference = next(iter(refs), None)
        d3 = vote(proposals_for(selected, PANEL_3), 2)
        d5 = vote(proposals_for(selected, PANEL_5), 3)
        changed = (d3["consensus"], d3["value"]) != (d5["consensus"], d5["value"])
        lines.append(f"| {case} | {reference} | {cell(d3, reference)} | {cell(d5, reference)} | {'OUI' if changed else 'non'} |")
        if changed:
            details.append(f"\n**{case}** (référence {reference}) : valeurs et verdicts des 5 modèles")
            for provider, model in PANEL_5:
                row = selected.get((provider, model), {})
                details.append(f"- {provider}:{model} -> value={row.get('value') or '-'}, "
                               f"verdict={row.get('verdict') or 'absent'}, "
                               f"http={row.get('http_status') or '-'}, error={row.get('error') or '-'}")

    output = "\n".join(lines)
    if details:
        output += "\n\n### Questions où la décision change (à commenter)\n" + "\n".join(details)
    print(output)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(output + "\n", encoding="utf-8")
        print(f"\nÉcrit dans {args.out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
