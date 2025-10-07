"""Utility script that fabricates demo LCI/IPD tables when raw inputs are absent."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from make_ipd import chain_fisher


ROOT = Path(__file__).resolve().parents[1]
INTERIM = ROOT / "data" / "interim"
TABLES = ROOT / "results" / "tables"
FIGURES = ROOT / "results" / "figures"


def _ensure_table_dirs() -> None:
    """Create the results sub-directories that the report expects."""

    TABLES.mkdir(parents=True, exist_ok=True)
    FIGURES.mkdir(parents=True, exist_ok=True)


def demo_dataframe() -> pd.DataFrame:
    """Return a deterministic seed dataset covering multiple families and dates."""

    rows = [
        {
            "date": "2025-01-01",
            "family": "QA",
            "provider": "example",
            "model": "example-A",
            "region": "global",
            "accuracy": 0.80,
            "a": 0.80,
            "p50_ms": 300,
            "p95_ms": 450,
            "q": 0.999,
            "s": 0.999,
            "tokens_per_sec": 0,
            "price_per_token_usd": 1.0e-5,
            "ops_pct": 0.0,
        },
        {
            "date": "2025-01-01",
            "family": "Code",
            "provider": "example",
            "model": "example-B",
            "region": "global",
            "accuracy": 0.70,
            "a": 0.70,
            "p50_ms": 400,
            "p95_ms": 600,
            "q": 0.999,
            "s": 0.999,
            "tokens_per_sec": 0,
            "price_per_token_usd": 1.2e-5,
            "ops_pct": 0.0,
        },
        {
            "date": "2025-01-01",
            "family": "Summarization",
            "provider": "example",
            "model": "example-C",
            "region": "global",
            "accuracy": 0.75,
            "a": 0.75,
            "p50_ms": 350,
            "p95_ms": 500,
            "q": 0.999,
            "s": 0.999,
            "tokens_per_sec": 0,
            "price_per_token_usd": 9.0e-6,
            "ops_pct": 0.0,
        },
        {
            "date": "2025-06-01",
            "family": "QA",
            "provider": "example",
            "model": "example-A2",
            "region": "global",
            "accuracy": 0.82,
            "a": 0.82,
            "p50_ms": 290,
            "p95_ms": 430,
            "q": 0.999,
            "s": 0.999,
            "tokens_per_sec": 0,
            "price_per_token_usd": 9.5e-6,
            "ops_pct": 0.0,
        },
        {
            "date": "2025-06-01",
            "family": "Code",
            "provider": "example",
            "model": "example-B2",
            "region": "global",
            "accuracy": 0.72,
            "a": 0.72,
            "p50_ms": 360,
            "p95_ms": 540,
            "q": 0.999,
            "s": 0.999,
            "tokens_per_sec": 0,
            "price_per_token_usd": 1.1e-5,
            "ops_pct": 0.0,
        },
        {
            "date": "2025-06-01",
            "family": "Summarization",
            "provider": "example",
            "model": "example-C2",
            "region": "global",
            "accuracy": 0.77,
            "a": 0.77,
            "p50_ms": 330,
            "p95_ms": 490,
            "q": 0.999,
            "s": 0.999,
            "tokens_per_sec": 0,
            "price_per_token_usd": 8.5e-6,
            "ops_pct": 0.0,
        },
    ]
    return pd.DataFrame(rows)


def load_inputs() -> pd.DataFrame:
    """Load merged inputs or fall back to the deterministic seed dataset."""

    merged = INTERIM / "merged_inputs.csv"
    if not merged.exists():
        df = demo_dataframe()
    else:
        df = pd.read_csv(merged)
        if df.empty:
            df = demo_dataframe()

    if "accuracy" not in df.columns and "a" in df.columns:
        df["accuracy"] = df["a"]
    if "a" not in df.columns and "accuracy" in df.columns:
        df["a"] = df["accuracy"]
    return df


def compute_lci_by_family(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate raw rows into per-family LCI slices."""

    BAR_L = 500.0

    df = df.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date", "a", "p95_ms", "price_per_token_usd"])
    phi = df["a"].astype(float).clip(lower=1e-6) * (
        BAR_L / np.maximum(df["p95_ms"].astype(float).clip(lower=1.0), BAR_L)
    ) ** 0.5
    cost = df["price_per_token_usd"].astype(float).clip(lower=1e-10)
    df["LCI"] = cost / phi

    by_family = (
        df.groupby(["date", "family"], as_index=False)
        .agg(
            LCI=("LCI", "median"),
            accuracy=("accuracy", "median"),
            p95_ms=("p95_ms", "median"),
            price_per_token_usd=("price_per_token_usd", "median"),
        )
        .sort_values(["date", "LCI"])
    )
    by_family["date"] = by_family["date"].dt.strftime("%Y-%m-%d")
    return by_family


def export_latex_table(by_family: pd.DataFrame) -> None:
    """Write a LaTeX table containing the latest snapshot."""

    if by_family.empty:
        return

    latest_date = by_family["date"].max()
    latest_rows = by_family[by_family["date"] == latest_date]
    header = [
        "\\begin{table}[t]",
        "\\centering",
        "\\caption{LCI by Task Family (demo)}",
        "\\label{tab:lci_by_family}",
        "\\begin{tabular}{lrrrr}",
        "\\toprule",
        "Family & LCI & Accuracy & p95 (ms) & Price/Token " + "\\\\",
        "\\midrule",
    ]
    body = [
        (
            f"{r['family']} & {r['LCI']:.2e} & {r['accuracy']:.3f} "
            f"& {r['p95_ms']:.0f} & {r['price_per_token_usd']:.2e} "
            "\\\\"
        )
        for _, r in latest_rows.iterrows()
    ]
    footer = [
        "\\bottomrule",
        "\\end{tabular}",
        "\\end{table}",
        "",
    ]
    tex = "\n".join(header + body + footer)
    (TABLES / "lci_by_family.tex").write_text(tex, encoding="utf-8")


def export_ipd(by_family: pd.DataFrame) -> None:
    """Derive a demo IPD series from the per-family slices."""

    if by_family.empty:
        (TABLES / "ipd.csv").write_text("date,IPD\n", encoding="utf-8")
        return

    lci_for_chain = by_family[["date", "family", "LCI"]].copy()
    lci_for_chain["date"] = pd.to_datetime(lci_for_chain["date"], errors="coerce")
    lci_for_chain = lci_for_chain.dropna()
    ipd = chain_fisher(lci_for_chain)
    ipd.to_csv(TABLES / "ipd.csv", index=False)


def main() -> None:
    _ensure_table_dirs()
    df = load_inputs()
    by_family = compute_lci_by_family(df)
    by_family.to_csv(TABLES / "lci_by_family.csv", index=False)
    export_ipd(by_family)
    export_latex_table(by_family)
    print("[OK] generated results/tables/{lci_by_family.csv, ipd.csv, lci_by_family.tex}")


if __name__ == "__main__":
    main()
