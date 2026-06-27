# Status: empirical result WITHDRAWN — under reconstruction

**As of this revision, the headline empirical result (the 2023→2025 IPD "≈54%
decline") and the market-wedge magnitudes are WITHDRAWN pending reconstruction.**
Do not cite or rely on them.

A code review identified blocking issues that invalidate the published numbers as
stated:

1. The code enforced only a latency feasibility check, while the paper defined a
   *joint* QoS chance constraint; under that definition the 2023 baseline is
   infeasible and the index is undefined.
2. Serving cost omitted the GPUs-per-instance factor, so absolute LCI and the
   PUI/LCI wedge were under-stated by ~8x.
3. The validated simulator (B=1 M/M/k mean wait) is not the regime used for the
   estimate (B=16, low-variance service, p95); "processor sharing" is mislabeled.
4. The written chain-Fisher equation is incorrect and, lacking expenditure
   shares, the statistic is not a superlative index.
5. Benchmark scores are not comparable across vintages (shot settings differ;
   base vs. instruct scores mixed within one model).
6. PUI and LCI were compared without matching QoS.

## What is being done

The framework is being **reframed around a soft, quality-adjusted estimand**
(see `docs/measurement_contract.md`): LCI = cost per quality-adjusted
task-equivalent, with QoS thresholds as *reference levels* (not constraints).
The hard SLA-constrained variant is deferred and will not back the cross-vintage
index without per-metric distributional evidence.

The conceptual reconstruction precedes any mechanical patch. Until it is
complete, treat this repository as **"an interesting quality-adjusted cost
framework whose empirical result is not yet established."**

Prior artifacts can be reproduced mechanically, but that reproducibility does not
validate the estimand, the applied simulator regime, or the withdrawn results. The
pipeline and CI will be revised during reconstruction.
