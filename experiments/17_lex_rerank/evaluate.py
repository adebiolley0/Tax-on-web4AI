#!/usr/bin/env python3
"""Stage 3 – evaluate exp-13 lexical + bge-reranker-v2-m3 at depths 20/30/50, with and without
interpolation of the reranker score with the BM25F score (β ∈ {0.5, 0.7, 1.0}, chosen on train),
save every run through rag_eval and run the paired significance tests on val against the bar.

  ../14_ltr_fusion/.venv/bin/python evaluate.py --corpus C
"""
from __future__ import annotations

import argparse
import json
from itertools import product

import numpy as np
from scipy import stats

from rag_eval import evaluate_rankings, save_result, load_questions_b, load_questions_c

from common17 import (BARS, BETAS, CACHE, DEPTHS, EXP, RUNS, LexStage1, load_rerank_cache, minmax,
                      per_question_ranks, rerank_cache_path, split_metrics_from_ranks)


def paired_tests(rr_new: np.ndarray, rr_ref: np.ndarray, seed: int = 0, n_boot: int = 20000) -> dict:
    d = rr_new - rr_ref
    n = len(d)
    wins, losses = int((d > 1e-12).sum()), int((d < -1e-12).sum())
    out = {"n": n, "mean_diff": float(d.mean()), "wins": wins, "losses": losses, "ties": n - wins - losses}
    if n > 1 and d.std() > 0:
        t = stats.ttest_rel(rr_new, rr_ref)
        out["t"] = float(t.statistic); out["p_t"] = float(t.pvalue)
        try:
            w = stats.wilcoxon(rr_new, rr_ref, zero_method="wilcox")
            out["p_wilcoxon"] = float(w.pvalue)
        except ValueError:
            out["p_wilcoxon"] = None
    else:
        out["t"] = None; out["p_t"] = None; out["p_wilcoxon"] = None
    out["p_sign"] = float(stats.binomtest(wins, wins + losses, 0.5).pvalue) if wins + losses else None
    rng = np.random.default_rng(seed)
    boots = np.array([d[rng.integers(0, n, n)].mean() for _ in range(n_boot)])
    out["ci95"] = [float(np.quantile(boots, 0.025)), float(np.quantile(boots, 0.975))]
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", required=True, choices=["B", "C"])
    ap.add_argument("--no-save", action="store_true")
    ap.add_argument("--tag", default="", help="reranker cache suffix (e.g. _len1024); appended to run names")
    a = ap.parse_args()
    st = LexStage1.load(a.corpus)
    questions = load_questions_c() if a.corpus == "C" else load_questions_b()
    assert [q.qid for q in questions] == st.qids
    nq = len(questions)
    rr_cache = load_rerank_cache(rerank_cache_path(a.corpus, a.tag))
    timing = json.loads((CACHE / f"{a.corpus}_rerank_timing{a.tag}.json").read_text())
    runs = timing.get("runs", [])
    s_per_pair = (sum(r["seconds"] for r in runs) / max(1, sum(r["pairs"] for r in runs))) if runs else float("nan")
    query_ms = st.timing["query_ms"]
    print(f"corpus {a.corpus}: {nq} questions, {len(rr_cache)} reranked pairs, {s_per_pair:.2f} s/pair, lexical {query_ms:.1f} ms/query", flush=True)

    results = {}
    for depth, beta in product(DEPTHS, BETAS):
        rankings = {}
        for qi, q in enumerate(questions):
            units, lex = st.candidates(qi, depth)
            rr = np.array([rr_cache[(qi, int(u))] for u in units], dtype=np.float64)
            fused = beta * minmax(rr) + (1 - beta) * minmax(lex.astype(np.float64)) if beta < 1 else rr
            order = np.argsort(-fused, kind="stable")
            seen, ranked = set(), []
            for j in order:
                d = st.doc_ids[int(st.unit_doc[units[j]])]
                if d not in seen:
                    seen.add(d); ranked.append(d)
            for d in st.doc_ranking(qi, 50):                     # tail: the lexical ranking beyond the reranked depth
                if d not in seen:
                    seen.add(d); ranked.append(d)
            rankings[q.qid] = ranked[:50]
        name = f"lex13+bge@{depth}" + (f"_beta{beta}" if beta < 1 else "") + a.tag
        res = evaluate_rankings(name, a.corpus, questions, rankings,
                                {"first_stage": "exp-13 lexical (BM25F title boost, tok01+num, per-corpus k1/b)", "reranker": "BAAI/bge-reranker-v2-m3",
                                 "max_length": int(timing["runs"][0]["max_length"]) if runs else None, "depth": depth, "beta": beta,
                                 "fusion": "beta*minmax(reranker) + (1-beta)*minmax(bm25f) over the candidates" if beta < 1 else "reranker only"},
                                {"per_query_s": round(query_ms / 1000 + depth * s_per_pair, 2), "s_per_pair": round(s_per_pair, 3),
                                 "lexical_query_ms": query_ms, "threads": 4})
        results[(depth, beta)] = res
        print(f"  {res.summary()}", flush=True)
        if not a.no_save:
            save_result(EXP, res)

    # ── selection on train ───────────────────────────────────────────────────
    sel_beta = {}
    for depth in DEPTHS:
        best = max(BETAS, key=lambda b: (results[(depth, b)].metrics["train_mrr"], b))      # ties → plain reranker
        sel_beta[depth] = best
    sel_all = max(results, key=lambda k: (results[k].metrics["train_mrr"], -k[0], k[1]))
    print(f"  β chosen on train per depth: {sel_beta}; (depth, β) chosen on train: {sel_all}", flush=True)

    # ── reference rows (stored per-question ranks) ───────────────────────────
    refs = {}
    for key in ("first_stage", "lex13", "bar", "bge_bar"):
        if key in BARS[a.corpus]:
            ranks = per_question_ranks(BARS[a.corpus][key])
            refs[key] = {"label": BARS[a.corpus].get(f"{key}_label", key), "ranks": ranks, "metrics": split_metrics_from_ranks(ranks, questions)}
    ours = {f"lex13+bge@{d}" + (f"_beta{b}" if b < 1 else "") + a.tag: {"ranks": {q: v["rank"] for q, v in results[(d, b)].per_question.items()}}
            for d, b in results}
    for k, v in ours.items():
        v["metrics"] = split_metrics_from_ranks(v["ranks"], questions)

    # ── paired tests on val vs the bar ───────────────────────────────────────
    val_q = [q.qid for q in questions if q.split == "val"]
    def rr_vec(ranks):
        return np.array([1.0 / ranks[q] if ranks.get(q) else 0.0 for q in val_q])
    tests = {}
    for ref_key in ("bar", "bge_bar", "lex13"):
        if ref_key not in refs:
            continue
        ref_rr = rr_vec(refs[ref_key]["ranks"])
        for name, v in ours.items():
            tests[f"{name} vs {ref_key}"] = paired_tests(rr_vec(v["ranks"]), ref_rr)
    # lexical-only vs old first stage and bar
    tests["lex13 vs first_stage"] = paired_tests(rr_vec(refs["lex13"]["ranks"]), rr_vec(refs["first_stage"]["ranks"]))
    tests["lex13 vs bar"] = paired_tests(rr_vec(refs["lex13"]["ranks"]), rr_vec(refs["bar"]["ranks"]))

    # ── per-question val table for the main pipeline ─────────────────────────
    main_name = "lex13+bge@30"
    rows = []
    for q in questions:
        if q.split != "val":
            continue
        rows.append({"qid": q.qid, "question": q.question[:80], "first_stage": refs["first_stage"]["ranks"].get(q.qid),
                     "lex13": refs["lex13"]["ranks"].get(q.qid), "bar": refs["bar"]["ranks"].get(q.qid),
                     **{n: ours[n + a.tag]["ranks"].get(q.qid) for n in ("lex13+bge@20", "lex13+bge@30", "lex13+bge@50")}})

    summary = {"corpus": a.corpus, "s_per_pair": s_per_pair, "query_ms": query_ms, "timing": timing,
               "refs": {k: {"label": v["label"], "metrics": v["metrics"]} for k, v in refs.items()},
               "ours": {k: v["metrics"] for k, v in ours.items()},
               "selected_beta_per_depth": sel_beta, "selected_depth_beta": list(sel_all),
               "tests_val": tests, "val_rows": rows}
    RUNS.mkdir(exist_ok=True)
    (RUNS / f"{a.corpus}_eval{a.tag}.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1, default=str))

    # ── markdown tables ──────────────────────────────────────────────────────
    def row(label, m, cost=""):
        return (f"| {label} | {m['train']['mrr']:.3f} | **{m['val']['mrr']:.3f}** | {m['all']['mrr']:.3f} | "
                f"{m['train']['hit@1']:.3f} | {m['val']['hit@1']:.3f} | {m['all']['hit@1']:.3f} | "
                f"{m['val']['recall@10']:.3f} | {m['all']['recall@10']:.3f} | {cost} |")
    lines = [f"### Corpus {a.corpus}{a.tag} ({nq} questions: {sum(q.split=='train' for q in questions)} train / {len(val_q)} val)", "",
             "| run | MRR train | MRR **val** | MRR all | H@1 train | H@1 val | H@1 all | R@10 val | R@10 all | cost / query |",
             "|---|---:|---:|---:|---:|---:|---:|---:|---:|---|"]
    lines.append(row(refs["first_stage"]["label"], refs["first_stage"]["metrics"], "ms"))
    lines.append(row("exp 13 lexical (this first stage)", refs["lex13"]["metrics"], f"{query_ms:.0f} ms"))
    lines.append(row(f"**bar** – {refs['bar']['label']}", refs["bar"]["metrics"], "≈20 s (exp 09, 1024 tok)" if a.corpus == "C" else "2 s"))
    if "bge_bar" in refs:
        lines.append(row("exp 03: e5-small + BM25 RRF + bge-reranker-v2-m3 @30", refs["bge_bar"]["metrics"], "≈20 s"))
    for d in DEPTHS:
        for b in BETAS:
            n = f"lex13+bge@{d}" + (f"_beta{b}" if b < 1 else "") + a.tag
            tag = " ← β chosen on train" if (b == sel_beta[d] and b < 1) else ""
            star = " **(train-selected depth, β)**" if (d, b) == sel_all else ""
            lines.append(row(f"exp 13 lexical + bge-reranker-v2-m3 @{d}" + (f", β = {b}" if b < 1 else "") + tag + star,
                             ours[n]["metrics"], f"{query_ms/1000 + d*s_per_pair:.1f} s"))
    lines += ["", f"Paired tests on val (n = {len(val_q)}), reciprocal-rank differences vs the bar:", "",
              "| run | mean Δrr | wins / losses / ties | paired t p | sign test p | Wilcoxon p | bootstrap 95 % CI |", "|---|---:|---|---:|---:|---:|---|"]
    for k, t in tests.items():
        if not k.endswith("vs bar"):
            continue
        lines.append(f"| {k[:-7]} | {t['mean_diff']:+.3f} | {t['wins']} / {t['losses']} / {t['ties']} | "
                     f"{t['p_t']:.3f} | {t['p_sign']:.3f} | {t['p_wilcoxon']:.3f} | [{t['ci95'][0]:+.3f}, {t['ci95'][1]:+.3f}] |"
                     if t["p_t"] is not None else f"| {k[:-7]} | {t['mean_diff']:+.3f} | {t['wins']} / {t['losses']} / {t['ties']} | – | – | – | – |")
    if "bge_bar" in refs:
        lines += ["", "Same tests vs the exp-03 bge-reranker run (RRF + bge @30):", "",
                  "| run | mean Δrr | wins / losses / ties | paired t p | sign test p | Wilcoxon p |", "|---|---:|---|---:|---:|---:|"]
        for k, t in tests.items():
            if k.endswith("vs bge_bar") and "beta" not in k:
                lines.append(f"| {k[:-11]} | {t['mean_diff']:+.3f} | {t['wins']} / {t['losses']} / {t['ties']} | {t['p_t']:.3f} | {t['p_sign']:.3f} | {t['p_wilcoxon']:.3f} |")
    lines += ["", "Per-question ranks on val (old first stage / exp-13 lexical / bar / lex13+bge @20 / @30 / @50):", "",
              "| qid | question | old 1st | lex13 | bar | @20 | @30 | @50 |", "|---|---|---:|---:|---:|---:|---:|---:|"]
    for r in rows:
        f = lambda x: "–" if x is None else str(x)
        lines.append(f"| {r['qid']} | {r['question']} | {f(r['first_stage'])} | {f(r['lex13'])} | {f(r['bar'])} | "
                     f"{f(r['lex13+bge@20'])} | {f(r['lex13+bge@30'])} | {f(r['lex13+bge@50'])} |")
    (RUNS / f"{a.corpus}_tables{a.tag}.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines[:4 + 4 + len(DEPTHS) * len(BETAS)]), flush=True)
    print("\ntests vs bar (val):")
    for k, t in tests.items():
        if k.endswith("vs bar"):
            print(f"  {k:32s} Δ={t['mean_diff']:+.3f} W/L/T={t['wins']}/{t['losses']}/{t['ties']} p_t={t['p_t']} p_sign={t['p_sign']} p_wilcoxon={t['p_wilcoxon']} CI={t['ci95']}")


if __name__ == "__main__":
    main()
