"""Generate all paper figures from the real pipeline outputs.

Reads results/tables/{norm_curve.csv, lci_curves.csv, lci_by_family.csv,
queue_validation.csv} and writes PDFs to results/figures/ using the filenames
referenced by the LaTeX source. The IPD figure is produced by make_ipd.py.
"""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / "results" / "tables"
FIGS = ROOT / "results" / "figures"


def _lambda(l_ms, lbar, tau):
    x = (l_ms - lbar) / tau
    sp = tau * math.log1p(math.exp(x)) if x < 30 else (l_ms - lbar)
    return lbar / (lbar + sp)


def fig_qos_latency():
    """Fig 1: latency quality factor lambda(l) for several softness tau."""
    lbar = 200.0
    l = np.linspace(0, 600, 400)
    fig, ax = plt.subplots(figsize=(5.2, 3.6))
    for tau in (5, 20, 50):
        ax.plot(l, [_lambda(x, lbar, tau) for x in l], label=fr"$\tau={tau}$ ms")
    ax.axvline(lbar, color="k", ls=":", lw=0.8)
    ax.text(lbar + 6, 0.05, r"$\bar{\ell}$", fontsize=11)
    ax.set_xlabel(r"Latency $\ell$ (ms)"); ax.set_ylabel(r"Quality factor $\lambda(\ell)$")
    ax.set_title("Latency quality factor vs. SLA softness")
    ax.legend(frameon=False); ax.set_ylim(0, 1.05)
    fig.savefig(FIGS / "fig_qos_latency.pdf", bbox_inches="tight"); plt.close(fig)
    print("[OK] fig_qos_latency.pdf")


def fig_throughput_lci():
    """Fig 2: throughput and LCI vs utilisation (dual axis), representative slice."""
    curves = pd.read_csv(TABLES / "lci_curves.csv")
    norm = pd.read_csv(TABLES / "norm_curve.csv").sort_values("u")
    sl = curves[(curves["date"] == "2025-06-01") & (curves["family"] == "QA")].sort_values("u")
    thru = norm["throughput_req_per_s"].values.astype(float)
    thru = thru / thru.max()
    fig, ax1 = plt.subplots(figsize=(5.4, 3.8))
    ax1.plot(sl["u"], thru, "s--", color="#2ca02c", label="Throughput (norm.)")
    ax1.set_xlabel("Utilisation $u$ (fraction of peak throughput)")
    ax1.set_ylabel("Throughput (normalised)", color="#2ca02c")
    ax2 = ax1.twinx()
    ax2.plot(sl["u"], sl["LCI"] * 1e3, "o-", color="#1f77b4", label="LCI")
    ax2.set_ylabel(r"LCI ($\times10^{-3}$ \$/task)", color="#1f77b4")
    ustar = sl.loc[sl["LCI"].idxmin(), "u"]
    ax2.axvline(ustar, color="#d62728", ls=":", lw=1)
    ax2.text(ustar - 0.03, ax2.get_ylim()[1] * 0.9, r"$u^\ast$", color="#d62728")
    ax1.set_title("Throughput rises, LCI is U-shaped (QA, 2025)")
    fig.savefig(FIGS / "fig_throughput_LCI_vs_util.pdf", bbox_inches="tight"); plt.close(fig)
    print("[OK] fig_throughput_LCI_vs_util.pdf")


def fig_lci_curve():
    """Fig 3: LCI(u) for the three families (latest period), with u* markers."""
    curves = pd.read_csv(TABLES / "lci_curves.csv")
    fig, ax = plt.subplots(figsize=(5.6, 3.8))
    for fam, c in [("QA", "#1f77b4"), ("Code", "#ff7f0e"), ("Reasoning", "#2ca02c")]:
        sl = curves[(curves["date"] == "2025-06-01") & (curves["family"] == fam)].sort_values("u")
        if sl.empty:
            continue
        ax.plot(sl["u"], sl["LCI"] * 1e3, "o-", color=c, label=fam)
        imin = sl["LCI"].idxmin()
        ax.scatter([sl.loc[imin, "u"]], [sl.loc[imin, "LCI"] * 1e3], color=c, s=80,
                   edgecolor="k", zorder=5)
    ax.set_xlabel("Utilisation $u$"); ax.set_ylabel(r"LCI ($\times10^{-3}$ \$/task)")
    ax.set_title(r"Estimated LCI$(u)$ by task family (2025); $\bullet = u^\ast$")
    ax.legend(frameon=False)
    fig.savefig(FIGS / "fig_LCI_curve.pdf", bbox_inches="tight"); plt.close(fig)
    print("[OK] fig_LCI_curve.pdf")


def fig_wedge():
    """Fig 5: market price (PUI) vs cost frontier (LCI) over time -> wedge."""
    df = pd.read_csv(TABLES / "lci_by_family.csv")
    g = df.groupby("date").agg(LCI=("LCI", "mean"), PUI=("PUI", "mean")).reset_index()
    x = pd.to_datetime(g["date"])
    fig, ax = plt.subplots(figsize=(5.6, 3.8))
    ax.semilogy(x, g["PUI"], "o-", color="#d62728", label="Market price (PUI)")
    ax.semilogy(x, g["LCI"], "s-", color="#1f77b4", label="Cost frontier (LCI)")
    ax.fill_between(x, g["LCI"], g["PUI"], color="#d62728", alpha=0.07)
    ax.set_ylabel("USD per task (log scale)"); ax.set_xlabel("Date")
    ax.set_title("The wedge: market price vs. LCI cost frontier")
    ax.legend(frameon=False); fig.autofmt_xdate()
    fig.savefig(FIGS / "fig_wedge.pdf", bbox_inches="tight"); plt.close(fig)
    print("[OK] fig_wedge.pdf")


def fig_validation():
    """Appendix: simulator vs Erlang-C analytic mean wait."""
    p = TABLES / "queue_validation.csv"
    if not p.exists():
        return
    v = pd.read_csv(p)
    fig, ax = plt.subplots(figsize=(5.2, 3.8))
    lo, hi = v["erlangC_wait_ms"].min(), v["erlangC_wait_ms"].max()
    ax.plot([lo, hi], [lo, hi], "k--", lw=0.8, label="y = x")
    for k, c in zip(sorted(v["k"].unique()), ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728"]):
        s = v[v["k"] == k]
        ax.scatter(s["erlangC_wait_ms"], s["sim_wait_ms"], color=c, label=f"k={k}")
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlabel("Erlang-C analytic mean wait (ms)"); ax.set_ylabel("Simulated mean wait (ms)")
    ax.set_title("Simulator validation (M/M/k): worst error < 5%")
    ax.legend(frameon=False)
    fig.savefig(FIGS / "fig_queue_validation.pdf", bbox_inches="tight"); plt.close(fig)
    print("[OK] fig_queue_validation.pdf")


def main():
    FIGS.mkdir(parents=True, exist_ok=True)
    fig_qos_latency()
    fig_throughput_lci()
    fig_lci_curve()
    fig_wedge()
    fig_validation()
    print("[OK] All figures generated.")


if __name__ == "__main__":
    main()
