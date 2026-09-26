#!/usr/bin/env python3
"""Part 3 – exp-14-style logistic ranker over cheap features + the three leg scores, trained on the mined TRAIN
split (145 questions, leak-free reception), tested on the mined VAL split (159), on the swapped fold (→ 2-fold
oof over the 304) and on the 40 human questions (true held-out; never used for any fit or selection).
Minimal re-implementation of 14_ltr_fusion/features.py + train_ltr.py (exp 21's feature cache did not exist yet).

  ../14_ltr_fusion/.venv/bin/python ltr.py   → runs/ltr.json, runs/ltr_tables.md
"""
from __future__ import annotations

import argparse
import json
import math
import re
import warnings

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GroupKFold
from sklearn.preprocessing import StandardScaler

from common22 import (EXP14, FUSIONS, HUMAN_HEAD, LEGS, MINED_HEAD, PAIRED_HEAD, REFS_HUMAN, RUNS, SLICES, evaluate_save, fmt_human,
                      fmt_mined, fmt_paired, fuse_z, load_legs, paired, questions_human, questions_mined, rankings_from, ranks_of,
                      ranks_of_file, slice_metrics, split_metrics, zscore)
from common14 import tokenize, ranks_of as rank_all  # noqa: E402
from features import doc_meta  # noqa: E402  (14_ltr_fusion; cached B_docmeta.json)
from cleanup import detect_region  # noqa: E402

warnings.filterwarnings("ignore")
TOP = 50
C_GRID = (0.01, 0.03, 0.1, 0.3, 1.0, 3.0)
FSETS = {"legs": lambda n: not n.startswith("meta:"), "cheap": lambda n: True}


def build(questions, legs: dict, fused: np.ndarray, doc_ids, doc_start, meta, title_toks, types):
    """Rows (question, candidate article): candidates = top-50 of every leg ∪ top-50 fused, minus `exclude`."""
    names = []
    for lg in LEGS:
        names += [f"{lg}_z", f"{lg}_logrank", f"{lg}_top30"]
    names += ["rec_positive", "fused_z", "fused_logrank", "n_legs_top30"]
    names += ["meta:log_doc_len", "meta:log_n_chunks", "meta:title_overlap", "meta:title_overlap_n", "meta:q_has_region",
              "meta:region_match", "meta:region_mismatch"] + [f"meta:type={t}" for t in types]
    rows_q, rows_d, X, y, tails = [], [], [], [], []
    doc_len = np.array([m["_len"] for m in meta])
    n_chunks = np.diff(doc_start)
    for qi, q in enumerate(questions):
        zs = {lg: zscore(legs[lg][qi]) for lg in LEGS}
        rk = {lg: rank_all(legs[lg][qi]) for lg in LEGS}
        fz, frk = zscore(fused[qi]), rank_all(fused[qi])
        excl = set(q.meta.get("exclude") or [])
        cand = set()
        for v in list(legs.values()) + [fused]:
            cand.update(np.argpartition(-v[qi], TOP)[:TOP].tolist())
        cand = sorted(d for d in cand if doc_ids[d] not in excl)
        tails.append([int(d) for d in np.argsort(-fused[qi], kind="stable")[:80] if doc_ids[d] not in excl])
        q_region = detect_region(q.question)
        qtoks = set(tokenize(q.question))
        exp, sec = set(q.expected), set(q.secondary)
        for d in cand:
            f = []
            ntop = 0
            for lg in LEGS:
                r = int(rk[lg][d]); f += [zs[lg][d], math.log1p(r), float(r <= 30)]; ntop += int(r <= 30)
            f += [float(legs["rec"][qi][d] > 0), fz[d], math.log1p(int(frk[d])), float(ntop)]
            m = meta[d]
            ov = len(qtoks & title_toks[d])
            reg = m["region"]
            f += [math.log1p(doc_len[d]), math.log1p(int(n_chunks[d])), ov / max(1, len(qtoks)), float(ov), float(q_region is not None),
                  float(q_region is not None and reg is not None and q_region in reg.split(",")),
                  float(q_region is not None and reg is not None and reg != "fed" and q_region not in reg.split(","))]
            f += [float(m["type"] == t) for t in types]
            rows_q.append(qi); rows_d.append(int(d)); X.append(f)
            y.append(1.0 if doc_ids[d] in exp else (0.5 if doc_ids[d] in sec else 0.0))
    X = np.asarray(X, dtype=np.float64)
    assert X.shape[1] == len(names)
    return np.asarray(rows_q), np.asarray(rows_d), X, np.asarray(y), names, tails


class Table:
    def __init__(self, questions, rows_q, rows_d, X, y, names, tails):
        self.questions, self.rows_q, self.rows_d, self.X, self.y, self.names, self.tails = questions, rows_q, rows_d, X, y, names, tails
        self.by_q = {qi: np.where(rows_q == qi)[0] for qi in range(len(questions))}


def fit(X, y, C):
    sc = StandardScaler().fit(X)
    m = LogisticRegression(C=C, max_iter=3000).fit(sc.transform(X), (y > 0).astype(int), sample_weight=np.where(y > 0, y, 1.0))
    return sc, m


def rank_table(tab: Table, cols, model, doc_ids, qis) -> dict:
    sc, m = model
    out = {}
    for qi in qis:
        rows = tab.by_q[qi]
        s = m.decision_function(sc.transform(tab.X[rows][:, cols]))
        order = rows[np.argsort(-s, kind="stable")]
        ranked = [int(tab.rows_d[r]) for r in order]
        seen = set(ranked)
        ranked += [d for d in tab.tails[qi] if d not in seen]
        out[tab.questions[qi].qid] = [doc_ids[d] for d in ranked[:60]]
    return out


def mrr_of(questions, rankings) -> float:
    from rag_eval import evaluate_rankings
    return evaluate_rankings("tmp", "B", questions, rankings).metrics["mrr"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-save", action="store_true")
    a = ap.parse_args()
    L = load_legs()
    z, doc_ids = L["z"], L["doc_ids"]
    doc_start = z["doc_start"]
    st = json.loads((RUNS / "stage1.json").read_text())
    selected = st["selected"]
    human, mined = questions_human(), questions_mined()
    nh = len(human)
    meta = doc_meta("B")
    docs_len = json.loads((EXP14 / "cache" / "B_stage1.json").read_text())["doc_len"]
    for m, l in zip(meta, docs_len):
        m["_len"] = l
    title_toks = [set(tokenize(m["title"])) for m in meta]
    tc = {}
    for m in meta:
        tc[m["type"]] = tc.get(m["type"], 0) + 1
    types = sorted(t for t, c in tc.items() if c >= 5)
    tabs = {}
    for w, qs, rows in (("human", human, slice(0, nh)), ("mined", mined, slice(nh, None))):
        legs = {"rec": z["rec_human"] if w == "human" else z["rec_mined"], "colbert": z["colbert_doc"][rows], "e5": z["e5_doc"][rows]}
        fused = fuse_z(legs, FUSIONS[selected])
        tabs[w] = Table(qs, *build(qs, legs, fused, doc_ids, doc_start, meta, title_toks, types))
        cov = np.mean([any(doc_ids[int(d)] in q.expected for d in tabs[w].rows_d[tabs[w].by_q[i]]) for i, q in enumerate(qs)])
        print(f"[{w}] {len(tabs[w].y)} rows ({len(tabs[w].y) / len(qs):.0f} docs/q), {len(tabs[w].names)} features, candidate recall {cov:.3f}", flush=True)
    mt = tabs["mined"]
    m_train = [i for i, q in enumerate(mined) if q.split == "train"]
    m_val = [i for i, q in enumerate(mined) if q.split == "val"]
    m_all = list(range(len(mined)))
    h_all = list(range(nh))

    def rows_of(qis):
        return np.where(np.isin(mt.rows_q, qis))[0]

    def select_C(qis, cols) -> tuple[float, dict]:
        """5-fold grouped CV on the mined train questions, metric = held-out MRR."""
        qis = np.array(qis)
        scores = {}
        for C in C_GRID:
            accs = []
            for tr, te in GroupKFold(5).split(qis, groups=qis):
                r = rows_of(qis[tr])
                model = fit(mt.X[r][:, cols], mt.y[r], C)
                rk = rank_table(mt, cols, model, doc_ids, qis[te])
                accs.append(mrr_of([mined[i] for i in qis[te]], rk))
            scores[C] = float(np.mean(accs))
        best = max(C_GRID, key=lambda c: (round(scores[c], 4), -abs(math.log10(c) + 0.5)))
        return best, scores

    results = {"human": {}, "mined": {}}
    refs = {k: {"label": v[1], "ranks": ranks_of_file(v[0])} for k, v in REFS_HUMAN.items() if v[0].exists()}
    sel1_h = st["per_question"]["human"]; sel1_m = st["per_question"]["mined"]
    stage1_h = {q: v[selected] for q, v in sel1_h.items()}; stage1_m = {q: v[selected] for q, v in sel1_m.items()}
    summary = {"selected_first_stage": selected, "fsets": {}}
    for fset, pred in FSETS.items():
        cols = [i for i, n in enumerate(mt.names) if pred(n) and mt.X[:, i].std() > 0]
        names = [mt.names[i] for i in cols]
        C, cv = select_C(m_train, cols)
        print(f"\n=== feature set '{fset}' ({len(cols)} features): C = {C} (grouped 5-fold CV on mined train: " + ", ".join(f"{c}: {v:.3f}" for c, v in cv.items()) + ")", flush=True)
        fits = {"fit-mtrain": m_train, "fit-mval": m_val, "fit-mall": m_all}
        models = {}
        for fname, qis in fits.items():
            r = rows_of(qis)
            models[fname] = fit(mt.X[r][:, cols], mt.y[r], C)
        # mined: held-out halves + oof
        rk_val = rank_table(mt, cols, models["fit-mtrain"], doc_ids, m_val)
        rk_tr = rank_table(mt, cols, models["fit-mval"], doc_ids, m_train)
        rk_resub = rank_table(mt, cols, models["fit-mtrain"], doc_ids, m_train)
        cfg = {"method": "logreg", "C": C, "features": fset, "n_features": len(cols), "first_stage_for_candidates": selected, "reception": "leak-free on mined"}
        res_val = evaluate_save(f"ltr__{fset}__fit-mtrain__minedval", [mined[i] for i in m_val], rk_val, {**cfg, "fit": "mined train (145)", "eval": "mined val (159)"}, "mined", save=not a.no_save)
        res_oof = evaluate_save(f"ltr__{fset}__oof", mined, {**rk_val, **rk_tr}, {**cfg, "fit": "2-fold over the mined set", "eval": "held-out halves merged"}, "mined", save=not a.no_save)
        rk_h = {fn: rank_table(tabs["human"], cols, models[fn], doc_ids, h_all) for fn in ("fit-mtrain", "fit-mall")}
        res_h = {fn: evaluate_save(f"ltr__{fset}__{fn}", human, rk_h[fn], {**cfg, "fit": fn, "eval": "human 40 (held out)"}, "human", save=not a.no_save) for fn in rk_h}
        # stability: six random half-fits of the mined train half → sd of the mined-val MRR, coefficient signs
        rng = np.random.default_rng(22)
        half_mrr, signs = [], []
        for _ in range(6):
            sub = rng.choice(m_train, size=len(m_train) // 2, replace=False)
            r = rows_of(sub)
            mdl = fit(mt.X[r][:, cols], mt.y[r], C)
            half_mrr.append(mrr_of([mined[i] for i in m_val], rank_table(mt, cols, mdl, doc_ids, m_val)))
            signs.append(np.sign(mdl[1].coef_[0]))
        agree = float(np.mean(np.abs(np.mean(signs, axis=0))))
        coef = sorted(zip(names, models["fit-mtrain"][1].coef_[0]), key=lambda t: -abs(t[1]))
        m_val_q = [mined[i] for i in m_val]
        out = {"C": C, "cv": cv, "n_features": len(cols),
               "mined_val": slice_metrics(ranks_of(res_val), m_val_q), "mined_train_resub": slice_metrics(ranks_of(evaluate_save("tmp", [mined[i] for i in m_train], rk_resub, {}, "mined", save=False)), [mined[i] for i in m_train]),
               "mined_oof": slice_metrics(ranks_of(res_oof), mined),
               "human": {fn: split_metrics(ranks_of(res_h[fn]), human) for fn in res_h},
               "stability": {"half_fit_val_mrr": half_mrr, "sd": float(np.std(half_mrr)), "coef_sign_agreement": agree},
               "coef_fit_mtrain": [(n, round(float(c), 3)) for n, c in coef]}
        summary["fsets"][fset] = out
        results["mined"][f"ltr__{fset}__oof"] = ranks_of(res_oof)
        results["mined"][f"ltr__{fset}__fit-mtrain__minedval"] = ranks_of(res_val)
        for fn in res_h:
            results["human"][f"ltr__{fset}__{fn}"] = ranks_of(res_h[fn])
        print(f"  mined val {out['mined_val']['all']['mrr']:.3f} (train resub {out['mined_train_resub']['all']['mrr']:.3f}); oof {out['mined_oof']['all']['mrr']:.3f} | "
              f"human fit-mtrain val {out['human']['fit-mtrain']['val']['mrr']:.3f} all {out['human']['fit-mtrain']['all']['mrr']:.3f}; fit-mall val {out['human']['fit-mall']['val']['mrr']:.3f} all {out['human']['fit-mall']['all']['mrr']:.3f} | "
              f"half-fit sd {out['stability']['sd']:.3f}, sign agreement {agree:.2f}", flush=True)
        print("  top coefficients: " + ", ".join(f"{n}={c:+.2f}" for n, c in coef[:8]), flush=True)

    # ── tests ────────────────────────────────────────────────────────────────
    tests = {"human": {}, "mined": {}}
    hq = {"val": [q.qid for q in human if q.split == "val"], "train": [q.qid for q in human if q.split == "train"], "all": [q.qid for q in human]}
    for name, rk in results["human"].items():
        for g, qids in hq.items():
            tests["human"][f"{name} vs {selected} first stage [{g}]"] = paired(stage1_h, rk, qids)
            for r_ in ("bar", "r2_best", "exp14_oof"):
                tests["human"][f"{name} vs {refs[r_]['label']} [{g}]"] = paired(refs[r_]["ranks"], rk, qids)
    mq = {"all": [q.qid for q in mined], "val": [q.qid for q in mined if q.split == "val"], "train": [q.qid for q in mined if q.split == "train"]}
    mq.update({sl: [q.qid for q in mined if q.meta.get("source") == sl] for sl in SLICES if sl != "faq"})
    rr_ = RUNS / "rerank.json"
    rer = json.loads(rr_.read_text()) if rr_.exists() else None
    for fset in FSETS:
        for g, qids in mq.items():
            tests["mined"][f"ltr__{fset}__oof vs {selected} first stage [{g}]"] = paired(stage1_m, results["mined"][f"ltr__{fset}__oof"], qids)
        for g in ("val", "pq", "ruling"):
            qids = [q for q in mq[g] if q in results["mined"][f"ltr__{fset}__fit-mtrain__minedval"]]
            tests["mined"][f"ltr__{fset}__fit-mtrain vs {selected} first stage [mined val ∩ {g}]"] = paired(stage1_m, results["mined"][f"ltr__{fset}__fit-mtrain__minedval"], qids)
    tests["mined"]["ltr__cheap__oof vs ltr__legs__oof [all]"] = paired(results["mined"]["ltr__legs__oof"], results["mined"]["ltr__cheap__oof"], mq["all"])
    summary["tests"] = tests
    (RUNS / "ltr.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1, default=str))

    T = ["### Corpus B – logistic ranker trained on the mined train split, human questions (true held-out)", "", *HUMAN_HEAD]
    for k in ("bar", "r2_best", "exp14_oof"):
        T.append(fmt_human(f"ref – {refs[k]['label']}", split_metrics(refs[k]["ranks"], human)))
    T.append(fmt_human(f"{selected} first stage (this experiment)", split_metrics(stage1_h, human)))
    for fset in FSETS:
        for fn in ("fit-mtrain", "fit-mall"):
            T.append(fmt_human(f"ltr__{fset}__{fn} (C {summary['fsets'][fset]['C']}, {summary['fsets'][fset]['n_features']} features)", summary["fsets"][fset]["human"][fn]))
    T += ["", "### Mined questions (fit on the mined train half, evaluated on the mined val half; oof = both held-out halves)", "", *MINED_HEAD]
    T.append(fmt_mined(f"{selected} first stage", slice_metrics(stage1_m, mined)))
    for fset in FSETS:
        T.append(fmt_mined(f"ltr__{fset}__oof", summary["fsets"][fset]["mined_oof"]))
        mv = summary["fsets"][fset]["mined_val"]
        T.append(f"| ltr__{fset}__fit-mtrain → mined val only | – | {mv['pq']['mrr']:.3f} / {mv['pq']['hit@1']:.3f} / {mv['pq']['recall@10']:.3f} / {mv['pq']['recall@30']:.3f} | "
                 f"{mv['ruling']['mrr']:.3f} / {mv['ruling']['hit@1']:.3f} / {mv['ruling']['recall@10']:.3f} / {mv['ruling']['recall@30']:.3f} | – | (resub {summary['fsets'][fset]['mined_train_resub']['all']['mrr']:.3f}) | {mv['all']['mrr']:.3f} / {mv['all']['hit@1']:.3f} / {mv['all']['recall@10']:.3f} / {mv['all']['recall@30']:.3f} |")
    for fset in FSETS:
        s = summary["fsets"][fset]
        T += ["", f"`{fset}`: C = {s['C']} (CV " + ", ".join(f"{c}: {v:.3f}" for c, v in s["cv"].items()) + f"); half-fit val MRR sd {s['stability']['sd']:.3f}, coefficient sign agreement {s['stability']['coef_sign_agreement']:.2f}; "
              "top coefficients: " + ", ".join(f"{n} {c:+.2f}" for n, c in s["coef_fit_mtrain"][:10])]
    for w in ("human", "mined"):
        T += ["", f"Paired tests, {w}:", "", *PAIRED_HEAD]
        for k, t in tests[w].items():
            T.append(fmt_paired(k, t))
    (RUNS / "ltr_tables.md").write_text("\n".join(T) + "\n")
    print("\n".join(T[:22]), flush=True)


if __name__ == "__main__":
    main()
