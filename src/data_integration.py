"""Merge the real public input CSVs into a single tidy table for inspection.

Sources (all public, version-controlled with source URLs and access dates):
  data/external/hardware.csv      -- cloud GPU list prices, TDP, decode rates
  data/external/energy_prices.csv -- EIA industrial electricity prices
  data/external/api_prices.csv    -- public LLM API list prices (for PUI)
  data/evals/accuracy.csv         -- published benchmark scores by model/date

Unlike the previous version, there is NO fabricated fallback: if an input file
is missing the script fails loudly rather than silently inventing data.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

BASE = Path(__file__).resolve().parents[1]
OUT = BASE / "data" / "interim" / "merged_inputs.csv"


def _require(p: Path) -> pd.DataFrame:
    if not p.exists():
        raise FileNotFoundError(f"Required input missing: {p}")
    df = pd.read_csv(p)
    if df.empty:
        raise ValueError(f"Required input is empty: {p}")
    return df


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    acc = _require(BASE / "data" / "evals" / "accuracy.csv")
    hw = _require(BASE / "data" / "external" / "hardware.csv")
    merged = acc.merge(
        hw[["date", "gpu", "price_usd_per_gpu_hr", "tdp_w_per_gpu",
            "decode_tok_per_s_per_gpu_70b_fp16"]],
        on="date", how="left",
    )
    merged.to_csv(OUT, index=False)
    print(f"[OK] Wrote {len(merged)} merged rows to {OUT} "
          f"({acc['date'].nunique()} dates, {acc['family'].nunique()} families).")


if __name__ == "__main__":
    main()
