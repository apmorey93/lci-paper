"""Step 2: assemble the comparable benchmark panel and its input confidence
intervals. Computes ONLY the accuracy CIs (panel inputs); it does NOT compute any
LCI, index, or wedge number.

Comparability finding (from web sourcing, see docs/benchmark_panel.md):
a fully comparable instruction-tuned panel across 2023–2025 does not exist in
public sources. Llama-3-70B-Instruct and Llama-3.1-70B-Instruct are mutually
comparable under one protocol per metric; Llama-2-70B-Chat is NOT (no Meta
instruct-variant scores under matching protocols; only base-model or
different-harness numbers). The 2023 vintage is therefore marked out-of-panel.
"""

from __future__ import annotations

import math
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "evals" / "accuracy_panel.csv"


def wilson(p_hat: float, n: int, z: float = 1.96):
    """Wilson score interval for a binomial proportion (p_hat in [0,1])."""
    denom = 1 + z * z / n
    center = (p_hat + z * z / (2 * n)) / denom
    half = z * math.sqrt(p_hat * (1 - p_hat) / n + z * z / (4 * n * n)) / denom
    return max(0.0, center - half), min(1.0, center + half)


# Sourced rows. in_panel=True only where the instruct variant + one fixed protocol
# is met from a consistent reputable source; CIs are Wilson at 95% over the test set.
# Protocols standardized for the EXTENDED panel (so Llama-3.3 can be included):
#   MMLU  = 0-shot CoT (the only MMLU protocol with values for L3/L3.1/L3.3)
#   HumanEval = 0-shot pass@1
#   GSM8K = 8-shot CoT (L3.3 label unconfirmed on card -> flagged)
# Models: frontier open ~70B-dense instruct at each date. 2025-06 reuses Llama-3.3
# weights (cost-only leg). NOTE saturation: MMLU flat 86.0; GSM8K ceiling ~93-95;
# HumanEval is the only family with real quality movement.
rows = [
    # ---- QA / MMLU (0-shot CoT) — saturated/flat at 86.0 ----
    dict(family="QA", benchmark="MMLU", date="2024-04-01", model="Llama-3-70B-Instruct",
         variant="instruct", protocol="0-shot CoT, macro-avg acc", score_pct=86.0, n=14042,
         in_panel=True, source="Llama 3 Herd of Models, arXiv:2407.21783 Table 2",
         url="https://arxiv.org/abs/2407.21783", confidence=0.90),
    dict(family="QA", benchmark="MMLU", date="2024-07-01", model="Llama-3.1-70B-Instruct",
         variant="instruct", protocol="0-shot CoT, macro-avg acc", score_pct=86.0, n=14042,
         in_panel=True, source="Llama 3 Herd of Models, arXiv:2407.21783 Table 2",
         url="https://arxiv.org/abs/2407.21783", confidence=0.92),
    dict(family="QA", benchmark="MMLU", date="2024-12-01", model="Llama-3.3-70B-Instruct",
         variant="instruct", protocol="0-shot CoT, macro-avg acc", score_pct=86.0, n=14042,
         in_panel=True, source="Llama-3.3-70B-Instruct model card",
         url="https://huggingface.co/meta-llama/Llama-3.3-70B-Instruct", confidence=0.90),
    dict(family="QA", benchmark="MMLU", date="2025-06-01", model="Llama-3.3-70B-Instruct",
         variant="instruct", protocol="0-shot CoT, macro-avg acc (same weights; cost-only leg)", score_pct=86.0, n=14042,
         in_panel=True, source="Llama-3.3-70B-Instruct model card (held for 2025 cost leg)",
         url="https://huggingface.co/meta-llama/Llama-3.3-70B-Instruct", confidence=0.85),
    # ---- Code / HumanEval (0-shot pass@1) — the only metric that moves ----
    dict(family="Code", benchmark="HumanEval", date="2024-04-01", model="Llama-3-70B-Instruct",
         variant="instruct", protocol="0-shot pass@1", score_pct=80.5, n=164,
         in_panel=True, source="Llama 3 Herd of Models, Table 18 (finetuned)",
         url="https://arxiv.org/abs/2407.21783", confidence=0.80),
    dict(family="Code", benchmark="HumanEval", date="2024-07-01", model="Llama-3.1-70B-Instruct",
         variant="instruct", protocol="0-shot pass@1", score_pct=80.5, n=164,
         in_panel=True, source="Llama-3.1-70B-Instruct model card",
         url="https://huggingface.co/meta-llama/Llama-3.1-70B-Instruct", confidence=0.75),
    dict(family="Code", benchmark="HumanEval", date="2024-12-01", model="Llama-3.3-70B-Instruct",
         variant="instruct", protocol="0-shot pass@1", score_pct=88.4, n=164,
         in_panel=True, source="Llama-3.3-70B-Instruct model card",
         url="https://huggingface.co/meta-llama/Llama-3.3-70B-Instruct", confidence=0.90),
    dict(family="Code", benchmark="HumanEval", date="2025-06-01", model="Llama-3.3-70B-Instruct",
         variant="instruct", protocol="0-shot pass@1 (same weights; cost-only leg)", score_pct=88.4, n=164,
         in_panel=True, source="Llama-3.3-70B-Instruct model card (held for 2025 cost leg)",
         url="https://huggingface.co/meta-llama/Llama-3.3-70B-Instruct", confidence=0.85),
    # ---- Reasoning / GSM8K (8-shot CoT) — ceiling band ~93-95 ----
    dict(family="Reasoning", benchmark="GSM8K", date="2024-04-01", model="Llama-3-70B-Instruct",
         variant="instruct", protocol="8-shot CoT, em_maj1@1", score_pct=93.0, n=1319,
         in_panel=True, source="Llama 3 70B Instruct model card",
         url="https://huggingface.co/meta-llama/Meta-Llama-3-70B-Instruct", confidence=0.92),
    dict(family="Reasoning", benchmark="GSM8K", date="2024-07-01", model="Llama-3.1-70B-Instruct",
         variant="instruct", protocol="8-shot CoT, em_maj1@1", score_pct=95.1, n=1319,
         in_panel=True, source="Llama-3.1-70B-Instruct model card",
         url="https://huggingface.co/meta-llama/Llama-3.1-70B-Instruct", confidence=0.93),
    dict(family="Reasoning", benchmark="GSM8K", date="2024-12-01", model="Llama-3.3-70B-Instruct",
         variant="instruct", protocol="8-shot CoT (label unconfirmed on 3.3 card)", score_pct=94.84, n=1319,
         in_panel=True, source="Llama-3.3-70B-Instruct model card eval-results (protocol label not pinned)",
         url="https://huggingface.co/meta-llama/Llama-3.3-70B-Instruct", confidence=0.60),
    dict(family="Reasoning", benchmark="GSM8K", date="2025-06-01", model="Llama-3.3-70B-Instruct",
         variant="instruct", protocol="8-shot CoT (label unconfirmed; same weights; cost-only leg)", score_pct=94.84, n=1319,
         in_panel=True, source="Llama-3.3-70B-Instruct model card (held for 2025 cost leg)",
         url="https://huggingface.co/meta-llama/Llama-3.3-70B-Instruct", confidence=0.55),
    # --- 2023 vintage: NOT comparable (variant/harness mismatch) -> excluded ---
    dict(family="QA", benchmark="MMLU", date="2023-07-01", model="Llama-2-70B-Chat",
         variant="instruct(?)", protocol="5-shot; THIRD-PARTY harness (not Meta); chat-variant unverified by Meta",
         score_pct=63.2, n=14042, in_panel=False,
         source="EleutherAI lm-eval-harness reproduction (issue #1213); Meta base-only 68.9",
         url="https://github.com/EleutherAI/lm-evaluation-harness/issues/1213", confidence=0.45),
    dict(family="Code", benchmark="HumanEval", date="2023-07-01", model="Llama-2-70B-Chat",
         variant="instruct(?)", protocol="0-shot pass@1 claimed; launch-blog table, unstated harness; Meta paper reports base-only 29.9",
         score_pct=25.6, n=164, in_panel=False,
         source="Meta Llama 3 launch blog comparison table",
         url="https://ai.meta.com/blog/meta-llama-3/", confidence=0.40),
    dict(family="Reasoning", benchmark="GSM8K", date="2023-07-01", model="Llama-2-70B(base)",
         variant="base (NOT instruct)", protocol="8-shot CoT; BASE model — no instruct/Chat GSM8K published",
         score_pct=56.8, n=1319, in_panel=False,
         source="Llama 2 paper, arXiv:2307.09288 (base model)",
         url="https://arxiv.org/abs/2307.09288", confidence=0.25),
]

recs = []
for r in rows:
    rr = dict(r)
    if r["in_panel"]:
        lo, hi = wilson(r["score_pct"] / 100.0, r["n"])
        rr["ci_method"] = "Wilson"
        rr["ci_level"] = 0.95
        rr["ci_low_pct"] = round(lo * 100, 2)
        rr["ci_high_pct"] = round(hi * 100, 2)
        rr["sampling_unit"] = "benchmark item (i.i.d. over the fixed test split)"
    else:
        rr["ci_method"] = ""; rr["ci_level"] = ""; rr["ci_low_pct"] = ""
        rr["ci_high_pct"] = ""; rr["sampling_unit"] = ""
    rr["accessed"] = "2026-06-27"
    recs.append(rr)

cols = ["family", "benchmark", "date", "model", "variant", "protocol", "score_pct",
        "n", "ci_method", "ci_level", "ci_low_pct", "ci_high_pct", "sampling_unit",
        "in_panel", "confidence", "source", "url", "accessed"]
df = pd.DataFrame(recs)[cols]
OUT.parent.mkdir(parents=True, exist_ok=True)
df.to_csv(OUT, index=False)
print(f"[OK] Wrote {OUT}")
print("\nIN-PANEL (comparable instruct, Wilson 95% CI):")
ip = df[df["in_panel"]]
print(ip[["family", "date", "score_pct", "ci_low_pct", "ci_high_pct"]].to_string(index=False))
print("\nOUT-OF-PANEL (2023, not comparable — excluded from any index):")
print(df[~df["in_panel"]][["family", "model", "variant", "score_pct"]].to_string(index=False))
print("\nComparable window:", sorted(ip["date"].unique()))
