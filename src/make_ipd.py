import sys, time, json, platform
from pathlib import Path
import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parents[1]

def chain_fisher(df):
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values(["date", "family"])
    dates = df["date"].drop_duplicates().tolist()
    if not dates:
        return pd.DataFrame(columns=["date","IPD"])

    # Equal weights for now (public calibration)
    fisher = {dates[0]: 1.0}
    for i in range(1, len(dates)):
        d0, d1 = dates[i-1], dates[i]
        prev = df[df["date"] == d0][["family","LCI"]].rename(columns={"LCI":"LCI0"})
        curr = df[df["date"] == d1][["family","LCI"]].rename(columns={"LCI":"LCI1"})
        merged = pd.merge(prev, curr, on="family", how="inner")
        if merged.empty:
            fisher[d1] = fisher[d0]
            continue
        L = (merged["LCI1"] / merged["LCI0"]).mean()
        P = 1.0 / ( (merged["LCI0"] / merged["LCI1"]).mean() )
        F = float(np.sqrt(L * P))
        fisher[d1] = fisher[d0] * F
    out = pd.DataFrame({"date": list(fisher.keys()), "IPD": list(fisher.values())}).sort_values("date")
    out["IPD"] = out["IPD"] / out["IPD"].iloc[0]
    return out

def main():
    tables = BASE / "results" / "tables" / "lci_by_family.csv"
    if not tables.exists():
        print("[ERR] lci_by_family.csv not found. Run lci_program.py first.")
        sys.exit(1)

    df = pd.read_csv(tables)
    subset = df[["date", "family", "LCI"]].dropna()
    ipd = chain_fisher(subset)

    out_csv = BASE / "results" / "tables" / "ipd.csv"
    ipd.to_csv(out_csv, index=False)
    print(f"[OK] Wrote {out_csv}")

    try:
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots()
        ax.plot(pd.to_datetime(ipd["date"]), ipd["IPD"])
        ax.set_title("Intelligence Price Deflator (IPD) — Chain Fisher (equal weights)")
        ax.set_ylabel("Index (t0 = 1)")
        ax.set_xlabel("Date")
        fig.autofmt_xdate()
        (BASE / "results" / "figures").mkdir(parents=True, exist_ok=True)
        fig.savefig(BASE / "results" / "figures" / "ipd_fan_chart.pdf", bbox_inches="tight")
        plt.close(fig)
        print("[OK] Wrote results/figures/ipd_fan_chart.pdf")
    except Exception as e:
        print("[WARN] Could not plot IPD:", e)

    meta_path = BASE / "results" / "meta.json"
    meta = {}
    if meta_path.exists():
        try:
            meta = json.loads(meta_path.read_text())
        except Exception:
            meta = {}
    meta.update({
        "make_ipd": {
            "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "python": sys.version,
            "platform": platform.platform(),
        }
    })
    meta_path.write_text(json.dumps(meta, indent=2))

if __name__ == "__main__":
    main()
