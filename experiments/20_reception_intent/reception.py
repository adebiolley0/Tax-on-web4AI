#!/usr/bin/env python3
"""Reception field for corpus B: for every statute article, the sentences of corpus-C documents
(circulars, commentary, rulings, parliamentary answers, FAQ, case law, notices) that cite it.

Re-runs the exp-11 reference grammar (refparse.iter_article_refs / classify_tail) over the
corpus-C source folders, resolves "art. 145/33 CIR 92"-style mentions to corpus-B article ids
(`cir92:145/33`; regional families → the citing document's region or all three regions) and keeps
the *sentence* around each mention, which the exp-11 graph did not store.

  ../14_ltr_fusion/.venv/bin/python reception.py     → cache/B_reception.json (+ stats on stdout)
"""
from __future__ import annotations

import bisect
import collections
import json
import re
import time

from common20 import CACHE, MYFIN, fold, sentence_spans  # noqa: E402  (sets sys.path)
from rag_eval import load_corpus_b
from rag_eval.corpora import _parse_front_matter
from refparse import iter_article_refs, classify_tail, expand_items  # noqa: E402
from graph_c import DOMAIN_FAMILY, region_of  # noqa: E402
from run_exp13 import default_codes_b  # noqa: E402

MAX_CHARS = 200_000
CAP_SENTENCES = 40
CAP_TITLES = 10
MAX_SENT = 600            # chars kept around the mention when the sentence is longer
SOURCE_TYPES = {
    "circulaires": "circ", "commentaires_dont_rep_rj": "com", "decisions_anticipees_l_24_12_2002": "ruling",
    "decisions_anticipees_art_345_cir_92": "ruling", "decisions_anticipees_ar_03_05_1999": "ruling",
    "questions_parlementaires": "qp", "faq": "faq", "jurisprudence_belge": "jur", "jurisprudence_europeenne": "jur",
    "avis": "avis", "communications": "avis", "informations_et_communications": "avis", "forfaits": "forfait",
}
FAM_CODES = {"cir92": ["cir92"], "arcir92": ["arcir92"], "ctva": ["ctva"], "crecouv": ["crecouv"], "cbpf": ["cbpf"], "vcf": ["vcf"]}
REGIONAL = ("csucc", "cenr", "cta")
_WS = re.compile(r"\s+")
_LETTERS = re.compile(r"[A-Za-zÀ-ÿ]")
# PDF-style spacing that defeats the reference grammar: "36 bis" → "36bis", "1 er" → "1er", "C . T . A ." → "C.T.A."
_SP_SUFFIX = re.compile(r"(?<=\d)\s+(bis|ter|quater|quinquies|sexies|septies|octies|novies|decies|undecies|duodecies)\b", re.I)
_SP_ORD = re.compile(r"(?<=\d)\s+(er|ère|e|ème)\b")
_SP_ABBR = re.compile(r"\b([A-Z])\s+\.(?=\s*[A-Z]\b|\s*$|\s*[,;)])")
_SP_SUP = re.compile(r"(?<=\d)\s*\^\s*(?=\d)")
_NL_WORDS = re.compile(r"\b(het|een|van|wordt|niet|zijn|voor|worden|bij|deze|die|dat|met|belasting)\b")
_FR_WORDS = re.compile(r"\b(le|la|les|des|une|est|pour|dans|par|qui|que|ce|cette|sont|impôt)\b")


_SP_SLASH = re.compile(r"(?i)\b(articles?|art\.)\s+(\d{1,3})\s+(\d{1,2})(?![\d°/%]|\s*(?:er|e|ème|bis|ter|quater|à|et|ou)\b|\s*\.\d)")
SLASH_STEMS: dict[str, set[str]] = {}       # filled in main(): article numbers that have N/k sub-articles in corpus B


def _slash(m: re.Match) -> str:
    return f"{m.group(1)} {m.group(2)}/{m.group(3)}" if m.group(3) in SLASH_STEMS.get(m.group(2), ()) else m.group(0)


def normalise_body(body: str) -> str:
    body = body.replace("|", " ")
    body = _SP_SLASH.sub(_slash, body)          # "article 145 33" (flattened superscript) → "article 145/33"
    body = _SP_SUFFIX.sub(lambda m: m.group(1).lower(), body)
    body = _SP_ORD.sub(lambda m: m.group(1), body)
    for _ in range(3):
        body = _SP_ABBR.sub(r"\1.", body)
    body = re.sub(r"(?<=\b[A-Z]\.)\s+(?=[A-Z]\.(?:\s|$))", "", body)      # "C. T. A." → "C.T.A."
    return _SP_SUP.sub("/", body)


def is_dutch(s: str) -> bool:
    return len(_NL_WORDS.findall(s.lower())) > len(_FR_WORDS.findall(s.lower()))


class Resolver:
    def __init__(self, ids: list[str]):
        self.idset = set(ids)
        self.by_code: dict[str, list[str]] = collections.defaultdict(list)
        for i in ids:
            self.by_code[i.split(":")[0]].append(i)
        self.pos = {i: k for lst in self.by_code.values() for k, i in enumerate(lst)}

    def codes_for(self, fam: str, region: str | None) -> list[str]:
        if fam in REGIONAL:
            return [f"{fam}_{region}"] if region in ("wal", "bxl", "vla") else [f"{fam}_{r}" for r in ("wal", "bxl", "vla")]
        return FAM_CODES.get(fam, [])

    def one(self, code: str, num: str, ar: str | None = None) -> list[str]:
        num = num.replace("er", "")
        key = f"{ar}:{num}" if ar else f"{code}:{num}"
        if key in self.idset:
            return [key]
        if "/" not in num and num.isdigit() and 3 <= len(num) <= 5:       # flattened superscript 14515 → 145/15
            for k in range(1, len(num)):
                c = f"{code}:{num[:k]}/{num[k:]}"
                if c in self.idset and num[k] != "0":
                    return [c]
        return []

    def rng(self, code: str, a: str, b: str, ar: str | None = None) -> list[str]:
        ia, ib = self.one(code, a, ar), self.one(code, b, ar)
        if not ia or not ib:
            return ia + ib
        lst = self.by_code[ia[0].split(":")[0]]
        pa, pb = self.pos[ia[0]], self.pos[ib[0]]
        if pa > pb or pb - pa > 40:
            return ia + ib
        return lst[pa: pb + 1]


def clean_sentence(text: str, a: int, b: int, mention: int) -> str:
    if b - a > MAX_SENT:
        a2, b2 = max(a, mention - MAX_SENT // 2), min(b, mention + MAX_SENT // 2)
        s = text[a2:b2]
        if a2 > a:
            s = s[s.find(" ") + 1:] if " " in s[:60] else s
        if b2 < b:
            s = s[: s.rfind(" ")] if " " in s[-60:] else s
    else:
        s = text[a:b]
    return _WS.sub(" ", s).strip()


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--exclude-mined", action="store_true",
                    help="drop every sentence whose citing document is the source_doc of a mined question (B or C set) → cache/B_reception_nomined.json")
    a = ap.parse_args()
    excluded_docs: set[str] = set()
    if a.exclude_mined:
        from rag_eval import load_questions_mined
        for c in ("B", "C"):
            excluded_docs |= {q.meta["source_doc"] for q in load_questions_mined(c) if q.meta.get("source_doc")}
    docs_b = load_corpus_b(codes=default_codes_b())
    R = Resolver([d.doc_id for d in docs_b])
    for d in docs_b:
        art = d.meta.get("article") or ""
        if "/" in art:
            a, b = art.split("/", 1)
            SLASH_STEMS.setdefault(a, set()).add(b)
    per_article: dict[str, list[dict]] = collections.defaultdict(list)
    st = collections.Counter()
    t0 = time.perf_counter()
    for folder, stype in SOURCE_TYPES.items():
        fdir = MYFIN / folder
        if not fdir.is_dir():
            continue
        for p in sorted(fdir.glob("*.md")):
            raw = p.read_text(encoding="utf-8", errors="replace")
            fm, body = _parse_front_matter(raw)
            body = body.strip()
            if body.startswith("# "):
                body = body.split("\n", 1)[1] if "\n" in body else ""
            body = normalise_body(body[:MAX_CHARS])
            did = f"{folder}/{p.stem}"
            if did in excluded_docs:
                st["docs_excluded_mined_source"] += 1
                continue
            title = fm.get("title", p.stem)
            path = fm.get("path", []) if isinstance(fm.get("path"), list) else []
            dom = path[1] if len(path) > 1 else ""
            own_fam = DOMAIN_FAMILY.get(dom)
            region = region_of(title, path)
            date = fm.get("document_date") or ""
            st[f"docs:{stype}"] += 1
            spans = None
            starts = None
            seen_here: set[tuple[str, int]] = set()
            for mstart, items, tail in iter_article_refs(body):
                st["mentions"] += 1
                kind, val = classify_tail(tail)
                if kind == "external":
                    st["unresolved:external"] += 1; continue
                ar = None
                if kind == "ar":
                    if own_fam != "ctva":
                        st["unresolved:ar_other"] += 1; continue
                    codes, ar = ["artva"], f"artva:AR{val}"
                elif kind == "family":
                    codes = R.codes_for(val, region)
                    if not codes:
                        st[f"unresolved:family_absent:{val}"] += 1; continue
                else:
                    if val in ("loi", "décret", "ordonnance", "wet", "decreet", "arrêté", "besluit"):
                        st["unresolved:same_law"] += 1; continue
                    if own_fam is None:
                        st["unresolved:no_default_code"] += 1; continue
                    codes = R.codes_for(own_fam, region)
                    if not codes:
                        st["unresolved:default_absent"] += 1; continue
                    st["bare"] += 1
                targets: set[str] = set()
                for code in codes:
                    targets |= expand_items(items, lambda n: R.one(code, n, ar), lambda a, b: R.rng(code, a, b, ar))
                if not targets:
                    st["unresolved:no_such_article"] += 1; continue
                st["resolved"] += 1
                if spans is None:
                    spans = sentence_spans(body)
                    starts = [s for s, _ in spans]
                k = bisect.bisect_right(starts, mstart) - 1
                if k < 0:
                    continue
                a, b = spans[k]
                sent = clean_sentence(body, a, b, mstart)
                if len(sent) < 40 or len(_LETTERS.findall(sent)) < 0.5 * len(sent):
                    st["sentence_dropped"] += 1; continue
                for t in targets:
                    key = (t, a)
                    if key in seen_here:
                        continue
                    seen_here.add(key)
                    per_article[t].append({"t": sent, "src": did, "type": stype, "date": date, "title": title, "nl": is_dutch(sent)})
                    st[f"pairs:{stype}"] += 1
    st["extract_s"] = round(time.perf_counter() - t0, 1)

    # cap per article: round-robin over source types, inside a type round-robin over documents (newest first)
    out = {}
    sizes = []
    for art, rows in per_article.items():
        by_type: dict[str, dict[str, list[dict]]] = collections.defaultdict(lambda: collections.defaultdict(list))
        seen_text: set[str] = set()
        for r in rows:
            k = fold(r["t"].lower())
            if k in seen_text:
                continue
            seen_text.add(k)
            by_type[r["type"]][r["src"]].append(r)
        queues = []
        for stype in sorted(by_type):
            docs = sorted(by_type[stype], key=lambda d: (not by_type[stype][d][0]["nl"], by_type[stype][d][0]["date"] or ""), reverse=True)
            queues.append([by_type[stype][d] for d in docs])       # list of per-doc lists
        picked: list[dict] = []
        titles: list[str] = []
        seen_titles: set[str] = set()
        while len(picked) < CAP_SENTENCES and any(queues):
            for q in queues:                                    # one sentence per type per round
                if not q or len(picked) >= CAP_SENTENCES:
                    continue
                docq = q.pop(0)
                r = docq.pop(0)
                picked.append(r)
                if r["title"] not in seen_titles and len(titles) < CAP_TITLES:
                    seen_titles.add(r["title"]); titles.append(r["title"])
                if docq:
                    q.append(docq)                              # the document goes to the back of its type queue
            queues = [q for q in queues if q]
        out[art] = {"sentences": [{"t": r["t"], "src": r["src"], "type": r["type"], "nl": r["nl"]} for r in picked],
                    "titles": titles, "n_raw": len(rows), "types": sorted(set(r["type"] for r in rows))}
        sizes.append(len(picked))
    sizes.sort()
    st["articles_with_reception"] = len(out)
    st["articles_total"] = len(docs_b)
    st["sentences_kept"] = sum(sizes)
    st["sentences_median"] = sizes[len(sizes) // 2] if sizes else 0
    st["articles_at_cap"] = sum(1 for s in sizes if s >= CAP_SENTENCES)
    st["sentences_dutch_kept"] = sum(1 for v in out.values() for r in v["sentences"] if r.get("nl"))
    st["top_articles"] = [f"{a} ({v['n_raw']})" for a, v in sorted(out.items(), key=lambda kv: -kv[1]["n_raw"])[:12]]
    by_code = collections.Counter(a.split(":")[0] for a in out)
    st["articles_by_code"] = dict(by_code.most_common())
    out_name = "B_reception_nomined.json" if a.exclude_mined else "B_reception.json"
    st["excluded_source_docs"] = len(excluded_docs)
    (CACHE / out_name).write_text(json.dumps({"articles": out, "stats": st, "cap_sentences": CAP_SENTENCES,
                                              "cap_titles": CAP_TITLES}, ensure_ascii=False))
    print(json.dumps(st, ensure_ascii=False, indent=1))
    for art in ("cir92:145/33", "cir92:14533", "ctva:44", "cir92:130", "cir92:36", "cir92:215"):
        if art in out:
            print(f"\n{art}: {out[art]['n_raw']} raw, {len(out[art]['sentences'])} kept, types {out[art]['types']}")
            for r in out[art]["sentences"][:4]:
                print(f"   [{r['type']}] {r['t'][:160]}")


if __name__ == "__main__":
    main()
