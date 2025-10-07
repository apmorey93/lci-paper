# Reproducibility Notes

This repository reproduces LCI calculations and the IPD figure using only the
files tracked in git. When the proprietary input bundles are missing, the demo
scripts fabricate deterministic seed data so that every stage of the pipeline
still runs to completion.

## Quickstart
1. Install requirements: `pip install -r requirements.txt`
2. (Optional) Drop real CSV inputs under `data/external/` and `data/evals/` to
   replace the demo seeds.
3. Run the main pipeline:
   - `python src/lci_program.py`
   - `python src/make_ipd.py`
   - `python src/figures.py`

## Metadata capture
`results/meta.json` records the UTC timestamp, Python version, and platform for
each tool invocation.
- If inputs are missing, `src/generate_demo_results.py` backfills
  `results/tables/lci_by_family.csv`, `ipd.csv`, and `lci_by_family.tex` with
  deterministic sample data.
- Figures include captions and units. Latency is measured in milliseconds;
  prices in USD.
## Notes
- If some inputs are missing, scripts emit template CSVs with the correct headers and exit with an informative message.
- Figures include captions and units. Latency in milliseconds; prices in USD.
