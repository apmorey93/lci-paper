import sys, time, json, platform, math
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

def chain_indices(df):
    """Return chained Fisher index plus its Laspeyres and Paasche bounds.

    All three are normalised to 1.0 at the base period. The Fisher index is the
    geometric mean of the (equal-weighted) Laspeyres and Paasche price relatives
    and therefore lies between them (Diewert 1976).
    """
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values(["date", "family"])
    dates = df["date"].drop_duplicates().tolist()
    if not dates:
        return pd.DataFrame(columns=["date", "IPD", "Laspeyres", "Paasche"])

    fisher = {dates[0]: 1.0}
    lasp = {dates[0]: 1.0}
    paa = {dates[0]: 1.0}
    for i in range(1, len(dates)):
        d0, d1 = dates[i - 1], dates[i]
        prev = df[df["date"] == d0][["family", "LCI"]].rename(columns={"LCI": "LCI0"})
        curr = df[df["date"] == d1][["family", "LCI"]].rename(columns={"LCI": "LCI1"})
        merged = pd.merge(prev, curr, on="family", how="inner")
        if merged.empty:
            fisher[d1], lasp[d1], paa[d1] = fisher[d0], lasp[d0], paa[d0]
            continue
        L = float((merged["LCI1"] / merged["LCI0"]).mean())          # Laspeyres relative
        P = float(1.0 / ((merged["LCI0"] / merged["LCI1"]).mean()))  # Paasche relative
        F = math.sqrt(L * P)
        fisher[d1] = fisher[d0] * F
        lasp[d1] = lasp[d0] * L
        paa[d1] = paa[d0] * P
    out = pd.DataFrame({
        "date": [d.strftime("%Y-%m-%d") for d in dates],
        "IPD": [fisher[d] for d in dates],
        "Laspeyres": [lasp[d] for d in dates],
        "Paasche": [paa[d] for d in dates],
    })
    base = out["IPD"].iloc[0]
    for c in ("IPD", "Laspeyres", "Paasche"):
        out[c] = out[c] / base * 100.0   # index, base = 100
    return out


def main():
    tables = BASE / "results" / "tables" / "lci_by_family.csv"
    if not tables.exists():
        print("[ERR] lci_by_family.csv not found. Run lci_program.py first.")
        sys.exit(1)

    df = pd.read_csv(tables)
    subset = df[["date", "family", "LCI"]].dropna()
    ipd = chain_indices(subset)

    out_csv = BASE / "results" / "tables" / "ipd.csv"
    ipd.to_csv(out_csv, index=False)
    print(f"[OK] Wrote {out_csv}")
    print(ipd.to_string(index=False))

    try:
        import matplotlib.pyplot as plt
        x = pd.to_datetime(ipd["date"])
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.plot(x, ipd["IPD"], "o-", color="#1f77b4", lw=2, label="Fisher (IPD)")
        ax.plot(x, ipd["Laspeyres"], ":", color="#888", label="Laspeyres")
        ax.plot(x, ipd["Paasche"], "--", color="#888", label="Paasche")
        ax.fill_between(x, ipd["Paasche"], ipd["Laspeyres"], color="#1f77b4", alpha=0.08)
        ax.set_title("Intelligence Price Deflator (IPD), base = 100 at Q3 2023")
        ax.set_ylabel("Index (base = 100)")
        ax.set_xlabel("Date")
        ax.legend(frameon=False)
        fig.autofmt_xdate()
        (BASE / "results" / "figures").mkdir(parents=True, exist_ok=True)
        fig.savefig(BASE / "results" / "figures" / "fig_IPD.pdf", bbox_inches="tight",
                    metadata={"CreationDate": None})
        plt.close(fig)
        print("[OK] Wrote results/figures/fig_IPD.pdf")
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
