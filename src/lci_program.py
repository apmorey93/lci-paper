import os, json, sys, time, platform
from pathlib import Path
Path('data/interim').mkdir(parents=True, exist_ok=True)
import pandas as pd
import numpy as np

BASE = Path(__file__).resolve().parents[1]

# QoS weights (priors) — adjust or grid in sensitivity analyses
ETA_A = 2.0
ETA_L = 0.5
ETA_Q = 0.2
ETA_S = 0.2

# Latency target (ms) by family (example defaults)
LATENCY_TARGET_MS = {"QA": 800, "Code": 1200, "Summ": 1200}

def ensure_inputs():
    schemas = {
        "data/evals/accuracy_schema.csv": "date,family,provider,model,region,metric,value,N,source,url,notes\n",
        "data/evals/latency_schema.csv": "date,provider,model,region,p50_ms,p95_ms,N,window_start,window_end,method,notes\n",
        "data/external/energy_prices_schema.csv": "date,region,price_usd_per_kwh,source,url,notes\n",
        "data/external/cloud_prices_schema.csv": "date,provider,endpoint,price_per_token_usd,egress_usd_per_gb,source,url,notes\n",
    }
    for rel, header in schemas.items():
        p = BASE / rel
        if not p.exists():
            p.write_text(header)

def latency_penalty(family: str, p95_ms: float, eta_l: float = ETA_L) -> float:
    bar = LATENCY_TARGET_MS.get(family, 1000)
    return (bar / max(p95_ms, bar)) ** eta_l

def qou_row(row):
    a = float(row.get("a", np.nan))
    lms = float(row.get("p95_ms", np.nan))
    q = float(row.get("q", 0.999))
    s = float(row.get("s", 0.99))
    tps = float(row.get("tokens_per_sec", np.nan))
    fam = row.get("family", "QA")
    if any(np.isnan(x) for x in [a, lms, tps]):
        return np.nan
    return tps * (a ** ETA_A) * (latency_penalty(fam, lms) ** 1.0) * (q ** ETA_Q) * (s ** ETA_S)

def all_in_cost(row):
    cpt = float(row.get("price_per_token_usd", np.nan))
    ops_pct = float(row.get("ops_pct", 0.10))
    if np.isnan(cpt):
        return np.nan
    return cpt * (1 + ops_pct)

def main():
    ensure_inputs()
    merged_path = BASE / "data" / "interim" / "merged_inputs.csv"
    if not merged_path.exists():
        template = "date,family,provider,model,region,a,p50_ms,p95_ms,q,s,tokens_per_sec,price_per_token_usd,ops_pct\n"
        merged_path.parent.mkdir(parents=True, exist_ok=True)\n    merged_path.write_text(template)
        print(f"[INFO] Created template {merged_path}. Please populate with public inputs.")
        sys.exit(1)

    df = pd.read_csv(merged_path)
    if df.empty:
        print("[ERR] merged_inputs.csv is empty. Add at least one row of public inputs.")
        sys.exit(1)

    df["QOU"] = df.apply(qou_row, axis=1)
    df["C_all_in"] = df.apply(all_in_cost, axis=1)
    df["LCI"] = df["C_all_in"] / df["QOU"]

    grp_cols = ["date", "family", "provider", "model", "region"]
    out = df[grp_cols + ["a", "p95_ms", "QOU", "C_all_in", "LCI"]].copy()

    results_dir = BASE / "results" / "tables"
    results_dir.mkdir(parents=True, exist_ok=True)
    out_csv = results_dir / "lci_by_family.csv"
    out_tex = results_dir / "lci_by_family.tex"
    out.to_csv(out_csv, index=False)

    def to_tex(df):
        cols = ["family", "provider", "region", "a", "p95_ms", "QOU", "LCI"]
        df2 = df[cols].copy()
        return df2.to_latex(index=False, float_format="%.4g", escape=False)

    out_tex.write_text(to_tex(out))
    print(f"[OK] Wrote {out_csv} and {out_tex}")

    meta = {
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "python": sys.version,
        "platform": platform.platform(),
        "packages": {
            "pandas": pd.__version__,
            "numpy": np.__version__,
        }
    }
    (BASE / "results" / "meta.json").write_text(json.dumps(meta, indent=2))

if __name__ == "__main__":
    main()



