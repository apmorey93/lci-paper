# Step 2 — Comparable Benchmark Panel: construction and finding

**Status: panel built (extended-forward path), corrected to official sources. No
LCI/index number computed.** Built per the signed measurement contract
(`docs/measurement_contract.md`, §§8–9). Output: `data/evals/accuracy_panel.csv`.

> **Correction (supersedes a prior draft of this file).** An earlier version
> mistakenly copied the Llama-3.1 column into the Llama-3 row and used the
> saturated GSM8K metric, which produced a false "quality is saturated / only cost
> moves" claim. **That claim is withdrawn.** All in-panel values below are now from
> Meta's **official model-card "Instruction tuned models" tables** (verified), and
> quality does move.

## Decision taken
A like-for-like instruct panel for **2023** does not exist publicly (Llama-2-70B-Chat
has only base-model / different-harness numbers). Per sign-off, we **excluded 2023
and extended forward** along the frontier open ~70B-dense instruct models, one
official protocol per metric.

## Panel (instruction-tuned; official model-card tables)
| Date | Model | MMLU (0-shot CoT) | HumanEval (0-shot pass@1) | MATH (0-shot CoT) |
|------|-------|---:|---:|---:|
| 2024-04 | Llama-3-70B-Instruct   | 80.9 | 81.7 | 51.0 |
| 2024-07 | Llama-3.1-70B-Instruct | 86.0 | 80.5 | 68.0 |
| 2024-12 | Llama-3.3-70B-Instruct | 86.0 | 88.4 | 77.0 |
| 2025-06 | Llama-3.3 (matched-model cost continuation) | 86.0 | 88.4 | 77.0 |

Sources: Llama-3.1-70B-Instruct card (L3 & L3.1, side by side) and Llama-3.3-70B-Instruct
card. `2025-06` reuses Llama-3.3 weights — a **matched-model cost continuation**,
not a new frontier-quality vintage.

## Reasoning metric: GSM8K → MATH (uniform replacement)
GSM8K is **excluded**: it is absent from the official Llama-3.3 table (and was
saturated, 93–95). The reasoning family is replaced **uniformly** by **MATH
(0-shot CoT)**, which has an official protocol-matched value for all three
vintages and is non-saturated (51 → 68 → 77). *Caveat:* the official metric string
changes at L3.3 (`final_em` on L3/L3.1 → `sympy_intersection_score` on L3.3);
matched on benchmark/shots/CoT but not on the exact scoring label — flagged in the
CSV.

## CI policy (provisional; per review)
Reconstructed CIs are **provisional** and given only where a binomial model
reasonably approximates the published estimand:
- **HumanEval** pass@1 over n=164 and **MATH** over n=5000 (assumed full test):
  provisional Wilson 95% (values are rounded; per-item binary is an approximation).
- **MMLU: no binomial CI** — the published value is a macro-average over 57
  subjects; per-subject counts are unavailable, so a single-binomial CI would
  misrepresent the estimand (`ci_status = "none …"`).
- Overlapping marginal CIs do **not** establish significance of a cross-model
  change (that needs paired item outcomes); **no significance is claimed.**

## Corrected finding
Quality **does** move on the official, protocol-matched panel: MATH rises
strongly (51→68→77), MMLU steps up then plateaus (80.9→86.0), HumanEval dips then
rises (81.7→80.5→88.4). So the eventual index will reflect **both** a real
quality improvement (reasoning especially) **and** cost change — not a pure cost
story. The 2025 leg isolates cost at fixed quality (matched model). Magnitudes
remain to be computed (Steps 3 & 5); none are reported here.

## Excluded (recorded, `in_panel=False`)
The 2023 Llama-2 rows are kept with mismatch notes and excluded from any index.

## Next
Steps 3 (instance-level recosting, Cloud regime) and 5 (geometric index) will
consume only `in_panel=True` rows under the balanced-panel rule. No empirical
LCI/index number has been computed yet.
