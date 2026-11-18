# TD 2: cross-review of Steps 1 and 2 by Pair C

Reviewers: Pair C (Franck TANKHAPANYA, Sina BALAEI, Nayl SAIFOUDINE). Read on commit `024a46d`, offline, on the stored TD 1 traces and the read-only database. Nothing was copied from the reviewed work: the vote, the table and the key figures were recomputed with our own scripts, and the function of Step 1 was stress-tested.

Verdict: both steps are sound. We found no wrong figure. The remarks concern evidence required by the assignment that is missing from the report (Step 1: C19 and the duplicate test; Step 2: the delta query by customer) and one claim that is stronger than what the code shows (Step 2: "model-free" population check).

## Step 1 (Pair A): the k-of-n vote

### What we checked and found correct

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

### To do before the hand-in

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

### Minor

4. `last_rows` keeps the last row **in file order**, not the highest attempt number. It works for this file (checked above) but would silently pick an older attempt if the traces were merged in another order. Selecting the highest `attempts`, with the date as a tie-break, removes the dependency.

## Step 2 (Pair B): the wrong consensus on C09

### What we checked and found correct

- **The scan.** Among the final results of the twenty questions, C09 is the only one where two models return the same wrong value (0, by qwen3.8-27b and dots-3-note). We also looked at non-zero values: no other value is shared between two wrong answers.
- **The reference and the population.** C09 = 487 980 cents. With a completed-age function written in Python, the target population is **6 customers and 68 order lines**, as announced.
- **The SQL causes**, replayed on the database:
  - qwen3.8-27b: the stored query returns 0. The lines go from 72 (order year minus birth year = 25), to 14 (`month-day(order) >= month-day(birth)`), to **0**, because the second bound compares the same month-day with itself. No customer is born on 29 February, so `+26 years` never changes a month-day;
  - dots-3-note: the stored query returns 0. "Exactly 25" is read as "turns 25 on 2026-09-26": exactly one customer is born on 2001-09-26. The added filter on the order date 2026-09-26 cannot match, since the last order is dated 2026-09-20.
- **The quorum table.** Fixed panel 2-of-3: abstention (1 vote). 3-of-5: abstention (2 votes). {gpt-oss-120b, qwen3.8-27b, dots-3-note}: wrong consensus on 0. This agrees with our own evaluation of the ten panels.
- **The zeros of the batch.** The wrong zeros are on C02, C09, C10, C11, C15 and C16, and the true zeros on C06 and C14, as announced.
- **The statement on panels.** Among the seven panels of distinct families, the three that hold qwen3.8-27b and dots-3-note together contain the wrong consensus, and two of them are the panels that answer most often (16 correct, 3 abstentions).
- **Reproducibility.** `python td2/wrong_consensus.py` runs offline, exits with code 0, and leaves the repository unchanged.
- **The independent window.** The `date()` window gives 82, 81, 68 and 60 lines for C02, C08, C09 and C11: exactly the population of the reference query.

### To do before the hand-in

1. **The delta query does not list the customers.** The assignment asks for a `SELECT` listing the `customer_id` rows and their revenue that the reference counts and the faulty queries miss, **with the exact cent difference**. The report gives a count (68 of 68 lines). Material, computed on the database (read-only):

   | customer_id | birth_date | order lines | revenue (cents) |
   |---|---|---|---|
   | C007 | 2000-11-30 | 18 | 118 740 |
   | C009 | 2001-03-10 | 9 | 61 330 |
   | C008 | 2001-05-15 | 11 | 99 090 |
   | C002 | 2001-09-24 | 6 | 25 920 |
   | C001 | 2001-09-25 | 18 | 135 000 |
   | C003 | 2001-09-26 | 6 | 47 900 |
   | **Total** | | **68** | **487 980** |

   ```sql
   SELECT c.customer_id, c.birth_date, COUNT(*) AS order_lines,
          SUM(o.quantity_product * p.price) AS revenue_cents
   FROM orders o
   JOIN product p   ON p.product_id  = o.product_id
   JOIN customers c ON c.customer_id = o.customer_id
   WHERE c.birth_date >  date('2026-09-26', '-26 years')
     AND c.birth_date <= date('2026-09-26', '-25 years')
   GROUP BY c.customer_id, c.birth_date
   ORDER BY c.birth_date, c.customer_id;
   ```

   The sum equals the reference, 487 980, and each wrong query returns 0, so the difference is 487 980 − 0 = **487 980 cents** for qwen3.8-27b and for dots-3-note.
2. **The "model-free" claim is stronger than the code.** The Summary and section 4 say that the population check flags every wrong 0 and no true zero, without any model. In `section_check`, the independent formulation (the `date()` window) exists for **four questions only**: C02, C08, C09 and C11. For the sixteen others, including **C10, C15 and C16, three of the six wrong zeros**, the population is `COUNT(*)` on the FROM and WHERE of the reference query. That needs the reference, which a live service does not have, so for these three questions the flag is circular. It is true for C02, C09 and C11. The Limitations section says part of this; the Summary and section 4 should say it too, or a reference-free population query should be written for C10 (age at the order), C15 and C16.

### Minor

3. "The fixed panel avoids C09 only because north-mini-code failed to run." Said more exactly, the protection is accidental: if north-mini-code had answered 0, the fixed panel would have decided a wrong consensus on 0; if it had answered 487 980, it would have decided the correct value. Both cases are worth stating.

## Effect on Step 3 (our own section)

The second remark changes a claim of Pair C. Our rule requires the zero check for F2 and F2b figures. It is model-free today only for F2 (C02, C08, C09, C11). For F2b (C10), the population still comes from the reference query. The zero check on F2b is therefore a requirement, not yet an implemented control. We added this limit to our section.
