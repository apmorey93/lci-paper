# Measurement Contract — Locational Cost of Intelligence (LCI) & Intelligence Price Deflator (IPD)

**Status: DRAFT for sign-off.** Defines the *primary* (soft, quality-adjusted)
estimand. Supersedes the joint chance-constraint formulation for the empirical
index. The prior "≈54% decline" is withdrawn pending reconstruction under this
contract (see `STATUS.md`).

## 1. Estimand
For a (task family `k`, location, period `t`) configuration,
```
LCI = C / Y_QATE        [USD per quality-adjusted task-equivalent, USD/QATE]
```
`C` = operating cost per unit time; `Y_QATE` = quality-adjusted task-equivalents
produced per unit time. LCI is a **supply-side unit cost of usable output** — not
a market price, and not an eligibility-gated quantity.

## 2. Output unit (QATE)
Raw throughput `T` (completions/hour) is converted to task-equivalents by a
hedonic quality factor `φ ∈ (0, 1]`:
```
Y_QATE = T · φ(a, ℓ, q, s)
```
**One QATE = one completion delivered at all reference levels.** A completion
below a reference contributes a fraction `φ < 1`; a completion at/beyond all
references contributes `1` (capped). `φ` is a **quality discount, not a
feasibility test** — every observation contributes.

## 3. Reference levels (references, NOT constraints)
`(ā, ℓ̄, q̄, s̄)` are declared, use-case reference levels (accuracy, p95 latency,
availability, safety). They mark where quality credit saturates (`g_i = 1`), not
eligibility. They are reported, varied in sensitivity, and **never used to drop
observations** in the primary index.

## 4. Quality functions (declared; each `= 1` exactly at/beyond reference)
```
g_a(a) = min(1, a / ā)                      # accuracy: linear fractional credit below ref
g_ℓ(ℓ) = exp( − (ℓ − ℓ̄)_+ / κ_ℓ )          # latency: =1 for ℓ≤ℓ̄, smooth decay above
g_q(q) = min(1, (1 − q̄) / (1 − q))          # availability: tolerated/actual downtime
g_s(s) = min(1, (1 − s̄) / (1 − s))          # safety: same form
φ      = g_a^{η_a} · g_ℓ^{η_ℓ} · g_q^{η_q} · g_s^{η_s},   η_i ≥ 0,  Σ η_i = 1
```
Weighted geometric mean. **Default reward rule: capped at the reference** (no
credit for exceeding it). A "rewarded" variant (`g_i` may exceed 1 up to a
declared cap) is optional and must be declared if used. The `exp` latency form is
chosen so `g_ℓ = 1` *exactly* at and below the SLO (fixing the prior
softplus-at-threshold contradiction).

## 5. Weighting
- **Within `φ`:** importance weights `η` are declared (default equal; baseline
  `(0.5,0.2,0.2,0.1)` reported with sensitivity).
- **Across families and time:** a **declared-weight chained index** over family
  weights `w_k` (default equal across included families). With **no observed
  expenditure shares, the index is NOT claimed to be a superlative (Fisher)
  index**; it is a fixed-weight chained price index, with Laspeyres/Paasche
  analogues reported only as bounds under the declared weights. A Fisher index
  may be substituted *iff* usage/expenditure shares become available.

## 6. Cost
`C` is the full operating cost of one serving **replica** per unit time:
```
C = (GPUs_per_replica × GPU_price) + energy + overhead,  summed over replicas
```
Per-GPU prices are multiplied by GPUs-per-replica (instance-level pricing);
energy scales with GPU count and power. (Corrects the prior per-GPU undercount.)

## 7. Eligibility — primary vs. SLA variant
- **Primary LCI/IPD:** no hard eligibility; every observation contributes via `φ`.
- **SLA-constrained LCI (optional, deferred):** restricts to configurations
  meeting all references with a stated tail probability; **requires per-metric
  distributions, not point values.** Reported only where every period has
  qualifying observations; **not used for the cross-vintage IPD** under current
  evidence. The chance-constraint / CVaR / Bonferroni / `ε` apparatus belongs
  only to this variant and is removed from the empirical contribution otherwise.

## 8. Scope & honesty rules (binding on the empirics)
- Latency/throughput are **simulated**; the simulator must be **validated for the
  operating regime actually used** (batch size, service-time variance, p95) or
  the claim narrowed to what is validated.
- Prices and benchmark accuracies are **sourced**; decode rates, token counts,
  references, and weights are **declared assumptions**.
- The benchmark panel must be **comparable across periods**: one model variant
  (e.g., all instruction-tuned) and a fixed evaluation protocol (fixed shot
  count / decoding) per metric. Mixed base/instruct or shot settings are
  disallowed.
- `PUI/LCI` is reported **only for QoS-matched products**.

---

### Open decisions for sign-off (these change downstream numbers)
1. **Accuracy quality function.** Default `g_a = min(1, a/ā)` (reference-relative;
   needs a declared `ā`). Alternative: `g_a = a` (treat the benchmark pass-rate
   directly as the usable fraction; removes the arbitrary accuracy reference).
   *Recommendation: `g_a = a` is cleaner and harder to attack; pick one.*
2. **Above-reference rule:** cap at 1 (default, conservative) vs. reward up to a
   cap. *Recommendation: cap.*
3. **Family weights `w_k`:** equal (default) vs. a usage proxy (e.g., public
   API-traffic mix). *Recommendation: equal, with sensitivity, until a sourced
   usage mix exists.*
4. **Latency softness:** keep `exp(−Δ/κ_ℓ)` (this draft) vs. a normalized
   softplus pinned to 1 at the SLO. *Recommendation: `exp`.*
