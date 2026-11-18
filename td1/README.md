# TD 1: five free models on twenty SQL revenue questions

Sub-group DIA2-1. Session of 21 October 2026. Assignment: [enonce-td1-en](../enonce-td1-en.md). Session report: [reports/td1.md](../reports/td1.md).

## Result

100 base cells (5 models x 20 questions), all real calls. Final results: 77 correct, 19 wrong values, 4 invalid SQL, no access failure.

| Model | Correct | Operator files |
|---|---|---|
| `groq:openai/gpt-oss-120b` | 20/20 | [traces-A.csv](../traces-A.csv), [state-A.jsonl](../state-A.jsonl) |
| `groq:openai/gpt-oss-20b` | 18/20 | [traces-B.csv](../traces-B.csv), [state-B.jsonl](../state-B.jsonl) |
| `groq:qwen/qwen3.8-27b` | 14/20 | [traces-D.csv](../traces-D.csv), [state-D.jsonl](../state-D.jsonl) |
| `openrouter:dots-studio/dots-3-note-preview:free` | 14/20 | [traces-E2.csv](../traces-E2.csv), [state-E2.jsonl](../state-E2.jsonl); first run refused with HTTP 401: [state-E.jsonl](../state-E.jsonl) |
| `openrouter:cohere/north-mini-code:free` | 11/20 | [traces-C.csv](../traces-C.csv), [state-C.jsonl](../state-C.jsonl) |

Every model answers all period and product-list questions correctly. All failures involve the completed-age convention.

## Deliverables

| Deliverable | File |
|---|---|
| Twenty references, independently checked | [reference-td1.csv](../reference-td1.csv) |
| Merged traces, one line per attempt | [traces-td1.csv](../traces-td1.csv), [traces-td1.jsonl](../traces-td1.jsonl) |
| Final result of each model/question, with its cause | [model-question-comparison-en.csv](../model-question-comparison-en.csv) |
| The five models: index, prices, access, results by family | [five-model-summary-en.csv](../five-model-summary-en.csv) |
| The prompt, as used | `SYSTEM_PROMPT` and `USER_PROMPT_TEMPLATE` in [skeleton-multi-llm-en.py](../skeleton-multi-llm-en.py), lines 104 to 121, unchanged from the kit |
| Session report | [reports/td1.md](../reports/td1.md) |

Cross-check queries written for C07 and C08: [C07.sql](../C07.sql), [C07-recoupement.sql](../C07-recoupement.sql), [C08.sql](../C08.sql), [C08-recoupement.sql](../C08-recoupement.sql).

## Reproduce the checks

All commands run from the repository root, offline, in the virtual environment of the kit.

```
python verify-data.py                                          # database and CSV hashes: last object has "ok": true
python skeleton-multi-llm-en.py --rates --state traces-td1.jsonl   # accuracy per model, from the stored traces
```

No new network call is needed to read the TD 1 results.
