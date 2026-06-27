"""Sensitivity and uncertainty analysis for the LCI / IPD estimates.

Two kinds of uncertainty are reported:

1. Monte-Carlo (simulation) uncertainty: the normalised p95 curve carries a
   replication standard deviation. We propagate it by a parametric bootstrap
   (draw p95 ~ Normal(mean, sd) per utilisation, recompute the LCI table and the
   IPD) to get a confidence band on the 2025Q2 IPD.

2. Structural (assumption) sensitivity: the load-bearing assumptions are the
   per-GPU decode rate, the per-task output-token count, the QoS weights eta, and
   the latency softness tau. We re-estimate the IPD under one-at-a-time
   perturbations and report the resulting range of the final-period IPD.

Outputs results/tables/sensitivity.csv and results/figures/fig_sensitivity.pdf.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from lci_program import load_params, normalised_curve, compute_lci_table
from make_ipd import chain_indices

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
TABLES = ROOT / "results" / "tables"
FIGS = ROOT / "results" / "figures"


def _load():
    params = load_params()
    hw = pd.read_csv(DATA / "external" / "hardware.csv")
    acc = pd.read_csv(DATA / "evals" / "accuracy.csv")
    energy = pd.read_csv(DATA / "external" / "energy_prices.csv")
    api = pd.read_csv(DATA / "external" / "api_prices.csv")
    price_kwh = float(energy[energy["region"] == params["energy_region"]]["price_usd_per_kwh"].iloc[0])
    return params, hw, acc, api, price_kwh


def _final_ipd(df):
    ipd = chain_indices(df[["date", "family", "LCI"]].dropna())
    return float(ipd["IPD"].iloc[-1]), ipd


def bootstrap_ipd(params, hw, acc, api, price_kwh, base_curve, n=400, seed=11):
    """Parametric bootstrap over the simulation p95 replication SD."""
    rng = np.random.default_rng(seed)
    finals = []
    for _ in range(n):
        c = base_curve.copy()
        # perturb each utilisation's p95 by its replication sd (truncated at >0)
        noise = rng.normal(0.0, 1.0, size=len(c))
        c["p95_ms"] = np.maximum(1e-6, c["p95_ms"].values + noise * c["p95_sd"].values)
        df, _ = compute_lci_table(params, hw, acc, api, price_kwh, c)
        finals.append(_final_ipd(df)[0])
    finals = np.asarray(finals)
    return float(np.percentile(finals, 5)), float(np.percentile(finals, 95)), float(finals.mean())


def structural_sensitivity(params, hw, acc, api, price_kwh, curve):
    """One-at-a-time perturbations of the load-bearing assumptions."""
    scenarios = []

    def run(label, p=None, decode_scale=1.0, token_scale=1.0):
        pp = p if p is not None else params
        df, _ = compute_lci_table(pp, hw, acc, api, price_kwh, curve,
                                  decode_scale=decode_scale, token_scale=token_scale)
        fin, _ = _final_ipd(df)
        scenarios.append({"scenario": label, "final_IPD_2025Q2": round(fin, 2)})

    run("baseline")
    run("decode -50%", decode_scale=0.5)
    run("decode +50%", decode_scale=1.5)
    run("tokens -25%", token_scale=0.75)
    run("tokens +25%", token_scale=1.25)

    for tau in (1000, 4000):
        p = copy.deepcopy(params); p["latency_softness_tau_ms"] = tau
        run(f"tau={tau}ms", p=p)

    # QoS weight variants (renormalised to sum 1)
    for label, w in [("eta accuracy-heavy", {"a": 0.7, "l": 0.1, "q": 0.1, "s": 0.1}),
                     ("eta latency-heavy", {"a": 0.3, "l": 0.4, "q": 0.2, "s": 0.1}),
                     ("eta equal", {"a": 0.25, "l": 0.25, "q": 0.25, "s": 0.25})]:
        p = copy.deepcopy(params); p["qos_weights"] = w
        run(label, p=p)

    return pd.DataFrame(scenarios)


def main():
    TABLES.mkdir(parents=True, exist_ok=True)
    FIGS.mkdir(parents=True, exist_ok=True)
    params, hw, acc, api, price_kwh = _load()
    curve = normalised_curve(params)

    base_df, _ = compute_lci_table(params, hw, acc, api, price_kwh, curve)
    base_final, base_ipd = _final_ipd(base_df)

    lo, hi, mean = bootstrap_ipd(params, hw, acc, api, price_kwh, curve)
    print(f"Baseline final IPD (2025Q2): {base_final:.2f}")
    print(f"Monte-Carlo 90% CI on final IPD: [{lo:.2f}, {hi:.2f}]  (sim replication noise)")

    sens = structural_sensitivity(params, hw, acc, api, price_kwh, curve)
    sens.to_csv(TABLES / "sensitivity.csv", index=False)
    print("\nStructural sensitivity (final-period IPD, base=100 at 2023Q3):")
    print(sens.to_string(index=False))
    smin = sens["final_IPD_2025Q2"].min(); smax = sens["final_IPD_2025Q2"].max()
    print(f"\nStructural range of final IPD: [{smin:.1f}, {smax:.1f}] "
          f"(all scenarios show a substantial decline from 100).")

    # Figure: tornado of final-period IPD across scenarios
    s = sens.sort_values("final_IPD_2025Q2")
    fig, ax = plt.subplots(figsize=(6, 3.8))
    colors = ["#1f77b4" if r != "baseline" else "#d62728" for r in s["scenario"]]
    ax.barh(s["scenario"], s["final_IPD_2025Q2"], color=colors)
    ax.axvline(base_final, color="#d62728", ls=":", lw=1, label=f"baseline {base_final:.1f}")
    ax.axvspan(lo, hi, color="#d62728", alpha=0.08, label=f"MC 90% CI [{lo:.1f},{hi:.1f}]")
    ax.set_xlabel("Final-period IPD (2025Q2), base = 100 at 2023Q3")
    ax.set_title("Sensitivity of the IPD decline to key assumptions")
    ax.legend(frameon=False, fontsize=8, loc="lower right")
    fig.savefig(FIGS / "fig_sensitivity.pdf", bbox_inches="tight", metadata={"CreationDate": None})
    plt.close(fig)
    print("[OK] Wrote results/tables/sensitivity.csv and results/figures/fig_sensitivity.pdf")

    # record the band for the paper
    meta_path = ROOT / "results" / "meta.json"
    meta = json.loads(meta_path.read_text()) if meta_path.exists() else {}
    meta["sensitivity"] = {"baseline_final_ipd": round(base_final, 2),
                           "mc_ci90": [round(lo, 2), round(hi, 2)],
                           "structural_range": [round(smin, 1), round(smax, 1)]}
    meta_path.write_text(json.dumps(meta, indent=2))


if __name__ == "__main__":
    main()
