# Step 2 — Comparable Benchmark Panel: construction and finding

**Status: panel built (extended-forward path chosen). No LCI/index number
computed.** Built per the signed measurement contract (`docs/measurement_contract.md`,
§§8–9): one model variant (instruction-tuned), one fixed protocol per metric,
with sample size and a confidence interval per accuracy observation. Output:
`data/evals/accuracy_panel.csv` (Wilson 95% CIs for in-panel rows).

## Decision taken
A like-for-like instruct panel spanning **2023** does not exist publicly
(Llama-2-70B-Chat has only base-model or different-harness numbers → variant/
harness mismatch). Per sign-off, we **excluded 2023 and extended the instruct
panel forward** along the frontier open ~70B-dense instruct models, holding one
protocol per metric.

## Panel (instruction-tuned; fixed protocol per metric)
Frontier open ~70B-dense instruct model at each date; `2025-06` reuses Llama-3.3
weights as a **cost-only leg** (no new quality):

| Date | Model | MMLU (0-shot CoT) | HumanEval (0-shot pass@1) | GSM8K (8-shot CoT) |
|------|-------|------------------:|--------------------------:|-------------------:|
| 2024-04 | Llama-3-70B-Instruct   | 86.0 | 80.5 | 93.0 |
| 2024-07 | Llama-3.1-70B-Instruct | 86.0 | 80.5 | 95.1 |
| 2024-12 | Llama-3.3-70B-Instruct | 86.0 | 88.4 | 94.84\* |
| 2025-06 | Llama-3.3 (cost-only)  | 86.0 | 88.4 | 94.84\* |

Wilson 95% CIs over the fixed test split (MMLU n=14042, HumanEval n=164,
GSM8K n=1319) are in the CSV. \*GSM8K protocol label is not pinned on the Llama-3.3
card (confidence 0.55–0.60).

## Protocol standardization (forced by the extension)
- **MMLU → 0-shot CoT** (the only MMLU protocol with values for all of L3/L3.1/L3.3;
  5-shot no-CoT dead-ends at L3.1). It is **flat at 86.0** across the panel.
- HumanEval 0-shot pass@1; GSM8K 8-shot CoT (kept).
- **Qwen2.5-72B-Instruct excluded** from the primary panel: its GSM8K is 4-shot CoT
  (≠ 8-shot) and its MMLU shot label is unpinned → protocol mismatch. It is a
  candidate robustness/alternative-frontier check, not a primary-panel row.

## Headline finding: quality is largely saturated; the deflator is a cost story
Across the comparable frontier instruct models, **two of three families are at or
near their benchmark ceiling and barely move**: MMLU is flat (86.0 everywhere) and
GSM8K sits in the 93–95 band. **HumanEval (code) is the only family with real
quality movement** (80.5 → 88.4 over 2024), and even that gain has overlapping
CIs at n=164. Therefore any LCI index over this panel will be **predominantly
cost-driven**, with a modest quality contribution from code — exactly the
cost-vs-quality decomposition the review required, now built in by construction.
The earlier "2023→2025 quality-driven decline" is **not supported**; the defensible
claim is "the cost of delivering a roughly fixed, near-saturated frontier-open
quality bar fell over 2024–2025, with continued gains in code."

## Excluded (recorded, `in_panel=False`)
The three 2023 Llama-2 rows are kept in the CSV with mismatch notes and excluded
from any index (base-variant or different-harness; not comparable).

## Next
Step 3 (instance-level recosting, Cloud regime) and Step 5 (geometric index) will
consume only `in_panel=True` rows under the balanced-panel rule. No empirical
LCI/index number has been computed yet.
