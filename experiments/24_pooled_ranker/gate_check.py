#!/usr/bin/env python3
"""Did the pooled ranker learn the exp-21/22 gate *in outcome terms*?  MRR of the saved exp-24 runs against the
un-reranked convex 0.5 and convex 0.5 → bge @20 on the same questions, split by query length (≤ 25 / > 25 words)
and by verbatim-ness (q_verbatim ≤ 0.2 / > 0.2): honest slices = human val half, human oof, mined val ∩ scored.
  cd experiments/14_ltr_fusion && uv run python ../24_pooled_ranker/gate_check.py --corpus B
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

EXP_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(EXP_DIR.parent / "21_mined_eval"))
from common21 import all_questions, is_human, load_saved  # noqa: E402
from rag_eval.stats import load_run  # noqa: E402

EXP = "24_pooled_ranker"


def rr(run, qids):
    pq = run["per_question"]
    return np.array([pq[q]["rr"] for q in qids])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", required=True)
    ap.add_argument("--models", default="lgbm-tiny__notype__pooled,lgbm-tiny__withtype__pooled,lgbm-tiny__notype__pooled-scored,lgbm-tiny__notype__mined,logreg__notype__pooled")
    a = ap.parse_args()
    qs = all_questions(a.corpus)
    ex = np.load(EXP_DIR / "cache" / f"{a.corpus}_extra.npz")
    q_len = dict(zip([q.qid for q in qs], ex["q_len"])); q_verb = dict(zip([q.qid for q in qs], ex["q_verbatim"]))
    full = dict(zip([q.qid for q in qs], ex["bge_full"]))
    refs = {"convex05 (h)": load_saved("human__convex05", a.corpus), "convex05+bge@20 (h)": load_saved("human__convex05+bge@20", a.corpus),
            "convex05 (m)": load_saved("mined__convex05", a.corpus), "convex05+bge@20 (m)": load_saved("sub__convex05+bge@20", a.corpus)}
    L = [f"### Gate check – corpus {a.corpus} (MRR; Δ vs convex 0.5 and vs convex 0.5 → bge @20 on the same questions)", "",
         "| slice | n | convex05 | +bge@20 | " + " | ".join(a.models.split(",")) + " |", "|---|--:|--:|--:|" + "--:|" * len(a.models.split(","))]
    out = {}
    for sl_name, base_h, base_b, pick in (
            ("human val, ≤25 words", "convex05 (h)", "convex05+bge@20 (h)", lambda q: is_human(q) and q.split == "val" and q_len[q.qid] <= 25),
            ("human val, >25 words", "convex05 (h)", "convex05+bge@20 (h)", lambda q: is_human(q) and q.split == "val" and q_len[q.qid] > 25),
            ("human oof (all), ≤25 words", "convex05 (h)", "convex05+bge@20 (h)", lambda q: is_human(q) and q_len[q.qid] <= 25),
            ("human oof (all), >25 words", "convex05 (h)", "convex05+bge@20 (h)", lambda q: is_human(q) and q_len[q.qid] > 25),
            ("mined val ∩ scored, ≤25 words", "convex05 (m)", "convex05+bge@20 (m)", lambda q: not is_human(q) and q.split == "val" and full[q.qid] and q_len[q.qid] <= 25),
            ("mined val ∩ scored, 26–50 words", "convex05 (m)", "convex05+bge@20 (m)", lambda q: not is_human(q) and q.split == "val" and full[q.qid] and 25 < q_len[q.qid] <= 50),
            ("mined val ∩ scored, >50 words", "convex05 (m)", "convex05+bge@20 (m)", lambda q: not is_human(q) and q.split == "val" and full[q.qid] and q_len[q.qid] > 50),
            ("mined val ∩ scored, verbatim ≤0.2", "convex05 (m)", "convex05+bge@20 (m)", lambda q: not is_human(q) and q.split == "val" and full[q.qid] and q_verb[q.qid] <= 0.2),
            ("mined val ∩ scored, verbatim >0.2", "convex05 (m)", "convex05+bge@20 (m)", lambda q: not is_human(q) and q.split == "val" and full[q.qid] and q_verb[q.qid] > 0.2),
            ("mined val all, ≤25 words", "convex05 (m)", None, lambda q: not is_human(q) and q.split == "val" and q_len[q.qid] <= 25),
            ("mined val all, >25 words", "convex05 (m)", None, lambda q: not is_human(q) and q.split == "val" and q_len[q.qid] > 25)):
        qids = [q.qid for q in qs if pick(q)]
        qids = [q for q in qids if q in refs[base_h]["per_question"] and (base_b is None or q in refs[base_b]["per_question"])]
        if not qids:
            continue
        cells = []
        row = {"n": len(qids), "convex05": float(rr(refs[base_h], qids).mean()), "bge20": float(rr(refs[base_b], qids).mean()) if base_b else None}
        for m in a.models.split(","):
            which = "human" if sl_name.startswith("human") else "mined"
            fit = "oof-human" if "oof" in sl_name else "fitA"
            try:
                run = load_run(EXP, f"{which}__ltr24__{m}__{fit}", a.corpus)
            except FileNotFoundError:
                cells.append("–"); continue
            ok = [q for q in qids if q in run["per_question"]]
            v = float(rr(run, ok).mean()); row[m] = v
            d1 = v - float(rr(refs[base_h], ok).mean())
            d2 = (v - float(rr(refs[base_b], ok).mean())) if base_b else None
            cells.append(f"{v:.3f} ({d1:+.3f}" + (f" / {d2:+.3f})" if d2 is not None else ")"))
        L.append(f"| {sl_name} | {len(qids)} | {row['convex05']:.3f} | " + (f"{row['bge20']:.3f}" if row["bge20"] is not None else "–") + " | " + " | ".join(cells) + " |")
        out[sl_name] = row
    (EXP_DIR / "runs" / f"gate_check_{a.corpus}.md").write_text("\n".join(L) + "\n")
    (EXP_DIR / "runs" / f"gate_check_{a.corpus}.json").write_text(json.dumps(out, indent=1))
    print("\n".join(L))


if __name__ == "__main__":
    main()
