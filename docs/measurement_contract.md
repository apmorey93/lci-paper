# Measurement Contract — Locational Cost of Intelligence (LCI) & the LCI Price Index

**DRAFT — NO EMPIRICAL RESULT CURRENTLY VALID.** Defines the *primary* (soft,
quality-adjusted) estimand. Supersedes the joint chance-constraint formulation
for the empirical index. The prior "≈54% decline" and all wedge magnitudes are
withdrawn pending reconstruction under this contract (see `STATUS.md`).
This text is awaiting a final review before any code or empirical work begins.

## 1. Estimand
For a (task family `k`, location, period `t`) configuration,
```
LCI = C / Y_QATE        [USD per quality-adjusted task-equivalent, USD/QATE]
```
`C` = operating cost per unit time; `Y_QATE` = quality-adjusted task-equivalents
produced per unit time. LCI is a **supply-side unit cost of usable output** — not
a market price, and not an eligibility-gated quantity.

## 2. Output unit (QATE) and the quality index
Raw throughput `T` (completions/hour) is converted to task-equivalents by a
**declared separable quality index** `φ ∈ (0, 1]`:
```
φ(a, ℓ, q, s) = a · g_ℓ(ℓ)^{η_ℓ} · g_q(q)^{η_q} · g_s(s)^{η_s}
Y_QATE        = T · φ
```
- `a` enters **linearly, with no reference and no exponent**: when the accuracy
  metric is a **fixed-protocol success/pass rate** (e.g. HumanEval pass@1, MMLU
  accuracy under a fixed shot/decoding protocol), `a` is the **empirical expected
  task yield** — the fraction of attempts that produce a correct completion. This
  interpretation is used **only** when that fixed-protocol condition holds.
- `g_ℓ, g_q, g_s ∈ (0,1]` are delivery-quality discounts relative to references,
  each **= 1 exactly at or beyond its reference** and `< 1` below (capped at 1
  above — no credit for exceeding).
- **φ is a declared separable quality index, NOT a joint success probability.**
  We do not interpret `φ` as `P(all QoS dimensions jointly met)`; a probabilistic
  reading requires independence or joint-outcome data, which we do not have.
- Interpretive note: if completions were retried **independently** until success,
  the expected attempts per usable completion would be `≈ 1/a`. We state this only
  as intuition; the estimate assumes no such independent-retry process.

## 3. Reference levels (references, NOT constraints; latency/availability/safety only)
`(ℓ̄, q̄, s̄)` are declared, use-case reference levels for p95 latency,
availability, and safety. They mark where each delivery discount saturates
(`g_i = 1`), not eligibility; they are reported, varied in sensitivity, and
**never used to drop observations** in the primary index. **Accuracy has no
reference** in the primary estimate.

## 4. Quality functions (declared)
```
g_ℓ(ℓ) = exp[ − max(0, ℓ − ℓ̄) / κ_ℓ ]      # = 1 for ℓ ≤ ℓ̄; smooth decay above
g_q(q) = min(1, (1 − q̄) / (1 − q))           # availability: tolerated/actual downtime
g_s(s) = min(1, (1 − s̄) / (1 − s))           # safety: same form
```
`κ_ℓ` (latency softness) is **predeclared** (default `κ_ℓ = ℓ̄`, i.e. one e-fold of
discount per SLO-worth of overrun) and **included in the sensitivity analysis**.

## 5. Weighting
- **Within `φ`:** delivery weights `η_ℓ, η_q, η_s ≥ 0`, `Σ η = 1`, **declared**
  (default equal = 1/3 each; reported with sensitivity). Accuracy carries no
  weight parameter (it is linear).
- **Across families and time — fixed-weight chained geometric LCI index:**
```
  I_t / I_{t-1} = ∏_k ( LCI_{k,t} / LCI_{k,t-1} )^{w_k},     Σ_k w_k = 1
```
  with **equal, fixed** family weights `w_k` (reported with sensitivity). This is
  a **fixed-weight chained geometric LCI index** — explicitly **NOT** a Fisher,
  superlative, or expenditure-weighted index, and Laspeyres/Paasche bounds do not
  apply. Uncertainty is reported via weight and assumption sensitivity, not via
  index-number bounds.

## 6. Cost
`C` is the full operating cost of one serving **replica** per unit time:
```
C = (GPUs_per_replica × GPU_price) + energy + overhead,   summed over replicas
```
Per-GPU prices are multiplied by GPUs-per-replica (instance-level pricing);
energy scales with GPU count and power. (Corrects the prior per-GPU undercount.)

## 7. Eligibility — primary vs. SLA variant
- **Primary LCI / LCI index:** no hard eligibility; every observation contributes
  via `φ`.
- **SLA-constrained LCI (optional, deferred):** restricts to configurations
  meeting all references with a stated tail probability; **requires per-metric
  distributions, not point values.** Reported only where every period has
  qualifying observations; **not used for the cross-vintage index** under current
  evidence. The chance-constraint / CVaR / Bonferroni / `ε` apparatus belongs
  only to this variant and is removed from the empirical contribution otherwise.

## 8. Scope & honesty rules (binding on the empirics)
- Latency/throughput are **simulated**; the simulator must be **validated for the
  operating regime actually used** (batch size, service-time variance, p95) or the
  claim narrowed to exactly what is validated. "Processor sharing" must be labeled
  accurately (the implementation is bulk-service), and the `u` axis must be named
  as offered-load / fraction-of-peak, not measured server utilization.
- Prices and benchmark accuracies are **sourced**; decode rates, token counts,
  references, weights, and `κ_ℓ` are **declared assumptions**.
- The benchmark panel must be **comparable across periods**: one model variant
  (e.g. all instruction-tuned), a fixed evaluation protocol (fixed shot count /
  decoding) per metric, and `a` admissible as expected yield only under that
  fixed protocol. Mixed base/instruct or shot settings are disallowed.
- `PUI / LCI` is reported **only for QoS-matched products**.

---

## Resolved decisions (sign-off received)
1. **Accuracy:** `g_a = a` (linear; no `ā`, no exponent); valid only for
   fixed-protocol success-rate metrics. ✔
2. **Above-reference:** capped at 1. ✔
3. **Family weights:** equal, fixed, with sensitivity; index is the fixed-weight
   chained geometric LCI index in §5 (not Fisher/superlative/expenditure-weighted). ✔
4. **Latency:** `g_ℓ = exp[−max(0, ℓ−ℓ̄)/κ_ℓ]`; `κ_ℓ` predeclared and in
   sensitivity. ✔
