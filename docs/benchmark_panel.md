# Step 2 — Comparable Benchmark Panel: construction and finding

**Status: panel attempted; key finding is a comparability limit. No LCI/index
number computed.** Built per the signed measurement contract (`docs/measurement_contract.md`,
§§8–9): one model variant (instruction-tuned), one fixed protocol per metric,
with sample size and a confidence interval per accuracy observation. Output:
`data/evals/accuracy_panel.csv` (Wilson 95% CIs for in-panel rows).

## Headline finding
**A comparable instruction-tuned panel spanning 2023→2025 does not exist in
public sources.** Web sourcing (3-agent verification, each citing URLs) found:

- **Llama-3-70B-Instruct ↔ Llama-3.1-70B-Instruct are cleanly comparable** under
  one protocol per metric, from Meta's own consistent reporting:
  - MMLU: 5-shot, no CoT — **83.6 → 83.6**
  - HumanEval: 0-shot pass@1 — **80.5 → 80.5**
  - GSM8K: 8-shot CoT, maj@1 — **93.0 → 95.1**
- **Llama-2-70B-Chat (2023) is the break point and is excluded.** Meta never
  published instruct-variant MMLU/HumanEval/GSM8K for Llama-2-70B-Chat under the
  protocols used for Llama-3/3.1. The widely-cited 2023 figures (MMLU 68.9,
  HumanEval 29.9, GSM8K 56.8) are all **base-model**; the only Chat-variant
  numbers come from different harnesses / launch-blog tables → variant and/or
  harness mismatch, which the contract forbids.

**Consequence.** Under the contract's comparability rule and balanced-panel rule,
the comparable window is **2024Q2 → 2024Q3 (Llama-3 → Llama-3.1 Instruct)** only.
Across that window instruct quality is **nearly flat** (two metrics unchanged,
GSM8K +2.1 pts). The previously-claimed 2023→2025 "quality improvement" is **not
supported** on a like-for-like instruct basis — consistent with review finding #6
(comparability was manufacturing the quality gain).

## What is in the panel
`in_panel = True` only for the six comparable Llama-3/3.1 Instruct rows (with
Wilson 95% CIs over the fixed test split: MMLU n=14042, HumanEval n=164,
GSM8K n=1319). The three 2023 rows are recorded with `in_panel = False` and a
mismatch note; they are **excluded from any index**.

## Decision required before Step 3
The comparable evidence is thin (2 periods, ~flat quality, 3-month span), so an
index over it would be almost entirely cost-driven. Options:

- **A. Accept the thin comparable window** (2024Q2→2024Q3, instruct). Honest but a
  short, mostly-cost "deflator" — a weak contribution.
- **B. Extend the instruct panel forward** to add genuinely comparable later
  vintages (e.g. Llama-3.3-70B-Instruct, Dec 2024; 2025 open instruct models)
  under the same Meta protocol per metric. Restores multiple periods and real
  quality movement; keeps 2023 out as non-comparable. *(Recommended; sourceable.)*
- **C. Re-evaluate all vintages (incl. Llama-2-70B-Chat) under one harness**
  (e.g. lm-eval-harness/HELM) so 2023 can be included like-for-like. The honest
  way to keep 2023, but requires running evals (compute) or a single public
  harness that demonstrably spans all three under one protocol/version.
- **D. Switch the comparability basis to base models** (Meta reports base 5-shot
  consistently). Comparable across vintages, but base ≠ the served product and
  conflicts with the QATE "served expected yield" interpretation and the
  contract's instruct choice.

No code beyond panel assembly has run; Steps 3–7 are paused on this decision.
