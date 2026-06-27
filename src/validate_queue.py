"""Validate the discrete-event simulator against the M/M/k Erlang-C analytic
mean waiting time. For batch_size=1 with exponential inter-arrivals and service,
the station is exactly M/M/k, so the simulated mean queue wait must match
``mmk_wait_mean`` within Monte-Carlo error.

Writes results/tables/queue_validation.csv and prints a pass/fail summary.
A relative error under ~5% across the grid is treated as validated.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from queueing_ps_batch import QueueConfig, simulate, mmk_wait_mean

ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / "results" / "tables"


def main(tol: float = 0.05) -> None:
    TABLES.mkdir(parents=True, exist_ok=True)
    ES = 1000.0  # ms
    rows = []
    worst = 0.0
    for k in (1, 2, 4, 8):
        for u in (0.5, 0.7, 0.85, 0.95):
            reps = [simulate(u, QueueConfig(k=k, service_time_ms=ES),
                             n_arrivals=300_000, warmup=30_000, seed=s)["wait_mean_ms"]
                    for s in range(6)]
            sim_wait = float(np.mean(reps))
            sim_sd = float(np.std(reps, ddof=1))
            ana_wait = mmk_wait_mean(k, u, ES)
            rel = abs(sim_wait - ana_wait) / ana_wait if ana_wait > 0 else 0.0
            worst = max(worst, rel)
            rows.append({
                "k": k, "u": u,
                "sim_wait_ms": round(sim_wait, 2),
                "sim_sd_ms": round(sim_sd, 2),
                "erlangC_wait_ms": round(ana_wait, 2),
                "rel_error": round(rel, 4),
            })
            print(f"k={k} u={u:.2f}  sim={sim_wait:8.1f}  erlangC={ana_wait:8.1f}  "
                  f"rel_err={rel*100:5.2f}%")

    df = pd.DataFrame(rows)
    df.to_csv(TABLES / "queue_validation.csv", index=False)
    print(f"\nWorst relative error: {worst*100:.2f}%  "
          f"-> {'PASS' if worst < tol else 'FAIL'} (tol={tol*100:.0f}%)")
    print(f"[OK] Wrote {TABLES / 'queue_validation.csv'}")


if __name__ == "__main__":
    main()
