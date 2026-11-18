# TD 2 report: the quorum, then the routing rule

Session 2, 18 November 2026. Kit pack 2026-10-14-students-1, database `data/boutique.sqlite` (seed 20260925). Sub-group DIA2-1. Assignment: [enonce-td2-en](../enonce-td2-en.md). Session index: [td2/README.md](../td2/README.md).

No new network batch: every result below comes from the stored TD 1 traces ([traces-td1.csv](../traces-td1.csv), nature `real`), the references ([reference-td1.csv](../reference-td1.csv)) and read-only queries on the database. Synthetic examples are labelled as such and kept out of every count.

## Summary

- **Step 1 (Pair A):** `Orchestrateur.vote_k_sur_n` is implemented in [skeleton-multi-llm-en.py](../skeleton-multi-llm-en.py) (commit f399f1a). *To complete by Pair A: the table of the twenty decisions.*
- **Step 2 (Pair B):** one real wrong consensus in our batch, **C09**: `qwen3.8-27b` and `dots-3-note` both return **0** cents for a reference of **487 980**, through two different SQL errors. The fixed 2-of-3 panel **abstains** on C09; a panel {gpt-oss, qwen, dots} would accept 0. A model-free population check flags every wrong 0 of the batch and no true zero.
- **Step 3 (Pair C):** the routing simulator is adapted to our five TD 1 models ([atelier-routage.py](../atelier-routage.py)), outputs before and after in [routage-avant.jsonl](../routage-avant.jsonl) and [routage-apres.jsonl](../routage-apres.jsonl). *To complete by Pair C: the one-page rule.*

## Work completed

| Step | Pair | Status | Evidence |
|---|---|---|---|
| Step 1: `vote_k_sur_n` | A | implemented; synthetic tests pass (see below) | [skeleton-multi-llm-en.py](../skeleton-multi-llm-en.py), `python atelier-vote.py` |
| Step 1: table of the twenty decisions | A | *to complete by Pair A* | |
| Step 2: wrong consensus, cause, quorum, check | B | done | [td2/wrong-consensus-C09.md](../td2/wrong-consensus-C09.md), [td2/wrong_consensus.py](../td2/wrong_consensus.py), [td2/pair-b-outputs/](../td2/pair-b-outputs/) |
| Step 3: simulator before / after | C | done | [routage-avant.jsonl](../routage-avant.jsonl), [routage-apres.jsonl](../routage-apres.jsonl) |
| Step 3: one-page routing rule | C | *to complete by Pair C* | |
| Prompts | all | unchanged since TD 1 | `SYSTEM_PROMPT` and `USER_PROMPT_TEMPLATE` in [skeleton-multi-llm-en.py](../skeleton-multi-llm-en.py) |

## Step 1: the k-of-n vote (Pair A)

Declared panel, fixed by `atelier-vote.py`: `groq:openai/gpt-oss-120b`, `openrouter:cohere/north-mini-code:free`, `groq:qwen/qwen3.8-27b`; threshold 2 of 3.

Synthetic tests (`python atelier-vote.py`, nature `simulation`, not shop data):

| Example | Proposals | Decision |
|---|---|---|
| agreement | 100, 100, 120 | consensus 100, 2 votes |
| disagreement | 100, 110, 120 | abstention, max 1 vote |
| unavailable | 100, error, error | abstention, 1 vote: the unavailable members stay in n |
| wrong consensus | 0, 0, 100 | consensus 0, 2 votes; reference 100, so wrong |

*To complete by Pair A: the duplicate-route test, and the table of the twenty decisions (consensus or abstention, value, votes, agreement with the reference) from `python atelier-vote.py --traces traces-td1.csv --case Cxx`.*

## Step 2: the wrong consensus (Pair B)

Full commentary: [td2/wrong-consensus-C09.md](../td2/wrong-consensus-C09.md). Every figure is reproduced by:

```
python td2/wrong_consensus.py      # sections scan, quorum, panels, cause, check, demo
```

### The case

| Field | Value |
|---|---|
| Identifier | C09, family "completed age at a date" |
| Nature | real batch (TD 1 traces) |
| Question | Revenue of the customers exactly 25 years old on 2026-09-26 (all their orders) |
| Independent reference | 487 980 cents: 68 order lines, 6 customers |
| Agreeing models | `groq:qwen/qwen3.8-27b` ([traces-D.csv](../traces-D.csv)) and `openrouter:dots-studio/dots-3-note-preview:free` ([traces-E2.csv](../traces-E2.csv)) |
| Shared wrong value | 0 cents, valid SQL, one attempt each |

Scanning the twenty questions × five models finds **one** question where at least two models return the same wrong value: C09. This is a count on our batch, not an error rate.

### Cause in the SQL

Each stored query was replayed on the database, condition by condition.

- **qwen3.8-27b** computes the age at the **order date** instead of the reference date, then adds `month-day(order) >= month-day(birth)` and `month-day(order) < month-day(birth + 26 years)`. Adding 26 years does not change a month-day (0 customers born on 29 February), so the two bounds contradict each other: 72 → 14 → **0** lines.
- **dots-3-note** reads "exactly 25" as "**turns** 25 on 2026-09-26" (one customer, born 2001-09-26), then adds an order-date filter on 2026-09-26 that the question does not contain. The last order in the base is dated 2026-09-20: 72 → 6 → **0** lines.
- Delta query (reference lines `EXCEPT` wrong-query lines): 68 of 68 reference lines missed by each model.

Observed: two **different** errors give the **same** value, because `COALESCE(SUM(...), 0)` turns any empty filter into 0, and 0 is a plausible answer (it is the correct value of C06 and C14). Hypothesis, not measured: 0 is the most likely shared wrong value for filter errors.

### Declared quorum and result

The vote decides before the reference is read.

| Quorum | Proposals on C09 | Decision |
|---|---|---|
| **Fixed panel 2-of-3** (gpt-oss-120b, north-mini-code, qwen3.8-27b) | 487 980 / no vote (SQL invalid, stays in n) / 0 | **abstention** (1 vote max) |
| 3-of-5 (the five TD 1 models) | 487 980 ×2 / no vote / 0 ×2 | **abstention** (2 votes max) |
| 2-of-3 {gpt-oss-120b, qwen3.8-27b, dots-3-note} | 487 980 / 0 / 0 | **wrong consensus on 0** |

The fixed-panel result was confirmed with Pair A's implementation: `python atelier-vote.py --traces traces-td1.csv --case C09` returns `{"consensus": false, "value": null, "votes": 1}`. The agreement of qwen and dots among the five TD 1 models does not make the fixed panel wrong: dots is not a member of it.

Across the seven 2-of-3 panels of three distinct families on the twenty questions, the three panels that hold both qwen and dots contain the wrong consensus on C09, and two of them are also the panels that answer most often (16 correct, 3 abstentions). Choosing a panel for its coverage brings in the shared error.

### Consequence and independent check

- **Panel:** for the age-at-a-date family, qwen3.8-27b and dots-3-note should not be able to outvote the strongest member together. Distinct families are necessary but not sufficient. The fixed panel avoids C09 only because north-mini-code failed to run; a different panel or an escalation is a candidate, not a guarantee.
- **Population check:** next to the SUM, the service counts the targeted order lines **without any model**, with a second formulation of the age rule (`date()` window, distinct from the `strftime` reference), and rejects a 0 when that population is not empty. On the twenty questions, it flags all the wrong zeros (C02, C09, C10, C11, C15, C16) and none of the true zeros (C06, C14).
- **Limit:** it does not catch a wrong non-zero value (e.g. qwen C16 = 367 050, off by one day). For an amount paid out, the reference query or a human review remains necessary.

### Supplied synthetic case DEMO-VOTE

**Synthetic**, supplied teaching example; it is not a model output or shop data. On a one-row toy table (sale of 100 cents on 2026-01-01, period [2026-01-01, 2026-01-02)), the strict bound `sale_date > '2026-01-01'` returns 0 and the inclusive bound `>=` returns 100. With proposals [0, 0, 100], the 2-of-3 vote returns consensus 0; the reference is 100. The mechanism is the same as C09: a filter that is too narrow, then `COALESCE` gives a plausible 0.

## Step 3: the routing rule (Pair C)

The simulator routes with the five TD 1 models plus the paid OpenRouter route of gpt-oss-120b. Each model's level is derived from its TD 1 results by family, and each `reason` cites the TD 1 cells. The seven original scenarios keep the same actions as the kit (run, run, defer, run, abstain, run, abstain); two scenarios were added ("customer figure", "combination dashboard").

```
python atelier-routage.py                        # nine scenarios
```

*To complete by Pair C: the one-page rule per family (first model, check by use, course of action if unavailable), with the TD 1 cells that justify it. Pair B's result to take into account: no 2-of-3 quorum holding both qwen3.8-27b and dots-3-note for the age families, and a population check before accepting a 0.*

## Cross-review by Pair B

Two rounds, offline, by reading the code, the diffs and the produced tables against the assignment.

### Second round (commit b1a5b35)

**Step 1 (Pair A).**

- **`vote_k_sur_n`: compliant with the contract.** `n // 2 < k <= n` is checked; a duplicate (provider, model) raises `ValueError`, errors included; errors and unavailable members stay in n without voting; an abstention returns `value = None`, `models = []` and the largest vote count. No defect found.
- **C19 is not commented, and the material for it was removed.** `tableau-vote.py` prints a block "questions where the decision changes" with the values and verdicts of the five models; commit 1ee622e deleted those lines from [td2-table.md](td2-table.md). The assignment asks to explain every difference between 2-of-3 and 3-of-5 with exact values and verdicts. To do: restore the block and comment C19 (2-of-3 abstains, 3-of-5 decides 1990, correct).
- **Margins not commented.** C02, C08, C11 and C18 pass the 2-of-3 panel with 2 votes only, because one member failed (invalid SQL or HTTP 429). The decision does not change, but the margin does; the assignment gives this as an example to explain.
- **Table not in the report.** It is in a separate file, in French, while the report is in English; the Step 1 section above still reads "to complete by Pair A". To do: move the table into this section, in English.
- **Minor.** The duplicate-route test is not shown, and the second member of Pair A is missing from the contributions.
- **Consistency with Step 2:** the fixed panel gives 15 correct, 5 abstentions, 0 wrong consensus, as in Pair B's [panels.json](../td2/pair-b-outputs/panels.json).

**Step 3 (Pair C).** Both first-round remarks are applied (commit e6d376b): the panel is declared, the zero check is added for F2 and F2b, and an unrun request shows "not applicable". The TD 1 rates of the draft agree with the failing cells it lists.

- **Panel P is not of three distinct families.** P = {gpt-oss-120b, gpt-oss-20b, qwen3.8-27b} holds two gpt-oss models, which Step 2 counts as one family, and it was chosen on the twenty questions it is evaluated on (Pair C states both limits). To do: either justify the coverage-versus-independence trade-off explicitly, or keep a panel of distinct families that does not hold qwen3.8-27b and dots-3-note together.
- **Rule and simulator disagree on the fallback.** For F2 the rule reads "wait for refill, then abstain", but the "urgent" scenario runs the paid gpt-oss-120b route (0.00033 USD). To do: add the paid route to the Fallback column.
- **"Deterministic check" for F2 dashboard is not defined.** "Read-only execution and plausibility" does not catch a wrong 0 (C09). To do: name the check, e.g. Pair B's population check, as already required for F2b.
- **Price ranking leaves out the free models.** dots-3-note and north-mini-code have no documented paid route, so they are never ranked, although they are free and correct on F1 and F3. To do: one sentence explaining why they are not the first model there.
- **Wording.** "Questions no free model handles alone" says only gpt-oss-120b has no error on F2, but gpt-oss-120b runs on the free Groq plan.
- **Not integrated yet.** The section is in [td2/draft-pair-C-section.md](../td2/draft-pair-C-section.md); the Step 3 section above still reads "to complete", and Pair C's contributions are empty.

### First round (commit 4cc60e5)

- **Step 1 (Pair A), consistent.** `python tableau-vote.py` gives, for the fixed 2-of-3 panel, 15 correct consensus, 5 abstentions (C09, C10, C16, C17, C19) and no wrong consensus. Pair B's independent count in [td2/pair-b-outputs/panels.json](../td2/pair-b-outputs/panels.json) gives the same 15 / 5 / 0. C19 is the only question where 3-of-5 decides (1990, correct) while 2-of-3 abstains. To do by Pair A: copy the table into this report (Step 1 section) and comment C19.
- **Step 3 (Pair C), one point to fix.** For F2 and F2b the check is a "2-of-3 quorum anchored on gpt-oss-120b", but the panel is not declared. Anchoring is not enough: the panel {gpt-oss-120b, qwen3.8-27b, dots-3-note} contains gpt-oss-120b and still accepts the wrong 0 on C09 (qwen and dots outvote it). The rule should name the panel and exclude having both qwen3.8-27b and dots-3-note in it for the age families, or add the population check before accepting a 0.
- **Step 3, minor.** In the "unknown capability" scenario the action is `abstain` but `checks` reads "2-of-3 quorum": a check on a request that is not run is confusing in the trace.

## Limitations

- One run per cell, 20 questions × 5 models: the results support hypotheses about this batch, not error rates, a ranking or a quorum guarantee.
- One wrong consensus only (C09). Its two causes are different; a conclusion about "shared errors" in general would need more cases.
- The population check uses a model-free `date()` window for the age-at-a-date family only. For the other families, the population was taken from the reference query, which a live service would not have: a model-free population query per family is still to write.

## Contributions

**Each member checks their line and completes it.**

| GitHub account | Pair | Contribution |
|---|---|---|
| ambrere | A | `vote_k_sur_n` (commit f399f1a) |
| *to complete* | A | |
| enkimlt | B | Step 2, shared equally with nohamsantenac and PierreBOUDRAA (see note below) |
| nohamsantenac | B | Step 2, shared equally with enkimlt and PierreBOUDRAA (see note below) |
| PierreBOUDRAA | B | Step 2, shared equally with enkimlt and nohamsantenac (see note below) |
| Nayl-git | C | Adaptation of the routing simulator (commit def1d6e); `td1/` and `td2/` folders |
| *to complete* | C | |

**Pair B note.** The three members of Pair B worked together on one machine, so every Pair B commit is under the `enkimlt` account. The work was split roughly equally between the three. It covers the wrong-consensus analysis of C09 (scan, declared quorums and panels, SQL cause and delta query, population check, DEMO-VOTE; [td2/](../td2/)), the Step 2 section of this report, and the cross-review of Steps 1 and 3.

## Use of coding assistance

As the assignment requires, we declare that a coding assistant was used for the analysis script of Step 2 and for drafting this report. Every figure comes from SQL executed read-only on the database or from the stored traces; the members remain responsible for the explanations.

## Next steps (TD 3)

- The price of checking: the age questions, which no free model except gpt-oss-120b answers alone in our batch, set the cost of the quorum or the reference in TD 3.
- Write a model-free population query for every family, so that the zero check can run without the reference.
- Choose the use case and its cost of error, then the configuration.
