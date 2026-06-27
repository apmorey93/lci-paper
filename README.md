# LCI Paper: Locational Cost of Intelligence & the Intelligence Price Deflator

This repository computes the **Locational Cost of Intelligence (LCI)** — the
minimum cost of one quality-adjusted task-equivalent of usable AI output under
quality-of-service (QoS) constraints — and chains it over time into an
**Intelligence Price Deflator (IPD)**.

- Author: **Aditya Morey** (ORCID: https://orcid.org/0009-0000-2864-4586)
- Paper source: `lci_paper.tex` (build with `make pdf`).

## What is real here (and what is modelled)

Every number in the paper traces to one of two honest sources:

1. **A validated discrete-event simulator** (`src/queueing_ps_batch.py`) of a
   `GI/G/k` processor-sharing station with server-side dynamic batching. It is
   **validated against the closed-form M/M/k Erlang-C** mean waiting time in
   `src/validate_queue.py` (worst-case error < 5% across `k∈{1,2,4,8}`,
   `u∈{0.5…0.95}`; see `results/tables/queue_validation.csv`). Latency (p95) and
   throughput vs. utilisation come from this simulator, not from a hand-chosen
   formula.
2. **Public, cited input data** under `data/` — cloud GPU list prices, EIA
   industrial energy prices, published LLM benchmark scores, and public LLM API
   list prices. These rows carry a `source`, `url`, and `accessed` date.

Three kinds of inputs, kept distinct:
- **Modeled (simulated, validated):** latency (p95) and throughput.
- **Sourced (public, cited):** GPU/energy/API prices and benchmark accuracies.
- **Assumed (documented, not sourced):** per-GPU decode rates (`decode_assumed=yes`
  in `hardware.csv`), per-task token counts, service-time variance, availability
  `q`, and safety `s` (see `data/params.json`).

We do **not** claim to have served a live LLM on a GPU. If you have real serving
traces, drop them into `data/evals/latency_schema.csv` and the pipeline will
consume them.

## Pipeline

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
make results     # validate -> integrate -> LCI -> IPD -> figures
make test        # unit tests (chain Fisher / IPD bounds)
make pdf         # build the paper
```

Stage by stage:

| Step | Script | Output |
|------|--------|--------|
| Validate simulator vs Erlang-C | `src/validate_queue.py` | `results/tables/queue_validation.csv` |
| Merge public inputs | `src/data_integration.py` | `data/interim/merged_inputs.csv` |
| Compute LCI(u), u\*, frontier, wedge | `src/lci_program.py` | `results/tables/lci_by_family.csv`, `lci_curves.csv` |
| Chain Fisher IPD (+ Laspeyres/Paasche bounds) | `src/make_ipd.py` | `results/tables/ipd.csv`, `results/figures/fig_IPD.pdf` |
| Paper figures | `src/figures.py` | `results/figures/*.pdf` |

## Method summary

For each `(date, task family)` and each GPU option available that date, set the
per-request service time `E[S] = out_tokens / decode_rate`, rescale the single
normalised simulation sweep, and compute

```
LCI(u) = raw_cost(u) / phi(u),     raw_cost = (GPU + energy) * overhead
phi    = alpha(a)^wa * lambda(l)^wl * rho(q)^wq * sigma(s)^ws   (paper Eq. 5)
```

`raw_cost(u)` falls with utilisation (cost spread over throughput) while
`1/phi(u)` rises (latency erodes quality), so `LCI(u)` is **U-shaped** with an
interior cost-minimising utilisation `u*`. The reported LCI per `(date, family)`
is the **minimum over GPU options** — the cost frontier. The market price (PUI)
comes from public API list prices; the wedge is `PUI / LCI`.

## Data inputs (sourced unless flagged assumed)

- `data/external/hardware.csv` — GPU list prices (AWS p4d/p5), TDP, decode rates.
- `data/external/energy_prices.csv` — EIA industrial electricity prices.
- `data/external/api_prices.csv` — public LLM API list prices (for PUI).
- `data/evals/accuracy.csv` — published Llama-2/3/3.1-70B benchmark scores.
- `data/params.json` — QoS weights, thresholds, task token counts, queue config.

## Reproducibility

- Deterministic seeds throughout; `results/meta.json` records versions, platform,
  parameters, and timestamps.
- `make results` regenerates every table and figure from the CSVs.
- Headline result: the IPD falls from 100 (2023-07) to ≈48 (2025-06) — a ~52%
  decline in the quality-adjusted cost of intelligence — driven by sourced GPU
  price cuts, faster decoding, and benchmark-accuracy gains.

## License & citation

- Code is MIT (`LICENSE`). Citation metadata in `CITATION.cff`.
