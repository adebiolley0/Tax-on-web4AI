"""Chunking strategies shared across experiments.

All functions take a list of :class:`~rag_eval.corpora.Doc` and return a list of
:class:`~rag_eval.corpora.Chunk` whose ids are ``<doc_id>#<i>``; every chunk keeps the document's
title and a copy of its ``meta``.  Whitespace is normalised first (non-breaking spaces, runs of
spaces / tabs, more than two blank lines).

* :func:`whole_doc` – one chunk per document, optionally truncated;
* :func:`fixed_chunks` – heading-aware recursive chunking (sections → paragraphs → sentences) with
  a character budget and overlap, optional title prefix ("contextual chunk header");
* :func:`article_chunks` – for corpus B, where a document *is* an article: prefix the code name +
  heading path so every chunk carries its legal context, then split long articles.
"""
from __future__ import annotations

import re

from rag_eval.corpora import Chunk, Doc

_WS = re.compile(r"[ \t]+")


def _norm(t: str) -> str:
    t = t.replace(" ", " ")
    t = _WS.sub(" ", t)
    return re.sub(r"\n{3,}", "\n\n", t).strip()


def whole_doc(docs: list[Doc], max_chars: int | None = None) -> list[Chunk]:
    """One chunk per document (optionally truncated to ``max_chars``)."""
    out = []
    for d in docs:
        t = _norm(d.text)
        if max_chars:
            t = t[:max_chars]
        out.append(Chunk(f"{d.doc_id}#0", d.doc_id, t, d.title, dict(d.meta)))
    return out


def _split_long(text: str, max_chars: int, overlap: int) -> list[str]:
    """Split on paragraph, then sentence-ish boundaries, respecting ``max_chars``; each piece after
    the first starts with the last ``overlap`` characters (word-aligned) of the previous one."""
    if len(text) <= max_chars:
        return [text]
    paras = [p for p in re.split(r"\n\s*\n", text) if p.strip()]
    pieces: list[str] = []
    buf = ""
    for p in paras:
        if len(p) > max_chars:
            if buf:
                pieces.append(buf); buf = ""
            sents = re.split(r"(?<=[.;:!?])\s+", p)
            sb = ""
            for s in sents:
                if len(sb) + len(s) + 1 > max_chars and sb:
                    pieces.append(sb); sb = s
                else:
                    sb = f"{sb} {s}".strip()
                while len(sb) > max_chars:  # pathological long sentence
                    pieces.append(sb[:max_chars]); sb = sb[max_chars:]
            if sb:
                pieces.append(sb)
        elif len(buf) + len(p) + 2 > max_chars and buf:
            pieces.append(buf); buf = p
        else:
            buf = f"{buf}\n\n{p}" if buf else p
    if buf:
        pieces.append(buf)
    if overlap > 0:
        with_ov = []
        for i, pc in enumerate(pieces):
            if i > 0:
                tail = pieces[i - 1][-overlap:]
                sp = tail.find(" ")
                tail = tail[sp + 1:] if sp > 0 else tail
                pc = tail + "\n" + pc
            with_ov.append(pc)
        pieces = with_ov
    return pieces


def fixed_chunks(docs: list[Doc], max_chars: int = 1500, overlap: int = 200,
                 heading_split: bool = True, prefix_title: bool = False) -> list[Chunk]:
    """Heading-aware recursive chunking.  Markdown sections (``#``–``####``) are split first and tiny
    ones merged forward, then each section is cut by :func:`_split_long`; ``prefix_title`` prepends
    the document title to every chunk."""
    out = []
    for d in docs:
        text = _norm(d.text)
        sections = re.split(r"(?=\n#{1,4}\s)", "\n" + text) if heading_split else [text]
        sections = [s.strip() for s in sections if s.strip()]
        merged: list[str] = []
        for s in sections:
            if merged and len(merged[-1]) + len(s) + 2 <= max_chars:
                merged[-1] = merged[-1] + "\n\n" + s
            else:
                merged.append(s)
        i = 0
        for sec in merged:
            for piece in _split_long(sec, max_chars, overlap):
                body = f"{d.title}\n\n{piece}" if prefix_title else piece
                out.append(Chunk(f"{d.doc_id}#{i}", d.doc_id, body, d.title, dict(d.meta)))
                i += 1
    return out


def article_chunks(docs: list[Doc], max_chars: int = 2000, overlap: int = 150,
                   prefix_context: bool = True) -> list[Chunk]:
    """Corpus B: prefix ``title`` + ``meta["heading_path"]`` (code > book > chapter …) to every piece
    of the article so each chunk carries its legal context."""
    out = []
    for d in docs:
        text = _norm(d.text)
        ctx = ""
        if prefix_context:
            hp = d.meta.get("heading_path") or []
            ctx = f"{d.title}\n" + (" > ".join(hp) + "\n" if hp else "") + "\n"
        for i, piece in enumerate(_split_long(text, max_chars, overlap)):
            out.append(Chunk(f"{d.doc_id}#{i}", d.doc_id, ctx + piece, d.title, dict(d.meta)))
    return out
