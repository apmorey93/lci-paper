"""Step 2: assemble the comparable benchmark panel and its (provisional) input
confidence intervals. Computes ONLY accuracy CIs (panel inputs); it does NOT
compute any LCI, index, or wedge number.

All in-panel values are from Meta's OFFICIAL model-card "Instruction tuned models"
comparison tables (verified; not the Herd paper, launch blogs, or community/EvalEval
results):
  - L3 vs L3.1: Llama-3.1-70B-Instruct card (side-by-side table)
  - L3.3:       Llama-3.3-70B-Instruct card
Balanced-panel families = metrics with an official protocol-matched value for ALL
of L3 / L3.1 / L3.3:
  QA        = MMLU   (0-shot CoT, macro_avg/acc)   80.9 / 86.0 / 86.0
  Code      = HumanEval (0-shot pass@1)            81.7 / 80.5 / 88.4
  Reasoning = MATH   (0-shot CoT)                  51.0 / 68.0 / 77.0   [metric-string
              changes at L3.3: final_em -> sympy_intersection_score; flagged]
GSM8K is EXCLUDED (omitted from the official L3.3 table). The 2023 Llama-2 vintage
is excluded (base-variant / different-harness only; not comparable).

CI policy (per review): reconstructed CIs are PROVISIONAL and only given where a
binomial model is a reasonable approximation of the published estimand:
  - HumanEval pass@1 over n=164: provisional Wilson (value is rounded).
  - MATH over n=5000 (full test set, assumed): provisional Wilson; the published
    metric (final_em / sympy_intersection_score) is treated as per-item binary,
    an approximation.
  - MMLU: NO binomial CI — the published value is a macro-average over 57 subjects;
    per-subject counts are unavailable, so a single-binomial CI would misrepresent
    the estimand. Marked ci_status="none (macro-avg; needs per-subject counts)".
Overlapping marginal CIs do NOT establish significance of cross-model change
(that needs paired item outcomes); no significance is claimed here.
"""

from __future__ import annotations

import math
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "evals" / "accuracy_panel.csv"
L31 = "https://huggingface.co/meta-llama/Llama-3.1-70B-Instruct"
L33 = "https://huggingface.co/meta-llama/Llama-3.3-70B-Instruct"


def wilson(p_hat: float, n: int, z: float = 1.96):
    denom = 1 + z * z / n
    center = (p_hat + z * z / (2 * n)) / denom
    half = z * math.sqrt(p_hat * (1 - p_hat) / n + z * z / (4 * n * n)) / denom
    return max(0.0, center - half), min(1.0, center + half)


# in-panel rows: (family, benchmark, protocol, date, model, score_pct, n, ci_mode, source_url, conf)
# ci_mode: "wilson" (provisional) or "none"
P = [
    # QA / MMLU (0-shot CoT, macro_avg/acc) — macro-average => no binomial CI
    ("QA", "MMLU", "0-shot CoT, macro_avg/acc", "2024-04-01", "Llama-3-70B-Instruct",   80.9, 14042, "none",   L31, 0.97),
    ("QA", "MMLU", "0-shot CoT, macro_avg/acc", "2024-07-01", "Llama-3.1-70B-Instruct", 86.0, 14042, "none",   L31, 0.97),
    ("QA", "MMLU", "0-shot CoT, macro_avg/acc", "2024-12-01", "Llama-3.3-70B-Instruct", 86.0, 14042, "none",   L33, 0.97),
    ("QA", "MMLU", "0-shot CoT, macro_avg/acc (matched-model cost continuation)", "2025-06-01", "Llama-3.3-70B-Instruct", 86.0, 14042, "none", L33, 0.90),
    # Code / HumanEval (0-shot pass@1) — provisional binomial
    ("Code", "HumanEval", "0-shot pass@1", "2024-04-01", "Llama-3-70B-Instruct",   81.7, 164, "wilson", L31, 0.97),
    ("Code", "HumanEval", "0-shot pass@1", "2024-07-01", "Llama-3.1-70B-Instruct", 80.5, 164, "wilson", L31, 0.97),
    ("Code", "HumanEval", "0-shot pass@1", "2024-12-01", "Llama-3.3-70B-Instruct", 88.4, 164, "wilson", L33, 0.95),
    ("Code", "HumanEval", "0-shot pass@1 (matched-model cost continuation)", "2025-06-01", "Llama-3.3-70B-Instruct", 88.4, 164, "wilson", L33, 0.90),
    # Reasoning / MATH (0-shot CoT) — provisional binomial; metric-string changes at L3.3
    ("Reasoning", "MATH", "0-shot CoT (final_em; n=5000 assumed)", "2024-04-01", "Llama-3-70B-Instruct",   51.0, 5000, "wilson", L31, 0.92),
    ("Reasoning", "MATH", "0-shot CoT (final_em; n=5000 assumed)", "2024-07-01", "Llama-3.1-70B-Instruct", 68.0, 5000, "wilson", L31, 0.92),
    ("Reasoning", "MATH", "0-shot CoT (sympy_intersection_score; n=5000 assumed)", "2024-12-01", "Llama-3.3-70B-Instruct", 77.0, 5000, "wilson", L33, 0.90),
    ("Reasoning", "MATH", "0-shot CoT (sympy; matched-model cost continuation)", "2025-06-01", "Llama-3.3-70B-Instruct", 77.0, 5000, "wilson", L33, 0.88),
]

# excluded 2023 rows (not comparable): kept for transparency, in_panel=False
EXCL = [
    ("QA", "MMLU", "5-shot; THIRD-PARTY harness; chat-variant unverified by Meta",
     "2023-07-01", "Llama-2-70B-Chat", 63.2, 14042,
     "EleutherAI lm-eval-harness reproduction (Meta base-only 68.9)",
     "https://github.com/EleutherAI/lm-evaluation-harness/issues/1213", 0.45),
    ("Code", "HumanEval", "0-shot pass@1 claimed; launch-blog table; Meta paper reports base-only 29.9",
     "2023-07-01", "Llama-2-70B-Chat", 25.6, 164,
     "Meta Llama 3 launch blog comparison table", "https://ai.meta.com/blog/meta-llama-3/", 0.40),
    ("Reasoning", "MATH/GSM8K", "no official instruct MATH or GSM8K for Llama-2-70B-Chat",
     "2023-07-01", "Llama-2-70B-Chat", float("nan"), 0,
     "no comparable instruct reasoning score published", "", 0.10),
]

recs = []
for fam, bench, proto, date, model, score, n, ci_mode, url, conf in P:
    lo = hi = ""
    ci_method = ci_level = sampling_unit = ""
    if ci_mode == "wilson":
        clo, chi = wilson(score / 100.0, n)
        lo, hi = round(clo * 100, 2), round(chi * 100, 2)
        ci_method, ci_level = "Wilson (provisional)", 0.95
        sampling_unit = "benchmark item (treated as i.i.d. binary; approximation)"
        ci_status = "provisional (rounded value; binomial approximation)"
    else:
        ci_status = "none (macro-avg over 57 subjects; needs per-subject counts)"
    recs.append(dict(family=fam, benchmark=bench, date=date, model=model, variant="instruct",
                     protocol=proto, score_pct=score, n=n, ci_method=ci_method, ci_level=ci_level,
                     ci_low_pct=lo, ci_high_pct=hi, ci_status=ci_status, sampling_unit=sampling_unit,
                     in_panel=True, confidence=conf, source="Meta official model card",
                     url=url, accessed="2026-06-27"))
for fam, bench, proto, date, model, score, n, src, url, conf in EXCL:
    recs.append(dict(family=fam, benchmark=bench, date=date, model=model, variant="base/unverified",
                     protocol=proto, score_pct=("" if score != score else score), n=n,
                     ci_method="", ci_level="", ci_low_pct="", ci_high_pct="",
                     ci_status="excluded (not comparable)", sampling_unit="",
                     in_panel=False, confidence=conf, source=src, url=url, accessed="2026-06-27"))

cols = ["family", "benchmark", "date", "model", "variant", "protocol", "score_pct", "n",
        "ci_method", "ci_level", "ci_low_pct", "ci_high_pct", "ci_status", "sampling_unit",
        "in_panel", "confidence", "source", "url", "accessed"]
df = pd.DataFrame(recs)[cols]
OUT.parent.mkdir(parents=True, exist_ok=True)
df.to_csv(OUT, index=False)
print(f"[OK] Wrote {OUT}")
ip = df[df["in_panel"]]
print("\nIN-PANEL (official instruct; provisional CIs where applicable):")
print(ip[["family", "date", "model", "score_pct", "ci_low_pct", "ci_high_pct", "ci_status"]].to_string(index=False))
print("\nFamilies x periods (movement):")
for fam in ["QA", "Code", "Reasoning"]:
    s = ip[ip["family"] == fam].sort_values("date")
    print(f"  {fam:9s}: " + " -> ".join(f"{v:g}" for v in s["score_pct"]))
print("\nComparable window:", sorted(ip["date"].unique()))
print("Excluded (2023):", df[~df["in_panel"]]["model"].unique().tolist())
