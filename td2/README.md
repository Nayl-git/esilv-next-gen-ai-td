# TD 2: the quorum, then the routing rule

Sub-group DIA2-1. Session of 18 November 2026. Assignment: [enonce-td2-en](../enonce-td2-en.md). Hand-in: `reports/td2.md` in this repository, by 23:59 Paris time on Sunday 22 November 2026.

No new batch of network calls: everything runs on the stored TD 1 traces ([traces-td1.csv](../traces-td1.csv)), the references ([reference-td1.csv](../reference-td1.csv)) and `data/boutique.sqlite`.

## Work by pair

| Pair | Step | Status | Files |
|---|---|---|---|
| A | Step 1: `Orchestrateur.vote_k_sur_n`, then the 2-of-3 vs 3-of-5 table on the twenty questions | to update by Pair A | [skeleton-multi-llm-en.py](../skeleton-multi-llm-en.py) |
| B | Step 2: a verified wrong consensus, with SQL root cause and delta query | done: C09, qwen3.8-27b and dots-3-note both return 0 (ref 487 980); fixed 2-of-3 panel abstains; population check flags it | [wrong-consensus-C09.md](wrong-consensus-C09.md), [wrong_consensus.py](wrong_consensus.py), [pair-b-outputs/](pair-b-outputs/) |
| C | Step 3: routing rule per question family, simulator before and after, priority analysis | simulator adapted; draft of the rule and the priority analysis in [draft-pair-C-section.md](draft-pair-C-section.md), to integrate in the report | [atelier-routage.py](../atelier-routage.py), [routage-avant.jsonl](../routage-avant.jsonl), [routage-apres.jsonl](../routage-apres.jsonl) |

Each pair keeps its own row up to date when it pushes. Pull before editing this file.

## Pair C: routing simulator

- `atelier-routage.py` routes with the five TD 1 models and one paid route. Each model's level is derived from its TD 1 results by family (F1 period, F2 age at a date, F2b age at the order, F3 product list, F4 combinations).
- The check depends on the family, the use (dashboard, customer, payout) and the TD 1 accuracy of the chosen model. `none` is only allowed for an internal dashboard when the model was 100 % correct on at least four questions of the family.
- Every `reason` cites the TD 1 cells that justify the decision.
- `routage-avant.jsonl` holds the seven outputs of the kit simulator; `routage-apres.jsonl` holds the nine outputs of the adapted one. The seven original scenarios give the same actions as before.

```
python atelier-routage.py                        # the nine scenarios
python atelier-routage.py --scenario deferrable  # one scenario
python td2/rates_by_family.py                    # TD 1 rates by question family (--failures for the failing cells)
python td2/panels.py                             # the ten 2-of-3 panels on the TD 1 traces
```

`rates_by_family.py` and `panels.py` read `traces-td1.csv` and `reference-td1.csv`, offline, standard library only. The reference is read only after each decision.

## Pair B: wrong consensus

- Real case **C09** (F2, age at a date): `groq:qwen/qwen3.8-27b` and `openrouter:dots-studio/dots-3-note-preview:free` both return 0 cents for a reference of 487 980, through two different SQL errors that both empty the filter.
- The fixed 2-of-3 panel and the 3-of-5 quorum **abstain** on C09; a panel {gpt-oss, qwen, dots} gives a **wrong consensus** on 0.
- Delta query: the six customers the two faulty queries miss, with their revenue; the sum is the whole gap, 487 980 cents.
- Independent check: a population count. A 0 is rejected when the targeted population is not empty. It is model-free for the age-at-a-date questions (it flags the wrong zeros of C02, C09, C11); for C10, C15 and C16 the population still comes from the reference query.
- Cross-reviews of Steps 2 and 3: [peer-review-pair-A.md](peer-review-pair-A.md) (by Pair A), [peer-review-pair-C.md](peer-review-pair-C.md) (by Pair C).
- Synthetic case DEMO-VOTE executed on its toy table, labelled synthetic.

```
python td2/wrong_consensus.py                   # scan, quorum, panels, cause, check, demo
```

## Commands of the other steps

```
python atelier-vote.py                                    # four synthetic examples, no network
python atelier-vote.py --traces traces-td1.csv --case C02 # real traces for one question
```

## Report

`reports/td2.md` is assembled after the internal cross-review (16:45 to 17:15) and is committed with the code, the prompts if changed, and the evidence. In the Moodle hand-in area: the full repository URL, the full commit hash of the session, and the link to the report at that commit.
