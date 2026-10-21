# TD 1 report: five free models on twenty SQL revenue questions

Session 1, 21 October 2026. Kit pack 2026-10-14-students-1, database `data/boutique.sqlite` (seed 20260925). All times in this report are UTC, as in the traces.

## Summary

We computed and checked the twenty reference values, then ran the five required models on the twenty questions: 100 base cells, all executed with real calls. 77 of the 100 final results are correct, 19 return a wrong value and 4 return invalid SQL. There was no access failure in the final results.

Every model answers all period questions (6/6) and all product-list questions (4/4) correctly. The failures are all on questions that filter on age, alone or combined with other filters. Only `groq:openai/gpt-oss-120b` gets 20/20.

## Work completed

| Step | Status | Evidence |
|---|---|---|
| Environment and access checks before the session | done | `check_access.py` output and screenshot, kept locally as personal files (excluded by `.gitignore`) |
| Step 1: twenty references, independently checked | done | [reference-td1.csv](../reference-td1.csv) |
| Step 2: five model batches, 100 base cells | done | [traces-A.csv](../traces-A.csv), [traces-B.csv](../traces-B.csv), [traces-C.csv](../traces-C.csv), [traces-D.csv](../traces-D.csv), [traces-E2.csv](../traces-E2.csv), with their `state-*.jsonl` files |
| Merged trace table | done | [traces-td1.csv](../traces-td1.csv) and [traces-td1.jsonl](../traces-td1.jsonl): 114 attempts, 100 cells |
| Step 3: model/question comparison | done | [model-question-comparison-en.csv](../model-question-comparison-en.csv): 100 final rows |
| Step 3: five-model summary | done | [five-model-summary-en.csv](../five-model-summary-en.csv) |
| Prompt, as used | done, unchanged from the kit | `SYSTEM_PROMPT` and `USER_PROMPT_TEMPLATE` in [skeleton-multi-llm-en.py](../skeleton-multi-llm-en.py), lines 104 to 121 |

All rows in the traces are of nature `real`. No replayed or simulated row is used in any count of this report.

## Step 1: the references

The twenty questions were shared among the members. Each reference is a SQLite `SELECT` executed on the read-only database, and its value is stored in `reference-td1.csv`.

**Independent checks.** We checked every value in two ways:
- the stored SQL was executed again and had to return its stored value;
- the value was recomputed in pure Python from the CSV files, with an explicit completed-age function.

For C07 and C08, a second SQL formulation gave the same value: a filter on the calendar day for C07, and the birth-date window from 2000-09-25 to 2001-09-24 for C08.

**Errors found and fixed before the model runs.** The first consolidated version had 8 faulty lines:
- C05 and C06 used the period of another question;
- C13 and C14 used tables and columns that do not exist (`order_lines`, `unit_price_cents`, `product.name`), so their values could not come from their SQL;
- C15 was a copy of the C16 query, without the period filter;
- C11, C12 and C16 had no value.

All 8 were corrected. The final file has 20 lines whose SQL executes and returns the stored value.

**Comparison with the published values.** The 20 values are equal to the reference values published for the session (page `reference-values-td1-en`, pack 2026-10-18-students-1). Our independent Python computation also matches them, which confirms that the published pack and our 2026-10-14 kit use the same database.

## Step 2: the model batches

| Op. | Model | Trace files | Attempts | Retries | Runs (UTC) | Median latency | Output tokens (mean) |
|---|---|---|---|---|---|---|---|
| A | `groq:openai/gpt-oss-120b` | traces-A.csv, state-A.jsonl | 20 | 0 | 13:12–13:14 | 883 ms | 262 |
| B | `groq:openai/gpt-oss-20b` | traces-B.csv, state-B.jsonl | 21 | 1 (C19) | 13:17–13:18 | 551 ms | 249 |
| C | `openrouter:cohere/north-mini-code:free` | traces-C.csv, state-C.jsonl | 20 | 0 | 13:27–13:32 | 2 520 ms | 144 |
| D | `groq:qwen/qwen3.8-27b` | traces-D.csv, state-D.jsonl | 25 | 5 | 13:37–13:40 | 650 ms | 143 |
| E | `openrouter:dots-studio/dots-3-note-preview:free` | traces-E2.csv, state-E2.jsonl (first run: state-E.jsonl) | 20 (+8) | 0 | 13:50–13:52 | 2 860 ms | 197 |

Latency and tokens are computed on the attempts that returned HTTP 200. The two OpenRouter models are 3 to 5 times slower than the Groq models in this run.

**Retries.** Six cells received HTTP 429 on their first attempt and were answered on their second attempt. That is one retry per cell, within the protocol limit.
- B C19: the Groq tokens-per-minute limit.
- D C08, C16, C18, C19 and C20: the Groq output-tokens-per-minute limit, "OTPM: Limit 1000" in the error field.

Both attempts are kept in the traces. The final row of each cell in the comparison mentions "last attempt 2".

**Operator E's first run.** The first E run, `state-E.jsonl`, failed with **HTTP 401 "User not found"** on its 8 attempts: the API key had been entered with an extra character. These attempts are access errors and contain no model answer. They are kept in `state-E.jsonl` and in the merged traces. After the key was corrected, the 20 cells were run again as a new experiment in `state-E2.jsonl` and `traces-E2.csv`, with the same prompt and the same references.

**Measurements.** OpenRouter returned a native cost of 0 for every call, as expected for `:free` routes. Groq does not return a native cost, so `cost_native` stays empty for the Groq rows. Reasoning tokens are reported for the two gpt-oss models only, with a mean of 158 and 142 tokens.

**Prompt fingerprint.** The same `prompt_sha256` is recorded for all five models on each question. The differences between models therefore cannot come from the wording.

## Results

`✓` correct, `✗` wrong value, `S` invalid SQL (`sql_invalid`). Final result of each cell, from [model-question-comparison-en.csv](../model-question-comparison-en.csv).

| Model | C01 | C02 | C03 | C04 | C05 | C06 | C07 | C08 | C09 | C10 | C11 | C12 | C13 | C14 | C15 | C16 | C17 | C18 | C19 | C20 | Correct |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `groq:openai/gpt-oss-120b` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | 20/20 |
| `groq:openai/gpt-oss-20b` | ✓ | ✗ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | 18/20 |
| `groq:qwen/qwen3.8-27b` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | ✗ | ✓ | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ | ✓ | ✗ | ✓ | 14/20 |
| `openrouter:dots-studio/dots-3-note-preview:free` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | ✗ | S | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | S | ✗ | ✓ | ✓ | 14/20 |
| `openrouter:cohere/north-mini-code:free` | ✓ | ✗ | ✓ | ✓ | ✓ | ✓ | ✓ | S | S | ✗ | ✗ | ✓ | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✓ | 11/20 |
| Failures | 0 | 2 | 0 | 0 | 0 | 0 | 0 | 2 | 3 | 3 | 2 | 0 | 0 | 0 | 1 | 3 | 3 | 2 | 2 | 0 | |

By question family. The period family is C01, C04 to C07 and C20; the age family is C02 and C08 to C11; the product family is C03 and C12 to C14; the combined family is C15 to C19. Combined questions are counted only in the combined column.

| Model | Period | Age | Product | Combined |
|---|---|---|---|---|
| gpt-oss-120b | 6/6 | 5/5 | 4/4 | 5/5 |
| gpt-oss-20b | 6/6 | 3/5 | 4/4 | 5/5 |
| qwen3.8-27b | 6/6 | 3/5 | 4/4 | 1/5 |
| dots-3-note | 6/6 | 2/5 | 4/4 | 2/5 |
| north-mini-code | 6/6 | 0/5 | 4/4 | 1/5 |

## Causes of the failures

Each cause below is read from the SQL and error fields of the trace. The full explanation of each cell is in the comparison file. All 23 failures involve the age condition. The prompt states the convention explicitly: completed age, computed from month and day, never from the year difference alone. Several models still did not apply it correctly.

| Cause | Cells |
|---|---|
| Birth-date window not shifted by 25 years, or of the wrong width | gpt-oss-20b C02 (window of the last year, value 0), C11 (5-year window); north-mini-code C11, C17 |
| Off by one day on the anniversary | qwen C16 and C17 (keeps 2000-09-25 and drops 2001-09-25); dots C08 (upper bound) |
| Faulty date arithmetic or text comparison | north-mini-code C02 (`CAST('2026-09' AS INTEGER)`), C10 (month-day cast to an integer), C19 (a `CASE` that returns 24 or 25 for every customer born before the reference date, so `= 25` filters almost nothing); dots C16 (YYYYMMDD arithmetic); qwen C19 (year string compared with a full date) |
| Contradictory conditions, so nothing matches (value 0) | qwen C09 and C15; north-mini-code C16 |
| Question misread | dots C09 ("exactly 25" read as "turns 25 that day", plus an order-date filter); qwen C09 (age computed on the order date instead of the reference date) |
| Age at the time of the order mishandled | qwen C10; north-mini-code C18; dots C18 |
| Invalid SQL | north-mini-code C08 and C09 (a column alias `AS age` inside `WHERE`); dots C10 and C17 (unbalanced parentheses, "incomplete input") |

The two `sql_invalid` answers from dots are not truncated outputs: they use 471 and 387 output tokens, well under the 1 024-token cap. No final failure is an access failure. The only access failures of the session are the 8 HTTP 401 attempts of the first E run and the 6 HTTP 429 attempts that were retried successfully.

## Routing hypothesis from this batch

This hypothesis rests on a single run of 20 questions per model. It is not a general ranking of the models.

- **Period and product-list questions:** every model was correct. The fastest free route, Groq gpt-oss-20b with a median latency of 551 ms, would be enough here.
- **Age questions, alone or combined:** only gpt-oss-120b was correct on all 10. gpt-oss-20b failed 2 of 10, and the other three models failed between 6 and 9 of 10. These questions should be routed to gpt-oss-120b, or checked by several models.
- **Prices:** see [five-model-summary-en.csv](../five-model-summary-en.csv).
  - gpt-oss-120b has a documented paid route in the portfolio: OpenRouter, USD 0.15 per million input tokens and 0.60 per million output tokens (portfolio of 2026-09-28).
  - The paid prices given for gpt-oss-20b and qwen3.8-27b come from Groq's pricing pages, read on 2026-10-21.
  - north-mini-code and dots-3-note are absent from the portfolio, so their prices are N/A.

## Input for TD 2

- **Wrong consensus:** on **C09**, qwen3.8-27b and dots-3-note both return **0** instead of 487 980, and north-mini-code returns invalid SQL. A majority vote among these three models would accept the wrong value. Among all five models, the wrong value 0 ties 2 to 2 with the correct value, which the two gpt-oss models return. This is the case for TD 2's "several models agree on a wrong value".
- **Questions most models miss:** C09, C10, C16 and C17 (3 failures each). All of them involve the completed-age convention.

## Limitations

- **One run per cell, at temperature 0.** Temperature 0 does not guarantee identical answers on a new run, so these results describe this batch only.
- **Small samples:** 20 questions per model and 4 to 6 per family. The family rates have a large uncertainty.
- **Latency depends on the conditions:** the network and the load on the providers at run time. The OpenRouter calls ran later than the Groq calls.
- **Rate limits:** the Groq free-plan limits caused 6 HTTP 429 responses. The protocol's single retry recovered all of them, but a stricter limit would have left cells unfinished.
- **Template change:** the five-model summary template listed `inclusionai/ling-3.0-flash-sante:free` as its third model. We replaced it with `cohere/north-mini-code:free`, the model of the 14 October selection in `modeles-autorises.json` that we actually ran.
- **Different packs:** the published reference values belong to pack 2026-10-18, while our kit is pack 2026-10-14. The database and the 20 values are identical. We did not compare the other files of the two packs.
- **Repository incidents:** a merge conflict was committed with its markers in the comparison file (commit 5f0202e), and several edits made in parallel overwrote each other. These were detected and repaired in commit e9206fa without any data loss. In TD 2, only one member at a time edits a shared file, and each member pulls before editing.

## Contributions

The table below is built from the Git history of this repository. **Each member checks their line and adds their name.**

| GitHub account | Role (to confirm) | Contribution visible in the history |
|---|---|---|
| AmandineBaranger | Operator A | References C01, C02; batch gpt-oss-120b (traces-A, state-A); comparison and summary rows for A; README |
| francktank | Operator B | References C11, C12; batch gpt-oss-20b (traces-B, state-B); comparison rows for B with their explanations; summary rows |
| ambrere | Operator C | References C05, C06, C17 (and an edit of C16); batch north-mini-code (traces-C, state-C); comparison rows for C; summary |
| PierreBOUDRAA | Operator D | References C15, C16; batch qwen3.8-27b (traces-D, state-D); comparison and summary rows for D |
| enkimlt | Operator E | References C18 to C20; batch dots-3-note (state-E, state-E2, traces-E2); merge into traces-td1.csv and traces-td1.jsonl |
| Nayl-git | Repository and checks | Repository set-up (kit, `.gitignore`, `.gitattributes`); references C07, C08 with cross-check queries; verification of the 20 references; fixes of C13 and C14; consistency checks and fixes of the two summaries; this report |
| FeliciaEsilv | References | References C03, C04 |
| nohamsantenac | References | References C09, C10 |
| SinaESILV | References | References C13, C14 |

## Use of coding assistance

As the assignment requires, we declare that a coding assistant (Claude, from Anthropic) was used for the following tasks:
- setting up the repository;
- writing and executing the C07 and C08 reference queries and their cross-checks;
- verifying the 20 references: SQL execution, an independent Python recomputation and the comparison with the published values;
- correcting the C13 and C14 queries;
- the consistency checks and corrections of the two summary files;
- drafting this report.

Every reference value comes from SQL executed on the database and from independent checks. No reference value was taken from a model's answer. The members remain responsible for the explanations, and each member must be able to explain the conventions and the traces of their own part.

## Next steps (TD 2)

- Read `atelier-vote.py` and the expected routing rule. The member who prepares TD 2 still has to be chosen.
- Use the saved traces. TD 2 requires no new network call.
- Study C09 as the wrong-consensus case, and C10, C16 and C17 as the questions most models miss.
- Rotate the roles, as the protocol requires.
