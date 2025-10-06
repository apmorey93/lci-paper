# src/generate_demo_results.py
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
INTERIM = ROOT / "data" / "interim"
RESULTS = ROOT / "results"
TABLES = RESULTS / "tables"
FIGS = RESULTS / "figures"

for d in (TABLES, FIGS):
    d.mkdir(parents=True, exist_ok=True)

merged = INTERIM / "merged_inputs.csv"
if not merged.exists() or merged.stat().st_size < 10:
    # Fallback demo rows if file empty
    df = pd.DataFrame([
        {"date":"2025-01-01","family":"QA","provider":"example","model":"example-A","region":"global",
         "a":0.80,"p50_ms":300,"p95_ms":450,"q":0.999,"s":0.999,"tokens_per_sec":0,
         "price_per_token_usd":1.0e-5,"ops_pct":0.0},
        {"date":"2025-01-01","family":"Code","provider":"example","model":"example-B","region":"global",
         "a":0.70,"p50_ms":400,"p95_ms":600,"q":0.999,"s":0.999,"tokens_per_sec":0,
         "price_per_token_usd":1.2e-5,"ops_pct":0.0},
        {"date":"2025-01-01","family":"Summarization","provider":"example","model":"example-C","region":"global",
         "a":0.75,"p50_ms":350,"p95_ms":500,"q":0.999,"s":0.999,"tokens_per_sec":0,
         "price_per_token_usd":9.0e-6,"ops_pct":0.0},
    ])
else:
    df = pd.read_csv(merged)

# Simple quality map (toy): phi = a * (bar_l / max(p95, bar_l))**0.5
BAR_L = 500.0
import numpy as np
phi = df["a"].clip(lower=1e-6) * (BAR_L / np.maximum(df["p95_ms"].astype(float).clip(lower=1.0), BAR_L))**0.5
cost = df["price_per_token_usd"].astype(float).clip(lower=1e-9)
lci = (cost / phi).rename("LCI")

df_calc = df.assign(phi=phi, LCI=lci)

by_family = (df_calc.groupby("family", as_index=False)
             .agg(LCI=("LCI","median"),
                  accuracy=("a","median"),
                  p95_ms=("p95_ms","median"),
                  price_per_token_usd=("price_per_token_usd","median"))
            ).sort_values("LCI")

# Write CSV tables the pipeline expects
out_csv = TABLES / "lci_by_family.csv"
by_family.to_csv(out_csv, index=False)

ipd = pd.DataFrame({"date":["2025-01-01","2025-06-01","2025-10-01"],
                    "IPD":[1.00,0.94,0.91]})
ipd.to_csv(TABLES / "ipd.csv", index=False)

# Minimal LaTeX for the paper build (booktabs-ready)
tex = r"""
\begin{table}[t]
\centering
\caption{LCI by Task Family (demo)}
\label{tab:lci_by_family}
\begin{tabular}{lrrrr}
\toprule
Family & LCI & Accuracy & p95 (ms) & Price/Token \\
\midrule
"""[1:]

for _, r in by_family.iterrows():
    tex += f"{r['family']} & {r['LCI']:.2e} & {r['accuracy']:.3f} & {r['p95_ms']:.0f} & {r['price_per_token_usd']:.2e} \\\\\n"

tex += r"""\bottomrule
\end{tabular}
\end{table}
"""

(TABLES / "lci_by_family.tex").write_text(tex, encoding="utf-8")

print(f"Wrote: {out_csv}")
print("Wrote: results/tables/ipd.csv")
print("Wrote: results/tables/lci_by_family.tex")
