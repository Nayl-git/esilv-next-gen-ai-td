# TD 2: cross-review of Step 1 (Pair A) by Pair C

Reviewers: Pair C (Franck TANKHAPANYA, Sina BALAEI, Nayl SAIFOUDINE). Reviewed: Pair A, Step 1 (the k-of-n vote). Read on commit `024a46d`, offline, on the stored TD 1 traces. Nothing was copied from the reviewed work: the vote and the table were recomputed with our own scripts, and the function was stress-tested.

Verdict: the step is sound. We found no wrong figure. The remarks concern evidence required by the assignment that is missing from the report (C19, the duplicate test, the table).

## What we checked and found correct

- **The five rules of `vote_k_sur_n`**, tested one by one with our own proposals:
  - an error or an unavailable member stays in n and casts no vote (`100, error, error` gives 1 vote, no consensus);
  - k must satisfy `n // 2 < k <= n`: `k=1` on n=3, `k=4` on n=3, `k=1` on n=2 and n=0 raise `ValueError`;
  - two proposals from the same provider and model raise `ValueError`, including when one of them is an error;
  - a value with at least k votes returns `consensus: true`, with the list of agreeing models; otherwise `consensus: false`, `value: null`, and the largest count (0 when everything failed);
  - **a value of 0 is a valid vote** (`0, 0, 7` gives consensus on 0): the code tests `is not None`, not truthiness;
  - `executed` with no value, and `error` with a value, both cast no vote.
- **The vote does not see the reference.** `tableau-vote.py` builds the proposals from the value and the verdict only, and compares with the reference after the decision.
- **The table [reports/td2-table.md](../reports/td2-table.md) matches an independent vote.** We reimplemented the vote with a counter, on the final attempt of each cell: 20 rows, **0 differences** on the reference, the 2-of-3 decision, the 3-of-5 decision and the "Change ?" column. Fixed panel 2-of-3: 15 correct, 5 abstentions (C09, C10, C16, C17, C19), 0 wrong. 3-of-5: 16 correct, 4 abstentions, 0 wrong.
- **The choice of the last attempt is right today.** `tableau-vote.py` keeps the last row of each cell in file order. In `traces-td1.csv` the last row is the highest attempt for all 100 cells (14 cells have several rows: 6 retried after HTTP 429, 8 from the first run of E refused with HTTP 401, which come before the rows of the second run).

## To do before the hand-in

1. **C19 is not commented, and the assignment asks for it.** C19 is the only question where the decision changes (abstention for the fixed panel, consensus 1 990 for 3-of-5). Material, from the traces:

   | Model | Value on C19 | Verdict | Note |
   |---|---|---|---|
   | gpt-oss-120b | 1 990 | correct | |
   | gpt-oss-20b | 1 990 | correct | first attempt HTTP 429, second attempt answered |
   | dots-3-note | 1 990 | correct | |
   | qwen3.8-27b | 83 580 | incorrect | first attempt HTTP 429, second attempt answered, still wrong |
   | north-mini-code | 71 640 | incorrect | |

   The fixed panel {gpt-oss-120b, north-mini-code, qwen3.8-27b} sees 1 990, 71 640 and 83 580: three different values, no value with 2 votes, so it abstains (1 vote). The 3-of-5 quorum sees 1 990 three times and decides, correctly. **The consensus depends on a retry**: without the second attempt of gpt-oss-20b after its HTTP 429, only gpt-oss-120b and dots-3-note would vote 1 990, which is 2 votes out of the 3 required, and 3-of-5 would abstain too. This is the case the assignment gives as an example, an HTTP 429 shifting the margin.
2. **The table is not in the report.** The Step 1 section of `reports/td2.md` still reads "to complete by Pair A", and the table is in a separate file, in French, while the report is in English. Copy the table into the report and translate its headers.
3. **The duplicate-route test is not recorded.** The function refuses a duplicate (we confirmed it), but none of the four synthetic examples of `atelier-vote.py` covers it, and the report says "to complete". Add the test, or paste the output of one.

## Minor

4. `last_rows` keeps the last row **in file order**, not the highest attempt number. It works for this file (checked above) but would silently pick an older attempt if the traces were merged in another order. Selecting the highest `attempts`, with the date as a tie-break, removes the dependency.

The response of Pair A is in [reports/td2.md](../reports/td2.md), Step 1 section; the selection of the last attempt by its number (remark 4) was applied in `tableau-vote.py`.
