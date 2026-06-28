# Measurement Contract — Locational Cost of Intelligence (LCI) & the LCI Price Index

**DRAFT — NO EMPIRICAL RESULT CURRENTLY VALID.** Defines the *primary* (soft,
quality-adjusted) estimand. Supersedes the joint chance-constraint formulation
for the empirical index. The prior "≈54% decline" and all wedge magnitudes are
withdrawn pending reconstruction (see `STATUS.md`). **Signed off at commit
`954dee1`.** Step 2 (comparable benchmark panel) is in progress; no empirical
number is computed or published until the panel and subsequent steps are reviewed.

## 1. Estimand
For a (task family `k`, location, period `t`) configuration,
```
LCI = C / Y_QATE        [USD per quality-adjusted task-equivalent, USD/QATE]
```
`C` = operating cost per unit time; `Y_QATE` = quality-adjusted task-equivalents
per unit time. LCI is a **supply-side unit cost of usable output** — not a market
price, not eligibility-gated. `C` and `Y_QATE` (via `T`) must cover the **same
serving pool over the same time interval**.

## 2. Output unit (QATE) and the quality index
```
φ(a, ℓ, q, s) = a · g_ℓ(ℓ) · g_q(q) · g_s(s)          (primary: unit exponents)
Y_QATE        = T · φ
```
**Throughput `T`.** `T` is the **full serving pool's raw completion throughput,
before any quality adjustment** — completions per unit time summed over all
replicas in the pool that `C` covers; one completion = one task attempt.
**Primary availability convention:** `T` is the **nominal up-state** full-pool
throughput and contains **no downtime factor**; availability quality enters
**only** through `g_q`. Using calendar-time throughput with `g_q ≡ 1` defines a
*different, separately labeled* estimand and **must not be mixed** into the primary
panel — the two are **not** numerically equal (e.g. at `q̄ = 0.99, q = 0.98`,
`g_q = 0.5`, whereas an uptime-deflated `T` would carry a `0.98` factor). `T` and
`C` cover the **same replicas over the same interval**. Replica scaling cancels in
`C/T` **only under identical-replica linear scaling**; otherwise `T` must be the
**full-pool simulated/measured** throughput, not a single replica's rate times a
replica count.

**Domain & normalization.** `a, q, s ∈ [0,1]`, `ℓ ≥ 0`, references `ℓ̄ > 0` and
`q̄, s̄ ∈ [0,1)`, `κ_ℓ > 0`, and `φ ∈ [0,1]`. (`ℓ̄ > 0` guarantees the default
`κ_ℓ = ℓ̄ > 0`; `q̄, s̄ < 1` keep `g_q, g_s` well-defined and in `(0,1]`, hence
`φ ∈ [0,1]`.) **One QATE is normalized to one completion at `a = 1` with every
delivery discount equal to 1.** If `φ = 0` (e.g. `a = 0`), then `Y_QATE = 0` and
`LCI = +∞` — stated exactly, with **no numerical clipping**.

- `a` enters **linearly, no reference, no exponent**: admissible as the
  **empirical expected task yield** *only* when the accuracy metric is a
  **fixed-protocol success/pass rate** (fixed shot count / decoding / version).
- `g_ℓ, g_q, g_s ∈ [0,1]` are delivery-quality discounts, **= 1 on the acceptable
  side of the reference** (`ℓ ≤ ℓ̄`, `q ≥ q̄`, `s ≥ s̄`) and **< 1 on the adverse
  side** (capped at 1 — no credit for exceeding a reference).
- **`φ` is a declared separable quality index, NOT a joint success probability.**
  A probabilistic reading would require independence or joint-outcome data, which
  we do not have. (Intuition only: under *independent* retries the expected
  attempts per usable completion would be `≈ 1/a`; the estimate assumes no such
  process.)

**Delivery exponents.** Primary specification uses **unit exponents
`η_ℓ = η_q = η_s = 1`**, so each declared function is a direct multiplicative
discount. Any weighted/elasticity variant (`g_i^{η_i}`, `η_i ≠ 1`) is a
**normative utility parameter**: it is treated as a *robustness scenario* and may
become primary only with separate sign-off.

## 3. References (acceptable-side saturation; latency/availability/safety only)
`(ℓ̄, q̄, s̄)` are declared, use-case references marking where each delivery
discount saturates at 1 on the acceptable side. They are **not** eligibility
tests and are **never** used to drop observations in the primary index; they are
reported and varied in sensitivity. **Accuracy has no reference.**

## 4. Quality functions (declared)
```
g_ℓ(ℓ) = exp[ − max(0, ℓ − ℓ̄) / κ_ℓ ]    # = 1 for ℓ ≤ ℓ̄; continuous exponential
                                          #   decay above ℓ̄ (kinked at ℓ̄, i.e.
                                          #   continuous but not differentiable there)
g_q(q) = min(1, (1 − q̄)/(1 − q)),  q < 1;   g_q(1) = 1   (convention)
g_s(s) = min(1, (1 − s̄)/(1 − s)),  s < 1;   g_s(1) = 1   (convention)
```
`κ_ℓ` (latency softness) is **predeclared** (default `κ_ℓ = ℓ̄`) and **included in
the sensitivity analysis**. The `g_q(1)=g_s(1)=1` conventions avoid division by
zero at perfect availability/safety.

## 5. Weighting & aggregation — fixed-weight chained geometric LCI index
```
I_t / I_{t-1} = ∏_k ( LCI_{k,t} / LCI_{k,t-1} )^{w_k},     Σ_k w_k = 1
```
with **equal, fixed** family weights `w_k`, reported with sensitivity. This is a
**fixed-weight chained geometric LCI index** — explicitly **NOT** Fisher,
superlative, or expenditure-weighted; Laspeyres/Paasche bounds do not apply.

**Balanced-panel and missing-data rule.**
- `I₀ = 100`.
- The family set `K` and weights `w_k` are fixed **before** computation.
- Every published link requires a **valid — finite and strictly positive — LCI
  for every `k ∈ K` in both periods**. An `LCI = +∞` (from `φ = 0`) is not valid
  and cannot enter an index ratio.
- Missing families are **never** carried forward, silently dropped, or followed by
  weight renormalization. **If the balanced link is unavailable, the index is not
  reported for that interval.**
- A missing link **breaks the chained level series** and cannot be bridged.
  Resuming publication after a gap requires an **explicit rebase** (a new base
  period set to `I = 100`), reported as such.

## 6. Cost — two mutually exclusive regimes (never blended)
```
Cloud:  C = replicas × ( instance_price_per_hour + separately_billed_services )
Owned:  C = replicas × ( annualized_hardware_host_cost_per_hour
                       + PUE × power_kW × energy_price_per_kWh
                       + facility/network/operations_cost_per_hour )
```
Cloud instance prices **already embed energy and facilities**, so EIA energy is
**not** added in the Cloud regime (adding it double-counts). The Owned regime
prices energy explicitly via PUE, where **`power_kW` is the total per-replica draw
(accelerators plus host)**, and its `C`/`T` cover the same replicas and interval.
A single observation uses exactly one regime; the two are never mixed. (The current
AWS-priced empirics are **Cloud**.)

## 7. Eligibility — primary vs. SLA variant
- **Primary LCI / LCI index:** no hard eligibility; every observation contributes
  via `φ`.
- **SLA-constrained LCI (deferred, and re-specified):** a hard-eligibility variant
  requires **either joint-outcome data, or an explicitly allocated marginal
  violation budget (`Σ_i ε_i ≤ ε`) enforced by a union bound.** Per-metric
  marginal distributions **alone do not identify a joint chance constraint.**
  Reported only where every period has qualifying observations; **not used for the
  cross-vintage index** under current evidence.
- **Retired as invalid (not merely deferred):** the previous nonnegative-loss
  `CVaR(L) ≤ 0` formulation — with `L ≥ 0` it forbids *all* loss rather than an
  `ε`-tail, so it never represented the chance constraint. It is removed.

## 8. Uncertainty vs. robustness (kept strictly separate)
- **Statistical uncertainty** is propagated *separately* for two sources and is
  the only thing called "uncertainty": (i) **accuracy `a`** — from the benchmark
  numerator/denominator (or sample size) as a confidence interval; (ii)
  **simulated latency** — from simulation replications. The two are **reported as
  separate source-specific intervals**, not combined into a single band unless
  statistical independence and a joint propagation method are explicitly assumed.
- **Robustness sensitivity** is variation of *declared assumptions* (references,
  `κ_ℓ`, delivery exponents, family weights, token counts, decode rates,
  availability `q`, safety `s`). It is reported as robustness scenarios and
  **never** labeled statistical uncertainty.
- **Step-2 data requirement:** each accuracy observation must record the benchmark
  numerator/denominator (or sample size), the exact protocol/version, and a CI for
  `a` **with its confidence level, construction method, and sampling unit** (not
  merely `N` and interval endpoints).
- **Amendment A1 (post-sign-off, per review).** When a primary source lacks the
  information needed for a *valid* CI — e.g. a macro-averaged metric without
  per-subject counts, or an undocumented evaluated denominator/scorer — the CI
  treatment is recorded as **"not estimable from published data"**, **never** as
  zero and never silently omitted. Any index built on such inputs is reported with
  **PARTIAL uncertainty**: the explicit caveat that one or more inputs carry no
  quantified statistical uncertainty. A metric whose **scoring rule** changes
  across vintages (not just shots/CoT) is **not one fixed protocol** and may not
  sit in the primary family set; it may appear only as a clearly labeled
  linked-protocol sensitivity.

## 9. Scope & honesty rules (binding on the empirics)
- Latency/throughput are **simulated**; the simulator must be **validated for the
  regime actually used** (batch size, service-time variance, p95) or the claim
  narrowed to exactly what is validated. The serving model must be **labeled
  accurately** (the implementation is bulk-service, **not** processor sharing),
  and the `u` axis named as **offered load / fraction of peak**, not measured
  server utilization. Numerical clipping that hides `φ = 0` is disallowed.
- Prices and benchmark accuracies are **sourced**; decode rates, token counts,
  **availability `q`, safety `s`**, references, weights, and `κ_ℓ` are **declared
  assumptions** (point values, varied in robustness §8) until a sourced
  measurement and uncertainty treatment for `q`, `s` is defined.
- The benchmark panel must be **comparable across periods**: one model variant,
  fixed evaluation protocol per metric; `a` admissible as yield only under that
  protocol. Mixed base/instruct or shot settings are disallowed.
- `PUI / LCI` is reported **only for QoS-matched products**.

---

## Resolved decisions (signed off at `954dee1`)
1. **Accuracy:** `g_a = a` (linear; no `ā`, no exponent); fixed-protocol only. ✔
2. **Above-reference:** capped at 1. ✔
3. **Index:** fixed-weight chained geometric LCI index (§5) with the balanced-panel
   rule; not Fisher/superlative/expenditure-weighted. ✔
4. **Latency:** `g_ℓ = exp[−max(0, ℓ−ℓ̄)/κ_ℓ]`; `κ_ℓ` predeclared and in
   sensitivity. ✔
5. **Delivery exponents:** unit (`η = 1`) in the primary estimate; weighted
   variants are normative/robustness only. ✔ (new, per review)
6. **Cost:** two mutually exclusive regimes (Cloud / Owned); no energy
   double-count. ✔ (new, per review)
