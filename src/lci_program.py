import csv
from pathlib import Path
import json

# === LCI Program Generator ===
# This script ensures schema templates exist for data collection
# and creates a merged_inputs.csv placeholder for pipeline stages.

def ensure_schema_files():
    """Create minimal schema templates for accuracy and latency inputs."""
    schema_dir = Path("data/evals")
    schema_dir.mkdir(parents=True, exist_ok=True)

    schemas = {
        "accuracy_schema.csv": "date,family,provider,model,region,metric,value,N,source,url,notes",
        "latency_schema.csv": "date,provider,model,region,p50_ms,p95_ms,N,window_start,window_end,method,notes"
    }

    for filename, header in schemas.items():
        path = schema_dir / filename
        if not path.exists():
            path.write_text(header + "\n")
            print(f"Created {path}")
        else:
            print(f"{path} already exists")

def create_merged_template():
    """Generate the merged_inputs.csv template used for integration."""
    merged_path = Path("data/interim/merged_inputs.csv")
    merged_path.parent.mkdir(parents=True, exist_ok=True)
    header = "date,family,provider,model,region,a,p50_ms,p95_ms,q,s,tokens_per_sec,price_per_token_usd,ops_pct"
    merged_path.write_text(header + "\n")
    print(f"Wrote schema template to {merged_path}")

if __name__ == "__main__":
    ensure_schema_files()
    create_merged_template()
