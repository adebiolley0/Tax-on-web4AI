#!/usr/bin/env python3
"""First-stage variants of experiment 20 on the mined question sets (rag_eval.load_questions_mined:
B 304 / C 697 questions with `source` slices pq / ruling / faq). No reranking. Leakage control:

* corpus B: the reception field is rebuilt without any sentence from a mined question's source document
  (cache/B_reception_nomined.json, reception.py --exclude-mined), because the mined labels are the
  articles cited in those very answers / objets;
* corpus C: bank entries whose source document is a mined question's source_doc are removed from the
  bank before scoring (the number is reported).

Configurations are the ones selected on the *human train split* (runs/B_stage1.json, runs/C_stage1.json);
the whole grid is reported for information, nothing is re-selected on the mined sets. Paired statistics
with rag_eval.stats.paired_stats (delta = variant − baseline) on the whole set and per source slice.

  ../14_ltr_fusion/.venv/bin/python run_mined.py --corpus B     (needs cache/B_mined_q_e5.npy: embed.py --what mined)
  ../14_ltr_fusion/.venv/bin/python run_mined.py --corpus C
"""
from __future__ import annotations

import argparse
import itertools
import json
import re
import time

import numpy as np

from common20 import CACHE, EXP, EXPS, RUNS, minmax
from rag_eval import evaluate_rankings, save_result, load_questions_mined
from rag_eval.cache import EmbeddingCache, _key
from rag_eval.stats import paired_stats
from lexical import Tokenizer, TokenStore, build_index, bm25f_matrix, scores_for, REGION_TOKEN  # noqa: E402
from run_exp13 import load_corpus, tokenize_corpus, query_weights  # noqa: E402
from common17 import LEX_CONFIG, b_code_cues  # noqa: E402
from cleanup import region_of_code  # noqa: E402
from models import MODELS  # noqa: E402

SLICES = ("pq", "ruling", "faq")


def slice_metrics(ranks: dict, questions) -> dict:
    out = {}
    for sl in ("all",) + SLICES + ("train", "val"):
        qs = [q for q in questions if sl == "all" or q.meta.get("source") == sl or q.split == sl]
        if not qs:
            continue
        rr = [1.0 / ranks[q.qid] if ranks.get(q.qid) else 0.0 for q in qs]
        out[sl] = {"n": len(qs), "mrr": float(np.mean(rr)),
                   "hit@1": float(np.mean([1.0 if ranks.get(q.qid) == 1 else 0.0 for q in qs])),
                   "recall@10": float(np.mean([1.0 if ranks.get(q.qid) and ranks[q.qid] <= 10 else 0.0 for q in qs])),
                   "recall@30": float(np.mean([1.0 if ranks.get(q.qid) and ranks[q.qid] <= 30 else 0.0 for q in qs]))}
    return out


def paired(ranks_a: dict, ranks_b: dict, questions, sl: str) -> dict:
    qs = [q for q in questions if sl == "all" or q.meta.get("source") == sl]
    if len(qs) < 3:
        return {"n": len(qs)}
    ra = np.array([1.0 / ranks_a[q.qid] if ranks_a.get(q.qid) else 0.0 for q in qs])
    rb = np.array([1.0 / ranks_b[q.qid] if ranks_b.get(q.qid) else 0.0 for q in qs])
    p = paired_stats(ra, rb, "rr")
    h = paired_stats((np.array([ranks_a.get(q.qid) or 10**9 for q in qs]) <= 10).astype(float),
                     (np.array([ranks_b.get(q.qid) or 10**9 for q in qs]) <= 10).astype(float), "hit@10")
    return {"n": p.n, "mrr_a": p.mean_a, "mrr_b": p.mean_b, "delta": p.delta, "ci": [p.ci_lo, p.ci_hi], "p_t": p.p_t, "p_perm": p.p_perm,
            "wins": p.wins, "losses": p.losses, "ties": p.ties, "effect": p.effect_size, "delta_hit10": h.delta, "p_t_hit10": h.p_t}


def fmt(label: str, m: dict) -> str:
    cells = []
    for sl in ("all",) + SLICES:
        d = m.get(sl)
        cells.append(f"{d['mrr']:.3f} / {d['hit@1']:.3f} / {d['recall@10']:.3f} / {d['recall@30']:.3f}" if d else "–")
    return f"| {label} | " + " | ".join(cells) + " |"


def fmt_p(label: str, t: dict) -> str:
    if "delta" not in t:
        return f"| {label} | n={t['n']} | – | – | – | – |"
    return (f"| {label} | {t['n']} | {t['mrr_a']:.3f} → {t['mrr_b']:.3f} | {t['delta']:+.3f} [{t['ci'][0]:+.3f}, {t['ci'][1]:+.3f}] | "
            f"{t['p_t']:.3f} / {t['p_perm']:.3f} | {t['wins']} / {t['losses']} / {t['ties']} | {t['delta_hit10']:+.3f} ({t['p_t_hit10']:.3f}) |")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", required=True, choices=["B", "C"])
    ap.add_argument("--no-save", action="store_true")
    a = ap.parse_args()
    questions = load_questions_mined(a.corpus)
    qids = [q.qid for q in questions]
    qm = json.loads((CACHE / f"{a.corpus}_mined_q_e5.json").read_text())
    assert qm["qids"] == qids
    q_e5 = np.load(CACHE / f"{a.corpus}_mined_q_e5.npy")
    nq = len(questions)
    cfg = LEX_CONFIG[a.corpus]
    tok = Tokenizer(**cfg["tokenizer"])
    C = load_corpus(a.corpus, cfg["clean_b"])
    doc_ids = [d.doc_id for d in C.docs]
    doc_index = {d: i for i, d in enumerate(doc_ids)}
    unit_doc_idx = np.array([doc_index[d] for d in C.unit_doc], dtype=np.int64)
    n_docs, n_units = len(doc_ids), len(unit_doc_idx)
    starts = np.flatnonzero(np.r_[True, unit_doc_idx[1:] != unit_doc_idx[:-1]])
    print(f"corpus {a.corpus} mined: {nq} questions ({dict((s, sum(1 for q in questions if q.meta.get('source') == s)) for s in SLICES)}); "
          f"{n_docs} docs / {n_units} units", flush=True)
    results: dict[str, dict] = {}
    notes: dict = {}

    def run(name: str, doc_scores: np.ndarray, config: dict, positive_only: bool = False):
        rk = {}
        for i, q in enumerate(questions):
            order = np.argsort(-doc_scores[i], kind="stable")[:60]
            rk[q.qid] = [doc_ids[j] for j in order if (doc_scores[i][j] > 0 or not positive_only)]
        res = evaluate_rankings(name + "__mined", a.corpus, questions, rk, {**config, "question_set": f"mined {a.corpus} ({nq})"}, {})
        if not a.no_save:
            save_result(EXP, res)
        ranks = {qid: v["rank"] for qid, v in res.per_question.items()}
        m = slice_metrics(ranks, questions)
        results[name] = {"ranks": ranks, "metrics": m}
        print(f"  {name:40s} all {m['all']['mrr']:.3f} | " + " ".join(f"{s} {m[s]['mrr']:.3f}" for s in SLICES if s in m)
              + f" | R@30 all {m['all']['recall@30']:.3f}", flush=True)

    if a.corpus == "B":
        store = tokenize_corpus(C, tok, cfg["clean_b"])
        cue_tokens = []
        for u in range(store.n):
            code = C.unit_meta[u].get("code", "")
            toks = [REGION_TOKEN[r] for r in region_of_code(code).split(",") if r in REGION_TOKEN]
            toks.append("dt" + re.sub(r"_(wal|bxl|vla)$", "", code))
            cue_tokens.append(toks)
        store.add_field("cue", cue_tokens)
        rec_all = json.loads((CACHE / "B_reception.json").read_text())
        rec = json.loads((CACHE / "B_reception_nomined.json").read_text())
        notes["reception"] = {"sentences_full": rec_all["stats"]["sentences_kept"], "sentences_leak_free": rec["stats"]["sentences_kept"],
                              "articles_full": rec_all["stats"]["articles_with_reception"], "articles_leak_free": rec["stats"]["articles_with_reception"],
                              "excluded_source_docs": rec["stats"]["excluded_source_docs"], "docs_actually_skipped": rec["stats"]["docs_excluded_mined_source"]}
        rec = rec["articles"]
        for name, with_titles in (("sent", False), ("sent+title", True)):
            per_art = {art: tok("\n".join(s["t"] for s in v["sentences"]) + ("\n" + "\n".join(v["titles"]) if with_titles else "")) for art, v in rec.items()}
            store.add_field(f"rec_{name}", [per_art.get(C.unit_doc[u], []) for u in range(store.n)])
        # e5 leg: cached exp-14 chunk embeddings (article_ctx_1200, raw articles) · mined query embeddings
        from common14 import load_corpus_and_chunks  # noqa: E402
        docs14, _, chunks14, _ = load_corpus_and_chunks("B")
        assert [d.doc_id for d in docs14] == doc_ids
        spec = MODELS["e5-small"]
        emb = np.load(EmbeddingCache().dir / (_key(spec.hf_id, [c.text for c in chunks14], "seq512|d_prefix='passage: '|article_ctx_1200") + ".npy"))
        chunk_doc14 = np.array([doc_index[c.doc_id] for c in chunks14])
        sims = q_e5 @ emb.T
        e5_doc = np.full((nq, n_docs), -1.0)
        for i in range(nq):
            np.maximum.at(e5_doc[i], chunk_doc14, sims[i].astype(np.float64))
        del emb, sims

        def lexical(fields_w: dict, b: dict) -> np.ndarray:
            fields = [f for f in fields_w if fields_w[f] > 0]
            index = build_index(store, fields)
            M = bm25f_matrix(index, {f: fields_w[f] for f in fields}, k1=cfg["k1"], b={**cfg["b"], **b})
            out = np.zeros((nq, n_docs))
            for i, q in enumerate(questions):
                w = query_weights(index, tok, q.question)
                for dt in b_code_cues(q.question):
                    w[dt] = w.get(dt, 0) + cfg["doctype_w"]
                np.maximum.at(out[i], unit_doc_idx, scores_for(M, index.query_vector(w)).astype(np.float64))
            return out

        base_w = dict(cfg["weights"])
        lex13 = lexical(base_w, {})
        run("lex13", lex13, {"stage": "lexical (exp-13 config)"}, True)
        run("lex13+e5", np.stack([0.5 * minmax(lex13[i]) + 0.5 * minmax(e5_doc[i]) for i in range(nq)]), {"stage": "fusion 0.5"})
        human = json.loads((RUNS / "B_stage1.json").read_text())
        sel_lex, sel_fused = human["selected_lexical"], human["selected_fused"]
        for name, w, b in itertools.product(("sent", "sent+title"), (0.3, 0.5, 1.0), (0.5, 0.75)):
            label = f"lexrec__{name}_w{w}_b{b}"
            lx = lexical({**base_w, f"rec_{name}": w}, {f"rec_{name}": b})
            run(label, lx, {"stage": "lexical + reception (leak-free)", "reception": name, "reception_weight": w, "reception_b": b}, True)
            run(label + "+e5", np.stack([0.5 * minmax(lx[i]) + 0.5 * minmax(e5_doc[i]) for i in range(nq)]), {"stage": "fusion + reception (leak-free)", "reception": name, "reception_weight": w, "reception_b": b})
        comparisons = [(sel_lex, "lex13"), (sel_fused, "lex13+e5"), (f"{sel_lex}+e5", "lex13+e5")]
        head = "| run | all MRR / H@1 / R@10 / R@30 | pq | ruling | faq |"
    else:
        store = tokenize_corpus(C, tok, False)
        index = build_index(store)
        M = bm25f_matrix(index, cfg["weights"], k1=cfg["k1"], b=cfg["b"])
        z14 = np.load(EXPS / "14_ltr_fusion" / "cache" / "C_stage1.npz", allow_pickle=False)
        assert np.array_equal(z14["chunk_doc"], unit_doc_idx)
        del z14
        from common_c import chunk_corpus_c  # noqa: E402
        spec = MODELS["e5-small"]
        _, chunks_c = chunk_corpus_c("fixed1200_title")
        texts_c = [c.text for c in chunks_c]
        assert len(texts_c) == n_units
        emb = np.load(EmbeddingCache().dir / (_key(spec.hf_id, texts_c, "seq512|d_prefix='passage: '|C/fixed1200_title") + ".npy"), mmap_mode="r")
        del chunks_c, texts_c
        t0 = time.perf_counter()
        lex_doc = np.zeros((nq, n_docs)); e5_doc = np.zeros((nq, n_docs)); fused_doc = np.zeros((nq, n_docs))
        embT = np.ascontiguousarray(emb.T)
        for i, q in enumerate(questions):
            l = scores_for(M, index.query_vector(query_weights(index, tok, q.question)))
            e = (q_e5[i] @ embT).astype(np.float32)
            lex_doc[i] = np.maximum.reduceat(l, starts)
            e5_doc[i] = np.maximum.reduceat(e, starts)
            fused_doc[i] = np.maximum.reduceat(0.5 * minmax(l) + 0.5 * minmax(e), starts)
            if (i + 1) % 100 == 0:
                print(f"    {i+1}/{nq} queries scored ({time.perf_counter()-t0:.0f}s)", flush=True)
        del embT, emb, M, index
        # intent bank minus the mined source documents
        bank_all = json.loads((CACHE / "C_bank.json").read_text())["units"]
        bank_e5_all = np.load(CACHE / "C_bank_e5.npy")
        excluded = {q.meta["source_doc"] for q in questions if q.meta.get("source_doc")}
        keep = [j for j, u in enumerate(bank_all) if u["doc"] not in excluded]
        bank = [bank_all[j] for j in keep]
        bank_e5 = bank_e5_all[keep]
        notes["bank"] = {"units_full": len(bank_all), "units_after_exclusion": len(bank), "units_excluded": len(bank_all) - len(bank),
                         "excluded_source_docs": len(excluded), "excluded_by_kind": {k: sum(1 for j, u in enumerate(bank_all) if j not in set(keep) and u["kind"] == k)
                                                                                   for k in ("pq_q", "pq_block", "pq_subject", "faq", "ruling_objet", "ruling_tags")}}
        print(f"  bank: {len(bank_all)} units → {len(bank)} after removing {len(bank_all) - len(bank)} whose source document is a mined question's source_doc", flush=True)
        cos = q_e5 @ bank_e5.T
        bstore = TokenStore.build({"q": [tok(u["q"]) for u in bank]})
        bindex = build_index(bstore)
        bM = bm25f_matrix(bindex, {"q": 1.0}, k1=1.5, b=0.75)
        bm = np.stack([scores_for(bM, bindex.query_vector(query_weights(bindex, tok, q.question))) for q in questions])
        bank_sim = {"e5": cos, "bm25": bm, "e5+bm25": np.stack([0.5 * minmax(cos[i]) + 0.5 * minmax(bm[i]) for i in range(nq)])}
        own = np.array([doc_index.get(u["doc"], -1) for u in bank])
        cr, cc = [], []
        for j, u in enumerate(bank):
            for d in u["cites"]:
                if d in doc_index:
                    cr.append(j); cc.append(doc_index[d])
        cr, cc = np.array(cr), np.array(cc)

        def intent_doc(sim: np.ndarray, gamma: float) -> np.ndarray:
            out = np.zeros((nq, n_docs))
            for i in range(nq):
                s = np.asarray(minmax(sim[i]))
                np.maximum.at(out[i], own[own >= 0], s[own >= 0])
                if gamma > 0 and len(cr):
                    np.maximum.at(out[i], cc, gamma * s[cr])
            return out

        def rrf_doc(mats, weights, k=60.0, depth=300):
            out = np.zeros((nq, n_docs))
            for m, w in zip(mats, weights):
                for i in range(nq):
                    top = np.argpartition(-m[i], depth)[:depth]
                    top = top[np.argsort(-m[i][top], kind="stable")]
                    top = top[m[i][top] > 0]
                    out[i, top] += w / (k + np.arange(1, len(top) + 1))
            return out

        run("lex13", lex_doc, {"stage": "lexical (exp-13 config)"}, True)
        run("lex13+e5", fused_doc, {"stage": "fusion 0.5 (chunk level, doc max)"})
        run("lex13+e5__rrf", rrf_doc([lex_doc, e5_doc], [1.0, 1.0]), {"stage": "RRF60(lex, e5)"})
        for sim in ("e5", "bm25", "e5+bm25"):
            for g in (0.0, 0.5):
                idoc = intent_doc(bank_sim[sim], g)
                run(f"intent_only__{sim}_g{g}", idoc, {"stage": "intent bank alone (leak-free)", "bank_sim": sim, "gamma": g}, True)
                for w3 in (0.1, 0.3, 0.5):
                    run(f"lex13+e5+intent__{sim}_g{g}_w{w3}", fused_doc + w3 * idoc, {"stage": "fusion + intent (leak-free bank)", "bank_sim": sim, "gamma": g, "w3": w3})
                for w3 in (0.3, 0.5, 1.0):
                    run(f"lex13+e5+intent__rrf_{sim}_g{g}_w{w3}", rrf_doc([lex_doc, e5_doc, idoc], [1.0, 1.0, w3]), {"stage": "RRF fusion + intent (leak-free bank)", "bank_sim": sim, "gamma": g, "w3": w3})
        human = json.loads((RUNS / "C_stage1.json").read_text())
        sel = human["selected"]
        base = "lex13+e5__rrf" if "rrf" in sel else "lex13+e5"
        comparisons = [(sel, base), (sel, "lex13"), ("lex13+e5", "lex13"), ("lex13+e5__rrf", "lex13")]
        head = "| run | all MRR / H@1 / R@10 / R@30 | pq | ruling (verbatim) | faq (verbatim) |"

    tests = {}
    for b_name, a_name in comparisons:
        for sl in ("all",) + SLICES:
            tests[f"{b_name} vs {a_name} [{sl}]"] = paired(results[a_name]["ranks"], results[b_name]["ranks"], questions, sl)
    summary = {"corpus": a.corpus, "n": nq, "notes": notes, "comparisons": comparisons, "runs": {k: v["metrics"] for k, v in results.items()}, "tests": tests}
    (RUNS / f"{a.corpus}_mined.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1, default=str))
    lines = [f"### Corpus {a.corpus} – mined questions ({nq}: " + ", ".join(f"{s} {sum(1 for q in questions if q.meta.get('source') == s)}" for s in SLICES) + "), first stage only", "",
             head, "|---|---|---|---|---|"]
    for k, v in results.items():
        lines.append(fmt(k, v["metrics"]))
    lines += ["", "Paired statistics (rag_eval.stats.paired_stats; Δ = variant − baseline, reciprocal rank; p = paired t / sign-flip permutation):", "",
              "| comparison [slice] | n | MRR base → variant | Δ MRR [95 % CI] | p_t / p_perm | W / L / T | Δ hit@10 (p_t) |", "|---|---:|---|---|---|---|---|"]
    for k, t in tests.items():
        lines.append(fmt_p(k, t))
    (RUNS / f"{a.corpus}_mined_tables.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines), flush=True)
    print(json.dumps(notes, indent=1))


if __name__ == "__main__":
    main()
