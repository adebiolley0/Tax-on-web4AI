#!/usr/bin/env python3
"""Stage E – reranked rankings (reranker score only over the top-20 canonical candidates, first
stage appended as the tail), metrics train / val / all, paired tests on val against the round-2
best (exp 17 lexical → bge @20) and between consecutive stack steps, per-question table, cost.

  cd experiments/17_lex_rerank && ../14_ltr_fusion/.venv/bin/python ../19_canonical_hybrid/evaluate.py
"""
from __future__ import annotations

import json

import numpy as np

from rag_eval import load_questions_c, evaluate_rankings, save_result

from common19 import (CACHE, EXP, RUNS, REFS, FUSION_W, FACET_BOOST, RERANK_DEPTH, RERANK_MAX_LEN, per_question_ranks,
                      split_metrics_from_ranks, paired_tests)
from retrieve import VARIANTS, RERANKED, edition_aware


def main():
    questions = load_questions_c()
    qidx = {q.qid: i for i, q in enumerate(questions)}
    meta = json.loads((CACHE / "meta.json").read_text())
    metas = json.loads((CACHE / "docs_meta.json").read_text())
    doc_ids = meta["doc_ids"]
    cands = json.loads((CACHE / "candidates.json").read_text())
    pre = json.loads((CACHE / "pre_rankings.json").read_text())
    scores = json.loads((CACHE / "rerank_scores.json").read_text())
    timing = json.loads((CACHE / "rerank_timing.json").read_text())
    runs = timing.get("runs", [])
    s_pair = sum(r["seconds"] for r in runs) / max(1, sum(r["pairs"] for r in runs)) if runs else float("nan")
    emb_t = json.loads((CACHE / "embed_timing.json").read_text()) if (CACHE / "embed_timing.json").exists() else {}

    ranks: dict[str, dict[str, int | None]] = {}
    results = {}
    for name in RERANKED:
        rankings = {}
        missing = 0
        for q in questions:
            lst = cands[name][q.qid]
            sc = []
            for c in lst:
                k = f"{qidx[q.qid]}|{c['sha']}"
                if k not in scores:
                    missing += 1
                sc.append(scores.get(k, -1e9))
            order = np.argsort(-np.asarray(sc), kind="stable")
            ranked = [lst[j]["doc"] for j in order]
            seen = set(ranked)
            for d in pre[name][q.qid]:
                if d not in seen:
                    seen.add(d); ranked.append(d)
            rankings[q.qid] = ranked[:50]
        text, quality, canon, facets = VARIANTS[name]
        cfg = {"stage": f"z-score convex fusion (w_dense={FUSION_W}) → facets/canon → bge-reranker-v2-m3 @{RERANK_DEPTH}",
               "text": text, "quality_filter": quality, "canonicalisation": canon, "facet_routing": facets,
               "facet_boost": FACET_BOOST if facets else None, "reranker": "BAAI/bge-reranker-v2-m3", "max_length": RERANK_MAX_LEN,
               "depth": RERANK_DEPTH, "candidates": "one chunk (best fused) per document / work"}
        tm = {"per_query_s": round(0.06 + RERANK_DEPTH * s_pair, 2), "s_per_pair": round(s_pair, 3), "first_stage_ms": 60}
        res = evaluate_rankings(f"rerank__{name}", "C", questions, rankings, cfg, tm)
        save_result(EXP, res)
        results[name] = res
        ranks[name] = {qid: v["rank"] for qid, v in res.per_question.items()}
        line = (f"  {name:24s} train {res.metrics['train_mrr']:.3f} | val {res.metrics['val_mrr']:.3f} H@1 {res.metrics['val_hit@1']:.3f} "
                f"R@10 {res.metrics['val_recall@10']:.3f} | all {res.metrics['mrr']:.3f} H@1 {res.metrics['hit@1']:.3f}")
        if canon:
            qs2, rk2 = edition_aware(questions, rankings, doc_ids, metas)
            res2 = evaluate_rankings(f"rerank__{name}__editionaware", "C", qs2, rk2, {**cfg, "eval": "edition-aware"}, tm)
            save_result(EXP, res2)
            results[name + "__editionaware"] = res2
            ranks[name + "__editionaware"] = {qid: v["rank"] for qid, v in res2.per_question.items()}
            line += f" || edition-aware val {res2.metrics['val_mrr']:.3f} all {res2.metrics['mrr']:.3f}"
        if missing:
            line += f"  (!! {missing} pairs without reranker score)"
        print(line, flush=True)

    # pre-reranker ranks from the saved results
    for name in VARIANTS:
        for suffix in ("", "__editionaware"):
            p = CACHE.parent.parent / "results" / EXP / f"C__pre__{name.replace('+', '_')}{suffix}.json"
            if p.exists():
                ranks["pre__" + name + suffix] = per_question_ranks(p)
    refs = {}
    for k, (p, label) in REFS.items():
        refs[k] = {"label": label, "ranks": per_question_ranks(p)}
        ranks[k] = refs[k]["ranks"]
    metrics = {k: split_metrics_from_ranks(v, questions) for k, v in ranks.items()}

    val_q = [q.qid for q in questions if q.split == "val"]
    all_q = [q.qid for q in questions]
    rr = lambda r, qs: np.array([1.0 / r[q] if r.get(q) else 0.0 for q in qs])
    tests = {}
    for name in RERANKED:
        tests[f"{name} vs round2_best"] = paired_tests(rr(ranks[name], val_q), rr(ranks["round2_best"], val_q))
        tests[f"{name} vs round2_best [all]"] = paired_tests(rr(ranks[name], all_q), rr(ranks["round2_best"], all_q))
    for a, b in zip(RERANKED[1:], RERANKED[:-1]):
        tests[f"{a} vs {b}"] = paired_tests(rr(ranks[a], val_q), rr(ranks[b], val_q))
    tests["full vs baseline"] = paired_tests(rr(ranks["full"], val_q), rr(ranks["baseline"], val_q))
    tests["pre__baseline vs lex13"] = paired_tests(rr(ranks["pre__baseline"], val_q), rr(ranks["lex13"], val_q))
    tests["pre__full vs pre__baseline"] = paired_tests(rr(ranks["pre__full"], val_q), rr(ranks["pre__baseline"], val_q))

    rows = []
    for q in questions:
        rows.append({"qid": q.qid, "split": q.split, "question": q.question[:70], "round2_best": ranks["round2_best"].get(q.qid),
                     **{n: ranks[n].get(q.qid) for n in RERANKED}, "pre_full": ranks["pre__full"].get(q.qid),
                     "pre_baseline": ranks["pre__baseline"].get(q.qid)})
    summary = {"s_per_pair": s_pair, "rerank_timing": timing, "embed_timing": emb_t, "metrics": metrics, "tests": tests, "rows": rows,
               "n_scores": len(scores)}
    RUNS.mkdir(exist_ok=True)
    (RUNS / "eval.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1, default=str))

    # ── markdown tables ──────────────────────────────────────────────────────
    def row(label, m, cost=""):
        return (f"| {label} | {m['train']['mrr']:.3f} | **{m['val']['mrr']:.3f}** | {m['all']['mrr']:.3f} | "
                f"{m['train']['hit@1']:.3f} | {m['val']['hit@1']:.3f} | {m['all']['hit@1']:.3f} | {m['val']['recall@10']:.3f} | {m['all']['recall@10']:.3f} | {cost} |")
    hdr = ["| run | MRR train | MRR **val** | MRR all | H@1 train | H@1 val | H@1 all | R@10 val | R@10 all | cost / query |",
           "|---|---:|---:|---:|---:|---:|---:|---:|---:|---|"]
    L = ["### References", ""] + hdr
    for k in ("lex13", "round1_bar", "round2_best"):
        L.append(row(refs[k]["label"], metrics[k], "27 ms" if k == "lex13" else ("≈21 s" if k == "round1_bar" else "≈19 s")))
    L += ["", "### Pre-reranker (fusion only)", ""] + hdr
    for name in ["lex_raw", "dense_raw"] + list(VARIANTS):
        k = "pre__" + name
        if k in metrics:
            L.append(row(f"pre {name}", metrics[k], "≈60 ms"))
        if k + "__editionaware" in metrics:
            L.append(row(f"pre {name} (edition-aware)", metrics[k + "__editionaware"], "≈60 ms"))
    L += ["", f"### Reranked (bge-reranker-v2-m3 @{RERANK_DEPTH}, max_length {RERANK_MAX_LEN}, reranker score only)", ""] + hdr
    for name in RERANKED:
        L.append(row(name, metrics[name], f"{0.06 + RERANK_DEPTH * s_pair:.1f} s"))
        if name + "__editionaware" in metrics:
            L.append(row(f"{name} (edition-aware)", metrics[name + "__editionaware"], ""))
    L += ["", f"### Paired tests on val (n = {len(val_q)}), reciprocal-rank differences", "",
          "| comparison | mean Δrr | wins / losses / ties | paired t p | sign test p | Wilcoxon p | bootstrap 95 % CI |", "|---|---:|---|---:|---:|---:|---|"]
    for k, t in tests.items():
        p = lambda v: "–" if v is None else f"{v:.3f}"
        L.append(f"| {k} | {t['mean_diff']:+.3f} | {t['wins']} / {t['losses']} / {t['ties']} | {p(t.get('p_t'))} | {p(t.get('p_sign'))} | {p(t.get('p_wilcoxon'))} | [{t['ci95'][0]:+.3f}, {t['ci95'][1]:+.3f}] |")
    L += ["", "### Per-question ranks (val), round-2 best vs the stack", "",
          "| qid | question | round-2 best | baseline | +quality | +zoning | +canon | full | pre full |", "|---|---|---:|---:|---:|---:|---:|---:|---:|"]
    f = lambda x: "–" if x is None else str(x)
    for r in rows:
        if r["split"] == "val":
            L.append(f"| {r['qid']} | {r['question']} | {f(r['round2_best'])} | {f(r['baseline'])} | {f(r['+quality'])} | {f(r['+quality+zoning'])} | "
                     f"{f(r['+quality+zoning+canon'])} | {f(r['full'])} | {f(r['pre_full'])} |")
    L += ["", "### Per-question ranks (train)", "", "| qid | question | round-2 best | baseline | +quality | +zoning | +canon | full | pre full |", "|---|---|---:|---:|---:|---:|---:|---:|---:|"]
    for r in rows:
        if r["split"] == "train":
            L.append(f"| {r['qid']} | {r['question']} | {f(r['round2_best'])} | {f(r['baseline'])} | {f(r['+quality'])} | {f(r['+quality+zoning'])} | "
                     f"{f(r['+quality+zoning+canon'])} | {f(r['full'])} | {f(r['pre_full'])} |")
    (RUNS / "tables.md").write_text("\n".join(L) + "\n")
    print("\n".join(L[: 8 + 2 + 14 + 4 + 2 * len(RERANKED) + 2]))
    print("\ntests (val):")
    for k, t in tests.items():
        print(f"  {k:40s} Δ={t['mean_diff']:+.3f} W/L/T={t['wins']}/{t['losses']}/{t['ties']} p_t={t.get('p_t')} p_sign={t.get('p_sign')} CI={t['ci95']}")


if __name__ == "__main__":
    main()
