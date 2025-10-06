# LCI Paper: Public Calibration & IPD

This repository contains code and data schemas to compute **Locational Cost of Intelligence (LCI)** for several task families using **public inputs** and to aggregate them into a provisional **Intelligence Price Deflator (IPD)**.

- Paper: *Pricing Usable Intelligence: A Location-Adjusted Cost Function with QoS Chance Constraints*
- Author: **Aditya Morey** (ORCID: https://orcid.org/0009-0000-2864-4586) — <adityamorey1723@gmail.com>

## What this repo provides
- \src/lci_program.py\ — computes QOU and LCI from public inputs.
- \src/make_ipd.py\ — builds a chain Fisher IPD across task families.
- \src/queueing_ps_batch.py\ — GI/G/k-PS batching approximation (p95 latency; convexity).
- \src/figures.py\ — produces paper figures from computed outputs.
- Data schemas under \data/\ for accuracy, latency, energy, and cloud prices.

All computations rely on **public datasets** (e.g., energy prices, cloud list prices, published benchmarks, light latency/accuracy probes). No proprietary data are required.

## Quick start
\\\ash
python -m venv .venv && source .venv/bin/activate    # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt

# 1) Place public CSVs in data/external and data/evals (see schemas below).
# 2) Optionally edit data/interim/merged_inputs.csv (a demo row is seeded).
# 3) Compute LCI, then IPD, then figures:
python src/lci_program.py
python src/make_ipd.py
python src/figures.py
\\\

Outputs go to \esults/tables\ and \esults/figures\. A metadata file \esults/meta.json\ records environment details.

## Data schemas (CSV)
**Accuracy (per family x model x region x date)** — \data/evals/accuracy_schema.csv\ header:
\\\
date,family,provider,model,region,metric,value,N,source,url,notes
\\\

**Latency (p95) probes** — \data/evals/latency_schema.csv\ header:
\\\
date,provider,model,region,p50_ms,p95_ms,N,window_start,window_end,method,notes
\\\

**Energy prices** — \data/external/energy_prices_schema.csv\ header:
\\\
date,region,price_usd_per_kwh,source,url,notes
\\\

**Cloud prices** — \data/external/cloud_prices_schema.csv\ header:
\\\
date,provider,endpoint,price_per_token_usd,egress_usd_per_gb,source,url,notes
\\\

## Reproducibility
- Deterministic seeds when simulating.
- \esults/meta.json\ captures versions and timestamps.
- All inputs are public; list and link sources in the CSVs.

## License & citation
- Code is MIT. See \LICENSE\.
- Citation metadata in \CITATION.cff\.

![Build Paper](https://github.com/apmorey93/lci-paper/actions/workflows/build_paper.yml/badge.svg)

