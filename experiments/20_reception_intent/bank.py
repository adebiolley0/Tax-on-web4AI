#!/usr/bin/env python3
"""Intent bank for corpus C: questions the corpus already contains, each mapped to its answer
document(s) — the document itself (weight 1) and the documents it cites (exp-11 graph edges,
weight γ chosen on train).

* parliamentary questions: the QUESTION block (sentences ending in '?', the whole block, the subject line)
* FAQ documents (faq/ + circulaires titled FAQ): headings ending in '?'
* rulings: the "Objet de la demande" paragraph and the topic tags at the top of the decision

  ../14_ltr_fusion/.venv/bin/python bank.py     → cache/C_bank.json
"""
from __future__ import annotations

import collections
import json
import re

from common20 import CACHE, EXPS, MYFIN, fold, sentence_spans  # noqa: E402
from rag_eval.corpora import _parse_front_matter

MAX_CITES = 30
_Q_HEAD = re.compile(r"^\s*(?:Q\s?UESTIONS?(?:\s+EN\s+RETOUR)?|VRAAG|VRAGEN)\s*:?\s*$", re.I)
_A_HEAD = re.compile(r"^\s*(?:R\s?[ÉE]\s?PONSE|ANTWOORD|R É PONSE)", re.I)
_SKIP_SUBJECT = re.compile(r"questions? [ée]crites|parlement|chambre|s[ée]nat|publication|deze tekst|ce texte|qrva|bulletin|session|zitting|schriftelijke", re.I)
_FAQ_NUM = re.compile(r"^\s*(?:Q(?:uestion)?\s*)?\d{1,3}\s*[.)]\s*|^\s*[a-h]\)\s*", re.I)
_OBJET = re.compile(r"^\s*(?:[IVX]+\.?|\d+\.?)?\s*(?:Objet de la demande|Voorwerp van de aanvraag)\s*:?\s*$", re.I)
_OBJET_INLINE = re.compile(r"(?:Objet de la demande|Voorwerp van de aanvraag)\s*:?\s*", re.I)
_NEXT_HEAD = re.compile(r"^\s*(?:II\b|2\b|D[ée]cision|Beslissing|Motivation|Motivering|(?:[IVX]+|\d+)\.\s+[A-ZÉ])", re.I)
_RESUME = re.compile(r"^\s*(?:R[ée]sum[ée]|Samenvatting|Objet de la demande|Voorwerp)", re.I)
_WS = re.compile(r"\s+")


def body_of(p) -> tuple[dict, list[str]]:
    fm, body = _parse_front_matter(p.read_text(encoding="utf-8", errors="replace"))
    body = body.strip()
    if body.startswith("# "):
        body = body.split("\n", 1)[1] if "\n" in body else ""
    return fm, [l.rstrip() for l in body.split("\n")]


def norm(s: str) -> str:
    return _WS.sub(" ", s).strip().lstrip("#* ").strip()


def questions_in(text: str, lo: int = 25, hi: int = 500) -> list[str]:
    out = []
    for a, b in sentence_spans(text):
        s = norm(text[a:b])
        if s.endswith("?") and lo <= len(s) <= hi:
            out.append(s)
    return out


def main():
    units: list[dict] = []
    st = collections.Counter()

    def add(kind, q, doc):
        q = norm(q)
        if len(q) < 15:
            return
        units.append({"kind": kind, "q": q, "doc": doc})
        st[f"units:{kind}"] += 1

    # ── parliamentary questions ─────────────────────────────────────────
    for p in sorted((MYFIN / "questions_parlementaires").glob("*.md")):
        fm, lines = body_of(p)
        doc = f"questions_parlementaires/{p.stem}"
        st["docs:pq"] += 1
        qi = next((i for i, l in enumerate(lines) if _Q_HEAD.match(l)), None)
        if qi is None:
            st["pq:no_question_heading"] += 1
            continue
        ai = next((i for i in range(qi + 1, len(lines)) if _A_HEAD.match(lines[i])), len(lines))
        block = norm("\n".join(lines[qi + 1: ai]))
        if not block:
            st["pq:empty_block"] += 1
            continue
        for q in questions_in(block):
            add("pq_q", q, doc)
        add("pq_block", block[:1500], doc)
        subj = [norm(l) for l in lines[1:qi] if norm(l) and not _SKIP_SUBJECT.search(l) and len(norm(l)) <= 250]
        subj = [s for s in subj if not s.lower().startswith(("question parlementaire", "parlementaire vraag", "(", "question n", "question écrite"))]
        if subj:
            add("pq_subject", max(subj, key=len), doc)

    # ── FAQ documents ───────────────────────────────────────────────────
    faq_files = sorted((MYFIN / "faq").glob("*.md")) + [p for p in sorted((MYFIN / "circulaires").glob("*.md")) if "faq" in p.stem.lower()]
    for p in faq_files:
        fm, lines = body_of(p)
        if "faq" not in fold(fm.get("title", "")).lower() and "faq" not in p.stem.lower():
            continue
        doc = f"{p.parent.name}/{p.stem}"
        st["docs:faq"] += 1
        seen = set()
        for l in lines:
            s = norm(l)
            if not s.endswith("?") or not (15 <= len(s) <= 350):
                continue
            s = _FAQ_NUM.sub("", s)
            k = fold(s.lower())
            if k in seen:
                continue
            seen.add(k)
            add("faq", s, doc)

    # ── rulings ─────────────────────────────────────────────────────────
    for folder in ("decisions_anticipees_l_24_12_2002", "decisions_anticipees_art_345_cir_92", "decisions_anticipees_ar_03_05_1999"):
        for p in sorted((MYFIN / folder).glob("*.md")):
            fm, lines = body_of(p)
            doc = f"{folder}/{p.stem}"
            st["docs:ruling"] += 1
            # topic tags: short lines between the repeated title and the summary / object heading
            tags = []
            for l in lines[1:40]:
                s = norm(l)
                if not s:
                    continue
                if _RESUME.match(s) or len(s) > 120 or s.endswith((".", ":")):
                    break
                if s.lower() != fm.get("title", "").lower():
                    tags.append(s)
            if len(tags) >= 2:
                add("ruling_tags", " ; ".join(tags[:12]), doc)
            oi = next((i for i, l in enumerate(lines) if _OBJET.match(l)), None)
            if oi is None:
                oi = next((i for i, l in enumerate(lines) if _OBJET_INLINE.search(l) and len(l) < 200), None)
                if oi is None:
                    st["ruling:no_objet"] += 1
                    continue
                first = _OBJET_INLINE.split(lines[oi], 1)[-1]
                seg = [first]
            else:
                seg = []
            for l in lines[oi + 1: oi + 60]:
                if _NEXT_HEAD.match(l) and seg and len(norm(" ".join(seg))) > 60:
                    break
                seg.append(l)
            objet = norm(" ".join(seg))
            objet = re.sub(r"^(?:La demande vise à obtenir (?:la )?confirmation (?:que|de ce que)\s*:?\s*|De aanvraag strekt ertoe (?:bevestiging te krijgen dat|te vernemen)\s*:?\s*)", "", objet, flags=re.I)
            if len(objet) >= 30:
                add("ruling_objet", objet[:1500], doc)
            else:
                st["ruling:objet_too_short"] += 1

    # ── cited documents (exp-11 graph) ──────────────────────────────────
    g = json.loads((EXPS / "11_graph_retrieval" / "cache" / "C_graph.json").read_text())
    cites: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
    for s, t, ty, n in g["edges"]:
        if ty.startswith("cite") and ty != "cite_toc":
            cites[s][t] += n
    del g
    n_c = 0
    for u in units:
        c = cites.get(u["doc"])
        u["cites"] = [d for d, _ in c.most_common(MAX_CITES)] if c else []
        n_c += len(u["cites"])
    st["units"] = len(units)
    st["units_with_cites"] = sum(1 for u in units if u["cites"])
    st["cites_per_unit_mean"] = round(n_c / max(1, len(units)), 1)
    st["docs_covered"] = len({u["doc"] for u in units})
    lens = sorted(len(u["q"]) for u in units)
    st["q_len_median"] = lens[len(lens) // 2] if lens else 0
    for i, u in enumerate(units):
        u["id"] = i
    (CACHE / "C_bank.json").write_text(json.dumps({"units": units, "stats": st}, ensure_ascii=False))
    print(json.dumps(st, ensure_ascii=False, indent=1))
    import random
    random.seed(1)
    for kind in ("pq_q", "pq_block", "pq_subject", "faq", "ruling_objet", "ruling_tags"):
        ex = [u for u in units if u["kind"] == kind]
        for u in random.sample(ex, min(2, len(ex))):
            print(f"[{kind}] {u['q'][:200]}  → {u['doc'][:60]} (+{len(u['cites'])} cited)")


if __name__ == "__main__":
    main()
