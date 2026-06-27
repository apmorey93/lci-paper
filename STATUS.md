# Status: empirical result WITHDRAWN — under reconstruction

**The headline empirical results in this repository — the 2023→2025 Intelligence
Price Deflator ("≈54% decline") and the market-price/LCI "wedge" magnitudes — are
WITHDRAWN. Do not cite or rely on them.**

A code review identified blocking issues that invalidate the published numbers as
stated:

1. **Joint QoS not enforced.** The code gated feasibility on latency only, while
   the paper defined a *joint* accuracy/latency/availability/safety chance
   constraint. Under that definition the 2023 baseline is infeasible and the
   index is undefined.
2. **Serving cost understated ~8×.** Cost omitted the GPUs-per-instance factor,
   so every absolute LCI and the entire wedge magnitude are wrong.
3. **Validation gap.** The validated simulator (B=1 M/M/k mean wait) is not the
   regime used for the estimate (batching, low-variance service, p95); the
   "processor sharing" label is inaccurate.
4. **Index mis-specified.** The written chain-Fisher equation is incorrect and,
   with no expenditure shares, the statistic is not a superlative index.
5. **Benchmarks not comparable across vintages** (shot settings differ; base vs.
   instruction-tuned scores mixed within one model), which can manufacture part
   of the apparent quality gain.
6. **PUI vs. LCI not QoS-matched**, so the "wedge" is a cross-product price
   comparison, not the defined markup.

## What is being done

The framework is being **reframed around a soft, quality-adjusted estimand**:
`LCI = cost per quality-adjusted task-equivalent`, with QoS thresholds treated as
*reference levels*, not constraints. The hard SLA-constrained variant is deferred
and will not back the cross-vintage index without per-metric distributional
evidence. The reconstruction (measurement contract → comparable benchmark panel →
instance-level recosting → narrowed simulator claim → re-built index) is in
progress on the `real-experiments-lci` branch and precedes any mechanical patch.

Until it is complete, treat this repository as **"an interesting quality-adjusted
cost framework whose empirical result is not yet established."** Prior artifacts
can be reproduced mechanically, but that reproducibility does not validate the
estimand, the applied simulator regime, or the withdrawn results. The pipeline and
CI will be revised during reconstruction.
