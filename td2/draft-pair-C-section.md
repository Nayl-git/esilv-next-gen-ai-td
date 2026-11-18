## Step 3: routing rule (Pair C)

> Draft section for `reports/td2.md`. Paste it under the step 3 heading once reviewed by Pair C.

### Goal and method

Each question goes to the cheapest model that is still reliable enough for its family, with a check that depends on the cost of an error. Everything below uses only the stored TD 1 traces ([traces-td1.csv](../traces-td1.csv)), the references ([reference-td1.csv](../reference-td1.csv)), the portfolio sheet ([five-model-summary-en.csv](../five-model-summary-en.csv)) and the simulator [atelier-routage.py](../atelier-routage.py). No network call was made. The simulator is a simulation: its resources, quotas and costs are scenario inputs, not provider measurements.

### TD 1 rates by family

Final result of each cell (last attempt), `correct / cases`. The five families partition the twenty questions. Reproduce with `python td2/rates_by_family.py` (add `--failures` for the failing cells).

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
| F1 period | gpt-oss-20b, 6/6 | none | 2-of-3 on P | 3-of-5 quorum, recomputation, human review | gpt-oss-120b, then wait, then paid route, then abstain |
| F3 product list | gpt-oss-20b, 4/4 | none | 2-of-3 on P | 3-of-5 quorum, recomputation, human review | gpt-oss-120b, then wait, then paid route, then abstain |
| F4 combinations | gpt-oss-20b, 5/5 | 2-of-3 on P | 2-of-3 on P | 3-of-5 quorum, recomputation, human review | gpt-oss-120b, then wait, then paid route, then abstain |
| F2 age at a date | gpt-oss-120b, 4/4 (the only model without an error) | read-only execution and zero check | 2-of-3 on P and zero check | 3-of-5 quorum, recomputation, human review | no other model is eligible: wait for refill, then paid gpt-oss-120b route, then abstain |
| F2b age at the order | gpt-oss-120b, 1/1 | 2-of-3 on P and zero check | 2-of-3 on P and zero check | 3-of-5 quorum, recomputation, human review | no other model is eligible: wait for refill, then paid gpt-oss-120b route, then abstain |

**Payout control.** A payout needs a control that exists in production, so it cannot rely on the reference of the lab. It is, in this order: the 3-of-5 quorum; a **deterministic recomputation**, a parameterised SQL template written once per family without any model, run on the same database with the parameters of the question (dates, product list, age and reference date), whose result must equal the value of the model; and a human review before the payment. The template is only as wide as the families we know: a free-text question outside them cannot be recomputed. Status today: the recomputation is implemented for the five families in [td2/recompute.py](../td2/recompute.py). One query builder with three optional filters (period, product list, completed age at a date or at the date of each order) produces a parameterised query, run read-only; the values never enter the SQL text. For the twenty TD 1 questions it equals the lab reference and a third path, plain Python on the CSV files, figure for figure. Applied to the 100 TD 1 cells (`python td2/recompute.py --traces`), it rejects the 19 wrong figures, 7 of them zeros, and accepts the 77 correct ones; the 4 cells without a figure (invalid SQL) have nothing to check. Its age rule is a birth-date window, a formulation different from the `strftime` year difference of the reference queries. Limits: the parameters are written by hand from the questions and must come from the structured request of a service, because if a model reads the question and produces them the control is no longer model-free; a free-text question outside the five families cannot be recomputed; a reference date or an order date of 29 February is not handled (none exists in the base). On TD 1 the recomputed value equals the lab reference, so its verdicts are the lab's verdicts: what it adds is the same control on a parameterised query that does not need the reference. The control is the same for every family.

Consistency with the constraint of the assignment:
- `none` appears only for an internal dashboard, on F1 and F3, where the first model had 100 % in TD 1 on at least four questions.
- F4 has 5/5 for gpt-oss-20b, but it is the same model that failed two of four plain age questions (F2). All five questions of F4 (C15 to C19) contain an age filter, so the comparison holds and the age logic is not stable for this model, and F4 keeps a quorum even for a dashboard.
- F2b rests on a single question (C10). A 100 % rate on one cell does not show reliability, so `none` is refused whatever the model.
- F2: gpt-oss-120b has 4/4, so `none` would be admissible by the criterion used for F1 and F3 (100 % on at least four questions). We still require a control, for two reasons. Four questions are a small sample: a model that is wrong on one question in five would still score 4/4 about 41 % of the time (0.8 to the power 4). And the errors of the other models on this family are silent: a valid query that returns a 0 or a plausible wrong amount, never an error message (C09: two zeros from valid SQL), so nothing in an answer shows that it is wrong. The simulator therefore grants `none` to F1 and F3 only.
- Any figure that reaches a customer or triggers a payout requires a quorum or a deterministic check, whatever the family.
- The F2 dashboard check is the read-only execution of the query plus the zero check. Read-only execution alone does not catch a wrong 0: the two wrong zeros of C09 are valid SQL that executes without error.
- Including gpt-oss-120b in the panel is not enough. On C09, qwen3.8-27b and dots-3-note both returned 0 instead of 487 980, while gpt-oss-120b and gpt-oss-20b returned the reference. The panel {gpt-oss-120b, qwen3.8-27b, dots-3-note} contains gpt-oss-120b and still accepts the wrong 0, because the two weaker models outvote it (Step 2, and the cross-review by Pair B). The panel therefore has to be declared, and it must not hold qwen3.8-27b and dots-3-note together. For the age families, the zero check is added as a second defence.

### 2-of-3 panels evaluated on the TD 1 traces

Each panel was evaluated with k = 2 on the twenty questions (the final result of each cell, compared with the reference only after the decision). Reproduce with `python td2/panels.py`; it lists all ten panels of three models, and the table below shows seven of them. `--panel PROVIDER:MODEL PROVIDER:MODEL PROVIDER:MODEL` evaluates one panel.

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

**Coverage versus independence.** P holds two gpt-oss models, which Step 2 counts as one family. A panel of distinct families that does not hold qwen3.8-27b and dots-3-note together is {gpt-oss-120b, qwen3.8-27b, north-mini-code}, the fixed panel of Step 1: it gives 15 correct consensus, 5 abstentions and 0 wrong consensus, so it never fails silently but abstains on a quarter of the questions (C09, C10, C16, C17, C19). P covers the twenty questions, at the price of a possible correlation between its two gpt-oss members. We keep P for customer-facing figures because an abstention only delays the answer, while the age families also pass the zero check and payouts get a deterministic recomputation and a human review on top of the quorum. If an error shared by the two gpt-oss models appears on a new question, the rule switches to the distinct-family panel, and a disagreement inside P is treated as an abstention. When P abstains, the model does not answer: the request goes to the deterministic recomputation of [td2/recompute.py](../td2/recompute.py) and, for a payout, to a human review.

Why these checks. A dashboard error is visible and cheap to fix, so a model with a perfect record may answer alone on the simple families. A figure shown to a customer cannot be corrected silently, so two independent models must agree. A payout is irreversible, so the 3-of-5 quorum is followed by a deterministic recomputation and by a human review.

### Simulator: before and after

The kit simulator ([routage-avant.jsonl](../routage-avant.jsonl)) uses three fictitious resources (a small free model of level 1, a senior subscription of level 3 with an allocation of 0.04, a senior token-priced API of level 3 with a cash cost of 0.30). The adapted version ([routage-apres.jsonl](../routage-apres.jsonl)) uses our five TD 1 models, one paid route (gpt-oss-120b on OpenRouter), a family and a use per request, and the check function above. Every `reason` now cites the TD 1 cells that justify it. The four branches of `choose` are unchanged: included capacity, defer, paid route within budget, abstain.

| Scenario | Before | After |
|---|---|---|
| simple | run, small-free | run, gpt-oss-20b free plan, F1 dashboard, check none (6/6 on C01, C04, C05, C06, C07, C20) |
| complex | run, senior-subscription | run, gpt-oss-120b free plan, F2 dashboard, read-only execution and zero check (4/4 on C02, C08, C09, C11) |
| deferrable | defer 60 min, senior-subscription | defer 60 min, gpt-oss-120b free plan, F2 |
| urgent | run, senior-api (0.30) | run, gpt-oss-120b paid route (0.00033), F2 |
| budget exhausted | abstain | abstain, "F2 needs level 3", check "not applicable (request not run)" |
| high impact | run, senior-subscription, source verification and human review | run, gpt-oss-120b free plan, F2 payout, 3-of-5 quorum, then deterministic recomputation, then human review |
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

#### Second cross-review (Pair A)

Pair A read Steps 2 and 3 without running anything (`peer-review-pair-A-section.txt`). Four of its remarks changed our section, so the results differ again from the previous version:

| Item | Before | After |
|---|---|---|
| Payout check | "reference check or human review" for F2, F2b and F4, "3-of-5 quorum, then human review" for F1 and F3: the lab reference does not exist in production, and F2, where the wrong consensus appeared, had the weakest control | the same control for every family: 3-of-5 quorum, deterministic recomputation, human review; the recomputation is implemented for F2 only |
| `none` refused on F2 although gpt-oss-120b has 4/4 | no reason given | two reasons stated: a small sample, and silent errors |
| Groq limits | "1 000 output tokens per minute" and "8 000 tokens per minute" without saying that they are two limits | two limits, each with its source |
| Scenario "high impact" in [routage-apres.jsonl](../routage-apres.jsonl) | check "reference check or human review" | check "3-of-5 quorum, then deterministic recomputation, then human review" |

The actions of the simulator did not change. The recomputation that the table above calls "implemented for F2 only" was then written for the five families ([td2/recompute.py](../td2/recompute.py)). The panel of two gpt-oss models is discussed in "Coverage versus independence", and the contributions of the trio are still to complete.

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
- The population check of Pair B is model-free only for F2 (C02, C08, C09, C11); for C10, C15 and C16 it uses the reference query (see the cross-review by Pair C of Step 2). For F2b and F4, the control that does not need the reference is the recomputation of [td2/recompute.py](../td2/recompute.py), which rejects every wrong 0 of TD 1. It depends on parameters that come from a structured request, not from a model.
- Variability: temperature 0 does not guarantee identical answers on a new run. The inconsistency of gpt-oss-20b between F2 (2/4) and F4 (5/5) is probably such variability, which is why F4 keeps a quorum.
- Prices come from two sources and two dates (portfolio of 2026-09-28, Groq pages of 2026-10-21). dots-3-note and north-mini-code have no documented paid route.
- The token envelope (1 000 input, 300 output) is an assumption; the TD 1 traces show about 600 input and 150 to 260 output tokens on average.
- Latency is not part of the rule, although it was measured: median 551 ms for gpt-oss-20b, 883 ms for gpt-oss-120b, 650 ms for qwen3.8-27b, 2.5 s and 2.9 s for the two OpenRouter models.
- Quotas are simulated. Two different Groq limits appear in TD 1 and must not be confused. The organisation limits read in the Groq console on 2026-10-19 for the three Groq models are 30 requests per minute, 1 000 requests per day, 8 000 tokens per minute (TPM) and 200 000 tokens per day (a reading on one member's account, with no copy in the repository, so the only evidence of the TPM limit that a reader can check is the following one); the HTTP 429 of gpt-oss-20b on C19 names that TPM limit ("Limit 8000", [traces-B.csv](../traces-B.csv)). The five HTTP 429 answers of qwen3.8-27b name another limit, 1 000 **output** tokens per minute (OTPM, "Limit 1000" in the error field of [traces-D.csv](../traces-D.csv)), which the console dialog did not show. The OpenRouter free routes are limited to 50 requests per day. A real deployment must measure these limits.

### Questions no free model handles alone

All five TD 1 routes are free (the Groq free plan and the OpenRouter `:free` routes). On F2 and F2b, four of the five models made at least one error, and only gpt-oss-120b has none; on F2b that rests on a single question. No single free model can therefore be trusted alone on the age questions, and gpt-oss-120b depends on one free plan whose quota limits an answer to what the plan allows (Groq console: 1 000 requests per day and 8 000 tokens per minute for the organisation; qwen3.8-27b also hit a separate limit of 1 000 output tokens per minute, see the limitations). These families set the checking cost carried into TD 3: every customer-facing or payout figure about a customer's age needs a quorum or a deterministic check on top of the model call.

### Contributions

Pair C is a trio: Franck TANKHAPANYA, Sina BALAEI and Nayl SAIFOUDINE. To fill in: who computed the rates, who adapted `RESOURCES` and `choose`, who wrote the analysis. A coding assistant was used to compute the rates from the traces, to adapt `atelier-routage.py` and to draft this section; the members of Pair C must be able to explain the rule, the simulator branches and the figures above.
