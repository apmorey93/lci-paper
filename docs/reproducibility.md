# Reproducibility Notes

This repository reproduces the LCI estimates, the Intelligence Price Deflator
(IPD), and every paper figure from the public inputs tracked in git. There is
**no fabricated-data fallback**: each stage reads real inputs and fails loudly if
a required input is missing.

## What is measured vs. modeled vs. assumed
- **Modeled (simulated, validated):** latency (p95) and throughput, from the
  discrete-event GI/G/k-PS+batching simulator in `src/queueing_ps_batch.py`,
  validated against the closed-form M/M/k Erlang-C wait in `src/validate_queue.py`
  (worst-case error < 5%). We do **not** serve a live model on a GPU.
- **Sourced (public, cited):** cloud-GPU list prices, EIA industrial energy
  tariffs, published Llama-2/3/3.1-70B benchmark scores, and public LLM API list
  prices. Each row in `data/external/` and `data/evals/` carries `source`, `url`,
  and `accessed`.
- **Assumed (documented):** per-GPU decode rates (`decode_assumed=yes` in
  `data/external/hardware.csv`), per-task token counts, service-time variance,
  availability `q`, and safety `s` (all in `data/params.json`).

## Quickstart
1. `pip install -r requirements.txt`
2. `make results` — runs, in order:
   - `src/validate_queue.py` (simulator vs Erlang-C)
   - `src/data_integration.py` (merge public inputs)
   - `src/lci_program.py` (LCI(u), cost frontier at the latency-feasibility u*)
   - `src/make_ipd.py` (chain Fisher IPD + Laspeyres/Paasche bounds)
   - `src/figures.py` (all paper figures)
3. `make test` — unit tests (chain Fisher / IPD bounds).
4. `make pdf` — build `lci_paper.tex` (the single paper source).

## Determinism
All simulation uses fixed seeds (`data/params.json` `sim.base_seed`), so
`results/tables/*.csv` regenerate byte-identically. CI (`.github/workflows/latex.yml`)
asserts this with `git diff --exit-code` on the result CSVs after re-running the
pipeline, then builds the PDF. Matplotlib figure PDFs may differ only in embedded
metadata; their content is deterministic.

## Metadata capture
`results/meta.json` records the UTC timestamp, Python/numpy/pandas versions,
platform, and the full parameter set for each run.
