# TD 2: cross-review of Step 3 (Pair C) by Pair B

Reviewers: Pair B (enkimlt, nohamsantenac, PierreBOUDRAA). Reviewed: Pair C, Step 3 (the routing rule).

**Provenance of this file.** Pair B reviewed offline, in two rounds (commits `4cc60e5` and `b1a5b35`), by reading the code, the diffs and the produced tables against the assignment, and recorded its remarks only as the section "Cross-review by Pair B" of [reports/td2.md](../reports/td2.md). This file reproduces the part of that section about Pair C (Step 3), word for word, so that each pair has one review file per pair reviewed. It was assembled from the report by Nayl SAIFOUDINE (Pair C), not written by Pair B, and adds no new check. Pair B should confirm that it matches what it did.

## Second round (commit b1a5b35)

**Step 3 (Pair C).** Both first-round remarks are applied (commit e6d376b): the panel is declared, the zero check is added for F2 and F2b, and an unrun request shows "not applicable". The TD 1 rates of the draft agree with the failing cells it lists.

- **Panel P is not of three distinct families.** P = {gpt-oss-120b, gpt-oss-20b, qwen3.8-27b} holds two gpt-oss models, which Step 2 counts as one family, and it was chosen on the twenty questions it is evaluated on (Pair C states both limits). To do: either justify the coverage-versus-independence trade-off explicitly, or keep a panel of distinct families that does not hold qwen3.8-27b and dots-3-note together.
- **Rule and simulator disagree on the fallback.** For F2 the rule reads "wait for refill, then abstain", but the "urgent" scenario runs the paid gpt-oss-120b route (0.00033 USD). To do: add the paid route to the Fallback column.
- **"Deterministic check" for F2 dashboard is not defined.** "Read-only execution and plausibility" does not catch a wrong 0 (C09). To do: name the check, e.g. Pair B's population check, as already required for F2b.
- **Price ranking leaves out the free models.** dots-3-note and north-mini-code have no documented paid route, so they are never ranked, although they are free and correct on F1 and F3. To do: one sentence explaining why they are not the first model there.
- **Wording.** "Questions no free model handles alone" says only gpt-oss-120b has no error on F2, but gpt-oss-120b runs on the free Groq plan.
- **Not integrated yet.** The section is in [td2/draft-pair-C-section.md](../td2/draft-pair-C-section.md); the Step 3 section above still reads "to complete", and Pair C's contributions are empty.

## First round (commit 4cc60e5)

- **Step 3 (Pair C), one point to fix.** For F2 and F2b the check is a "2-of-3 quorum anchored on gpt-oss-120b", but the panel is not declared. Anchoring is not enough: the panel {gpt-oss-120b, qwen3.8-27b, dots-3-note} contains gpt-oss-120b and still accepts the wrong 0 on C09 (qwen and dots outvote it). The rule should name the panel and exclude having both qwen3.8-27b and dots-3-note in it for the age families, or add the population check before accepting a 0.
- **Step 3, minor.** In the "unknown capability" scenario the action is `abstain` but `checks` reads "2-of-3 quorum": a check on a request that is not run is confusing in the trace.

The response of Pair C is in [reports/td2.md](../reports/td2.md), section "Cross-review by Pair B" and Step 3 section.
