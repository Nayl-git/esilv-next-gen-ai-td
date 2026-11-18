# TD 2: cross-review of Step 3 (Pair C) by Pair A

Reviewers: Pair A. Reviewed: Pair C, Step 3 (the routing rule). Scope: [draft-pair-C-section.md](draft-pair-C-section.md) and [README.md](README.md), read before commit a7d2394. Nothing was re-executed (no traces, reference, `data/boutique.sqlite` or `atelier-routage.py`): this is a check of internal consistency only.

Converted from the original plain-text file `peer-review-pair-A-section.txt` (commit a7d2394) to Markdown and English, then split in two so that each file reviews one pair: this one is the part about Pair C. Three statements of the original were corrected after checking them against the repository; each correction is marked *Checked*.

## What is solid

- The five families partition the twenty questions (6 + 4 + 1 + 4 + 5).
- The totals per model are consistent (20, 18, 14, 14, 11).
- The panel table of Pair C agrees with that of Pair B (15 / 5 / 0, 16 / 3 / 1, 13 / 6 / 1). The vote redone by hand on the listed failures gives the same abstentions.
- Pair C states its weaknesses (panel chosen after reading the traces, samples of one to six questions).

## Pair C (Step 3): to discuss or fix

1. **Panel P = {gpt-oss-120b, gpt-oss-20b, qwen3.8-27b}** holds two models of the same family. The docstring of `vote_k_sur_n` (Lecture 2) asks to keep the panel to distinct model families. P is chosen for its 20/20, in-sample and after the fact. It also contradicts Pair B's message ("distinct families are necessary but not sufficient"). Either justify it better, or plan an escalation when the distinct-family panel abstains. This is the most fragile point.
   *Checked:* the original text said "the assignment and the lecture"; the requirement is in the docstring of `vote_k_sur_n`, which refers to Lecture 2, not in the assignment page.
2. **"Reference check" (payout rows) does not exist in production** (lecture: references exist in the lab, not in real life). Name a feasible check: a second independent query, the population check, human review.
3. **Payouts are inconsistent:** F1 and F3 get a 3-of-5 quorum plus human review; F2 and F4 get only "reference check or human review". Yet F2 is the family where the wrong consensus appeared: that is where the strongest check is needed.
4. **F2:** gpt-oss-120b has 4/4, so `none` would be admissible under Pair C's own criterion (100 % on at least four questions). Pair C requires a check anyway (prudent): write down the reason (the other models produce silent zeros).
5. **The zero check on F2b and F4 cannot be implemented without the reference query.** Acknowledged in the limitations, but required in the rule table.
6. **Groq limits:** "1 000 output tokens per minute" (the HTTP 429 of qwen3.8-27b) and "8 000 tokens per minute" further down.
   *Checked:* these are not contradictory. They are two different limits on two different models, both recorded in [five-model-summary-en.csv](../five-model-summary-en.csv): OTPM 1 000 for qwen3.8-27b (HTTP 429 on C08, C16, C18, C19, C20) and TPM 8 000 for gpt-oss-20b (HTTP 429 on C19). Remaining point: Pair C quotes "8 000 tokens per minute" for the plan of gpt-oss-120b, whereas the trace that shows this limit is gpt-oss-20b's; cite the source.
7. **F4 argument:** "the age logic is not stable for this model" assumes that F4 contains age questions.
   *Checked:* it does. C15, C16, C17 and C19 combine a period or a product with "exactly 25 years old on 2026-09-25", and C18 with "25 years old at the time of the order" ([questions-td1.json](../questions-td1.json)). The argument holds.
8. **The Contributions section is empty** (required).

## Questions for the oral cross-review

- Pair C: why does `choose` prefer available included capacity to `defer`? When should that be reversed?
- Everyone: why does a model in error stay in n?

The response of Pair C is in [reports/td2.md](../reports/td2.md), section "Cross-review by Pair A".
