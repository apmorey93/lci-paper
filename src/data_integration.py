import os
import pandas as pd
import requests
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]

def fetch_mlperf_results(version="v5.0"):
    url = f"https://raw.githubusercontent.com/mlcommons/inference_results_{version}/main/results/inference_v5.0_latencies.csv"
    try:
        resp = requests.get(url)
        resp.raise_for_status()
        df = pd.read_csv(pd.compat.StringIO(resp.text))
        return df
    except Exception as e:
        print("Could not fetch MLPerf results:", e)
        return pd.DataFrame()

def fetch_open_llm_leaderboard():
    try:
        from datasets import load_dataset
        ds = load_dataset("open-llm-leaderboard/results", split="train")
        return pd.DataFrame(ds)
    except Exception as e:
        print("Could not load OpenLLM dataset:", e)
        return pd.DataFrame()

def normalize_mlperf(df_ml):
    if df_ml.empty:
        return pd.DataFrame()
    df = df_ml.rename(columns={
        "system": "provider_model",
        "latency_95p_ms": "p95_ms",
        "throughput_ops_per_sec": "tokens_per_sec",
    })
    df["a"] = 1.0
    df["q"] = 1.0
    df["s"] = 1.0
    df["price_per_token_usd"] = 1e-6
    df["ops_pct"] = 0.10
    if "provider_model" in df.columns:
        split_cols = df["provider_model"].str.split("-", 1, expand=True)
        df["provider"] = split_cols[0]
        df["model"] = split_cols[1] if split_cols.shape[1] > 1 else split_cols[0]
    df["date"] = pd.to_datetime("2025-10-06")
    df["family"] = "QA"
    df["region"] = "us-east-1"
    df["p50_ms"] = df.get("p95_ms", 100) * 0.5
    return df[[
        "date","family","provider","model","region","a","p50_ms","p95_ms",
        "q","s","tokens_per_sec","price_per_token_usd","ops_pct"
    ]].dropna(how="any")

def normalize_llm(df_llm):
    if df_llm.empty:
        return pd.DataFrame()
    df = df_llm.copy()
    df = df[df["metric_name"].isin(["accuracy","f1"])]
    df = df.rename(columns={"metric_value":"a"})
    df["p50_ms"] = 100.0
    df["p95_ms"] = 200.0
    df["tokens_per_sec"] = 1.0
    df["price_per_token_usd"] = 1e-6
    df["ops_pct"] = 0.10
    df["q"] = 1.0
    df["s"] = 1.0
    df["date"] = pd.to_datetime("2025-10-06")
    df["family"] = "QA"
    df["region"] = "global"
    df["provider"] = df["model"].apply(lambda x: x.split("_")[0] if "_" in x else x)
    return df[[
        "date","family","provider","model","region","a","p50_ms","p95_ms",
        "q","s","tokens_per_sec","price_per_token_usd","ops_pct"
    ]].dropna(how="any")

def create_merged_inputs():
    df_ml = fetch_mlperf_results()
    df1 = normalize_mlperf(df_ml)
    df_ll = fetch_open_llm_leaderboard()
    df2 = normalize_llm(df_ll)
    df_all = pd.concat([df1, df2], ignore_index=True)
    out_path = BASE / "data" / "interim" / "merged_inputs.csv"
    df_all.to_csv(out_path, index=False)
    print(f"Wrote {len(df_all)} rows to", out_path)

if __name__ == "__main__":
    create_merged_inputs()

