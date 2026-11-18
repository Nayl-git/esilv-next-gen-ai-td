# TD 2: cross-review of Step 1 (Pair A) by Pair B

Reviewers: Pair B (enkimlt, nohamsantenac, PierreBOUDRAA). Reviewed: Pair A, Step 1 (the k-of-n vote).

**Provenance of this file.** Pair B reviewed offline, in two rounds (commits `4cc60e5` and `b1a5b35`), by reading the code, the diffs and the produced tables against the assignment, and recorded its remarks only as the section "Cross-review by Pair B" of [reports/td2.md](../reports/td2.md). This file reproduces the part of that section about Pair A (Step 1), word for word, so that each pair has one review file per pair reviewed. It was assembled from the report by Nayl SAIFOUDINE (Pair C), not written by Pair B, and adds no new check. Pair B should confirm that it matches what it did.

## Second round (commit b1a5b35)

- **`vote_k_sur_n`: compliant with the contract.** `n // 2 < k <= n` is checked; a duplicate (provider, model) raises `ValueError`, errors included; errors and unavailable members stay in n without voting; an abstention returns `value = None`, `models = []` and the largest vote count. No defect found.
- **C19 is not commented, and the material for it was removed.** `tableau-vote.py` prints a block "questions where the decision changes" with the values and verdicts of the five models; commit 1ee622e deleted those lines from [td2-table.md](../reports/td2-table.md). The assignment asks to explain every difference between 2-of-3 and 3-of-5 with exact values and verdicts. To do: restore the block and comment C19 (2-of-3 abstains, 3-of-5 decides 1990, correct).
- **Margins not commented.** C02, C08, C11 and C18 pass the 2-of-3 panel with 2 votes only, because one member failed (invalid SQL or HTTP 429). The decision does not change, but the margin does; the assignment gives this as an example to explain.
- **Table not in the report.** It is in a separate file, in French, while the report is in English; the Step 1 section above still reads "to complete by Pair A". To do: move the table into this section, in English.
- **Minor.** The duplicate-route test is not shown, and the second member of Pair A is missing from the contributions.
- **Consistency with Step 2:** the fixed panel gives 15 correct, 5 abstentions, 0 wrong consensus, as in Pair B's [panels.json](../td2/pair-b-outputs/panels.json).

## First round (commit 4cc60e5)

- **Step 1 (Pair A), consistent.** `python tableau-vote.py` gives, for the fixed 2-of-3 panel, 15 correct consensus, 5 abstentions (C09, C10, C16, C17, C19) and no wrong consensus. Pair B's independent count in [td2/pair-b-outputs/panels.json](../td2/pair-b-outputs/panels.json) gives the same 15 / 5 / 0. C19 is the only question where 3-of-5 decides (1990, correct) while 2-of-3 abstains. To do by Pair A: copy the table into this report (Step 1 section) and comment C19.

The response of Pair A is in [reports/td2.md](../reports/td2.md), Step 1 section.
