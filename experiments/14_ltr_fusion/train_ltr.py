#!/usr/bin/env python3
"""Learning-to-rank over the cheap feature table (features.py).

Methods
* logreg          pointwise logistic regression (standardised features, L2, sample weight = label)
* pairwise-linear RankSVM-style: logistic regression on within-query feature differences (linear LTR)
* lgbm-tiny/small/medium  LightGBM LambdaMART (lambdarank objective), 5-seed bagging

Every method x feature set is fitted on train and evaluated on val, then the fold is swapped
(fit on val, evaluate on train); "oof" merges both held-out halves (2-fold CV over all questions).

  uv run python train_ltr.py --corpus A
"""
from __future__ import annotations

import argparse
import json
import time
import warnings

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

from rag_eval import load_questions_a, load_questions_b, load_questions_c
from common14 import CACHE, Stage1
from features import FEATURE_SETS, build_table, select_features
from protocol import fold_report, split_masks

warnings.filterwarnings("ignore")
LOADERS = {"A": load_questions_a, "B": load_questions_b, "C": load_questions_c}

LGBM = {
    "lgbm-tiny": dict(num_leaves=3, n_estimators=100, learning_rate=0.05, min_child_samples=10, reg_lambda=5.0,
                      subsample=0.8, subsample_freq=1, colsample_bytree=0.8, min_split_gain=0.0),
    "lgbm-small": dict(num_leaves=7, n_estimators=200, learning_rate=0.05, min_child_samples=5, reg_lambda=1.0,
                       subsample=0.8, subsample_freq=1, colsample_bytree=0.8),
    "lgbm-medium": dict(num_leaves=15, n_estimators=300, learning_rate=0.05, min_child_samples=3, reg_lambda=0.0,
                        subsample=0.8, subsample_freq=1, colsample_bytree=0.8),
}
SEEDS = [0, 1, 2, 3, 4]


class Model:
    def __init__(self, kind: str, C: float = 1.0):
        self.kind, self.C = kind, C

    def fit(self, X, y, groups):
        if self.kind == "logreg":
            self.sc = StandardScaler().fit(X)
            self.m = LogisticRegression(C=self.C, max_iter=2000)
            self.m.fit(self.sc.transform(X), (y > 0).astype(int), sample_weight=np.where(y > 0, y, 1.0))
        elif self.kind == "pairwise-linear":
            self.sc = StandardScaler().fit(X)
            Xs = self.sc.transform(X)
            D, L, W = [], [], []
            start = 0
            for g in groups:
                Xi, yi = Xs[start:start + g], y[start:start + g]
                start += g
                pos = np.where(yi > 0)[0]
                for i in pos:
                    for j in range(g):
                        if yi[i] > yi[j]:
                            D.append(Xi[i] - Xi[j]); L.append(1); W.append(yi[i] - yi[j])
                            D.append(Xi[j] - Xi[i]); L.append(0); W.append(yi[i] - yi[j])
            self.m = LogisticRegression(C=self.C, fit_intercept=False, max_iter=5000)
            self.m.fit(np.asarray(D), np.asarray(L), sample_weight=np.asarray(W))
        else:
            import lightgbm as lgb
            self.ms = []
            lab = np.rint(2 * y).astype(int)
            for seed in SEEDS:
                m = lgb.LGBMRanker(objective="lambdarank", label_gain=[0, 1, 2], random_state=seed, verbose=-1,
                                   n_jobs=2, **LGBM[self.kind])
                m.fit(X, lab, group=groups)
                self.ms.append(m)
        return self

    def predict(self, X):
        if self.kind in ("logreg", "pairwise-linear"):
            return self.m.decision_function(self.sc.transform(X))
        return np.mean([m.predict(X) for m in self.ms], axis=0)

    def importance(self, names):
        if self.kind in ("logreg", "pairwise-linear"):
            coef = self.m.coef_[0]
            return sorted(zip(names, coef), key=lambda t: -abs(t[1]))
        imp = np.mean([m.booster_.feature_importance("gain") for m in self.ms], axis=0)
        return sorted(zip(names, imp / max(imp.sum(), 1e-9)), key=lambda t: -t[1])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", required=True)
    ap.add_argument("--methods", default="logreg,pairwise-linear,lgbm-tiny,lgbm-small,lgbm-medium")
    ap.add_argument("--fsets", default="all,cheap,minimal,minimal+meta")
    ap.add_argument("--C", type=float, default=0.3)
    ap.add_argument("--no_save", action="store_true")
    a = ap.parse_args()
    st = Stage1(a.corpus)
    questions = LOADERS[a.corpus]()
    t0 = time.perf_counter()
    tab = build_table(a.corpus, st, questions)
    nq = len(questions)
    groups_all = np.bincount(tab.rows_q, minlength=nq)
    # candidate ceiling
    exp_hit = [any(st.doc_ids[d] in q.expected for d in tab.rows_d[tab.rows_of(i)]) for i, q in enumerate(questions)]
    print(f"corpus {a.corpus}: {len(tab.y)} rows ({len(tab.y)/nq:.0f} docs/q), {len(tab.names)} features, "
          f"positives {int((tab.y == 1).sum())} (+{int((tab.y == 0.5).sum())} secondary); candidate recall "
          f"{np.mean(exp_hit):.3f}; built in {time.perf_counter()-t0:.0f}s", flush=True)
    summary = []
    for fset in a.fsets.split(","):
        X, names = select_features(tab, fset)
        print(f"\n=== feature set '{fset}': {len(names)} features", flush=True)
        for meth in a.methods.split(","):
            def fit(mask, meth=meth, X=X):
                qs = np.where(mask)[0]
                rows = np.isin(tab.rows_q, qs)
                # rows are grouped by question in table order
                order = np.argsort(tab.rows_q[rows], kind="stable")
                Xr, yr = X[rows][order], tab.y[rows][order]
                groups = [int(groups_all[q]) for q in sorted(qs)]
                return Model(meth, a.C).fit(Xr, yr, groups)

            def rank(model, qi, X=X):
                rows = tab.rows_of(qi)
                return tab.ranking(st, qi, model.predict(X[rows]))

            t1 = time.perf_counter()
            out = fold_report(f"ltr__{meth}__{fset}", a.corpus, questions, fit, rank,
                              describe=lambda m: {"method": m.kind, "C": a.C, "features": fset, "n_features": len(names)},
                              save=not a.no_save)
            m_tr, m_va, m_oof = out["fit-train"].metrics, out["fit-val"].metrics, out["oof"].metrics
            summary.append({"method": meth, "fset": fset, "train_resub": m_tr["train_mrr"], "val": m_tr["val_mrr"],
                            "val_resub": m_va["val_mrr"], "train_heldout": m_va["train_mrr"],
                            "oof_mrr": m_oof["mrr"], "oof_h1": m_oof["hit@1"], "oof_r10": m_oof["recall@10"],
                            "oof_ndcg5": m_oof["ndcg@5"], "seconds": round(time.perf_counter() - t1, 1)})
            masks = split_masks(questions)
            mdl = fit(masks["train"])
            imp = mdl.importance(names)[:8]
            print("    top features (fit-train): " + ", ".join(f"{n}={v:+.2f}" for n, v in imp), flush=True)
    (CACHE / f"{a.corpus}_ltr_summary.json").write_text(json.dumps(summary, indent=1))
    print("\nsummary (MRR): method / fset : train(resub) -> val | val(resub) -> train | oof-all")
    for s in summary:
        print(f"  {s['method']:16s} {s['fset']:13s} {s['train_resub']:.3f} -> {s['val']:.3f} | "
              f"{s['val_resub']:.3f} -> {s['train_heldout']:.3f} | {s['oof_mrr']:.3f} (H@1 {s['oof_h1']:.3f} R@10 {s['oof_r10']:.3f})")


if __name__ == "__main__":
    main()
