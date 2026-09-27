"""Round-3 evaluation hygiene (a): paired statistics for the round-2 claims.

Reads experiments/results/*/{A,B,C}__*.json (per-question ranks) and writes
experiments/18_eval_hygiene/README.md plus stats_summary.json.  No model, no GPU:
numpy + scipy through rag_eval.stats.

Run from a venv that has rag_eval + scipy, e.g.
    cd experiments/13_lexical_upgrades && uv run python ../18_eval_hygiene/report.py
"""
from __future__ import annotations

import json
import math
import sys
import time
from collections import defaultdict
from pathlib import Path

import numpy as np

from rag_eval.corpora import question_split
from rag_eval.results import RESULTS_DIR
from rag_eval.stats import (compare_loaded, compare_many, min_detectable_delta, paired_stats, rr_vector,
                            hit_vector, se_of_mean, questions_needed)

HERE = Path(__file__).resolve().parent
OUT_MD = HERE / "README.md"
OUT_JSON = HERE / "stats_summary.json"

ROUND2 = {"11_graph_retrieval", "12_sparse_colbert", "13_lexical_upgrades", "14_ltr_fusion", "15_finetune",
          "16_legal_models", "17_lex_rerank"}
TOP = 10
N_PERM_MAXT = 10_000
SEED = 0

# Round-1 bars (EXPERIMENTS.md §2).  "val" = the validation-split bar; "full" = the best full-set round-1 run.
BARS = {
    "A": {"val": ("01_bm25", "doc|stem+stop+qstop+noaccent"),
          "full": ("04_lancedb", "lancedb__e5-small__hybrid_rrf+bge-reranker-v2-m3@30")},
    "B": {"val": ("03_hybrid_rerank", "e5-small__article_ctx_1200__rrf+mmarco-minilm@30"),
          "full": ("03_hybrid_rerank", "e5-small__article_ctx_1200__rrf+mmarco-minilm@30")},
    "C": {"val": ("09_corpus_c", "bm25__fixed1200_title__bm25+bge-reranker-v2-m3@30"),
          "full": ("09_corpus_c", "e5-small__fixed1200_title__convex0.5+bge-reranker-v2-m3@30")},
}
BAR_LABEL = {"A": "BM25 whole doc (exp 01)", "B": "e5-small RRF + mMARCO@30 (exp 03)",
             "C": "BM25 chunks + bge-reranker@30 (exp 09)"}
FULL_LABEL = {"A": "e5-small RRF + bge-reranker@30 (exp 04, LanceDB)", "B": "e5-small RRF + mMARCO@30 (exp 03)",
              "C": "e5-small convex 0.5 + bge-reranker@30 (exp 09)"}
# The exp-14 "learned ranker" recipe as reported in EXPERIMENTS.md §3.10 (oof numbers)
LTR_RECIPE = {"A": ("14_ltr_fusion", "ltr__logreg__cheap__oof"), "B": ("14_ltr_fusion", "ltr__logreg__minimal+meta__oof"),
              "C": ("14_ltr_fusion", "ltr__lgbm-tiny__all__oof")}
# Named round-2 claims from EXPERIMENTS.md §2 / §3.11 to test explicitly against the val bar
NAMED_CLAIMS = {
    "A": [("13_lexical_upgrades", "bm25f__best_fw__k12.0_b0.75_bfield0.75", "exp-13 k1/b on whole docs, val 0.756"),
          ("12_sparse_colbert", "sparse-opensearch+bm25doc__rrf", "exp-12 OpenSearch sparse + BM25 RRF, val 0.808"),
          ("12_sparse_colbert", "sparse-opensearch+colbert-colbert-fr+bm25doc__rrf", "exp-12 … + colbert-fr, all 0.738"),
          ("14_ltr_fusion", "ltr__logreg__cheap__oof", "exp-14 logreg cheap features, oof 0.732")],
    "B": [("14_ltr_fusion", "tune__e5+bm25chunk__rerank_mmarco-minilm_only__oof", "exp-14 e5 + mMARCO@20 β=0.8, val 0.610 / oof 0.548"),
          ("11_graph_retrieval", "rrf+expand_sel+mmarco-minilm@30", "exp-11 graph-expanded → mMARCO, val 0.592"),
          ("14_ltr_fusion", "ltr__logreg__minimal+meta__oof", "exp-14 logreg 7 features, oof 0.608"),
          ("17_lex_rerank", "lex13+bge@30", "exp-17 lexical → bge@30, val 0.440")],
    "C": [("13_lexical_upgrades", "bm25_concat__title_x3_head_x3", "exp-13 lexical upgrades, val 0.616 (lexical only)"),
          ("17_lex_rerank", "lex13+bge@20", "exp-17 lexical → bge@20, val 0.688"),
          ("17_lex_rerank", "lex13+bge@30", "exp-17 lexical → bge@30, val 0.675 / all 0.733"),
          ("14_ltr_fusion", "ltr__lgbm-tiny__all__oof", "exp-14 LambdaMART 15 trees, oof 0.723")],
}
MDD_NS = (12, 16, 29, 35, 40, 64, 133, 500)
MDD_SDS = (0.20, 0.30, 0.40)


# ── loading ─────────────────────────────────────────────────────────────────
def load_all() -> dict[str, list[dict]]:
    runs: dict[str, list[dict]] = defaultdict(list)
    for f in sorted(RESULTS_DIR.glob("*/*.json")):
        r = json.loads(f.read_text())
        if r.get("corpus") not in ("A", "B", "C") or "per_question" not in r:
            continue
        r["_experiment"] = f.parent.name
        r["_file"] = str(f.relative_to(RESULTS_DIR))
        r["_key"] = f"{f.parent.name}/{r['name']}"
        runs[r["corpus"]].append(r)
    return runs


def find(runs: list[dict], exp: str, name: str) -> dict:
    for r in runs:
        if r["_experiment"] == exp and r["name"] == name:
            return r
    raise KeyError(f"{exp}/{name}")


def split_qids(run: dict, split: str | None) -> list[str]:
    q = sorted(run["per_question"])
    return q if split in (None, "all") else [x for x in q if question_split(x) == split]


def mean_rr(run: dict, split: str | None) -> float:
    return float(rr_vector(run, split_qids(run, split)).mean())


def rank_signature(run: dict, qids: list[str]) -> tuple:
    return tuple(run["per_question"][q]["rank"] for q in qids)


def eligible(runs: list[dict], split: str) -> list[dict]:
    """Round-2 runs whose per-question ranks on ``split`` are out-of-sample."""
    out = []
    for r in runs:
        if r["_experiment"] not in ROUND2:
            continue
        n = r["name"]
        if split == "val" and n.endswith("__fit-val"):
            continue                      # fitted on val: in-sample on val
        if split == "all" and (n.endswith("__fit-val") or n.endswith("__fit-train")):
            continue                      # one half in-sample; oof is the honest full-set run
        out.append(r)
    return out


def dedupe(cands: list[dict], bar: dict, qids: list[str]) -> tuple[list[dict], int, dict[str, list[str]]]:
    """Collapse runs with identical rank vectors on ``qids``; drop clusters identical to the bar.
    Returns (representatives, n_identical_to_bar, aliases)."""
    bar_sig = rank_signature(bar, qids)
    clusters: dict[tuple, list[dict]] = defaultdict(list)
    for c in cands:
        clusters[rank_signature(c, qids)].append(c)
    reps, aliases, same_as_bar = [], {}, 0
    for sig, members in clusters.items():
        if sig == bar_sig:
            same_as_bar += len(members)
            continue
        members.sort(key=lambda r: (0 if r["name"].endswith("__oof") else 1, r["_key"]))
        rep = members[0]
        reps.append(rep)
        aliases[rep["_key"]] = [m["_key"] for m in members[1:]]
    return reps, same_as_bar, aliases


# ── formatting ──────────────────────────────────────────────────────────────
def f3(x: float) -> str:
    return "–" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{x:.3f}"


def fd(x: float) -> str:
    return f"{x:+.3f}"


def pfmt(p: float, exact: bool = True) -> str:
    s = f"{p:.3f}"
    if p < 0.05:
        s = f"**{s}**"
    return s if exact else f"~{s}"


def short(key: str, n: int = 58) -> str:
    return key if len(key) <= n else key[: n - 1] + "…"


def comparison_table(bar: dict, rows: list[dict], split: str, maxt: dict[str, dict], aliases: dict[str, list[str]],
                     metric_label: str) -> list[str]:
    hdr = (f"| # | run | {metric_label} | Δ MRR | 95 % CI | p_t | p_perm | p_maxT | W/L/T | Δ H@1 | p_perm H@1 | Δ H@10 |\n"
           f"|--:|---|--:|--:|:--|--:|--:|--:|:--|--:|--:|--:|")
    lines = [hdr]
    for i, c in enumerate(rows, 1):
        cmp = compare_loaded(bar, c, split, ks=(1, 10), seed=SEED)
        rr, h1, h10 = cmp.rr, cmp.hits[1], cmp.hits[10]
        mt = maxt.get(c["_key"], {})
        ali = f" (+{len(aliases[c['_key']])} identical)" if aliases.get(c["_key"]) else ""
        lines.append(
            f"| {i} | `{short(c['_key'])}`{ali} | {f3(rr.mean_b)} | {fd(rr.delta)} | [{fd(rr.ci_lo)}, {fd(rr.ci_hi)}] "
            f"| {pfmt(rr.p_t)} | {pfmt(rr.p_perm, rr.perm_exact)} | {pfmt(mt.get('p_adj', float('nan')))} "
            f"| {rr.wins}/{rr.losses}/{rr.ties} | {fd(h1.delta)} | {pfmt(h1.p_perm, h1.perm_exact)} | {fd(h10.delta)} |")
        c.setdefault("_cmp", {})[split] = cmp
    return lines


def claim_lines(bar: dict, runs: list[dict], claims: list[tuple[str, str, str]], split: str) -> list[str]:
    lines = ["| claim | run | split | n | bar | run MRR | Δ | 95 % CI | p_t | p_perm | W/L/T | Δ H@1 |",
             "|---|---|---|--:|--:|--:|--:|:--|--:|--:|:--|--:|"]
    for exp, name, label in claims:
        try:
            r = find(runs, exp, name)
        except KeyError:
            lines.append(f"| {label} | `{exp}/{name}` | – | – | – | – | *run file not found* | | | | | |")
            continue
        for sp in (split, "all"):
            cmp = compare_loaded(bar, r, sp, ks=(1,), seed=SEED)
            rr, h1 = cmp.rr, cmp.hits[1]
            lines.append(f"| {label if sp == split else ''} | `{short(r['_key'], 48)}` | {sp} | {rr.n} | {f3(rr.mean_a)} | {f3(rr.mean_b)} "
                         f"| {fd(rr.delta)} | [{fd(rr.ci_lo)}, {fd(rr.ci_hi)}] | {pfmt(rr.p_t)} | {pfmt(rr.p_perm, rr.perm_exact)} "
                         f"| {rr.wins}/{rr.losses}/{rr.ties} | {fd(h1.delta)} |")
    return lines


# ── main ────────────────────────────────────────────────────────────────────
def main() -> None:
    t_start = time.time()
    runs = load_all()
    md: list[str] = []
    summary: dict = {"generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "corpora": {}}

    md.append("# 18 — Evaluation hygiene (a): paired statistics and provenance for the round-2 claims\n")
    md.append("*Generated by `report.py` from `experiments/results/*/{A,B,C}__*.json` (per-question ranks); "
              "no model was run. Statistics: `rag_eval.stats` (numpy + scipy).*\n")
    md.append("## 0. What this is\n")
    md.append(
        "Round 2 (`EXPERIMENTS.md` §2, §3.10–3.11) reported validation-split MRRs against the round-1 bars "
        "(A 0.736 / B 0.570 / C 0.665) and full-set / out-of-fold numbers against the round-1 full-set bests "
        "(A 0.703 / B 0.522 / C 0.703). Those are point estimates on 12 / 16 / 35 validation questions. This report "
        "re-reads every claim as a **paired, per-question comparison** against the bar run: the delta of reciprocal "
        "rank (and hit@k) on each question, with a paired t-test, an exact sign-flip (randomisation) test, a bootstrap "
        "95 % CI (BCa) of the mean delta, win / loss / tie counts and a **max-T correction** over the whole family of "
        "round-2 runs that were scored on that corpus (the leaderboard *is* a multiple comparison).\n")
    md.append("Conventions: Δ = candidate − bar (positive = candidate better). `p_perm` is exact when the number of "
              "non-tied questions is ≤ 20 (`~` marks a Monte-Carlo estimate). `p_maxT` is the single-step "
              "Westfall–Young adjusted p-value over *all* eligible round-2 runs on that corpus/split (family size K in "
              "each section), not just the ten shown. Bold = p < 0.05. Runs with identical rank vectors on the split are "
              "collapsed (`+k identical`); clusters identical to the bar are dropped and counted.\n")
    md.append("Eligibility. On the **val** split: every round-2 run (experiments 11–17) except exp-14 `__fit-val` runs, "
              "whose val half is in-sample. On the **full set**: exp-14 `__oof` runs and every run that was not fitted "
              "on questions (`__fit-train` / `__fit-val` are excluded because one half is in-sample). Exp-14 `__oof` and "
              "`__fit-train` share the same val ranks, so they collapse to one row on val.\n")
    md.append("Provenance: from this commit on, `rag_eval.save_result` stamps every result JSON and leaderboard row with "
              "git commit + dirty flag, UTC time, host, harness version, SHA-256 of the question file and of the scored "
              "question ids, and a corpus fingerprint (n docs + SHA-256 of sorted ids). Existing rows are untouched; "
              "all runs analysed here predate the stamp and are identified by file path instead.\n")

    md.append("### Files and usage\n")
    md.append("* `experiments/common/rag_eval/stats.py` — `compare_runs(exp_a, run_a, exp_b, run_b, corpus, split=None)`, "
              "`compare_many(baseline, candidates, split, ...)` (max-T), `min_detectable_delta(n, sd_delta)`, "
              "`questions_needed(delta, sd_delta)`; CLI `python -m rag_eval.stats A|B|C exp/runA exp/runB [--split val] [--json]` "
              "(needs scipy: the `stats` extra of `rag-eval`, present in the 13 / 14 / 17 venvs).\n"
              "* `experiments/common/rag_eval/results.py` — `save_result(experiment, result, docs=None)` now stamps "
              "`result.provenance` / leaderboard `prov` (`build_provenance`, `corpus_fingerprint`, `docs_fingerprint`, `safe_name`).\n"
              "* `experiments/18_eval_hygiene/report.py` — regenerates this README and `stats_summary.json`: "
              "`cd experiments/13_lexical_upgrades && uv run python ../18_eval_hygiene/report.py` (≈ 15 s, CPU only). "
              "The hand-written reading is `reading.md`, appended verbatim as section (d).\n")
    md.append("```\n$ python -m rag_eval.stats C 09_corpus_c/bm25__fixed1200_title__bm25+bge-reranker-v2-m3@30 17_lex_rerank/lex13+bge@20 --split val\n"
              "corpus C, split val, n=35 ... rr  Δ=+0.023 [+0.000, +0.083]  p_t=0.193 p_perm=0.312  W/L/T=4/1/30\n```\n")

    for corpus in ("A", "B", "C"):
        cr = runs[corpus]
        bar_val = find(cr, *BARS[corpus]["val"])
        bar_full = find(cr, *BARS[corpus]["full"])
        summary["corpora"][corpus] = {"bar_val": bar_val["_key"], "bar_full": bar_full["_key"]}
        qids_val = split_qids(bar_val, "val")
        qids_all = split_qids(bar_val, None)
        md.append(f"\n## Corpus {corpus}\n")
        md.append(f"Round-1 validation bar: `{bar_val['_key']}` — {BAR_LABEL[corpus]}: val MRR {f3(mean_rr(bar_val, 'val'))} "
                  f"(n = {len(qids_val)}; SE of that mean {f3(se_of_mean(rr_vector(bar_val, qids_val)))}), "
                  f"full set {f3(mean_rr(bar_val, None))} (n = {len(qids_all)}, SE {f3(se_of_mean(rr_vector(bar_val, qids_all)))}). "
                  f"Per-question ranks present: yes (`results/{bar_val['_file']}`).\n")
        if bar_full is not bar_val:
            md.append(f"Round-1 full-set best: `{bar_full['_key']}` — {FULL_LABEL[corpus]}: full set {f3(mean_rr(bar_full, None))}, "
                      f"val {f3(mean_rr(bar_full, 'val'))}. Per-question ranks present: yes (`results/{bar_full['_file']}`).\n")
        else:
            md.append("Round-1 full-set best is the same run as the validation bar.\n")

        # (a) validation split vs val bar
        for split, bar, title in (("val", bar_val, "(a) validation split vs the round-1 validation bar"),
                                  ("all", bar_full, "(b) full set vs the round-1 full-set best")):
            qids = split_qids(bar, split)
            cands = [c for c in eligible(cr, split) if set(c["per_question"]) >= set(qids)]
            reps, same, aliases = dedupe(cands, bar, qids)
            reps.sort(key=lambda r: -mean_rr(r, split))
            maxt_rows = compare_many(bar, reps, split=split, n_resamples=N_PERM_MAXT, seed=SEED)
            maxt = {r["_key"]: m for r, m in zip(reps, maxt_rows)}
            n_sig_raw = sum(1 for m in maxt_rows if m["p_raw"] < 0.05 and m["delta"] > 0)
            n_sig_adj = sum(1 for m in maxt_rows if m["p_adj"] < 0.05 and m["delta"] > 0)
            n_pos = sum(1 for m in maxt_rows if m["delta"] > 0)
            md.append(f"\n### {corpus} — {title}\n")
            md.append(f"Bar: `{bar['_key']}`, MRR {f3(mean_rr(bar, split))} on n = {len(qids)}. Family: {len(cands)} eligible "
                      f"round-2 runs → {len(reps)} distinct rank vectors ({same} identical to the bar, dropped); "
                      f"{n_pos} of {len(reps)} have Δ > 0, {n_sig_raw} at raw p < 0.05, **{n_sig_adj} after max-T**. "
                      f"Top {TOP} by {'val' if split == 'val' else 'full-set'} MRR:\n")
            md.extend(comparison_table(bar, reps[:TOP], split, maxt, aliases, f"MRR ({split})"))
            md.append("")
            summary["corpora"][corpus][split] = {
                "bar": bar["_key"], "n": len(qids), "family": len(reps), "identical_to_bar": same,
                "n_positive": n_pos, "n_sig_raw": n_sig_raw, "n_sig_maxT": n_sig_adj,
                "top": [{"run": r["_key"], "mrr": mean_rr(r, split), **{k: v for k, v in maxt[r["_key"]].items() if k not in ("name", "experiment")},
                         "rr": r["_cmp"][split].rr.to_dict(), "hit1": r["_cmp"][split].hits[1].to_dict()} for r in reps[:TOP]],
                "sd_delta_median_top": float(np.median([r["_cmp"][split].rr.sd_delta for r in reps[:TOP]])) if reps else None,
            }
            # best-by-max-T note
            if maxt_rows:
                best = min(maxt_rows, key=lambda m: (m["p_adj"], -m["delta"]))
                md.append(f"Smallest adjusted p in the family: `{short(best['name'], 60)}` Δ = {fd(best['delta'])}, raw p = {best['p_raw']:.3f}, "
                          f"max-T p = {best['p_adj']:.3f}.\n")

        # named claims vs val bar
        md.append(f"\n### {corpus} — the named round-2 claims, paired against the validation bar\n")
        md.extend(claim_lines(bar_val, cr, NAMED_CLAIMS[corpus], "val"))
        md.append("")

    # pooled: exp-14 recipe and val bars vs full-set bests over A+B+C
    md.append("\n## Pooled over A + B + C (133 questions, paired within corpus)\n")
    md.append("Pooling the per-question deltas of one *recipe* across the three corpora is the only way to reach n > 100 "
              "with today's question sets. The pairing is within corpus, so corpus difficulty cancels; the sign-flip "
              "test is blocked by construction.\n")
    md.append("| recipe | baseline | n | base MRR | recipe MRR | Δ | 95 % CI | p_t | p_perm | W/L/T | Δ H@1 | Δ H@10 |\n"
              "|---|---|--:|--:|--:|--:|:--|--:|--:|:--|--:|--:|")
    pooled_specs = [
        ("exp-14 learned ranker (A logreg-cheap, B logreg-minimal+meta, C lgbm-tiny-all; oof)", LTR_RECIPE, "full"),
        ("exp-14 learned ranker (same runs, oof)", LTR_RECIPE, "val"),
        ("round-1 validation bars scored on the full set", {c: BARS[c]["val"] for c in "ABC"}, "full"),
    ]
    summary["pooled"] = []
    for label, recipe, base_kind in pooled_specs:
        xa, xb, h1a, h1b, h10a, h10b = [], [], [], [], [], []
        for c in "ABC":
            base = find(runs[c], *BARS[c][base_kind])
            r = find(runs[c], *recipe[c])
            if base is r:
                continue
            q = sorted(set(base["per_question"]) & set(r["per_question"]))
            xa.append(rr_vector(base, q)); xb.append(rr_vector(r, q))
            h1a.append(hit_vector(base, q, 1)); h1b.append(hit_vector(r, q, 1))
            h10a.append(hit_vector(base, q, 10)); h10b.append(hit_vector(r, q, 10))
        if not xa:
            continue
        rr = paired_stats(np.concatenate(xa), np.concatenate(xb), "rr", seed=SEED)
        h1 = paired_stats(np.concatenate(h1a), np.concatenate(h1b), "hit@1", seed=SEED)
        h10 = paired_stats(np.concatenate(h10a), np.concatenate(h10b), "hit@10", seed=SEED)
        base_label = "round-1 full-set bests" if base_kind == "full" else "round-1 validation bars (full set)"
        md.append(f"| {label} | {base_label} | {rr.n} | {f3(rr.mean_a)} | {f3(rr.mean_b)} | {fd(rr.delta)} | [{fd(rr.ci_lo)}, {fd(rr.ci_hi)}] "
                  f"| {pfmt(rr.p_t)} | {pfmt(rr.p_perm, rr.perm_exact)} | {rr.wins}/{rr.losses}/{rr.ties} | {fd(h1.delta)} | {fd(h10.delta)} |")
        summary["pooled"].append({"recipe": label, "baseline": base_label, "rr": rr.to_dict(), "hit1": h1.to_dict(), "hit10": h10.to_dict()})
    md.append("")

    # (c) minimum detectable deltas
    md.append("\n## (c) Minimum detectable paired delta (two-sided α = 0.05, 80 % power)\n")
    md.append("Δ_min = (t₀.₉₇₅,ₙ₋₁ + t₀.₈,ₙ₋₁) · sd_d / √n, where sd_d is the standard deviation of the per-question "
              "RR delta between the two systems. Observed sd_d in the tables above (median over the top-10 rows): "
              + ", ".join(f"{c} val {f3(summary['corpora'][c]['val']['sd_delta_median_top'])} / full {f3(summary['corpora'][c]['all']['sd_delta_median_top'])}"
                          for c in "ABC")
              + ". Related systems (same reranker, different first stage) sit near 0.10–0.25; unrelated systems "
                "(lexical vs reranked) near 0.35–0.45.\n")
    md.append("| n | " + " | ".join(f"sd_d = {s:.2f}" for s in MDD_SDS) + " | questions ≈ |\n|--:|" + "--:|" * (len(MDD_SDS) + 1))
    names = {12: "A val", 16: "B val", 29: "A all / C train", 35: "C val", 40: "B all", 64: "C all", 133: "A+B+C", 500: "target"}
    for n in MDD_NS:
        md.append(f"| {n} | " + " | ".join(f3(min_detectable_delta(n, s)) for s in MDD_SDS) + f" | {names.get(n, '')} |")
    md.append("")
    md.append("Questions needed to detect Δ = 0.03 / 0.05 / 0.10 at sd_d = 0.30: "
              f"{questions_needed(0.03, 0.30)} / {questions_needed(0.05, 0.30)} / {questions_needed(0.10, 0.30)}; "
              f"at sd_d = 0.20: {questions_needed(0.03, 0.20)} / {questions_needed(0.05, 0.20)} / {questions_needed(0.10, 0.20)}.\n")
    summary["mdd"] = {str(n): {str(s): min_detectable_delta(n, s) for s in MDD_SDS} for n in MDD_NS}

    md.append(READING)
    md.append(f"\n---\n*Report generated in {time.time() - t_start:.0f} s; max-T with {N_PERM_MAXT:,} sign-flip resamples, "
              f"bootstrap 10,000 resamples, seed {SEED}. Machine-readable numbers: `stats_summary.json`.*\n")
    OUT_MD.write_text("\n".join(md), encoding="utf-8")
    OUT_JSON.write_text(json.dumps(summary, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {OUT_MD} and {OUT_JSON} in {time.time() - t_start:.0f} s")


READING = (Path(__file__).with_name("reading.md").read_text(encoding="utf-8")
           if Path(__file__).with_name("reading.md").exists() else "\n## (d) Reading\n\n*(reading.md missing)*\n")

if __name__ == "__main__":
    main()
