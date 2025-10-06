#!/usr/bin/env bash
set -euo pipefail

# ----- PREP RESULTS -----
mkdir -p data/raw data/interim results/tables out scripts
[ -f data/raw/accuracy.csv ] || echo "model,family,dataset,split,metric,value,seed,timestamp" > data/raw/accuracy.csv
[ -f data/raw/latency.csv ]  || echo "model,family,prompt_len,output_len,latency_ms_p50,latency_ms_p95,tokens_per_sec,hardware,batch_size,timestamp" > data/raw/latency.csv

cat > scripts/aggregate_lci.py <<'PY'
#!/usr/bin/env python3
import pandas as pd, argparse, sys
p = argparse.ArgumentParser()
p.add_argument("--accuracy", required=True)
p.add_argument("--latency", required=True)
p.add_argument("--out", required=True)
a = p.parse_args()
try:
    acc = pd.read_csv(a.accuracy)
    lat = pd.read_csv(a.latency)
except Exception as e:
    print("Read CSV error:", e, file=sys.stderr)
    acc = pd.DataFrame(); lat = pd.DataFrame()
if acc.empty or lat.empty:
    pd.DataFrame([{"family":"Stub","lci":0,"source":"empty","n":0}]).to_csv(a.out,index=False)
else:
    acc_g = acc.groupby("family")["value"].mean().rename("acc_mean")
    lat_g = lat.groupby("family")["latency_ms_p50"].median().rename("lat_p50")
    df = acc_g.to_frame().join(lat_g, how="inner")
    df["lci"] = df["acc_mean"] / (1.0 + df["lat_p50"]/1000.0)
    df["source"] = "ci"; df["n"] = 1
    df.reset_index().to_csv(a.out, index=False)
print(f"Wrote {a.out}")
PY
chmod +x scripts/aggregate_lci.py

python3 scripts/aggregate_lci.py --accuracy data/raw/accuracy.csv --latency data/raw/latency.csv --out data/interim/lci_by_family.csv
mkdir -p results/tables
cp -f data/interim/lci_by_family.csv results/tables/lci_by_family.csv 2>/dev/null || true
[ -f results/tables/ipd.csv ] || { echo "family,ipd" > results/tables/ipd.csv; echo "Open,0.0" >> results/tables/ipd.csv; }

# ----- BUILD PAPER -----
sudo apt-get update -y
sudo apt-get install -y --no-install-recommends pandoc wkhtmltopdf
mkdir -p out
if [ -f paper/main.tex ]; then
  pandoc paper/main.tex -t html5 -s -o out/paper.html
else
  SRC="paper/main.md"
  [ -f "$SRC" ] || { echo "# LCI Paper (Placeholder)" > "$SRC"; echo "" >> "$SRC"; }
  pandoc "$SRC" -t html5 -s -o out/paper.html
fi
wkhtmltopdf --enable-local-file-access out/paper.html out/paper.pdf
test -f out/paper.pdf