"""Experiment 01 – BM25 lexical baselines.

Runs a family of BM25 configurations (bm25s + PyStemmer) on corpus A (91 Fisconet+
markdown docs, 31 questions) and, when ``questions_b.json`` exists, on corpus B
(article-level PDF corpus, default subset).  Every run is scored at *document*
level with the shared harness and saved to ``experiments/results/01_bm25``.

Usage::

    uv run python run_bm25.py            # both corpora (B only if questions exist)
    uv run python run_bm25.py A          # one corpus
    uv run python run_bm25.py A --no-save
"""
from __future__ import annotations

import json
import re
import sys
import time
import unicodedata
from collections import defaultdict
from dataclasses import dataclass, asdict

import bm25s
import Stemmer
from bm25s.stopwords import STOPWORDS_FRENCH

from rag_eval import (
    Chunk, Doc, Question,
    load_corpus, load_corpus_b, load_questions_b,
    whole_doc, fixed_chunks, article_chunks,
    evaluate_rankings, save_result, print_leaderboard, RunResult,
)
from rag_eval.corpora import DATA_DIR, QUESTIONS_B

EXPERIMENT = "01_bm25"
TOP_N_DOCS = 50          # doc ids kept per question in the saved result
CHUNK_K = 2000           # chunk hits pulled before aggregating to documents

# --------------------------------------------------------------------------- tokenization

_TOKEN_RE = re.compile(r"\w+", re.UNICODE)
_STEMMER = Stemmer.Stemmer("french")
# interrogatives / modals / filler that occur in almost every user question but are
# absent from bm25s' French stoplist (they pull in random long docs otherwise)
QUESTION_STOPWORDS = {
    "quel", "quelle", "quels", "quelles", "comment", "pourquoi", "combien", "quand", "où",
    "puis", "peux", "peut", "dois", "doit", "faut", "obligé", "obligée", "existe", "fonctionne",
    "etc", "tant", "tous", "toutes", "tout", "toute", "ai", "il", "y", "a",
}


def strip_accents(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))


@dataclass(frozen=True)
class TokCfg:
    stem: bool = False
    stopwords: bool = False
    accents: bool = True       # keep accents (False → NFKD strip)
    qstop: bool = False        # also drop QUESTION_STOPWORDS

    @property
    def key(self) -> str:
        if not (self.stem or self.stopwords or not self.accents or self.qstop):
            return "plain"
        parts = ["stem" if self.stem else "nostem"]
        if self.stopwords:
            parts.append("stop")
        if self.qstop:
            parts.append("qstop")
        if not self.accents:
            parts.append("noaccent")
        return "+".join(parts)


def make_tokenizer(cfg: TokCfg):
    stop = set(STOPWORDS_FRENCH) if cfg.stopwords else set()
    if cfg.qstop:
        stop |= QUESTION_STOPWORDS
    if not cfg.accents:
        stop = {strip_accents(w) for w in stop}

    def tok(text: str) -> list[str]:
        text = text.lower()
        if not cfg.accents:
            text = strip_accents(text)
        toks = [t for t in _TOKEN_RE.findall(text) if len(t) > 1 or t.isdigit()]
        if stop:
            toks = [t for t in toks if t not in stop]
        if cfg.stem:
            toks = _STEMMER.stemWords(toks)
        return toks
    return tok


# --------------------------------------------------------------------------- units (doc vs chunk)

@dataclass(frozen=True)
class UnitCfg:
    kind: str = "doc"            # doc | fixed | article
    max_chars: int = 1500
    overlap: int = 200
    prefix: bool = False         # fixed: prefix_title, article: prefix_context
    agg: str = "max"             # max | sumtop3 (ignored for doc)

    @property
    def key(self) -> str:
        if self.kind == "doc":
            return "doc"
        if self.kind == "fixed":
            return f"fixed{self.max_chars}" + ("+title" if self.prefix else "") + f"|{self.agg}"
        return "article" + ("+ctx" if self.prefix else "-ctx") + f"|{self.agg}"

    @property
    def chunk_key(self) -> tuple:  # what determines the chunk texts (not the agg)
        return (self.kind, self.max_chars, self.overlap, self.prefix)


def make_units(docs: list[Doc], u: UnitCfg) -> list[Chunk]:
    if u.kind == "doc":
        return whole_doc(docs)
    if u.kind == "fixed":
        return fixed_chunks(docs, max_chars=u.max_chars, overlap=u.overlap, prefix_title=u.prefix)
    if u.kind == "article":
        return article_chunks(docs, max_chars=u.max_chars, overlap=u.overlap, prefix_context=u.prefix)
    raise ValueError(u.kind)


# --------------------------------------------------------------------------- BM25 run

@dataclass(frozen=True)
class BM25Cfg:
    k1: float = 1.5
    b: float = 0.75
    method: str = "lucene"

    @property
    def key(self) -> str:
        return f"k1={self.k1},b={self.b}|{self.method}"


class Experiment:
    def __init__(self, corpus: str, docs: list[Doc], questions: list[Question], save: bool = True):
        self.corpus, self.docs, self.questions, self.save = corpus, docs, questions, save
        self._chunks: dict[tuple, list[Chunk]] = {}
        self._tokens: dict[tuple, list[list[str]]] = {}
        self.results: list[RunResult] = []

    def chunks(self, u: UnitCfg) -> list[Chunk]:
        if u.chunk_key not in self._chunks:
            self._chunks[u.chunk_key] = make_units(self.docs, u)
        return self._chunks[u.chunk_key]

    def tokens(self, u: UnitCfg, t: TokCfg) -> tuple[list[list[str]], float]:
        key = (u.chunk_key, t)
        if key in self._tokens:
            return self._tokens[key], 0.0
        tok = make_tokenizer(t)
        t0 = time.perf_counter()
        self._tokens[key] = [tok(c.text) for c in self.chunks(u)]
        return self._tokens[key], time.perf_counter() - t0

    def run(self, name: str, u: UnitCfg, t: TokCfg, b: BM25Cfg = BM25Cfg()) -> RunResult:
        chunks = self.chunks(u)
        corpus_tokens, tok_s = self.tokens(u, t)
        tok = make_tokenizer(t)

        t0 = time.perf_counter()
        retriever = bm25s.BM25(k1=b.k1, b=b.b, method=b.method)
        retriever.index(corpus_tokens, show_progress=False)
        index_s = time.perf_counter() - t0

        k = min(len(chunks), TOP_N_DOCS if u.kind == "doc" else CHUNK_K)
        q_tokens = [tok(q.question) for q in self.questions]
        t0 = time.perf_counter()
        idx, scores = retriever.retrieve(q_tokens, k=k, show_progress=False)
        query_s = time.perf_counter() - t0

        rankings: dict[str, list[str]] = {}
        for qi, q in enumerate(self.questions):
            hits = [(chunks[int(i)].doc_id, float(s)) for i, s in zip(idx[qi], scores[qi]) if s > 0]
            if u.kind == "doc":
                ranked = [d for d, _ in hits]
            else:
                per_doc: dict[str, list[float]] = defaultdict(list)
                for d, s in hits:                      # hits already sorted by score desc
                    per_doc[d].append(s)
                if u.agg == "max":
                    agg = {d: ss[0] for d, ss in per_doc.items()}
                elif u.agg == "sumtop3":
                    agg = {d: sum(ss[:3]) for d, ss in per_doc.items()}
                else:
                    raise ValueError(u.agg)
                ranked = sorted(agg, key=lambda d: -agg[d])
            rankings[q.qid] = ranked[:TOP_N_DOCS]

        config = {"unit": asdict(u), "tokenizer": asdict(t), "bm25": asdict(b),
                  "n_docs": len(self.docs), "n_units": len(chunks)}
        timing = {"tokenize_s": round(tok_s, 2), "index_s": round(index_s, 2), "query_s": round(query_s, 3)}
        res = evaluate_rankings(name, self.corpus, self.questions, rankings, config, timing)
        self.results.append(res)
        if self.save:
            save_result(EXPERIMENT, res)
        print(res.summary(), f"  [{len(chunks)} units, idx {index_s:.1f}s]")
        return res

    def best(self, prefix: str | None = None) -> RunResult:
        pool = [r for r in self.results if prefix is None or r.name.startswith(prefix)]
        return max(pool, key=lambda r: (r.metrics["mrr"], r.metrics["ndcg@5"]))


# --------------------------------------------------------------------------- run plan

def run_plan(exp: Experiment) -> None:
    is_b = exp.corpus == "B"
    doc = UnitCfg("doc")

    print(f"\n=== [{exp.corpus}] 1. doc-level, plain tokenization ===")
    exp.run("doc|plain", doc, TokCfg())

    print(f"\n=== [{exp.corpus}] 2. doc-level, stemming / stopwords / accents ===")
    tok_variants = [TokCfg(stem=True), TokCfg(stopwords=True), TokCfg(stem=True, stopwords=True),
                    TokCfg(stem=True, stopwords=True, accents=False),
                    TokCfg(stem=True, stopwords=True, accents=False, qstop=True)]
    for t in tok_variants:
        exp.run(f"doc|{t.key}", doc, t)
    best_tok = TokCfg(**exp.best("doc|").config["tokenizer"])
    print(f"--> best tokenizer on doc-level: {best_tok.key}")

    print(f"\n=== [{exp.corpus}] 3. chunk-level (doc score = agg over chunks), tokenizer={best_tok.key} ===")
    if is_b:
        # each doc *is* an article: article_chunks with/without the legal-context prefix
        chunk_units = [UnitCfg("article", 2000, 150, prefix=True, agg="max"),
                       UnitCfg("article", 2000, 150, prefix=False, agg="max"),
                       UnitCfg("article", 2000, 150, prefix=True, agg="sumtop3"),
                       UnitCfg("fixed", 1500, 200, prefix=True, agg="max"),
                       UnitCfg("fixed", 1500, 200, prefix=False, agg="max")]
    else:
        chunk_units = [UnitCfg("fixed", 1500, 200, prefix=False, agg="max"),
                       UnitCfg("fixed", 1500, 200, prefix=False, agg="sumtop3"),
                       UnitCfg("fixed", 1500, 200, prefix=True, agg="max"),
                       UnitCfg("fixed", 1500, 200, prefix=True, agg="sumtop3")]
    for u in chunk_units:
        exp.run(f"{u.key}|{best_tok.key}", u, best_tok)
    # also the plain tokenizer on the first chunk unit, to see chunking vs tokenization effects
    exp.run(f"{chunk_units[0].key}|plain", chunk_units[0], TokCfg())

    best_unit = UnitCfg(**exp.best().config["unit"])
    print(f"--> best unit so far: {best_unit.key}")

    print(f"\n=== [{exp.corpus}] 4. k1/b grid x method on unit={best_unit.key}, tokenizer={best_tok.key} ===")
    for k1, b in [(1.2, 0.75), (1.5, 0.75), (0.9, 0.4)]:
        for method in ["lucene", "bm25+"]:
            bc = BM25Cfg(k1, b, method)
            exp.run(f"{best_unit.key}|{best_tok.key}|{bc.key}", best_unit, best_tok, bc)
    if best_unit.kind != "doc":
        # and the grid's best (k1,b,method) applied to plain doc-level for reference
        bb = BM25Cfg(**exp.best(f"{best_unit.key}|{best_tok.key}|k1").config["bm25"])
        exp.run(f"doc|{best_tok.key}|{bb.key}", doc, best_tok, bb)


# --------------------------------------------------------------------------- reporting

def markdown_table(results: list[RunResult]) -> str:
    hdr = "| run | MRR | nDCG@5 | nDCG@10 | H@1 | H@3 | H@5 | H@10 | R@5 | R@10 | units | idx s |\n"
    hdr += "|---|---|---|---|---|---|---|---|---|---|---|---|\n"
    rows = []
    for r in results:
        m = r.metrics
        rows.append(f"| `{r.name}` | {m['mrr']:.3f} | {m['ndcg@5']:.3f} | {m['ndcg@10']:.3f} | {m['hit@1']:.3f} | "
                    f"{m['hit@3']:.3f} | {m['hit@5']:.3f} | {m['hit@10']:.3f} | {m['recall@5']:.3f} | {m['recall@10']:.3f} | "
                    f"{r.config['n_units']} | {r.timing['index_s']} |")
    return hdr + "\n".join(rows)


def failure_analysis(exp: Experiment, res: RunResult, tok: TokCfg, max_rank: int = 10) -> None:
    """Print the questions the best run gets wrong (rank None or > max_rank) with
    enough context to explain why: query tokens vs. expected doc vs. top hit."""
    tokf = make_tokenizer(tok)
    by_id = {d.doc_id: d for d in exp.docs}
    print(f"\n=== [{exp.corpus}] failure analysis for `{res.name}` (rank None or > {max_rank}) ===")
    n_fail = 0
    for q in exp.questions:
        pq = res.per_question[q.qid]
        if pq["rank"] is not None and pq["rank"] <= max_rank:
            continue
        n_fail += 1
        qt = tokf(q.question)
        exp_doc = by_id.get(q.expected[0])
        exp_tok = set(tokf(exp_doc.text)) if exp_doc else set()
        top1 = by_id.get(pq["top5"][0]) if pq["top5"] else None
        top_tok = set(tokf(top1.text)) if top1 else set()
        print(f"\n{q.qid} rank={pq['rank']}  Q: {q.question}")
        print(f"   expected : {q.expected[0]}  ({(exp_doc.title if exp_doc else '?')[:90]}, "
              f"{len(exp_doc.text) if exp_doc else 0} chars)")
        for i, d in enumerate(pq["top5"][:3]):
            dd = by_id.get(d)
            print(f"   top{i+1}     : {d}  ({(dd.title if dd else '?')[:90]}, {len(dd.text) if dd else 0} chars)")
        print(f"   q tokens : {qt}")
        print(f"   in expected: {[t for t in qt if t in exp_tok]}")
        print(f"   in top1 only: {[t for t in qt if t in top_tok and t not in exp_tok]}")
    print(f"\n{n_fail}/{len(exp.questions)} questions with rank None or > {max_rank}")


def default_subset_codes() -> list[str]:
    report = json.loads((DATA_DIR / "corpus_b" / "parse_report.json").read_text())
    return [code for code, info in report.items() if isinstance(info, dict) and info.get("default_subset")]


def main(argv: list[str]) -> None:
    save = "--no-save" not in argv
    wanted = [a for a in argv if a in ("A", "B")] or ["A", "B"]
    tables: dict[str, str] = {}
    for corpus in wanted:
        if corpus == "A":
            docs, questions = load_corpus("A")
        else:
            if not QUESTIONS_B.exists():
                print(f"\n[B] {QUESTIONS_B} not found – skipping corpus B.")
                continue
            codes = default_subset_codes()
            docs, questions = load_corpus_b(codes=codes), load_questions_b()
            print(f"[B] default subset: {len(codes)} codes -> {len(docs)} articles")
        print(f"\n##### corpus {corpus}: {len(docs)} docs, {len(questions)} questions #####")
        exp = Experiment(corpus, docs, questions, save=save)
        t0 = time.perf_counter()
        run_plan(exp)
        print(f"\n[{corpus}] {len(exp.results)} runs in {time.perf_counter() - t0:.1f}s")

        print(f"\n=== [{corpus}] all runs ===")
        for r in sorted(exp.results, key=lambda r: -r.metrics["mrr"]):
            print(r.summary())
        best = exp.best()
        print(f"\n[{corpus}] BEST: {best.summary()}")
        failure_analysis(exp, best, TokCfg(**best.config["tokenizer"]))
        tables[corpus] = markdown_table(sorted(exp.results, key=lambda r: -r.metrics["mrr"]))

    for corpus, tbl in tables.items():
        print(f"\n### corpus {corpus} (markdown)\n{tbl}")
    if save:
        print("\n=== leaderboard (all experiments) ===")
        print_leaderboard()


if __name__ == "__main__":
    main(sys.argv[1:])
