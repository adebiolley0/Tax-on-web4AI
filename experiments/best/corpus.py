"""Corpora, chunk universes and the exp-08 corpus-B cleanup.

* :func:`load_b` / :func:`load_c` / :func:`load_a` – documents through ``rag_eval`` (A: 91 Fisconet+ docs, B: the
  5,853-article default subset of the legal-code PDFs, C: the 21,259 Fisconet+ markdown documents).
* :class:`Universe` – the chunk universe of the dense / ColBERT / reranker stages (B: article_ctx_1200 over the raw
  articles, 10,869 chunks; C: fixed1200_title, 201,404 chunks) with the chunk → document map and a fingerprint that
  every cache carries.
* :func:`lexical_fields` – the per-unit fields (title / heading / body / meta) of the exp-13 lexical index
  (B: cleaned articles in 2,000-char units; C: the same chunks as the universe; A: whole documents).
* :func:`clean_article`, :func:`region_of_code` – experiment 08 (amendment-preamble stripping, region per code).
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass

import numpy as np

from rag_eval import Chunk, Doc, article_chunks, fixed_chunks, load_corpus_a, load_corpus_b, load_corpus_c, whole_doc
from rag_eval.corpora import DATA_DIR

from config import C_MAX_CHARS, CHUNKING, fingerprint

# ── experiment 08: corpus-B cleanup + region metadata ────────────────────────────────────────────────────────
_PREAMBLE_LINE = re.compile(
    r"^(?:\(?\s*(?:Art\.|Article|L'art\.|Les art\.|L'article)\s.*?(?:applicable|en vigueur|abrog|remplac|ins[ée]r|modifi|r[ée]tabli|compl[ée]t)"
    r"|\(?\s*(?:al\.|alin[ée]a|§)\s.*?(?:applicable|en vigueur|abrog|remplac|ins[ée]r|modifi)"
    r"|\(\s*(?:modifi|remplac|ins[ée]r|abrog|compl[ée]t|r[ée]tabli)|\[.*?(?:index|Numac|Toute modification).*?\]"
    r"|\(?\s*Le texte de l.AR n°)",
    re.IGNORECASE)
_NOTE_TAIL = re.compile(r"(?:Numac\s*:?\s*\d+\)?|M\.B\.,?\s*\d{2}\.\d{2}\.\d{4}[^)]*\)?)\s*$")


def clean_article(text: str) -> str:
    """Strip amendment-history preambles, "[montants indexés …]" markers and "(modifié par …)" notes (exp 08)."""
    out: list[str] = []
    head = True
    for ln in text.split("\n"):
        s = ln.strip()
        if head and (_PREAMBLE_LINE.match(s) or _NOTE_TAIL.search(s) or not s):
            continue
        head = False
        if re.match(r"^\[.*(?:index|Numac|Toute modification).*\]$", s):
            continue
        out.append(ln)
    cleaned = "\n".join(out).strip()
    return cleaned if len(cleaned) >= 15 else text


_REGION = {
    "wal": {"csucc_wal", "cenr_wal", "cta_wal", "cir92_wal", "arcir92_wal"},
    "bxl": {"csucc_bxl", "cenr_bxl", "cta_bxl", "cbpf", "agbxl2019", "cir92_bxl", "arcir92_bxl"},
    "vla": {"csucc_vla", "cenr_vla", "cta_vla", "vcf", "avcf", "ar1936_vla", "cir92_vla", "arcir92_vla"},
}


def region_of_code(code: str) -> str:
    for r, codes in _REGION.items():
        if code in codes:
            return r
    return "bxl,wal" if code == "ar1936_bxl" else "fed"


# ── loaders ──────────────────────────────────────────────────────────────────────────────────────────────────
def default_codes_b() -> list[str]:
    rep = json.loads((DATA_DIR / "corpus_b" / "parse_report.json").read_text())
    return [k for k, v in rep.items() if isinstance(v, dict) and v.get("default_subset")]


def load_b(clean: bool = False) -> list[Doc]:
    docs = load_corpus_b(codes=default_codes_b())
    if clean:
        docs = [Doc(d.doc_id, d.title, clean_article(d.text), dict(d.meta)) for d in docs]
    return docs


def load_c() -> list[Doc]:
    return load_corpus_c(max_chars=C_MAX_CHARS)


def load_a() -> list[Doc]:
    return load_corpus_a()


# ── chunk universe ───────────────────────────────────────────────────────────────────────────────────────────
@dataclass
class Universe:
    corpus: str
    docs: list[Doc]
    chunks: list[Chunk]
    doc_ids: list[str]
    chunk_doc: np.ndarray          # chunk → doc index
    doc_start: np.ndarray          # (n_docs + 1,) chunk range of every doc (chunks are grouped per doc)

    @property
    def n_docs(self) -> int:
        return len(self.doc_ids)

    @property
    def n_chunks(self) -> int:
        return len(self.chunks)

    @property
    def texts(self) -> list[str]:
        return [c.text for c in self.chunks]

    def fingerprint(self) -> str:
        return fingerprint(self.texts)

    def doc_index(self) -> dict[str, int]:
        return {d: i for i, d in enumerate(self.doc_ids)}


def _universe(corpus: str, docs: list[Doc], chunks: list[Chunk]) -> Universe:
    doc_ids = [d.doc_id for d in docs]
    di = {d: i for i, d in enumerate(doc_ids)}
    chunk_doc = np.array([di[c.doc_id] for c in chunks], dtype=np.int64)
    assert np.all(np.diff(chunk_doc) >= 0), "chunks must be grouped per document"
    counts = np.bincount(chunk_doc, minlength=len(doc_ids))
    doc_start = np.concatenate([[0], np.cumsum(counts)]).astype(np.int64)
    return Universe(corpus, docs, chunks, doc_ids, chunk_doc, doc_start)


def universe_b(docs: list[Doc] | None = None) -> Universe:
    docs = docs or load_b(clean=False)
    _, max_chars, overlap = CHUNKING["B"]
    return _universe("B", docs, article_chunks(docs, max_chars, overlap, prefix_context=True))


def universe_c(docs: list[Doc] | None = None) -> Universe:
    docs = docs or load_c()
    _, max_chars, overlap = CHUNKING["C"]
    return _universe("C", docs, fixed_chunks(docs, max_chars, overlap, prefix_title=True))


# ── lexical units and their fields (exp 13 `load_corpus`) ───────────────────────────────────────────────────
@dataclass
class LexicalUnits:
    corpus: str
    doc_ids: list[str]
    unit_doc: np.ndarray                 # unit → doc index
    fields: dict[str, list[str]]         # field → raw text per unit
    unit_meta: list[dict]
    unit_texts: list[str]                # the text a reranker / reader sees for the unit


def lexical_units_b(docs_clean: list[Doc] | None = None) -> LexicalUnits:
    """Cleaned articles in 2,000-char units without the context prefix; fields title / heading path / body / (cue)."""
    docs = docs_clean or load_b(clean=True)
    units = article_chunks(docs, 2000, 150, prefix_context=False)
    di = {d.doc_id: i for i, d in enumerate(docs)}
    fields = {"title": [c.title for c in units],
              "heading": [" ".join(c.meta.get("heading_path") or []) for c in units],
              "body": [c.text for c in units]}
    texts = []
    for c in units:
        hp = c.meta.get("heading_path") or []
        texts.append(f"{c.title}\n" + (" > ".join(hp) + "\n" if hp else "") + "\n" + c.text)
    return LexicalUnits("B", [d.doc_id for d in docs], np.array([di[c.doc_id] for c in units], dtype=np.int64),
                        fields, [c.meta for c in units], texts)


def lexical_units_c(uni: Universe) -> LexicalUnits:
    """The universe chunks themselves (unit index == chunk index, so reranker caches are shared)."""
    bodies = []
    for c in uni.chunks:
        pre = f"{c.title}\n\n"
        bodies.append(c.text[len(pre):] if c.text.startswith(pre) else c.text)
    fields = {"title": [c.title for c in uni.chunks],
              "heading": [" ".join((c.meta.get("path") or []) + [c.meta.get("document_type") or ""]) for c in uni.chunks],
              "body": bodies}
    return LexicalUnits("C", uni.doc_ids, uni.chunk_doc.copy(), fields, [c.meta for c in uni.chunks], uni.texts)


def lexical_units_a(docs: list[Doc] | None = None) -> LexicalUnits:
    docs = docs or load_a()
    units = whole_doc(docs)
    return LexicalUnits("A", [d.doc_id for d in docs], np.arange(len(units), dtype=np.int64),
                        {"body": [c.text for c in units]}, [c.meta for c in units], [c.text for c in units])
