# TD 2: cross-review of Step 2 (Pair B) by Pair A

Reviewers: Pair A. Reviewed: Pair B, Step 2 (the wrong consensus). Scope: [wrong-consensus-C09.md](wrong-consensus-C09.md), [wrong_consensus.py](wrong_consensus.py) and [README.md](README.md), read before commit a7d2394. Nothing was re-executed (no traces, reference or `data/boutique.sqlite`): this is a check of internal consistency only.

Converted from the original plain-text file `peer-review-pair-A-section.txt` (commit a7d2394) to Markdown and English, then split in two so that each file reviews one pair: this one is the part about Pair B. Three statements of the original were corrected after checking them against the repository; each correction is marked *Checked*.

## What is solid

- The panel tables of Pairs B and C agree (15 / 5 / 0, 16 / 3 / 1, 13 / 6 / 1). The vote redone by hand on the listed failures gives the same abstentions.
- Pair B has a real case (C09) and is honest about its limits: the fixed panel abstains only because north-mini-code failed.

## Pair B (Step 2): to fix before the hand-in

1. **The delta query does not follow the assignment.** The assignment asks for a `SELECT` listing the `customer_id` rows and their revenue excluding VAT, whose sum explains the exact difference in cents. The document only gives "68 lines missed", and in the script the SQL is a placeholder. Both faulty queries return 0, so the delta is the whole reference. Provide an executed `SELECT` (`GROUP BY c.customer_id`, `WHERE` = the reference condition of C09): six rows summing to 487 980.
2. **The two complete queries are missing** (only the `WHERE` clauses are shown). Reproduce the full queries as stored in the traces.
3. **Claim too strong:** "every wrong 0 is flagged, no true zero rejected". For C10, C15 and C16 the population check reuses the reference query (circular). The independent formulation exists only for C02, C08, C09 and C11. Restrict the sentence to these four.
4. **To verify:** `load_last()` keeps the last row read per (model, question). If the merged traces (`traces-D.csv`, `traces-E2.csv`…) are not in attempt order, "last attempt" is wrong.
   *Checked:* in `traces-td1.csv`, the last row read is also the highest attempt for all 100 cells, so no figure is affected today; the dependency on file order is a robustness issue, not an error.

## Questions for the oral cross-review

- Pair B: why do two different queries give the same 0? Which condition makes qwen's `WHERE` empty?
- Everyone: why does a model in error stay in n?

The response of Pair B is in [reports/td2.md](../reports/td2.md), section "Cross-review by Pair A".
