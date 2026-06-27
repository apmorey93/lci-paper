"""Compute the Locational Cost of Intelligence (LCI) from measured queueing
behaviour and real public price/benchmark data.

Pipeline
--------
1. Run ONE normalised GI/G/k-PS+batching simulation sweep (service time E[S]=1)
   to obtain the dimensionless latency/throughput-vs-utilisation curves. Because
   latency scales linearly with E[S] and throughput inversely, this single sweep
   rescales exactly to every (date, GPU, family) -- see ``queueing_ps_batch``.
2. For each (date, family), for each GPU option available that date, set the
   per-request service time E[S] = out_tokens / decode_rate, rescale the sweep,
   and compute the cost-per-quality-adjusted-task curve
       LCI(u) = (raw $/task)(u) / phi(u),      phi from Eq. (5) of the paper.
   Take the interior minimiser u* (the cost-minimising utilisation).
3. The LCI for (date, family) is the minimum over GPU options -- the cost
   frontier. We also record the market price (PUI) from public API list prices
   and the wedge PUI/LCI.

Every dollar figure traces to ``data/external/*.csv`` (sourced list prices,
EIA energy) or ``data/evals/accuracy.csv`` (published benchmarks); every latency
figure traces to the validated simulator. Outputs go to ``results/tables``.
"""

from __future__ import annotations

import json
import math
import platform
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

from queueing_ps_batch import QueueConfig, sweep

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
TABLES = ROOT / "results" / "tables"


# --------------------------------------------------------------------------- #
# QoS aggregator (paper Eq. 5): multiplicative, normalised to ~1 at/below target
# --------------------------------------------------------------------------- #
def phi(a, l_ms, fam, op, weights, tau):
    abar = fam["accuracy_target_abar"]
    lbar = fam["latency_target_ms"]
    qbar, q = op["availability_target_qbar"], op["availability_q"]
    sbar, s = op["safety_target_sbar"], op["safety_s"]

    alpha = min(1.0, a / abar)
    x = (l_ms - lbar) / tau
    softplus = tau * math.log1p(math.exp(x)) if x < 30 else (l_ms - lbar)
    lam = lbar / (lbar + softplus)                       # ~1 for l << lbar
    rho = min(1.0, (1.0 - qbar) / (1.0 - q)) if q < 1 else 1.0
    sig = min(1.0, (1.0 - sbar) / (1.0 - s)) if s < 1 else 1.0

    wa, wl, wq, ws = weights["a"], weights["l"], weights["q"], weights["s"]
    return (alpha ** wa) * (lam ** wl) * (rho ** wq) * (sig ** ws)


def load_params():
    return json.loads((DATA / "params.json").read_text())


def normalised_curve(params):
    """Run the single normalised sweep (E[S]=1 ms). Returns DataFrame over u."""
    q = params["queue"]
    cfg = QueueConfig(k=q["k"], scv_arrival=q["scv_arrival"], scv_service=q["scv_service"],
                      batch_size=q["batch_size"], batch_timeout_ms=q["batch_timeout_ms"],
                      service_time_ms=1.0)
    s = params["sim"]
    recs = sweep(params["u_grid"], cfg, n_arrivals=s["n_arrivals"], warmup=s["warmup"],
                 replications=s["replications"], base_seed=s["base_seed"])
    return pd.DataFrame(recs)


def lci_curve_for(es_ms, price_gpu_hr, tdp_w, price_kwh, a, fam, op, weights, tau, k, curve):
    """Rescale the normalised curve to E[S]=es_ms and compute LCI(u)."""
    out = []
    for _, row in curve.iterrows():
        u = row["u"]
        p95_ms = row["p95_ms"] * es_ms                      # rescale latency
        thru_req_s = row["throughput_req_per_s"] / es_ms    # rescale throughput
        if thru_req_s <= 0:
            continue
        gpu_s_per_task = k / thru_req_s                      # GPU-seconds per task
        gpu_cost = price_gpu_hr / 3600.0 * gpu_s_per_task
        energy_cost = (tdp_w / 1000.0) * (gpu_s_per_task / 3600.0) * price_kwh
        raw = (gpu_cost + energy_cost) * op["ops_overhead_factor"]
        ph = phi(a, p95_ms, fam, op, weights, tau)
        feasible = p95_ms <= fam["latency_target_ms"]        # QoS latency chance constraint
        out.append({"u": u, "p95_ms": p95_ms, "phi": ph, "raw_cost": raw,
                    "LCI": raw / max(ph, 1e-9), "feasible": bool(feasible)})
    return pd.DataFrame(out)


def compute_lci_table(params, hw, acc, api, price_kwh, curve,
                      decode_scale=1.0, token_scale=1.0):
    """Compute the per-(date, family) cost-frontier LCI table.

    decode_scale / token_scale perturb the assumed decode rate and per-task
    output tokens (used by the sensitivity analysis). Returns (df, curve_rows).
    """
    weights = params["qos_weights"]
    tau = params["latency_softness_tau_ms"]
    op = params["operational"]
    k = params["queue"]["k"]
    rows, curve_rows = [], []
    for date in sorted(acc["date"].unique()):
        hw_d = hw[hw["date"] == date]
        if hw_d.empty:                       # nearest earlier hardware snapshot
            cand = sorted([d for d in hw["date"].unique() if d <= date])
            hw_d = hw[hw["date"] == cand[-1]] if cand else hw
        for fam_name, fam in params["families"].items():
            arow = acc[(acc["date"] == date) & (acc["family"] == fam_name)]
            if arow.empty:
                continue
            a = float(arow["score_pct"].iloc[0]) / 100.0
            out_tokens = fam["out_tokens"] * token_scale
            best = None
            for _, h in hw_d.iterrows():
                decode = float(h["decode_tok_per_s_per_gpu_70b_fp16"]) * decode_scale
                es_ms = out_tokens / decode * 1000.0
                lc = lci_curve_for(es_ms, float(h["price_usd_per_gpu_hr"]), float(h["tdp_w_per_gpu"]),
                                   price_kwh, a, fam, op, weights, tau, k, curve)
                if lc.empty:
                    continue
                feas = lc[lc["feasible"]]
                if feas.empty:                 # no utilisation meets the latency SLO
                    continue
                imin = feas["LCI"].idxmin()    # cost-min among QoS-feasible u; keep full lc for plotting
                cand = {"date": date, "family": fam_name, "model": arow["model"].iloc[0],
                        "gpu": h["gpu"], "benchmark": fam["benchmark"], "a": a,
                        "u_star": float(lc.loc[imin, "u"]), "p95_ms": float(lc.loc[imin, "p95_ms"]),
                        "phi": float(lc.loc[imin, "phi"]), "raw_cost": float(lc.loc[imin, "raw_cost"]),
                        "LCI": float(lc.loc[imin, "LCI"]),
                        "price_gpu_hr": float(h["price_usd_per_gpu_hr"])}
                if best is None or cand["LCI"] < best["LCI"]:
                    best = cand
                    best_curve = lc.assign(date=date, family=fam_name, gpu=h["gpu"])
            if best is None:
                continue
            # PUI: cheapest public API list price at/just before this date
            api_d = api[api["date"] <= date]
            if not api_d.empty:
                api_d = api_d.copy()
                api_d["pui"] = (fam["in_tokens"] * api_d["price_in_usd_per_1m_tok"]
                                + out_tokens * api_d["price_out_usd_per_1m_tok"]) / 1e6
                jmin = api_d["pui"].idxmin()
                best["PUI"] = float(api_d.loc[jmin, "pui"])
                best["PUI_model"] = api_d.loc[jmin, "model"]
                best["wedge_x"] = best["PUI"] / best["LCI"]
            rows.append(best)
            curve_rows.append(best_curve)
    return pd.DataFrame(rows).sort_values(["date", "family"]), curve_rows


def main():
    TABLES.mkdir(parents=True, exist_ok=True)
    params = load_params()

    hw = pd.read_csv(DATA / "external" / "hardware.csv")
    acc = pd.read_csv(DATA / "evals" / "accuracy.csv")
    energy = pd.read_csv(DATA / "external" / "energy_prices.csv")
    api = pd.read_csv(DATA / "external" / "api_prices.csv")

    price_kwh = float(energy[energy["region"] == params["energy_region"]]["price_usd_per_kwh"].iloc[0])

    print("Running normalised simulation sweep (E[S]=1 ms) ...")
    curve = normalised_curve(params)
    curve.to_csv(TABLES / "norm_curve.csv", index=False)

    df, curve_rows = compute_lci_table(params, hw, acc, api, price_kwh, curve)
    df.to_csv(TABLES / "lci_by_family.csv", index=False)
    pd.concat(curve_rows, ignore_index=True).to_csv(TABLES / "lci_curves.csv", index=False)
    print(f"[OK] Wrote {TABLES / 'lci_by_family.csv'} ({len(df)} rows)")

    # Metadata for reproducibility
    meta_path = ROOT / "results" / "meta.json"
    meta = json.loads(meta_path.read_text()) if meta_path.exists() else {}
    meta.update({"lci_program": {
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "python": sys.version.split()[0], "platform": platform.platform(),
        "numpy": np.__version__, "pandas": pd.__version__,
        "params": params, "energy_price_usd_per_kwh": price_kwh,
    }})
    meta_path.write_text(json.dumps(meta, indent=2))

    with pd.option_context("display.width", 200, "display.max_columns", 20):
        print(df[["date", "family", "gpu", "a", "u_star", "p95_ms", "phi", "LCI", "PUI", "wedge_x"]].to_string(index=False))


if __name__ == "__main__":
    main()
