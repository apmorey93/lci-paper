# Step 2 — Comparable Benchmark Panel: construction and finding

**Status: panel built and contract-aligned. No LCI/index number computed.**
Per the signed measurement contract (`docs/measurement_contract.md`, §§8–9, incl.
Amendment A1). Output: `data/evals/accuracy_panel.csv` (built by `src/build_panel.py`,
which now asserts the rules below at build time).

> **Corrections applied (supersede earlier drafts).** (a) An earlier draft copied
> the Llama-3.1 column into the Llama-3 row and used saturated GSM8K, producing a
> false "saturation" claim — **withdrawn**; values are now the official side-by-side
> card numbers. (b) MATH is **not** one fixed protocol (its scoring rule changes at
> L3.3) and is **demoted to a sensitivity**. (c) MMLU has **no valid binomial CI**.

## PRIMARY panel — family set K = {QA, Code}
The only two metrics with **one fixed official protocol (including scoring rule)**
across Llama-3 / 3.1 / 3.3 Instruct:

| Date | Model | MMLU 0-shot CoT (QA) | HumanEval pass@1 (Code) |
|------|-------|---:|---:|
| 2024-04 | Llama-3-70B-Instruct   | 80.9 | 81.7 |
| 2024-07 | Llama-3.1-70B-Instruct | 86.0 | 80.5 |
| 2024-12 | Llama-3.3-70B-Instruct | 86.0 | 88.4 |
| 2025-06 | Llama-3.3 (matched-model cost continuation) | 86.0 | 88.4 |

- **MMLU CI:** *not estimable from published data* — the value is a macro-average
  over 57 subjects without per-subject counts. Recorded as such (never zero/blank).
- **HumanEval CI:** provisional Wilson 95% over n=164 (rounded value; binomial
  approximation; sampling unit = benchmark item).
- Because one primary input (MMLU) has no quantified statistical uncertainty, any
  index built on K carries **PARTIAL uncertainty** (contract §8 Amendment A1).

## SENSITIVITY (not primary) — MATH
MATH (0-shot CoT) is **0-shot CoT** for all three but the **official scoring metric
changes** (`final_em` on L3/L3.1 → `sympy_intersection_score` on L3.3), so it is
**not one fixed protocol** and is excluded from K. It is retained only as a
**linked-protocol sensitivity** (values 51.0 → 68.0 → 77.0; CI *not estimable* —
evaluated denominator/scorer not pinned). Use it only with the scorer-change
caveat; never in the primary index.

## Excluded
- **GSM8K** — absent from the official Llama-3.3 table.
- **2023 Llama-2-70B-Chat** — base-variant / different-harness only; not comparable
  (`panel_role = excluded`).

## Provenance (pinned)
Each row records `source_table = "Instruction tuned models"` and `source_revision`
= the canonical `meta-llama/llama-models` `MODEL_CARD.md` path (L3/L3.1 card for
L3 & L3.1; L3.3 card for L3.3), accessed 2026-06-27. (Upgrade to exact commit SHAs
on request.)

## Build-time guards (in `build_panel.py`)
Assertions prevent silent violations: every `primary` row has a non-empty
`ci_status`; the primary family set is a subset of {QA, Code}; MATH never appears
as primary; and each primary family has a single uniform protocol string.

## Finding (valid panel)
On the corrected primary panel, **quality moves**: MMLU steps up then plateaus
(80.9→86.0), HumanEval dips then rises (81.7→80.5→88.4); the MATH sensitivity rises
strongly (51→68→77). So a future index will reflect **both** quality and cost
change (not a pure cost story), and the 2025 leg isolates cost at fixed quality.
Magnitudes are deferred to Steps 3 & 5; none are reported here.

## Next
Steps 3 (instance-level recosting, Cloud regime) and 5 (geometric index, balanced
over K = {QA, Code}) consume only `panel_role = primary` rows; MATH enters only as
a sensitivity. No empirical LCI/index number has been computed.
