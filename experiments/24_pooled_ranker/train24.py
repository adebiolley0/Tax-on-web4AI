#!/usr/bin/env python3
"""Experiment 24 – LightGBM-tiny / logreg ranker on POOLED labels (mined train split + human TRAIN half).

Feature table = exp-21 table (cache/<c>_features.npz, mMARCO and bge columns dropped) + exp-24 extension
(cache/<c>_extra.npz: query length, verbatim 8-gram / 3-gram overlap, bge doc score recomputed from every
existing cache + missing flag + question-level coverage) + explicit bge × gate interactions for the linear model.

Pools (training questions):  mined = mined train only (same features: the exp-24 replication of the mined-only
ranker);  pooled = mined train + human train;  pooled-scored = mined train with a fully scored convex top-20 +
human train.  Human sample weight w ∈ {1, 5, 10} (and logreg C) chosen by 5-fold grouped CV inside the training
pool (criterion = mean of the held-out mined MRR and the held-out human-train MRR); the human VAL half never
enters any selection.
Fits: A = pool → human val (honest) / mined val (honest);  B = mined train + human val → human train;
oof-human = A on human val ∪ B on human train (all 40 / 64 honest);  C / D = the same with ALL mined questions.
  cd experiments/14_ltr_fusion && uv run python ../24_pooled_ranker/train24.py --corpus B
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
import warnings
from pathlib import Path

import numpy as np
from scipy.stats import spearmanr
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

EXP_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(EXP_DIR.parent / "21_mined_eval"))
from rag_eval import evaluate_rankings, save_result  # noqa: E402
from rag_eval.corpora import REPO_ROOT  # noqa: E402
from rag_eval.results import build_provenance  # noqa: E402
from common21 import (CACHE as CACHE21, PAIRED_HEADER, QFILES, REFS, SOURCES, Stage1, all_questions, as_run, fmt_paired,  # noqa: E402
                      hit_at, is_human, load_ref, load_saved, paired, recall_at, short_metrics, slices)
from features21 import load_table  # noqa: E402

warnings.filterwarnings("ignore")
EXP = "24_pooled_ranker"
CACHE = EXP_DIR / "cache"
RUNS = EXP_DIR / "runs"
LGBM_TINY = dict(num_leaves=3, n_estimators=100, learning_rate=0.05, min_child_samples=10, reg_lambda=5.0,
                 subsample=0.8, subsample_freq=1, colsample_bytree=0.8, min_split_gain=0.0)
SEEDS = [0, 1, 2, 3, 4]
C_GRID = [0.03, 0.1, 0.3, 1.0, 3.0]
W_GRID = [1.0, 5.0, 10.0]
GATE_FEATS = ("q_len_words", "q_log_len", "ov8_max", "ov3_max", "ov8_any", "q_verbatim",
              "bge_norm_x_loglen", "bge_norm_x_verbatim", "bge_norm_x_ov8")
SMALL = ("e5_norm", "bm25_norm", "bm25doc_norm", "convex05", "lex13_norm", "title_overlap", "log_doc_len", "is_yearly_edition",
         "bge_max", "bge_norm", "bge_missing", "bge_qcov", "q_len_words", "ov8_max", "q_verbatim",
         "bge_norm_x_loglen", "bge_norm_x_verbatim", "bge_norm_x_ov8")
FSETS = {
    "withtype": lambda n: True,
    "notype": lambda n: not n.startswith("type="),
    "notype-nogate": lambda n: not n.startswith("type=") and n not in GATE_FEATS,
    "notype-nobge": lambda n: not n.startswith("type=") and not n.startswith("bge"),
    "small": lambda n: n in SMALL,
}


# ── saving with the right question-file stamp (mirrors common21.save21 for this experiment) ─────────
def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def save24(res, corpus: str, which: str):
    prov = build_provenance(res)
    human_f, mined_f = QFILES[corpus]
    files = [human_f] if which == "human" else [mined_f]
    prov["questions_file"] = "+".join(str(f.relative_to(REPO_ROOT)) for f in files)
    prov["questions_sha256"] = "+".join(_sha(f) for f in files)
    res.provenance = prov
    return save_result(EXP, res)


class Model:
    def __init__(self, kind: str, C: float = 0.3):
        self.kind, self.C = kind, C

    def fit(self, X, y, groups, w=None):
        w = np.ones(len(y)) if w is None else np.asarray(w, dtype=np.float64)
        if self.kind == "logreg":
            self.sc = StandardScaler().fit(X)
            self.m = LogisticRegression(C=self.C, max_iter=3000)
            self.m.fit(self.sc.transform(X), (y > 0).astype(int), sample_weight=np.where(y > 0, y, 1.0) * w)
        else:
            import lightgbm as lgb
            self.ms = []
            lab = np.rint(2 * y).astype(int)
            for seed in SEEDS:
                m = lgb.LGBMRanker(objective="lambdarank", label_gain=[0, 1, 2], random_state=seed, verbose=-1, n_jobs=4, **LGBM_TINY)
                m.fit(X, lab, group=groups, sample_weight=w)
                self.ms.append(m)
        return self

    def predict(self, X):
        if self.kind == "logreg":
            return self.m.decision_function(self.sc.transform(X))
        return np.mean([m.predict(X) for m in self.ms], axis=0)

    def contrib(self, X):
        """Per-feature additive contributions (logreg: standardised x · coef; lgbm: tree SHAP via pred_contrib)."""
        if self.kind == "logreg":
            return self.sc.transform(X) * self.m.coef_[0]
        return np.mean([m.booster_.predict(X, pred_contrib=True)[:, :-1] for m in self.ms], axis=0)

    def importance(self, names):
        if self.kind == "logreg":
            return sorted(zip(names, self.m.coef_[0]), key=lambda t: -abs(t[1]))
        imp = np.mean([m.booster_.feature_importance("gain") for m in self.ms], axis=0)
        return sorted(zip(names, imp / max(imp.sum(), 1e-9)), key=lambda t: -t[1])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", required=True, choices=["B", "C"])
    ap.add_argument("--fsets", default="notype,withtype,notype-nogate,notype-nobge,small")
    ap.add_argument("--methods", default="lgbm-tiny,logreg")
    ap.add_argument("--pools", default="mined,pooled,pooled-scored")
    ap.add_argument("--no-save", action="store_true")
    a = ap.parse_args()
    t0 = time.perf_counter()
    st = Stage1(a.corpus)
    questions = all_questions(a.corpus)
    assert [q.qid for q in questions] == st.qids
    tab = load_table(a.corpus, CACHE21 / f"{a.corpus}_features.npz")
    ex = np.load(CACHE / f"{a.corpus}_extra.npz"); exm = json.load(open(CACHE / f"{a.corpus}_extra.json"))
    assert exm["qids"] == tab.qids
    keep = [i for i, n in enumerate(tab.names) if not (n.startswith("mmarco") or n.startswith("bge"))]
    names = [tab.names[i] for i in keep] + exm["names"]
    X = np.concatenate([tab.X[:, keep], ex["X"].astype(np.float64)], axis=1)
    ci = {n: i for i, n in enumerate(names)}
    inter = np.stack([X[:, ci["bge_norm"]] * X[:, ci["q_log_len"]], X[:, ci["bge_norm"]] * X[:, ci["q_verbatim"]],
                      X[:, ci["bge_norm"]] * X[:, ci["ov8_max"]]], axis=1)
    X = np.concatenate([X, inter], axis=1); names += ["bge_norm_x_loglen", "bge_norm_x_verbatim", "bge_norm_x_ov8"]
    ci = {n: i for i, n in enumerate(names)}
    y = tab.y
    nq = len(questions)
    groups_all = np.bincount(tab.rows_q, minlength=nq)
    human = np.array([is_human(q) for q in questions]); mined = ~human
    split = np.array([q.split for q in questions])
    bge_full = ex["bge_full"].astype(bool); q_len = ex["q_len"]; q_verb = ex["q_verbatim"]
    M = {"htrain": human & (split == "train"), "hval": human & (split == "val"), "mtrain": mined & (split == "train"),
         "mval": mined & (split == "val"), "mall": mined, "mtrain_sc": mined & (split == "train") & bge_full,
         "mval_sc": mined & (split == "val") & bge_full}
    POOLS = {"mined": M["mtrain"], "pooled": M["mtrain"] | M["htrain"], "pooled-scored": M["mtrain_sc"] | M["htrain"]}
    exp_hit = np.array([any(st.doc_ids[d] in q.expected for d in tab.rows_d[tab.rows_of(i)]) for i, q in enumerate(questions)])
    print(f"corpus {a.corpus}: {len(y)} rows, {len(names)} features; human train/val {M['htrain'].sum()}/{M['hval'].sum()}, "
          f"mined train/val {M['mtrain'].sum()}/{M['mval'].sum()} (bge fully scored {M['mtrain_sc'].sum()}/{M['mval_sc'].sum()}); "
          f"candidate recall human {exp_hit[human].mean():.3f} mined {exp_hit[mined].mean():.3f}; {time.perf_counter()-t0:.0f}s", flush=True)

    def cols_of(fset, rows):
        pred = FSETS[fset]
        return [i for i, n in enumerate(names) if pred(n) and X[rows, i].std() > 0]

    def fit_model(kind, fset, qmask, w_h=1.0, C=0.3):
        qs = np.where(qmask)[0]
        rows = np.isin(tab.rows_q, qs)
        order = np.argsort(tab.rows_q[rows], kind="stable")
        cols = cols_of(fset, rows)
        Xr, yr = X[rows][order][:, cols], y[rows][order]
        groups = [int(groups_all[q]) for q in sorted(qs)]
        w = np.where(human[tab.rows_q[rows][order]], w_h, 1.0)
        return Model(kind, C).fit(Xr, yr, groups, w), cols

    def rank_q(model, cols, qmask):
        return {questions[qi].qid: tab.ranking(st, qi, model.predict(X[tab.rows_of(qi)][:, cols])) for qi in np.where(qmask)[0]}

    def mrr_of(rankings, qmask):
        qs = [questions[i] for i in np.where(qmask)[0] if questions[i].qid in rankings]
        return evaluate_rankings("tmp", a.corpus, qs, rankings).metrics["mrr"] if qs else float("nan")

    saved: dict[str, dict] = {}

    def eval_save(name, rankings, config, qmask):
        out = {}
        qs_all = [questions[i] for i in np.where(qmask)[0] if questions[i].qid in rankings]
        for sl, qs in slices(qs_all).items():
            if not qs:
                continue
            res = evaluate_rankings(f"{sl}__{name}", a.corpus, qs, rankings, {**config, "questions": sl})
            res.metrics["recall@30"] = round(recall_at(qs, rankings, 30), 4); res.metrics["hit@30"] = round(hit_at(qs, rankings, 30), 4)
            if not a.no_save:
                save24(res, a.corpus, "human" if sl == "human" else "mined")
            out[sl] = short_metrics(res); saved[f"{sl}__{name}"] = as_run(res)
        return out

    # ── nested CV folds inside each pool (human and mined questions spread separately over 5 folds) ──
    rng = np.random.default_rng(0)

    def folds_of(pool_mask):
        f = np.full(nq, -1)
        for grp in (pool_mask & human, pool_mask & mined):
            idx = rng.permutation(np.where(grp)[0])
            for k, part in enumerate(np.array_split(idx, 5)):
                f[part] = k
        return f

    def cv_score(kind, fset, pool_mask, folds, w_h, C):
        rk = {}
        for k in range(5):
            held = folds == k
            mdl, cols = fit_model(kind, fset, pool_mask & ~held, w_h, C)
            rk.update(rank_q(mdl, cols, held))
        m_m, m_h = mrr_of(rk, pool_mask & mined), mrr_of(rk, pool_mask & human)
        return {"mined": round(m_m, 4), "human": round(m_h, 4), "crit": round(float(np.nanmean([m_m, m_h])), 4)}

    summary = {"corpus": a.corpus, "n_features": len(names), "features": names, "coverage": exm["coverage"], "bge_sources": exm["bge_sources"],
               "candidate_recall": {"human": float(exp_hit[human].mean()), "mined": float(exp_hit[mined].mean())}, "models": {}}
    for pool in a.pools.split(","):
        pm = POOLS[pool]
        folds = folds_of(pm)
        for fset in a.fsets.split(","):
            for meth in a.methods.split(","):
                key = f"{meth}__{fset}__{pool}"
                t1 = time.perf_counter()
                # selection grid (w only for pools with human questions; C for logreg)
                wgrid = W_GRID if pool != "mined" else [1.0]
                cgrid = C_GRID if meth == "logreg" else [None]
                cv = {}
                for w_h in wgrid:
                    for C in cgrid:
                        cv[(w_h, C)] = cv_score(meth, fset, pm, folds, w_h, C or 0.3)
                best_w, best_C = max(cv, key=lambda k: (cv[k]["crit"], -(k[1] or 0), -k[0]))
                entry = {"pool": pool, "fset": fset, "method": meth, "n_pool": int(pm.sum()), "n_pool_human": int((pm & human).sum()),
                         "w_human": best_w, "C": best_C, "cv": {f"w={k[0]}" + (f",C={k[1]}" if k[1] else ""): v for k, v in cv.items()}}
                cfg = {"method": meth, "features": fset, "pool": pool, "w_human": best_w, "C": best_C, "n_pool": int(pm.sum())}
                # fit A: pool → everything
                mdl, cols = fit_model(meth, fset, pm, best_w, best_C or 0.3)
                cfg["n_features"] = len(cols)
                rkA = rank_q(mdl, cols, np.ones(nq, dtype=bool))
                name = f"ltr24__{key}"
                resA = eval_save(f"{name}__fitA", rkA, {**cfg, "fit": "A: pool (human train + mined train are resubstitution)"}, np.ones(nq, dtype=bool))
                ev = lambda m: short_metrics(evaluate_rankings("t", a.corpus, [questions[i] for i in np.where(m)[0]], rkA))  # noqa: E731
                entry["fitA"] = {"human_val": ev(M["hval"]), "human_train_resub": ev(M["htrain"]), "mined_val": ev(M["mval"]), "mined_val_scored": ev(M["mval_sc"]),
                                 "mined_train_resub": ev(M["mtrain"]),
                                 "mined_val_by_src": {s: ev(M["mval"] & (np.array([q.meta.get("source") for q in questions]) == s)) for s in SOURCES
                                                      if (M["mval"] & (np.array([q.meta.get("source") for q in questions]) == s)).any()}}
                entry["importance"] = [(n, round(float(v), 4)) for n, v in mdl.importance([names[c] for c in cols])[:15]]
                # fit B: mined train + human val → human train;  oof-human
                if pool == "mined":                      # no human question in any fit: fit A is already out-of-fold on all of them
                    oof, fitdesc = {questions[i].qid: rkA[questions[i].qid] for i in np.where(human)[0]}, "mined-only fit A (all human questions held out)"
                else:
                    pmB = (pm & mined) | M["hval"]
                    mdlB, colsB = fit_model(meth, fset, pmB, best_w, best_C or 0.3)
                    rkB = rank_q(mdlB, colsB, human)
                    oof = {questions[i].qid: (rkA if split[i] == "val" else rkB)[questions[i].qid] for i in np.where(human)[0]}
                    fitdesc = "oof: A on human val, B (mined train + human val) on human train"
                entry["oof_human"] = eval_save(f"{name}__oof-human", oof, {**cfg, "fit": fitdesc}, human)["human"]
                if pool != "mined":
                    # fits C / D: ALL mined + one human half
                    pmC, pmD = M["mall"] | M["htrain"], M["mall"] | M["hval"]
                    mdlC, colsC = fit_model(meth, fset, pmC, best_w, best_C or 0.3); rkC = rank_q(mdlC, colsC, human)
                    mdlD, colsD = fit_model(meth, fset, pmD, best_w, best_C or 0.3); rkD = rank_q(mdlD, colsD, human)
                    oof2 = {questions[i].qid: (rkC if split[i] == "val" else rkD)[questions[i].qid] for i in np.where(human)[0]}
                    entry["fitC_human_val"] = short_metrics(evaluate_rankings("t", a.corpus, [questions[i] for i in np.where(M["hval"])[0]], rkC))
                    entry["oof_human_allmined"] = eval_save(f"{name}__oof-human-allmined", oof2, {**cfg, "fit": "oof: all mined + other human half"}, human)["human"]
                    # post-hoc (NOT used for selection): human val of fit A under every w
                    entry["posthoc_w_human_val"] = {}
                    for w_h in wgrid:
                        if w_h == best_w:
                            entry["posthoc_w_human_val"][f"w={w_h}"] = entry["fitA"]["human_val"]["mrr"]; continue
                        m_, c_ = fit_model(meth, fset, pm, w_h, best_C or 0.3)
                        entry["posthoc_w_human_val"][f"w={w_h}"] = round(mrr_of(rank_q(m_, c_, M["hval"]), M["hval"]), 4)
                # length-gate diagnostics on the fit-A model (human + mined val questions)
                if meth == "lgbm-tiny" and fset in ("notype", "withtype") and pool != "mined" and "bge_norm" in [names[c] for c in cols]:
                    entry["gate"] = gate_diagnostics(mdl, cols, names, X, tab, questions, human | M["mval"], q_len, bge_full)
                entry["seconds"] = round(time.perf_counter() - t1, 1)
                summary["models"][key] = entry
                fa = entry["fitA"]
                print(f"  {key:40s} w={best_w:<4} C={best_C} | CV crit {cv[(best_w, best_C)]['crit']:.3f} (mined {cv[(best_w, best_C)]['mined']:.3f} / human {cv[(best_w, best_C)]['human']:.3f}) | "
                      f"human val {fa['human_val']['mrr']:.3f} | human oof {entry['oof_human']['mrr']:.3f}"
                      + (f" | oof allmined {entry['oof_human_allmined']['mrr']:.3f}" if 'oof_human_allmined' in entry else "")
                      + f" | mined val {fa['mined_val']['mrr']:.3f} (scored {fa['mined_val_scored']['mrr']:.3f}) | {entry['seconds']}s", flush=True)
                print("     top: " + ", ".join(f"{n}={v:+.3f}" for n, v in entry["importance"][:8]), flush=True)

    # ── paired tests ──────────────────────────────────────────────────────────
    refs = {}
    for k in REFS[a.corpus]:
        try:
            refs[k] = load_ref(a.corpus, k)
        except FileNotFoundError:
            print(f"  (reference {k} missing)")
    for n, exp_, run in (("convex05", "21_mined_eval", "human__convex05"), ("convex05+bge@20", "21_mined_eval", "human__convex05+bge@20"),
                         ("exp21-ranker cheap+bge", "21_mined_eval", "human__ltr__lgbm-tiny__cheap+bge__bal__fit-mtrain"),
                         ("exp21-ranker cheap", "21_mined_eval", "human__ltr__lgbm-tiny__cheap__bal__fit-mtrain"),
                         ("exp22 gate T25", "22_reception_colbert", "gate_T25__mmarco_b0.8__rec_e5")):
        try:
            from rag_eval.stats import load_run
            r = load_run(exp_, run, a.corpus); r["_experiment"] = exp_; refs[n] = r
        except FileNotFoundError:
            pass
    mined_refs = {}
    for n, run in (("convex05", "mined__convex05"), ("exp13_lex", "mined__exp13_lex"),
                   ("exp21-ranker cheap+bge", "mined__ltr__lgbm-tiny__cheap+bge__bal__fit-mtrain"), ("exp21-ranker cheap", "mined__ltr__lgbm-tiny__cheap__bal__fit-mtrain"),
                   ("convex05+bge@20 (sub)", "sub__convex05+bge@20")):
        try:
            mined_refs[n] = load_saved(run, a.corpus)
        except FileNotFoundError:
            pass
    own_mined = {k: v for k, v in saved.items() if "__mined__" in k}      # exp-24 mined-only rankers
    tests = {"human_val": {}, "human_all": {}, "mined_val": {}}
    for key, entry in summary["models"].items():
        name = f"ltr24__{key}"
        runA, runO = saved[f"human__{name}__fitA"], saved[f"human__{name}__oof-human"]
        rowv, rowa = {}, {}
        for k, ref in refs.items():
            rowv[f"vs {k}"] = paired(ref, runA, split="val")
            rowa[f"vs {k}"] = paired(ref, runO)
        if entry["pool"] != "mined":
            own = f"human__ltr24__{entry['method']}__{entry['fset']}__mined"
            if f"{own}__fitA" in saved:
                rowv["vs exp24 mined-only (same features)"] = paired(saved[f"{own}__fitA"], runA, split="val")
                rowa["vs exp24 mined-only (same features)"] = paired(saved[f"{own}__oof-human"], runO)
            if f"human__{name}__oof-human-allmined" in saved:
                for k, ref in refs.items():
                    rowa[f"[all-mined oof] vs {k}"] = paired(ref, saved[f"human__{name}__oof-human-allmined"])
        tests["human_val"][name], tests["human_all"][name] = rowv, rowa
        runM = saved[f"mined__{name}__fitA"]
        rowm = {}
        for k, ref in mined_refs.items():
            rowm[f"vs {k}"] = paired(ref, runM, split="val")
        if entry["pool"] != "mined":
            own = f"mined__ltr24__{entry['method']}__{entry['fset']}__mined__fitA"
            if own in saved:
                rowm["vs exp24 mined-only (same features)"] = paired(saved[own], runM, split="val")
        tests["mined_val"][name] = rowm
    summary["tests"] = tests
    RUNS.mkdir(exist_ok=True)
    (RUNS / f"train24_{a.corpus}.json").write_text(json.dumps(summary, indent=1, default=float))
    write_md(a.corpus, summary)
    print(f"done in {time.perf_counter()-t0:.0f}s")


def gate_diagnostics(mdl, cols, names, X, tab, questions, qmask, q_len, bge_full):
    """Did the tree learn the length gate?  Tree-SHAP contribution of the bge features per query-length bin
    (scored questions only), its slope on bge_norm within the bin, and a partial dependence of the prediction
    on bge_norm per bin."""
    cn = [names[c] for c in cols]
    bge_cols = [i for i, n in enumerate(cn) if n.startswith("bge")]
    j_norm = cn.index("bge_norm")
    qs = [qi for qi in np.where(qmask & bge_full)[0]]
    rows = np.concatenate([tab.rows_of(qi) for qi in qs])
    rq = tab.rows_q[rows]
    Xr = X[rows][:, cols]
    contrib = mdl.contrib(Xr)
    bc = contrib[:, bge_cols].sum(axis=1)
    tot = np.abs(contrib).sum(axis=1)
    bins = [(0, 25), (26, 50), (51, 100), (101, 10_000)]
    out = {"bins": []}
    scored = Xr[:, cn.index("bge_missing")] == 0
    for lo, hi in bins:
        m = (q_len[rq] >= lo) & (q_len[rq] <= hi) & scored
        if m.sum() < 30:
            continue
        nqb = len(set(rq[m].tolist()))
        slope = float(np.polyfit(Xr[m, j_norm], bc[m], 1)[0])
        rho = float(spearmanr(Xr[m, j_norm], bc[m]).correlation)
        # partial dependence: mean prediction when bge_norm is set to v (other features fixed)
        pd = []
        for v in (0.0, 0.25, 0.5, 0.75, 1.0):
            Xm = Xr[m].copy(); Xm[:, j_norm] = v
            pd.append(float(mdl.predict(Xm).mean()))
        out["bins"].append({"words": f"{lo}–{hi if hi < 10_000 else '∞'}", "n_rows": int(m.sum()), "n_questions": nqb,
                            "mean_abs_bge_contrib": round(float(np.abs(bc[m]).mean()), 4),
                            "share_of_abs_contrib": round(float(np.abs(bc[m]).sum() / max(tot[m].sum(), 1e-9)), 3),
                            "slope_on_bge_norm": round(slope, 4), "spearman": round(rho, 3),
                            "pd_bge_norm_0_to_1": [round(x, 4) for x in pd], "pd_range": round(pd[-1] - pd[0], 4)})
    return out


def write_md(corpus, s):
    L = [f"### Experiment 24 – corpus {corpus}: pooled-label ranker", "",
         f"Coverage: `{json.dumps(s['coverage'])}`; bge sources `{json.dumps(s['bge_sources'])}`; candidate recall human {s['candidate_recall']['human']:.3f} / mined {s['candidate_recall']['mined']:.3f}", "",
         "| pool | features | method | n pool (human) | w_h / C (nested CV crit: mined / human) | human **val** MRR (H@1 / R@10) | human oof all | human oof (all mined) | human train resub | mined val (scored) | mined val per source | mined train resub | post-hoc human val per w |",
         "|---|---|---|--:|---|---|--:|--:|--:|---|---|--:|---|"]
    for key, e in s["models"].items():
        fa = e["fitA"]; hv = fa["human_val"]
        cvb = e["cv"][f"w={e['w_human']}" + (f",C={e['C']}" if e["C"] else "")]
        L.append(f"| {e['pool']} | {e['fset']} | {e['method']} | {e['n_pool']} ({e['n_pool_human']}) | {e['w_human']:g} / {e['C'] or '–'} ({cvb['crit']:.3f}: {cvb['mined']:.3f} / {cvb['human']:.3f}) | "
                 f"**{hv['mrr']:.3f}** ({hv['hit@1']:.3f} / {hv['recall@10']:.3f}) | **{e['oof_human']['mrr']:.3f}** | "
                 f"{e['oof_human_allmined']['mrr'] if 'oof_human_allmined' in e else float('nan'):.3f} | {fa['human_train_resub']['mrr']:.3f} | "
                 f"{fa['mined_val']['mrr']:.3f} ({fa['mined_val_scored']['mrr']:.3f}) | " + ", ".join(f"{k} {v['mrr']:.3f}" for k, v in fa["mined_val_by_src"].items()) +
                 f" | {fa['mined_train_resub']['mrr']:.3f} | " + ", ".join(f"{k} {v:.3f}" for k, v in e.get("posthoc_w_human_val", {}).items()) + " |")
    L += ["", "Nested-CV grid (criterion = mean of held-out mined and held-out human-train MRR):", ""]
    for key, e in s["models"].items():
        if e["pool"] != "mined":
            L.append(f"* `{key}`: " + "; ".join(f"{k}: {v['crit']:.3f} ({v['mined']:.3f}/{v['human']:.3f})" for k, v in e["cv"].items()))
    L += ["", "Top features (fit A):", ""]
    for key, e in s["models"].items():
        L.append(f"* `{key}`: " + ", ".join(f"{n} {v:+.3f}" for n, v in e["importance"][:10]))
    L += ["", "Length-gate diagnostics (fit A, tree-SHAP contribution of the bge features; scored questions, human + mined val):", "",
          "| model | words | n rows (q) | mean abs bge contrib | share of abs contrib | slope on bge_norm | Spearman | PD(bge_norm 0→1) | PD range |", "|---|---|--:|--:|--:|--:|--:|---|--:|"]
    for key, e in s["models"].items():
        for b in e.get("gate", {}).get("bins", []):
            L.append(f"| {key} | {b['words']} | {b['n_rows']} ({b['n_questions']}) | {b['mean_abs_bge_contrib']:.3f} | {b['share_of_abs_contrib']:.3f} | {b['slope_on_bge_norm']:+.3f} | {b['spearman']:+.2f} | "
                     + " / ".join(f"{x:.2f}" for x in b["pd_bge_norm_0_to_1"]) + f" | {b['pd_range']:+.3f} |")
    for sec, title in (("human_val", "Human VAL half – paired tests (Δ = exp-24 fit A − reference)"), ("human_all", "Human full set – paired tests (Δ = exp-24 oof − reference)"),
                       ("mined_val", "Mined val split – paired tests (Δ = exp-24 fit A − reference)")):
        L += ["", f"**{title}**", "", "| run | reference " + PAIRED_HEADER[1:], "|---|---|:--|--:|--:|:--|--:|--:|"]
        for name, row in s["tests"][sec].items():
            for k, t in row.items():
                L.append(f"| {name} | {k} (n={t['n']}, ref {t['mrr_a']:.3f} → {t['mrr_b']:.3f}) | {fmt_paired(t)} |")
    (RUNS / f"train24_{corpus}.md").write_text("\n".join(L) + "\n")


if __name__ == "__main__":
    main()
