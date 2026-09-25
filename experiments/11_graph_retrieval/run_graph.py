#!/usr/bin/env python3
"""Experiment 11 driver: first-stage baselines → graph expansion / personalized PageRank
(tuned on the train split, reported on val) → edge-type ablations → duplicate collapsing (C)
→ structure prior → stack. Every saved run goes through rag_eval.save_result.

  uv run python run_graph.py --corpus B --tag B_raw --bases bm25,dense,rrf
  uv run python run_graph.py --corpus C --bases bm25,dense,rrf,convex0.5
"""
from __future__ import annotations

import argparse
import csv
import json
import time

import numpy as np

from rag_eval import evaluate_rankings, save_result, load_questions_b, load_questions_c
from common11 import FirstStage, CACHE, EXP, HERE, minmax, ranking_from_scores
from propagate import PropGraph, top_k_seeds
from prior import boost_matrix, doc_attrs_b, doc_attrs_c

ALPHAS = [0.02, 0.05, 0.1, 0.2, 0.3, 0.5, 0.8, 1.2, 2.0]


def rownorm(P: np.ndarray) -> np.ndarray:
    """Scale each query's propagated vector to max 1, so alpha is relative to the top first-stage score."""
    mx = P.max(axis=1, keepdims=True)
    return P / np.maximum(mx, 1e-12)
KS = [10, 30, 100]
NORMS = ["sum", "mean", "sym"]
HOPS = [1, 2]
PPR_BETAS = [0.5, 0.85]
GAMMAS = [0.05, 0.1, 0.2, 0.3, 0.5]


def collapse_ranking(s: np.ndarray, gid: np.ndarray, n_groups: int, doc_ids: list[str], top: int = 50) -> list[str]:
    """Rank groups by their best member, expand members in score order."""
    gmax = np.full(n_groups, -np.inf, dtype=np.float64)
    np.maximum.at(gmax, gid, s)
    order = np.lexsort((-s, -gmax[gid]))[:top]
    return [doc_ids[j] for j in order]


class Runner:
    def __init__(self, corpus: str, tag: str):
        self.corpus, self.tag = corpus, tag
        self.fs = FirstStage(tag)
        self.prefix = "" if tag in ("B_raw", "C") else tag.split("_", 1)[1] + ":"   # B_clean → "clean:" so result files do not collide
        self.questions = load_questions_b() if corpus == "B" else load_questions_c()
        assert [q.qid for q in self.questions] == self.fs.qids
        g = json.loads((CACHE / f"{tag}_graph.json").read_text())
        self.gstats = g["stats"]
        self.G = PropGraph(self.fs.doc_ids, g["edges"], g["groups"])
        self.W_all = {t: 1.0 for t in self.G.types}
        self.canonical = g.get("canonical", {})
        self.rows: list[dict] = []
        self.grid: list[dict] = []
        if corpus == "B":
            self.regions, self.domains = doc_attrs_b(self.fs.doc_ids)
        else:
            meta = json.loads((CACHE / "C_docs_meta.json").read_text())
            self.regions, self.domains = doc_attrs_c(self.fs.doc_ids, meta)
        self.collapse_maps: dict[str, tuple[np.ndarray, int]] = {}
        for level, cmap in self.canonical.items():
            keys = {}
            gid = np.array([keys.setdefault(cmap[d], len(keys)) for d in self.fs.doc_ids])
            self.collapse_maps[level] = (gid, len(keys))
        print(f"{corpus}/{tag}: {self.fs.n_docs} docs, {len(self.questions)} q, graph types {self.G.types}, "
              f"dropped edges {self.G.dropped_edges}", flush=True)

    # ── evaluation ─────────────────────────────────────────────────────
    def evaluate(self, name: str, S: np.ndarray, config: dict, collapse: str | None = None, save: bool = True, timing=None):
        rankings = {}
        for i, q in enumerate(self.questions):
            if collapse:
                gid, ng = self.collapse_maps[collapse]
                rankings[q.qid] = collapse_ranking(S[i], gid, ng, self.fs.doc_ids)
            else:
                rankings[q.qid] = ranking_from_scores(S[i], self.fs.doc_ids)
        res = evaluate_rankings(self.prefix + name, self.corpus, self.questions, rankings, config={"tag": self.tag, **config}, timing=timing or {})
        if save:
            save_result(EXP, res)
            self.rows.append(self.row(res))
            print(res.summary(), flush=True)
        return res

    @staticmethod
    def row(res) -> dict:
        m = res.metrics
        return {"name": res.name, "train_mrr": m["train_mrr"], "val_mrr": m["val_mrr"], "mrr": m["mrr"],
                "hit@1": m["hit@1"], "val_hit@1": m["val_hit@1"], "recall@10": m["recall@10"], "val_recall@10": m["val_recall@10"],
                "ndcg@5": m["ndcg@5"], "config": res.config}

    def grid_eval(self, name: str, S: np.ndarray, config: dict) -> dict:
        res = self.evaluate(name, S, config, save=False)
        r = self.row(res); self.grid.append(r)
        return r

    # ── methods ────────────────────────────────────────────────────────
    def run_base(self, base: str):
        S = self.fs.doc_scores(base)
        Sn = np.stack([minmax(r) for r in S]).astype(np.float32)
        base_res = self.evaluate(base, Sn, {"method": "first_stage", "base": base})
        base_train = base_res.metrics["train_mrr"]
        # 1. neighbour expansion grid (all edge types, weight 1)
        t0 = time.perf_counter()
        props = {}
        for K in KS:
            seeds = top_k_seeds(Sn, K)
            for norm in NORMS:
                for hops in HOPS:
                    prop = rownorm(self.G.expand(seeds, self.W_all, norm, hops))
                    props[(K, norm, hops)] = prop
                    for a in ALPHAS:
                        self.grid_eval(f"{base}+expand[k{K},{norm},h{hops},a{a}]", Sn + a * prop,
                                       {"method": "expand", "base": base, "k": K, "norm": norm, "hops": hops, "alpha": a})
        grid_s = time.perf_counter() - t0
        rows = [r for r in self.grid if r["config"]["method"] == "expand" and r["config"]["base"] == base]
        best = max(rows, key=lambda r: (r["train_mrr"], -r["config"]["alpha"]))
        oracle = max(rows, key=lambda r: r["val_mrr"])
        c = best["config"]
        prop = props[(c["k"], c["norm"], c["hops"])]
        self.evaluate(f"{base}+expand[k{c['k']},{c['norm']},h{c['hops']},a{c['alpha']}]", Sn + c["alpha"] * prop,
                      {**c, "types": list(self.W_all), "selected_on": "train", "val_oracle": oracle["name"],
                       "val_oracle_mrr": oracle["val_mrr"], "grid_size": len(rows)},
                      timing={"grid_s": round(grid_s, 1), "per_query_ms": round(1000 * grid_s / len(rows) / len(self.questions), 2)})
        # 2. edge-type ablation at the selected configuration
        seeds = top_k_seeds(Sn, c["k"])
        only_rows = {}
        for t in self.G.types:
            p = rownorm(self.G.expand(seeds, {t: 1.0}, c["norm"], c["hops"]))
            r = self.evaluate(f"{base}+expand[k{c['k']},{c['norm']},h{c['hops']},a{c['alpha']}]__only_{t}", Sn + c["alpha"] * p,
                              {**c, "types": [t], "ablation": "only"})
            only_rows[t] = r.metrics
            if len(self.G.types) > 2:
                w = {u: 1.0 for u in self.G.types if u != t}
                p = rownorm(self.G.expand(seeds, w, c["norm"], c["hops"]))
                self.evaluate(f"{base}+expand[k{c['k']},{c['norm']},h{c['hops']},a{c['alpha']}]__without_{t}", Sn + c["alpha"] * p,
                              {**c, "types": list(w), "ablation": "without"})
        # 3. re-tune alpha with the edge types that help on train individually
        sel = [t for t, m in only_rows.items() if m["train_mrr"] > base_train] or list(self.G.types)
        W_sel = {t: 1.0 for t in sel}
        sel_rows = []
        for K in KS:
            sd = top_k_seeds(Sn, K)
            for norm in NORMS:
                for hops in HOPS:
                    p = rownorm(self.G.expand(sd, W_sel, norm, hops))
                    for a in ALPHAS:
                        r = self.grid_eval(f"{base}+expand_sel[k{K},{norm},h{hops},a{a}]", Sn + a * p,
                                           {"method": "expand_sel", "base": base, "k": K, "norm": norm, "hops": hops, "alpha": a, "types": sel})
                        sel_rows.append((r, p))
        bsel, pbest = max(sel_rows, key=lambda rp: (rp[0]["train_mrr"], -rp[0]["config"]["alpha"]))
        cs = bsel["config"]
        self.evaluate(f"{base}+expand_sel[k{cs['k']},{cs['norm']},h{cs['hops']},a{cs['alpha']}]", Sn + cs["alpha"] * pbest,
                      {**cs, "selected_on": "train", "val_oracle_mrr": max(r["val_mrr"] for r, _ in sel_rows)})
        # 4. personalized PageRank from the top-k
        ppr_rows = []
        t0 = time.perf_counter()
        for K in [10, 30]:
            sd = top_k_seeds(Sn, K)
            for beta in PPR_BETAS:
                p = self.G.ppr(sd, self.W_all, beta)
                for a in ALPHAS:
                    r = self.grid_eval(f"{base}+ppr[k{K},b{beta},a{a}]", Sn + a * p, {"method": "ppr", "base": base, "k": K, "beta": beta, "alpha": a})
                    ppr_rows.append((r, p))
        ppr_s = time.perf_counter() - t0
        bp, pp = max(ppr_rows, key=lambda rp: (rp[0]["train_mrr"], -rp[0]["config"]["alpha"]))
        cp = bp["config"]
        self.evaluate(f"{base}+ppr[k{cp['k']},b{cp['beta']},a{cp['alpha']}]", Sn + cp["alpha"] * pp,
                      {**cp, "selected_on": "train", "val_oracle_mrr": max(r["val_mrr"] for r, _ in ppr_rows)},
                      timing={"grid_s": round(ppr_s, 1)})
        # 5. structure prior (region + domain cues), tuned on train
        prior_rows = []
        for gr in [0.0] + GAMMAS:
            for gd in [0.0] + GAMMAS:
                if gr == 0 and gd == 0:
                    continue
                Bm = boost_matrix(self.questions, self.regions, self.domains, gr, gd)
                r = self.grid_eval(f"{base}+prior[r{gr},d{gd}]", Sn * Bm, {"method": "prior", "base": base, "gamma_region": gr, "gamma_domain": gd})
                prior_rows.append((r, Bm))
        bpr, Bbest = max(prior_rows, key=lambda rb: (rb[0]["train_mrr"], -(rb[0]["config"]["gamma_region"] + rb[0]["config"]["gamma_domain"])))
        cpr = bpr["config"]
        self.evaluate(f"{base}+prior[r{cpr['gamma_region']},d{cpr['gamma_domain']}]", Sn * Bbest,
                      {**cpr, "selected_on": "train", "val_oracle_mrr": max(r["val_mrr"] for r, _ in prior_rows)})
        # 6. duplicate collapsing (corpus C) on the baseline and on the best expansion
        for level in self.collapse_maps:
            self.evaluate(f"{base}+collapse_{level}", Sn, {"method": "collapse", "base": base, "level": level}, collapse=level)
            self.evaluate(f"{base}+expand_sel[...]+collapse_{level}", Sn + cs["alpha"] * pbest,
                          {**cs, "method": "expand_sel+collapse", "level": level}, collapse=level)
        # 7. stack: prior × first stage + selected expansion (+ collapse on C)
        seeds = top_k_seeds(Sn * Bbest, cs["k"])
        p = rownorm(self.G.expand(seeds, W_sel, cs["norm"], cs["hops"]))
        stack = Sn * Bbest + cs["alpha"] * p
        self.evaluate(f"{base}+stack[prior+expand_sel]", stack, {**cs, "method": "stack", "gamma_region": cpr["gamma_region"], "gamma_domain": cpr["gamma_domain"]})
        for level in self.collapse_maps:
            self.evaluate(f"{base}+stack[prior+expand_sel]+collapse_{level}", stack, {**cs, "method": "stack+collapse", "level": level}, collapse=level)

    def finish(self):
        with (HERE / f"results_grid_{self.tag}.csv").open("w", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["name", "train_mrr", "val_mrr", "mrr", "hit@1", "val_hit@1", "recall@10", "val_recall@10", "ndcg@5"])
            for r in self.grid:
                w.writerow([r["name"], r["train_mrr"], r["val_mrr"], r["mrr"], r["hit@1"], r["val_hit@1"], r["recall@10"], r["val_recall@10"], r["ndcg@5"]])
        (HERE / f"summary_{self.tag}.json").write_text(json.dumps({"graph_stats": self.gstats, "runs": self.rows}, ensure_ascii=False, indent=1))
        print(f"\n{'run':70s} {'train':>6s} {'val':>6s} {'all':>6s} {'H@1':>6s} {'vH@1':>6s} {'R@10':>6s} {'vR@10':>6s}")
        for r in self.rows:
            print(f"{r['name'][:70]:70s} {r['train_mrr']:6.3f} {r['val_mrr']:6.3f} {r['mrr']:6.3f} {r['hit@1']:6.3f} {r['val_hit@1']:6.3f} {r['recall@10']:6.3f} {r['val_recall@10']:6.3f}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", required=True, choices=["B", "C"])
    ap.add_argument("--tag", default=None)
    ap.add_argument("--bases", default="bm25,dense,rrf")
    a = ap.parse_args()
    tag = a.tag or ("B_raw" if a.corpus == "B" else "C")
    r = Runner(a.corpus, tag)
    for base in a.bases.split(","):
        r.run_base(base)
    r.finish()


if __name__ == "__main__":
    main()
