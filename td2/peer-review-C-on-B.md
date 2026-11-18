# TD 2: cross-review of Step 2 (Pair B) by Pair C

Reviewers: Pair C (Franck TANKHAPANYA, Sina BALAEI, Nayl SAIFOUDINE). Reviewed: Pair B, Step 2 (the wrong consensus on C09). Read on commit `024a46d`, offline, on the stored TD 1 traces and the read-only database. Nothing was copied from the reviewed work: the key figures were recomputed with our own scripts.

Verdict: the step is sound. We found no wrong figure. The remarks concern evidence required by the assignment that is missing from the report (the delta query by customer) and one claim that is stronger than what the code shows ("model-free" population check).

## What we checked and found correct

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

## To do before the hand-in

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

## Minor

3. "The fixed panel avoids C09 only because north-mini-code failed to run." Said more exactly, the protection is accidental: if north-mini-code had answered 0, the fixed panel would have decided a wrong consensus on 0; if it had answered 487 980, it would have decided the correct value. Both cases are worth stating.

## Effect on our own section (Step 3, Pair C)

The second remark changes a claim of Pair C. Our rule requires the zero check for F2 and F2b figures. It is model-free today only for F2 (C02, C08, C09, C11). For F2b (C10), the population still comes from the reference query. The zero check on F2b was therefore a requirement, not an implemented control. We added this limit to our section, then wrote `td2/recompute.py`, a parameterised recomputation for the five families that does not need the reference and rejects every wrong 0 of TD 1. It also gives Pair B a model-free formulation for C10, C15 and C16.

The response of Pair B is in [reports/td2.md](../reports/td2.md), section "Cross-review by Pair C".
