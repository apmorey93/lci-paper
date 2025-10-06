# Reproducibility Notes

This repository reproduces LCI calculations and the IPD figure using only public inputs.

## One-command run
1. Install requirements: \pip install -r requirements.txt\
2. Ensure CSV inputs exist under \data/external\ and \data/evals\ following the schema files.
3. Run:
   - \python src/lci_program.py\
   - \python src/make_ipd.py\
   - \python src/figures.py\

## Metadata capture
Each run writes \esults/meta.json\ (UTC timestamp, Python version, platform, package versions).

## Notes
- If some inputs are missing, scripts emit template CSVs with the correct headers and exit with an informative message.
- Figures include captions and units. Latency in milliseconds; prices in USD.
