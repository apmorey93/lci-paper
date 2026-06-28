"""Step 2: assemble the comparable benchmark panel and its (provisional) input
confidence intervals. Computes ONLY accuracy CIs (panel inputs); it does NOT
compute any LCI, index, or wedge number.

PRIMARY family set K = {QA (MMLU), Code (HumanEval)} — the only two metrics with
ONE fixed official protocol (incl. scoring rule) across L3 / L3.1 / L3.3.
MATH is demoted to a LINKED-PROTOCOL SENSITIVITY (its scoring rule changes at
L3.3: final_em -> sympy_intersection_score, so it is not one fixed protocol).
GSM8K is EXCLUDED (absent from the official L3.3 table). 2023 Llama-2 is EXCLUDED.

Values are from Meta's OFFICIAL model-card "Instruction tuned models" tables:
  L3 & L3.1: Llama-3.1-70B-Instruct card ; L3.3: Llama-3.3-70B-Instruct card.

CI policy (contract §8 + Amendment A1):
  - HumanEval pass@1 over n=164: provisional Wilson 95% (rounded value; binomial
    approximation; sampling unit = benchmark item).
  - MMLU: "not estimable from published data" — macro-average over 57 subjects;
    per-subject counts unpublished. (Recorded, never zero, never blank-without-status.)
  - MATH (sensitivity): "not estimable from published data" — evaluated denominator
    and scorer not pinned. No Wilson.
  Index uncertainty built on these inputs is therefore PARTIAL.
"""

from __future__ import annotations

import math
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "evals" / "accuracy_panel.csv"
L31 = "https://huggingface.co/meta-llama/Llama-3.1-70B-Instruct"
L33 = "https://huggingface.co/meta-llama/Llama-3.3-70B-Instruct"
L31_REV = "github.com/meta-llama/llama-models/models/llama3_1/MODEL_CARD.md (accessed 2026-06-27)"
L33_REV = "github.com/meta-llama/llama-models/models/llama3_3/MODEL_CARD.md (accessed 2026-06-27)"
TABLE = "Instruction tuned models"


def wilson(p_hat: float, n: int, z: float = 1.96):
    denom = 1 + z * z / n
    center = (p_hat + z * z / (2 * n)) / denom
    half = z * math.sqrt(p_hat * (1 - p_hat) / n + z * z / (4 * n * n)) / denom
    return max(0.0, center - half), min(1.0, center + half)


# (family, benchmark, protocol, date, model, score, n, ci_mode, note, src_rev, url, conf)
PRIMARY = [
    # QA / MMLU (0-shot CoT, macro_avg/acc) — CI not estimable (macro-average)
    ("QA", "MMLU", "0-shot CoT, macro_avg/acc", "2024-04-01", "Llama-3-70B-Instruct",   80.9, 14042, "none", "", L31_REV, L31, 0.97),
    ("QA", "MMLU", "0-shot CoT, macro_avg/acc", "2024-07-01", "Llama-3.1-70B-Instruct", 86.0, 14042, "none", "", L31_REV, L31, 0.97),
    ("QA", "MMLU", "0-shot CoT, macro_avg/acc", "2024-12-01", "Llama-3.3-70B-Instruct", 86.0, 14042, "none", "", L33_REV, L33, 0.97),
    ("QA", "MMLU", "0-shot CoT, macro_avg/acc", "2025-06-01", "Llama-3.3-70B-Instruct", 86.0, 14042, "none", "matched-model cost continuation", L33_REV, L33, 0.90),
    # Code / HumanEval (0-shot pass@1) — provisional Wilson over n=164
    ("Code", "HumanEval", "0-shot pass@1", "2024-04-01", "Llama-3-70B-Instruct",   81.7, 164, "wilson", "", L31_REV, L31, 0.97),
    ("Code", "HumanEval", "0-shot pass@1", "2024-07-01", "Llama-3.1-70B-Instruct", 80.5, 164, "wilson", "", L31_REV, L31, 0.97),
    ("Code", "HumanEval", "0-shot pass@1", "2024-12-01", "Llama-3.3-70B-Instruct", 88.4, 164, "wilson", "", L33_REV, L33, 0.95),
    ("Code", "HumanEval", "0-shot pass@1", "2025-06-01", "Llama-3.3-70B-Instruct", 88.4, 164, "wilson", "matched-model cost continuation", L33_REV, L33, 0.90),
]
# MATH: sensitivity only (scoring rule changes across vintages -> not one fixed protocol)
SENSITIVITY = [
    ("Reasoning", "MATH", "0-shot CoT, final_em",                 "2024-04-01", "Llama-3-70B-Instruct",   51.0, None, "none", "", L31_REV, L31, 0.92),
    ("Reasoning", "MATH", "0-shot CoT, final_em",                 "2024-07-01", "Llama-3.1-70B-Instruct", 68.0, None, "none", "", L31_REV, L31, 0.92),
    ("Reasoning", "MATH", "0-shot CoT, sympy_intersection_score", "2024-12-01", "Llama-3.3-70B-Instruct", 77.0, None, "none", "scoring rule differs from L3/L3.1", L33_REV, L33, 0.90),
    ("Reasoning", "MATH", "0-shot CoT, sympy_intersection_score", "2025-06-01", "Llama-3.3-70B-Instruct", 77.0, None, "none", "matched-model cost continuation; scorer differs", L33_REV, L33, 0.85),
]
EXCLUDED = [  # 2023 Llama-2: base/different-harness only -> not comparable
    ("QA", "MMLU", "5-shot; THIRD-PARTY harness; chat unverified", "2023-07-01", "Llama-2-70B-Chat", 63.2, 14042,
     "EleutherAI lm-eval-harness reproduction (Meta base-only 68.9)",
     "https://github.com/EleutherAI/lm-evaluation-harness/issues/1213", 0.45),
    ("Code", "HumanEval", "0-shot pass@1 claimed; launch-blog; Meta base-only 29.9", "2023-07-01", "Llama-2-70B-Chat", 25.6, 164,
     "Meta Llama 3 launch blog table", "https://ai.meta.com/blog/meta-llama-3/", 0.40),
]


def _ci(score, n, mode):
    if mode == "wilson":
        lo, hi = wilson(score / 100.0, n)
        return ("Wilson (provisional)", 0.95, round(lo * 100, 2), round(hi * 100, 2),
                "provisional (rounded value; binomial approximation)",
                "benchmark item (treated as i.i.d. binary; approximation)")
    # not estimable
    return ("not estimable", "n/a", "", "",
            "not estimable from published data", "n/a")


recs = []
for fam, bench, proto, date, model, score, n, mode, note, rev, url, conf in PRIMARY:
    m, lvl, lo, hi, status, su = _ci(score, n, mode)
    if mode == "none":
        status = "not estimable from published data (macro-avg over 57 subjects; per-subject counts unpublished)"
    recs.append(dict(family=fam, benchmark=bench, date=date, model=model, variant="instruct",
                     protocol=proto, score_pct=score, n=n, ci_method=m, ci_level=lvl,
                     ci_low_pct=lo, ci_high_pct=hi, ci_status=status, sampling_unit=su,
                     panel_role="primary", note=note, confidence=conf,
                     source="Meta official model card", source_table=TABLE,
                     source_revision=rev, url=url, accessed="2026-06-27"))
for fam, bench, proto, date, model, score, n, mode, note, rev, url, conf in SENSITIVITY:
    recs.append(dict(family=fam, benchmark=bench, date=date, model=model, variant="instruct",
                     protocol=proto, score_pct=score, n="", ci_method="not estimable", ci_level="n/a",
                     ci_low_pct="", ci_high_pct="",
                     ci_status="not estimable from published data (denominator/scorer not pinned)",
                     sampling_unit="n/a", panel_role="sensitivity", note=note, confidence=conf,
                     source="Meta official model card", source_table=TABLE,
                     source_revision=rev, url=url, accessed="2026-06-27"))
for fam, bench, proto, date, model, score, n, src, url, conf in EXCLUDED:
    recs.append(dict(family=fam, benchmark=bench, date=date, model=model, variant="base/unverified",
                     protocol=proto, score_pct=score, n=n, ci_method="", ci_level="",
                     ci_low_pct="", ci_high_pct="", ci_status="excluded (not comparable)",
                     sampling_unit="", panel_role="excluded", note="2023 vintage not comparable",
                     confidence=conf, source=src, source_table="", source_revision="",
                     url=url, accessed="2026-06-27"))

df = pd.DataFrame(recs)

# ---- guard assertions: no in-panel/primary row may silently violate the rules ----
prim = df[df["panel_role"] == "primary"]
assert (prim["ci_status"].str.len() > 0).all(), "primary row with empty ci_status"
assert set(prim["family"]) <= {"QA", "Code"}, "primary family set must be {QA, Code}"
assert "MATH" not in set(prim["benchmark"]), "MATH must not be in the primary panel"
for fam, g in prim.groupby("family"):
    assert g["protocol"].nunique() == 1, f"primary family {fam} has non-uniform protocol"
assert df[df["panel_role"] == "sensitivity"]["benchmark"].eq("MATH").all(), "sensitivity is MATH-only here"

cols = ["family", "benchmark", "date", "model", "variant", "protocol", "score_pct", "n",
        "ci_method", "ci_level", "ci_low_pct", "ci_high_pct", "ci_status", "sampling_unit",
        "panel_role", "note", "confidence", "source", "source_table", "source_revision",
        "url", "accessed"]
df = df[cols]
OUT.parent.mkdir(parents=True, exist_ok=True)
df.to_csv(OUT, index=False)
print(f"[OK] Wrote {OUT}  (assertions passed)")
print("\nPRIMARY panel K = {QA, Code}:")
print(prim[["family", "date", "model", "score_pct", "ci_low_pct", "ci_high_pct", "ci_status"]].to_string(index=False))
print("\nSENSITIVITY (MATH; linked-protocol, scorer changes; CI not estimable):")
print(df[df["panel_role"] == "sensitivity"][["date", "score_pct", "protocol"]].to_string(index=False))
print("\nMovement (primary):")
for fam in ["QA", "Code"]:
    s = prim[prim["family"] == fam].sort_values("date")
    print(f"  {fam:5s}: " + " -> ".join(f"{v:g}" for v in s["score_pct"]))
