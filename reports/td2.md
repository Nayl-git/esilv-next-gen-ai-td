# TD 2 report: the quorum, then the routing rule

Session 2, 18 November 2026. Kit pack 2026-10-14-students-1, database `data/boutique.sqlite` (seed 20260925). Sub-group DIA2-1. Assignment: [enonce-td2-en](../enonce-td2-en.md). Session index: [td2/README.md](../td2/README.md).

No new network batch: every result below comes from the stored TD 1 traces ([traces-td1.csv](../traces-td1.csv), nature `real`), the references ([reference-td1.csv](../reference-td1.csv)) and read-only queries on the database. Synthetic examples are labelled as such and kept out of every count.

## Summary

- **Step 1 (Pair A):** `Orchestrateur.vote_k_sur_n` is implemented in [skeleton-multi-llm-en.py](../skeleton-multi-llm-en.py) (commit f399f1a). *To complete by Pair A: the table of the twenty decisions.*
- **Step 2 (Pair B):** one real wrong consensus in our batch, **C09**: `qwen3.8-27b` and `dots-3-note` both return **0** cents for a reference of **487 980**, through two different SQL errors. The fixed 2-of-3 panel **abstains** on C09; a panel {gpt-oss, qwen, dots} would accept 0. A model-free population check flags every wrong 0 of the batch and no true zero.
- **Step 3 (Pair C):** the routing simulator is adapted to our five TD 1 models ([atelier-routage.py](../atelier-routage.py)), outputs before and after in [routage-avant.jsonl](../routage-avant.jsonl) and [routage-apres.jsonl](../routage-apres.jsonl). The rule gives, for each question family, a first model, a check by use and a fallback, and declares the quorum panel {gpt-oss-120b, gpt-oss-20b, qwen3.8-27b}. **The results of the first version differ from the final ones because of the cross-review by Pair B**: the panel was not declared and a panel holding qwen3.8-27b and dots-3-note accepts the wrong 0 of C09; see "Effect of the cross-review on the results".

## Work completed

| Step | Pair | Status | Evidence |
|---|---|---|---|
| Step 1: `vote_k_sur_n` | A | implemented; synthetic tests pass (see below) | [skeleton-multi-llm-en.py](../skeleton-multi-llm-en.py), `python atelier-vote.py` |
| Step 1: table of the twenty decisions | A | *to complete by Pair A* | |
| Step 2: wrong consensus, cause, quorum, check | B | done | [td2/wrong-consensus-C09.md](../td2/wrong-consensus-C09.md), [td2/wrong_consensus.py](../td2/wrong_consensus.py), [td2/pair-b-outputs/](../td2/pair-b-outputs/) |
| Step 3: simulator before / after | C | done | [routage-avant.jsonl](../routage-avant.jsonl), [routage-apres.jsonl](../routage-apres.jsonl) |
| Step 3: one-page routing rule | C | done, revised after the cross-review of Pair B | Step 3 section below, [td2/draft-pair-C-section.md](../td2/draft-pair-C-section.md) |
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

### Goal and method

Each question goes to the cheapest model that is still reliable enough for its family, with a check that depends on the cost of an error. Everything below uses only the stored TD 1 traces ([traces-td1.csv](../traces-td1.csv)), the references ([reference-td1.csv](../reference-td1.csv)), the portfolio sheet ([five-model-summary-en.csv](../five-model-summary-en.csv)) and the simulator [atelier-routage.py](../atelier-routage.py). No network call was made. The simulator is a simulation: its resources, quotas and costs are scenario inputs, not provider measurements.

### TD 1 rates by family

Final result of each cell (last attempt), `correct / cases`. The five families partition the twenty questions.

| Family | Questions | gpt-oss-120b | gpt-oss-20b | qwen3.8-27b | dots-3-note | north-mini-code |
|---|---|---|---|---|---|---|
| F1 period | C01, C04, C05, C06, C07, C20 | 6/6 | 6/6 | 6/6 | 6/6 | 6/6 |
| F2 completed age at a date | C02, C08, C09, C11 | 4/4 | 2/4 | 3/4 | 2/4 | 0/4 |
| F2b completed age at the order | C10 | 1/1 | 1/1 | 0/1 | 0/1 | 0/1 |
| F3 product list | C03, C12, C13, C14 | 4/4 | 4/4 | 4/4 | 4/4 | 4/4 |
| F4 combinations | C15, C16, C17, C18, C19 | 5/5 | 5/5 | 1/5 | 2/5 | 1/5 |
| Total | C01 to C20 | 20/20 | 18/20 | 14/20 | 14/20 | 11/20 |

Failing cells: gpt-oss-20b C02, C11; qwen C09, C10, C15, C16, C17, C19; dots C08, C09 (wrong value), C10, C17 (invalid SQL), C16, C18 (wrong value); north-mini C02, C10, C11, C16 to C19 (wrong value), C08, C09 (invalid SQL). `F4` is our label for the combined questions.

### Reference prices

Paid route of the same model, USD per million tokens (input, output), from the portfolio sheet: gpt-oss-20b 0.075 and 0.30 (Groq pricing page, read on 2026-10-21); gpt-oss-120b 0.15 and 0.60 (OpenRouter, portfolio of 2026-09-28); qwen3.8-27b 0.80 and 4.00 (Groq, 2026-10-21). dots-3-note and north-mini-code have no documented paid route (N/A), so they cannot be ranked by price. They are free on OpenRouter and correct on F1 and F3, but they are not the first model there for two reasons: a price rule needs a price, and the OpenRouter free routes are limited to 50 requests per day, which a first-line model cannot depend on. In the simulator they come after every priced model, as a fallback. With an assumed envelope of 1 000 input and 300 output tokens per request, one request costs 0.000165 USD on gpt-oss-20b, 0.00033 USD on gpt-oss-120b and 0.002 USD on qwen3.8-27b.

### The rule

First model: the cheapest model by reference price that answered every question of the family correctly in TD 1. Fallback, in the order of the branches of `choose`: the next eligible model on included capacity, then wait for the free quota to refill if the request can wait, then the paid gpt-oss-120b route if it fits the budget (0.00033 USD per request), then abstain.

Declared panel **P** = {gpt-oss-120b, gpt-oss-20b, qwen3.8-27b}, used for every "2-of-3" below (k = 2, a value needs two votes, no value is invented when none reaches k). P never holds qwen3.8-27b and dots-3-note together (see the panel results below). "Zero check" is Pair B's population check: a result of 0 is not accepted when the targeted population is not empty.

| Family | First model (TD 1 evidence) | Internal dashboard | Customer-facing figure | Payout | Fallback |
|---|---|---|---|---|---|
| F1 period | gpt-oss-20b, 6/6 | none | 2-of-3 on P | 3-of-5 quorum, then human review | gpt-oss-120b, then wait, then paid route, then abstain |
| F3 product list | gpt-oss-20b, 4/4 | none | 2-of-3 on P | 3-of-5 quorum, then human review | gpt-oss-120b, then wait, then paid route, then abstain |
| F4 combinations | gpt-oss-20b, 5/5 | 2-of-3 on P | 2-of-3 on P | reference check or human review | gpt-oss-120b, then wait, then paid route, then abstain |
| F2 age at a date | gpt-oss-120b, 4/4 (the only model without an error) | read-only execution and zero check | 2-of-3 on P and zero check | reference check or human review | no other model is eligible: wait for refill, then paid gpt-oss-120b route, then abstain |
| F2b age at the order | gpt-oss-120b, 1/1 | 2-of-3 on P and zero check | 2-of-3 on P and zero check | reference check or human review | no other model is eligible: wait for refill, then paid gpt-oss-120b route, then abstain |

Consistency with the constraint of the assignment:
- `none` appears only for an internal dashboard, on F1 and F3, where the first model had 100 % in TD 1 on at least four questions.
- F4 has 5/5 for gpt-oss-20b, but it is the same model that failed two of four plain age questions (F2). The age logic is therefore not stable for this model, and F4 keeps a quorum even for a dashboard.
- F2b rests on a single question (C10). A 100 % rate on one cell does not show reliability, so `none` is refused whatever the model.
- Any figure that reaches a customer or triggers a payout requires a quorum or a deterministic check, whatever the family.
- The F2 dashboard check is the read-only execution of the query plus the zero check. Read-only execution alone does not catch a wrong 0: the two wrong zeros of C09 are valid SQL that executes without error.
- Including gpt-oss-120b in the panel is not enough. On C09, qwen3.8-27b and dots-3-note both returned 0 instead of 487 980, while gpt-oss-120b and gpt-oss-20b returned the reference. The panel {gpt-oss-120b, qwen3.8-27b, dots-3-note} contains gpt-oss-120b and still accepts the wrong 0, because the two weaker models outvote it (Step 2, and the cross-review by Pair B). The panel therefore has to be declared, and it must not hold qwen3.8-27b and dots-3-note together. For the age families, the zero check is added as a second defence.

### 2-of-3 panels evaluated on the TD 1 traces

Each panel was evaluated with k = 2 on the twenty questions (the final result of each cell, compared with the reference only after the decision):

| Panel | Correct consensus | Abstentions | Wrong consensus | Questions not correct |
|---|---|---|---|---|
| gpt-oss-120b, gpt-oss-20b, qwen3.8-27b (**P**) | 20 | 0 | 0 | none |
| gpt-oss-120b, gpt-oss-20b, dots-3-note | 20 | 0 | 0 | none |
| gpt-oss-120b, gpt-oss-20b, north-mini-code | 18 | 2 | 0 | C02, C11 abstain |
| gpt-oss-120b, qwen3.8-27b, north-mini-code | 15 | 5 | 0 | C09, C10, C16, C17, C19 abstain |
| gpt-oss-120b, qwen3.8-27b, dots-3-note | 16 | 3 | **1** | **C09 wrong (0)**; C10, C16, C17 abstain |
| gpt-oss-20b, qwen3.8-27b, dots-3-note | 16 | 3 | **1** | **C09 wrong (0)**; C10, C16, C17 abstain |
| qwen3.8-27b, dots-3-note, north-mini-code | 13 | 6 | **1** | **C09 wrong (0)**; C08, C10, C16, C17, C18, C19 abstain |

The only wrong consensus of the batch appears in the three panels that contain qwen3.8-27b and dots-3-note together. P and {gpt-oss-120b, gpt-oss-20b, dots-3-note} both reach 20/20. We keep P because its three members run on one provider, Groq, with documented paid prices, whereas dots-3-note has no documented paid route. Two caveats: P was chosen after reading these traces, so its 20/20 is an optimistic in-sample figure, and gpt-oss-120b and gpt-oss-20b belong to the same model family, so their errors may be correlated (in TD 1 the two errors of gpt-oss-20b, C02 and C11, were outvoted by the two other members).

**Coverage versus independence.** P holds two gpt-oss models, which Step 2 counts as one family. A panel of distinct families that does not hold qwen3.8-27b and dots-3-note together is {gpt-oss-120b, qwen3.8-27b, north-mini-code}, the fixed panel of Step 1: it gives 15 correct consensus, 5 abstentions and 0 wrong consensus, so it never fails silently but abstains on a quarter of the questions (C09, C10, C16, C17, C19). P covers the twenty questions, at the price of a possible correlation between its two gpt-oss members. We keep P for customer-facing figures because an abstention only delays the answer, while the age families also pass the zero check and payouts need a reference check or a human review on top. If an error shared by the two gpt-oss models appears on a new question, the rule switches to the distinct-family panel, and a disagreement inside P is treated as an abstention.

Why these checks. A dashboard error is visible and cheap to fix, so a model with a perfect record may answer alone on the simple families. A figure shown to a customer cannot be corrected silently, so two independent models must agree. A payout is irreversible, so on top of the quorum a deterministic recomputation or a human review closes the loop.

### Simulator: before and after

The kit simulator ([routage-avant.jsonl](../routage-avant.jsonl)) uses three fictitious resources (a small free model of level 1, a senior subscription of level 3 with an allocation of 0.04, a senior token-priced API of level 3 with a cash cost of 0.30). The adapted version ([routage-apres.jsonl](../routage-apres.jsonl)) uses our five TD 1 models, one paid route (gpt-oss-120b on OpenRouter), a family and a use per request, and the check function above. Every `reason` now cites the TD 1 cells that justify it. The four branches of `choose` are unchanged: included capacity, defer, paid route within budget, abstain.

| Scenario | Before | After |
|---|---|---|
| simple | run, small-free | run, gpt-oss-20b free plan, F1 dashboard, check none (6/6 on C01, C04, C05, C06, C07, C20) |
| complex | run, senior-subscription | run, gpt-oss-120b free plan, F2 dashboard, read-only execution and zero check (4/4 on C02, C08, C09, C11) |
| deferrable | defer 60 min, senior-subscription | defer 60 min, gpt-oss-120b free plan, F2 |
| urgent | run, senior-api (0.30) | run, gpt-oss-120b paid route (0.00033), F2 |
| budget exhausted | abstain | abstain, "F2 needs level 3", check "not applicable (request not run)" |
| high impact | run, senior-subscription, source verification and human review | run, gpt-oss-120b free plan, F2 payout, reference check or human review |
| unknown capability | abstain | abstain, "family never evaluated in TD 1", check "not applicable (request not run)" |
| customer figure (new) | | run, gpt-oss-20b free plan, F1 customer, 2-of-3 on P |
| combination dashboard (new) | | run, gpt-oss-20b free plan, F4 dashboard, 2-of-3 on P |

An abstention used to display a quorum check on a request that was not run, which made the trace confusing (remark of the cross-review by Pair B). The check now reads "not applicable (request not run)".

The seven original scenarios give the same action as before (run, run, defer, run, abstain, run, abstain). What changes is the resource, the check and the reason. The levels come from TD 1: level 3 (F2) is reached only by gpt-oss-120b; level 2 (F4, F2b) by gpt-oss-20b; level 1 (F1, F3) by every model. In the "exhausted" scenarios, we assume the Groq free plan refills in 60 minutes; this is a scenario input.

### Effect of the cross-review on the results

The first version of the rule and of the simulator (commit def1d6e) was changed after the cross-review by Pair B, so its results and its outputs differ from the final ones. The actions of the simulator did not change; the checks, the panel and the figures did.

| Item | First version (def1d6e) | After round 1 (e6d376b) | After round 2 (final) |
|---|---|---|---|
| Quorum for F2 and F2b figures | "2-of-3 quorum anchored on gpt-oss-120b", panel not declared | panel P declared; zero check added for F2 and F2b | unchanged, with the coverage-versus-independence trade-off stated |
| Wrong consensus on C09 | possible: {gpt-oss-120b, qwen3.8-27b, dots-3-note} accepts the wrong 0 and anchoring on gpt-oss-120b does not prevent it | none in P: 20 correct, 0 abstention, 0 wrong on the TD 1 traces | unchanged |
| Check of an abstention (budget exhausted, unknown capability) | a check was displayed for a request that is not run ("deterministic check", "2-of-3 quorum") | "not applicable (request not run)" | unchanged |
| F2 dashboard check | "deterministic check (read-only execution and plausibility)", which does not catch a wrong 0 | unchanged | read-only execution and zero check |
| Fallback of F2 and F2b | "wait for refill, then abstain", while the "urgent" scenario runs the paid route | unchanged | wait, then paid gpt-oss-120b route, then abstain |
| Price ranking | free models left out without explanation | unchanged | explanation added |
| Outputs [routage-apres.jsonl](../routage-apres.jsonl) | nine scenarios, checks of the first version | checks of the abstentions and of the customer figures changed | checks of the three F2 dashboard scenarios (complex, deferrable, urgent) changed |

The seven original scenarios keep the same actions as the kit in all three versions (run, run, defer, run, abstain, run, abstain). The evidence of the first version stays in the history of the repository.

### Priority analysis: included capacity before deferring

In `choose`, a resource enters the first branch when it is eligible, `available` and `cash == 0`. A subscription resource with `allocation > 0` fits that test: it can answer now at no new cost. An exhausted free resource (`allocation == 0`, `available == False`) does not fit it; it is only considered in the second branch, and only if the request can wait and the refill falls before `deadline_minutes`. So the code answers now whenever it can, and defers only when nothing eligible is available.

Reasons for this priority:
1. **Time.** Capacity available now answers in one call. A deferral spends `reset_minutes` of the deadline, 60 minutes in our scenarios, and leaves less room for a second attempt.
2. **A refill is a promise, not a measurement.** The docstring states it: reaching a reset time does not prove that capacity is available. The resource must be measured again at wake-up, and it can still be exhausted, for instance after another user consumed the refill.
3. **No new spending.** The subscription is already paid; using it costs nothing more, whereas waiting delivers no value in the meantime.

The priority should be reversed when the already available capacity is scarce and worth more elsewhere, and the waiting is cheap. Concretely: when the allocation is small (the kit's subscription has 0.04) and is needed for requests that only it can serve (level 3, urgent or high impact), while the current request is easy, not urgent, has a deadline much longer than the refill time, and the refill has proven reliable. Then deferring to the free resource keeps the scarce allocation for the requests that need it.

In our adapted rule the same order applies to the paid route. In the "deferrable" scenario, the paid gpt-oss-120b route (0.00033 USD) is available and inside the budget (0.001), but the simulator still defers to the free Groq plan, because the defer branch comes before the paid branch. The order should be reversed when the cost of waiting exceeds 0.00033 USD per request, for example for a payout with a close deadline; the "urgent" scenario shows this case, where `can_wait` is false and the paid route runs.

### Limitations

- Small samples: four to six questions per family, and a single question for F2b. The rates are a routing hypothesis for this batch, not a ranking of the models.
- Panel P was selected on the same twenty questions it is evaluated on; its 20/20 is not a guarantee on new questions. It holds two models of the same family, so their errors may be correlated.
- Variability: temperature 0 does not guarantee identical answers on a new run. The inconsistency of gpt-oss-20b between F2 (2/4) and F4 (5/5) is probably such variability, which is why F4 keeps a quorum.
- Prices come from two sources and two dates (portfolio of 2026-09-28, Groq pages of 2026-10-21). dots-3-note and north-mini-code have no documented paid route.
- The token envelope (1 000 input, 300 output) is an assumption; the TD 1 traces show about 600 input and 150 to 260 output tokens on average.
- Latency is not part of the rule, although it was measured: median 551 ms for gpt-oss-20b, 883 ms for gpt-oss-120b, 650 ms for qwen3.8-27b, 2.5 s and 2.9 s for the two OpenRouter models.
- Quotas are simulated. In TD 1, the Groq output-tokens-per-minute limit (1 000) caused five HTTP 429 answers on qwen3.8-27b, and the OpenRouter free routes are limited to 50 requests per day; a real deployment must measure them.

### Questions no free model handles alone

All five TD 1 routes are free (the Groq free plan and the OpenRouter `:free` routes). On F2 and F2b, four of the five models made at least one error, and only gpt-oss-120b has none; on F2b that rests on a single question. No single free model can therefore be trusted alone on the age questions, and gpt-oss-120b depends on one free plan whose quota limits an answer to what the plan allows (Groq: 1 000 requests per day, 8 000 tokens per minute). These families set the checking cost carried into TD 3: every customer-facing or payout figure about a customer's age needs a quorum or a deterministic check on top of the model call.

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
- **Pair C response, applied.** The five remarks are answered in the Step 3 section: the trade-off between coverage and independence of panel P is stated with the figures of the distinct-family panel (15 / 5 / 0); the fallback of F2 and F2b now includes the paid route; the F2 dashboard check is read-only execution plus the zero check (the simulator and `routage-apres.jsonl` were regenerated); the free models are explained in the price ranking; the wording on the free model is corrected. The section is integrated. The results of the first version and the final ones are compared in "Effect of the cross-review on the results".

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
| Nayl-git (Nayl SAIFOUDINE) | C | Adaptation of the routing simulator (commits def1d6e, e6d376b); rule, panel evaluation and Step 3 section revised after the cross-review; `td1/` and `td2/` folders |
| francktank (Franck TANKHAPANYA) | C | *to complete* |
| SinaESILV (Sina BALAEI) | C | *to complete* |

**Pair C note.** Pair C is a trio: Franck TANKHAPANYA, Sina BALAEI and Nayl SAIFOUDINE. The commits of the Step 3 files are under the `Nayl-git` account. The contribution of each member is to be completed by the trio.

**Pair B note.** The three members of Pair B worked together on one machine, so every Pair B commit is under the `enkimlt` account. The work was split roughly equally between the three. It covers the wrong-consensus analysis of C09 (scan, declared quorums and panels, SQL cause and delta query, population check, DEMO-VOTE; [td2/](../td2/)), the Step 2 section of this report, and the cross-review of Steps 1 and 3.

## Use of coding assistance

As the assignment requires, we declare that a coding assistant was used for the analysis script of Step 2, for Step 3 (the TD 1 rates by family, the adaptation of `atelier-routage.py`, the evaluation of the 2-of-3 panels and the draft of the section) and for drafting this report. Every figure comes from SQL executed read-only on the database or from the stored traces; the members remain responsible for the explanations.

## Next steps (TD 3)

- The price of checking: the age questions, which no free model except gpt-oss-120b answers alone in our batch, set the cost of the quorum or the reference in TD 3.
- Write a model-free population query for every family, so that the zero check can run without the reference.
- Choose the use case and its cost of error, then the configuration.
