#!/usr/bin/env python3
"""Part 3 – learned ranker on real (mined) labels.

Fit on the mined TRAIN split, evaluate on (i) the mined VAL split (per source and pooled), (ii) the human
questions (true held-out; all and the val half that the round-1 bars were reported on); also the swapped fold
(fit on mined val → mined train) and a fit on all mined questions → human. Logistic regression first (C chosen
by 5-fold grouped CV on mined train, stability checked on random half-fits); LightGBM tiny (LambdaMART, 5-seed
bag) only when logreg is stable. Reranker features only on questions whose convex top-20 was scored in Part 2.
  uv run python ../21_mined_eval/train21.py --corpus B
"""
from __future__ import annotations

import argparse
import json
import time
import warnings

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

from rag_eval import evaluate_rankings
from common21 import (CACHE, PAIRED_HEADER, REFS, RUNS, LexStage1, Stage1, all_questions, fmt_paired, hit_at, load_ref,
                      load_saved, paired, recall_at, save21, short_metrics, slices, SOURCES)
from features21 import FEATURE_SETS, RERANK_TAGS, build_table, load_table, save_table, select_features

warnings.filterwarnings("ignore")
LGBM_TINY = dict(num_leaves=3, n_estimators=100, learning_rate=0.05, min_child_samples=10, reg_lambda=5.0,
                 subsample=0.8, subsample_freq=1, colsample_bytree=0.8, min_split_gain=0.0)
SEEDS = [0, 1, 2, 3, 4]
C_GRID = [0.03, 0.1, 0.3, 1.0, 3.0]


class Model:
    def __init__(self, kind: str, C: float = 0.3):
        self.kind, self.C = kind, C

    def fit(self, X, y, groups):
        if self.kind == "logreg":
            self.sc = StandardScaler().fit(X)
            self.m = LogisticRegression(C=self.C, max_iter=3000)
            self.m.fit(self.sc.transform(X), (y > 0).astype(int), sample_weight=np.where(y > 0, y, 1.0))
        else:
            import lightgbm as lgb
            self.ms = []
            lab = np.rint(2 * y).astype(int)
            for seed in SEEDS:
                m = lgb.LGBMRanker(objective="lambdarank", label_gain=[0, 1, 2], random_state=seed, verbose=-1, n_jobs=2, **LGBM_TINY)
                m.fit(X, lab, group=groups)
                self.ms.append(m)
        return self

    def predict(self, X):
        if self.kind == "logreg":
            return self.m.decision_function(self.sc.transform(X))
        return np.mean([m.predict(X) for m in self.ms], axis=0)

    def importance(self, names):
        if self.kind == "logreg":
            return sorted(zip(names, self.m.coef_[0]), key=lambda t: -abs(t[1]))
        imp = np.mean([m.booster_.feature_importance("gain") for m in self.ms], axis=0)
        return sorted(zip(names, imp / max(imp.sum(), 1e-9)), key=lambda t: -t[1])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", required=True, choices=["B", "C"])
    ap.add_argument("--fsets", default="cheap,minimal+meta,legs-only,cheap+mmarco,cheap+bge")
    ap.add_argument("--rebuild", action="store_true")
    ap.add_argument("--no-save", action="store_true")
    ap.add_argument("--force-lgbm", action="store_true")
    a = ap.parse_args()
    st = Stage1(a.corpus)
    questions = all_questions(a.corpus)
    assert [q.qid for q in questions] == st.qids
    lx = LexStage1(a.corpus, "exp13_lex")
    tf = CACHE / f"{a.corpus}_features.npz"
    t0 = time.perf_counter()
    if tf.exists() and not a.rebuild:
        tab = load_table(a.corpus, tf)
    else:
        tab = build_table(a.corpus, st, questions, lx)
        save_table(tab, tf)
    nq = len(questions)
    groups_all = np.bincount(tab.rows_q, minlength=nq)
    human = np.array([q.meta.get("source") is None for q in questions])
    mined = ~human
    split = np.array([q.split for q in questions])
    masks = {"human": human, "mined_train": mined & (split == "train"), "mined_val": mined & (split == "val"), "mined_all": mined}
    exp_hit = np.array([any(st.doc_ids[d] in q.expected for d in tab.rows_d[tab.rows_of(i)]) for i, q in enumerate(questions)])
    print(f"corpus {a.corpus}: {len(tab.y)} rows ({len(tab.y)/nq:.0f} docs/q), {len(tab.names)} features; candidate recall "
          f"human {exp_hit[human].mean():.3f} / mined {exp_hit[mined].mean():.3f}; table {time.perf_counter()-t0:.0f}s", flush=True)
    for rk, cov in tab.rerank_cov.items():
        print(f"  reranker {rk}: convex top-20 fully scored for {int(cov[human].sum())} human / {int(cov[mined].sum())} mined questions", flush=True)

    def fit_model(kind, fset, qmask, C=0.3):
        qs = np.where(qmask)[0]
        rows = np.isin(tab.rows_q, qs)
        order = np.argsort(tab.rows_q[rows], kind="stable")
        cols, names = select_features(tab, fset, rows)
        Xr, yr = tab.X[rows][order][:, cols], tab.y[rows][order]
        groups = [int(groups_all[q]) for q in sorted(qs)]
        return Model(kind, C).fit(Xr, yr, groups), cols, names

    def rank_all(model, cols, qmask):
        return {questions[qi].qid: tab.ranking(st, qi, model.predict(tab.X[tab.rows_of(qi)][:, cols])) for qi in np.where(qmask)[0]}

    def mrr_of(rankings, qmask):
        qs = [questions[i] for i in np.where(qmask)[0] if questions[i].qid in rankings]
        return evaluate_rankings("tmp", a.corpus, qs, rankings).metrics["mrr"] if qs else float("nan")

    def eval_save(name, rankings, config, qmask):
        """Evaluate on every slice restricted to qmask and the questions ranked; save; return metrics per slice."""
        out = {}
        qs_all = [questions[i] for i in np.where(qmask)[0] if questions[i].qid in rankings]
        for sl, qs in slices(qs_all).items():
            if not qs:
                continue
            res = evaluate_rankings(f"{sl}__{name}", a.corpus, qs, rankings, {**config, "questions": sl, "part": 3})
            res.metrics["recall@30"] = round(recall_at(qs, rankings, 30), 4)
            res.metrics["hit@30"] = round(hit_at(qs, rankings, 30), 4)
            if not a.no_save:
                save21(res, a.corpus, "human" if sl == "human" else "mined")
            out[sl] = short_metrics(res)
        return out

    summary = {"corpus": a.corpus, "n_rows": int(len(tab.y)), "candidate_recall": {"human": float(exp_hit[human].mean()), "mined": float(exp_hit[mined].mean())},
               "rerank_coverage": {k: {"human": int(v[human].sum()), "mined": int(v[mined].sum())} for k, v in tab.rerank_cov.items()},
               "models": {}}
    rng = np.random.default_rng(0)
    for fset in a.fsets.split(","):
        # eligible questions: for reranker feature sets only those with complete reranker scores
        elig = np.ones(nq, dtype=bool)
        for rk, tag in RERANK_TAGS.items():
            if tag in fset or fset == "all":
                if rk not in tab.rerank_cov:
                    elig[:] = False
                else:
                    elig &= tab.rerank_cov[rk]
        m_tr, m_va, m_hu, m_all = masks["mined_train"] & elig, masks["mined_val"] & elig, human & elig, mined & elig
        if m_tr.sum() < 20 or m_hu.sum() < 10:
            print(f"\n=== '{fset}': skipped (train {int(m_tr.sum())} q, human {int(m_hu.sum())} q eligible)", flush=True)
            summary["models"][fset] = {"skipped": True, "n_train": int(m_tr.sum()), "n_human": int(m_hu.sum())}
            continue
        print(f"\n=== feature set '{fset}': train {int(m_tr.sum())} / val {int(m_va.sum())} / human {int(m_hu.sum())} questions", flush=True)
        entry = {"n_train": int(m_tr.sum()), "n_val": int(m_va.sum()), "n_human": int(m_hu.sum()), "methods": {}}
        # ── logreg: C by 5-fold grouped CV on mined train ─────────────────────
        tr_q = np.where(m_tr)[0]
        folds = np.array_split(rng.permutation(tr_q), 5)
        cv = {}
        for C in C_GRID:
            rr = []
            for k in range(5):
                held = np.zeros(nq, dtype=bool); held[folds[k]] = True
                fitm = m_tr & ~held
                mdl, cols, _ = fit_model("logreg", fset, fitm, C)
                rr.append(mrr_of(rank_all(mdl, cols, held), held))
            cv[C] = float(np.mean(rr))
        bestC = max(C_GRID, key=lambda c: (cv[c], -c))
        print(f"  logreg CV on mined train (MRR): " + ", ".join(f"C={c}: {v:.3f}" for c, v in cv.items()) + f" → C={bestC}", flush=True)
        # stability: 6 random half-fits of mined train → val MRR, coefficient signs
        half_mrr, signs = [], []
        for s in range(6):
            r = np.random.default_rng(100 + s)
            pick = r.choice(tr_q, size=len(tr_q) // 2, replace=False)
            hm = np.zeros(nq, dtype=bool); hm[pick] = True
            mdl, cols, names = fit_model("logreg", fset, hm, bestC)
            half_mrr.append(mrr_of(rank_all(mdl, cols, m_va), m_va))
            signs.append(np.sign(mdl.m.coef_[0]))
        sign_agree = float(np.mean(np.abs(np.mean(signs, axis=0)) == 1.0)) if signs else 0.0
        stable = float(np.std(half_mrr)) <= 0.02
        print(f"  half-fit val MRR: mean {np.mean(half_mrr):.3f} sd {np.std(half_mrr):.3f} (range {min(half_mrr):.3f}–{max(half_mrr):.3f}); "
              f"coefficient sign agreement {sign_agree:.2f} → {'stable' if stable else 'unstable'}", flush=True)
        entry["logreg_cv"] = cv; entry["logreg_C"] = bestC
        entry["stability"] = {"half_fit_val_mrr": [round(x, 4) for x in half_mrr], "sd": round(float(np.std(half_mrr)), 4),
                              "sign_agreement": round(sign_agree, 3), "stable": stable}
        methods = ["logreg"] + (["lgbm-tiny"] if (stable or a.force_lgbm) else [])
        for meth in methods:
            t1 = time.perf_counter()
            res = {}
            # fit on mined train → mined val (honest), mined train (resub), human (held out)
            mdl, cols, names = fit_model(meth, fset, m_tr, bestC)
            rk = rank_all(mdl, cols, elig)
            cfg = {"method": meth, "features": fset, "n_features": len(names), "C": bestC if meth == "logreg" else None, "fit": "mined train"}
            res["fit-mtrain"] = eval_save(f"ltr__{meth}__{fset}__fit-mtrain", rk, cfg, elig)
            res["fit-mtrain"]["mined_val"] = short_metrics(evaluate_rankings("t", a.corpus, [questions[i] for i in np.where(m_va)[0]], rk))
            res["fit-mtrain"]["mined_val_by_src"] = {s: short_metrics(evaluate_rankings("t", a.corpus, qs, rk))
                                                     for s in SOURCES if (qs := [questions[i] for i in np.where(m_va)[0] if questions[i].meta.get("source") == s])}
            res["fit-mtrain"]["human_val"] = short_metrics(evaluate_rankings("t", a.corpus, [questions[i] for i in np.where(m_hu)[0] if questions[i].split == "val"], rk))
            imp = mdl.importance(names)[:10]
            res["fit-mtrain"]["top_features"] = [(n, round(float(v), 3)) for n, v in imp]
            # swapped fold: fit on mined val → mined train (honest)
            mdl2, cols2, _ = fit_model(meth, fset, m_va, bestC)
            rk2 = rank_all(mdl2, cols2, elig)
            res["fit-mval"] = eval_save(f"ltr__{meth}__{fset}__fit-mval", rk2, {**cfg, "fit": "mined val"}, elig)
            res["fit-mval"]["mined_train"] = short_metrics(evaluate_rankings("t", a.corpus, [questions[i] for i in np.where(m_tr)[0]], rk2))
            # oof over the mined set (val from fit-mtrain, train from fit-mval)
            oof = {questions[i].qid: (rk if questions[i].split == "val" else rk2)[questions[i].qid] for i in np.where(m_all)[0]}
            res["oof-mined"] = eval_save(f"ltr__{meth}__{fset}__oof-mined", oof, {**cfg, "fit": "2-fold oof over mined"}, m_all)
            # fit on all mined → human
            mdl3, cols3, _ = fit_model(meth, fset, m_all, bestC)
            rk3 = rank_all(mdl3, cols3, elig)
            res["fit-mall"] = eval_save(f"ltr__{meth}__{fset}__fit-mall", rk3, {**cfg, "fit": "all mined (mined slices are resubstitution)"}, elig)
            res["fit-mall"]["human_val"] = short_metrics(evaluate_rankings("t", a.corpus, [questions[i] for i in np.where(m_hu)[0] if questions[i].split == "val"], rk3))
            res["seconds"] = round(time.perf_counter() - t1, 1)
            entry["methods"][meth] = res
            f1, fv, fm = res["fit-mtrain"], res["fit-mval"], res["fit-mall"]
            print(f"  {meth:10s} fit-mtrain: mined val {f1['mined_val']['mrr']:.3f} (" +
                  ", ".join(f"{s} {m['mrr']:.3f}" for s, m in f1["mined_val_by_src"].items()) +
                  f") | train resub {f1['mined']['train_mrr']:.3f} | human all {f1['human']['mrr']:.3f} val {f1['human_val']['mrr']:.3f} || "
                  f"fit-mval → train {fv['mined_train']['mrr']:.3f} | oof-mined {res['oof-mined']['mined']['mrr']:.3f} || "
                  f"fit-mall → human all {fm['human']['mrr']:.3f} val {fm['human_val']['mrr']:.3f}", flush=True)
            print("    top features: " + ", ".join(f"{n}={v:+.2f}" for n, v in imp[:8]), flush=True)
        summary["models"][fset] = entry

    # ── paired tests ───────────────────────────────────────────────────────────
    tests = {"human": {}, "mined_val": {}}
    refs = {k: load_ref(a.corpus, k) for k in REFS[a.corpus]}
    base_runs = {n: load_saved(f"human__{n}", a.corpus) for n in ("convex05", "rrf60", "exp13_lex", "bm25_tok01")}
    for extra in ("convex05+bge@20", "convex05+mmarco@20", "lex13+bge@20"):
        try:
            base_runs[extra] = load_saved(f"human__{extra}", a.corpus)
        except FileNotFoundError:
            pass
    for fset, entry in summary["models"].items():
        if entry.get("skipped"):
            continue
        for meth in entry["methods"]:
            for fit in ("fit-mtrain", "fit-mall"):
                name = f"ltr__{meth}__{fset}__{fit}"
                run = load_saved(f"human__{name}", a.corpus)
                row = {}
                for k, ref in refs.items():
                    row[f"vs {k} (all)"] = paired(ref, run)
                    row[f"vs {k} (val)"] = paired(ref, run, split="val")
                for k, ref in base_runs.items():
                    row[f"vs {k} (all)"] = paired(ref, run)
                tests["human"][name] = row
            name = f"ltr__{meth}__{fset}__fit-mtrain"
            run = load_saved(f"mined__{name}", a.corpus)
            row = {}
            for k in ("convex05", "rrf60", "exp13_lex", "bm25_tok01"):
                ref = load_saved(f"mined__{k}", a.corpus)
                row[f"vs {k} (val, pooled)"] = paired(ref, run, split="val")
                for s in SOURCES:
                    try:
                        ref_s = load_saved(f"mined__src_{s}__{k}", a.corpus)
                        run_s = load_saved(f"mined__src_{s}__{name}", a.corpus)
                    except FileNotFoundError:
                        continue
                    if len(set(ref_s["per_question"]) & set(run_s["per_question"])) >= 5:
                        row[f"vs {k} (val, {s})"] = paired(ref_s, run_s, split="val")
            for k in ("convex05+bge@20", "convex05+mmarco@20", "lex13+bge@20"):
                try:
                    ref = load_saved(f"sub__{k}", a.corpus)
                except FileNotFoundError:
                    continue
                row[f"vs {k} (subsample ∩ val)"] = paired(ref, run, split="val")
            tests["mined_val"][name] = row
    summary["tests"] = tests
    (RUNS / f"part3_{a.corpus}.json").write_text(json.dumps(summary, indent=1, default=float))

    # ── markdown ────────────────────────────────────────────────────────────
    L = [f"### Part 3 – corpus {a.corpus}: learned ranker trained on mined labels", "",
         "| features | method | C | n train | mined val MRR (H@1 / R@10) | per source (val) | train resub | swapped: val→train | oof mined | human all MRR (H@1 / R@10) | human val | fit-all-mined → human all / val | half-fit val sd |",
         "|---|---|--:|--:|---|---|--:|--:|--:|---|--:|---|--:|"]
    for fset, entry in summary["models"].items():
        if entry.get("skipped"):
            L.append(f"| {fset} | – | | {entry['n_train']} | skipped (not enough scored questions) | | | | | | | | |"); continue
        for meth, r in entry["methods"].items():
            f1, fv, fm = r["fit-mtrain"], r["fit-mval"], r["fit-mall"]
            mv, hu = f1["mined_val"], f1["human"]
            L.append(f"| {fset} | {meth} | {entry['logreg_C'] if meth == 'logreg' else '–'} | {entry['n_train']} | "
                     f"**{mv['mrr']:.3f}** ({mv['hit@1']:.3f} / {mv['recall@10']:.3f}) | "
                     + ", ".join(f"{s} {m['mrr']:.3f}" for s, m in f1["mined_val_by_src"].items()) +
                     f" | {f1['mined']['train_mrr']:.3f} | {fv['mined_train']['mrr']:.3f} | {r['oof-mined']['mined']['mrr']:.3f} | "
                     f"**{hu['mrr']:.3f}** ({hu['hit@1']:.3f} / {hu['recall@10']:.3f}) | {f1['human_val']['mrr']:.3f} | "
                     f"{fm['human']['mrr']:.3f} / {fm['human_val']['mrr']:.3f} | {entry['stability']['sd']:.3f} |")
    L += ["", "Top features (fit on mined train):", ""]
    for fset, entry in summary["models"].items():
        for meth, r in entry.get("methods", {}).items():
            L.append(f"* `{fset}` / {meth}: " + ", ".join(f"{n} {v:+.2f}" for n, v in r["fit-mtrain"]["top_features"][:8]))
    L += ["", "**Human sets – paired tests (Δ = LTR − reference)**", "", "| LTR run | reference " + PAIRED_HEADER[1:], "|---|---|:--|--:|--:|:--|--:|--:|"]
    for name, row in tests["human"].items():
        for k, t in row.items():
            L.append(f"| {name} | {k} (n={t['n']}) | {fmt_paired(t)} |")
    L += ["", "**Mined val split – paired tests (Δ = LTR − reference)**", "", "| LTR run | reference " + PAIRED_HEADER[1:], "|---|---|:--|--:|--:|:--|--:|--:|"]
    for name, row in tests["mined_val"].items():
        for k, t in row.items():
            L.append(f"| {name} | {k} (n={t['n']}) | {fmt_paired(t)} |")
    (RUNS / f"part3_{a.corpus}.md").write_text("\n".join(L) + "\n")
    print("\n".join(L[:12]))


if __name__ == "__main__":
    main()
