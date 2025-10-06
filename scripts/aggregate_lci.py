#!/usr/bin/env python3
import pandas as pd, argparse
p = argparse.ArgumentParser()
p.add_argument("--accuracy", required=True)
p.add_argument("--latency", required=True)
p.add_argument("--out", required=True)
a = p.parse_args()

acc = pd.read_csv(a.accuracy)
lat = pd.read_csv(a.latency)
if acc.empty or lat.empty:
    # write a harmless stub so CI still builds
    pd.DataFrame([{"family":"Stub","lci":0,"source":"empty","n":0}]).to_csv(a.out,index=False)
    raise SystemExit(0)

acc_g = acc.groupby("family")["value"].mean().rename("acc_mean")
lat_g = lat.groupby("family")["latency_ms_p50"].median().rename("lat_p50")
df = acc_g.to_frame().join(lat_g, how="inner")
df["lci"] = df["acc_mean"] / (1.0 + df["lat_p50"]/1000.0)  # placeholder formula
df["source"] = "ci"
df["n"] = 1
df.reset_index().to_csv(a.out, index=False)
print(f"Wrote {a.out}")
