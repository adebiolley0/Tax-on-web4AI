#!/usr/bin/env python3
"""Reception field for corpus C: for every Fisconet+ document, the sentences of *other* corpus-C documents
that cite it (by article reference, circular number, ruling number, court decision, parliamentary question,
royal-decree number or Rép. RJ commentary number).

Resolution = experiment 11's `graph_c.GraphC` (title keys, article / circular / ruling / case-law / PQ / AR
grammars, region-aware article resolution) after experiment 20's PDF-flattening normalisation of the body;
this module only adds the *position* of every resolved mention and keeps the sentence around it
(experiment 20's sentence splitter), which the exp-11 graph did not store.

  cd experiments/13_lexical_upgrades && .venv/bin/python ../23_reception_c/reception_c.py                  → cache/C_reception.json
  cd experiments/13_lexical_upgrades && .venv/bin/python ../23_reception_c/reception_c.py --exclude-mined  → cache/C_reception_nomined.json
"""
from __future__ import annotations

import argparse
import bisect
import collections
import json
import re
import time

from common23 import CACHE, EXPS, STATUTE_FOLDERS  # noqa: E402 (sets sys.path)
from rag_eval import load_questions_c, load_questions_mined
from rag_eval.corpora import CORPUS_C_DIR, _parse_front_matter
from refparse import iter_article_refs, classify_tail, expand_items  # noqa: E402
import graph_c  # noqa: E402
from graph_c import (GraphC, title_keys, canonical, region_of, DOMAIN_FAMILY, CIRC_TEXT_RE, ET_TEXT_RE, DA_TEXT_RE, DA_LIST_RE,
                     JUR_TEXT_RE, CASS_TEXT_RE, CASE_RE, QP_TEXT_RE, AR_TEXT_RE, norm_court, norm_date)  # noqa: E402
import reception as rec20  # noqa: E402  (experiment 20: normalise_body, clean_sentence, is_dutch)
from common20 import sentence_spans, fold  # noqa: E402

MAX_CHARS = 200_000
CAP_SENTENCES = 40
CAP_TITLES = 10
SOURCE_TYPE = {
    "circulaires": "circ", "commentaires_dont_rep_rj": "com", "questions_parlementaires": "qp", "faq": "faq",
    "decisions_anticipees_l_24_12_2002": "ruling", "decisions_anticipees_art_345_cir_92": "ruling", "decisions_anticipees_ar_03_05_1999": "ruling",
    "decisions": "ruling", "jurisprudence_belge": "jur", "jurisprudence_europeenne": "jur",
    "avis": "avis", "communications": "avis", "informations_et_communications": "avis", "actes_administratifs": "avis",
    "forfaits": "forfait", "conventions_preventives_de_la_double_imposition": "cpdi", "traites_et_accords_internationaux": "cpdi",
    "arretes_royaux": "ar", "arretes_ministeriels": "ar",
    "code_et_legislation": "code", "legislation_et_reglementation_regionale_et_locale": "code", "reglementation_europeenne": "code",
    "annexes": "other", "sans_type": "other",
}
# round-robin priority when the cap binds: paraphrase-rich sources first, statute cross-references last
TYPE_ORDER = ["circ", "com", "qp", "faq", "ruling", "jur", "avis", "forfait", "cpdi", "ar", "code", "other"]
_LETTERS = re.compile(r"[A-Za-zÀ-ÿ]")
# Rép. RJ commentary numbers: title "Numéro R 117, § 1/10-01" ↔ text "Rép. RJ R 117, § 1/10-01"
RJ_TITLE_RE = re.compile(r"^Num[ée]ro\s+([A-Z])\s?(\d+(?:\^\d+)?)\s*(?:,\s*(§\s?\d+|al\.\s?\d+|\d+°))?\s*/\s?(\d{2}-\d{2})", re.I)
RJ_TEXT_RE = re.compile(r"R[ée]p\.?\s?RJ\s*,?\s*([A-Z])\s?(\d+(?:[\^/]\d+)?)\s*,?\s*(§\s?\d+|al\.\s?\d+|\d+°)?\s*/\s?(\d{2}-\d{2})")


def rj_key(letter: str, num: str, qual: str | None, code: str) -> str:
    q = re.sub(r"\s+", "", qual or "")
    return f"rj:{letter.lower()}{num.replace('^', '/')}{q}/{code}"


class ReceptionC(GraphC):
    """exp-11 graph builder + document dates, twin keys, RJ keys and mention positions."""

    def load(self) -> list[tuple[str, str]]:
        bodies = []
        t0 = time.perf_counter()
        for folder in sorted(p for p in CORPUS_C_DIR.iterdir() if p.is_dir()):
            for p in sorted(folder.glob("*.md")):
                raw = p.read_text(encoding="utf-8", errors="replace")
                fm, body = _parse_front_matter(raw)
                body = body.strip()
                if body.startswith("# "):
                    body = body.split("\n", 1)[1] if "\n" in body else ""
                did = f"{folder.name}/{p.stem}"
                title = fm.get("title", p.stem)
                path = fm.get("path", []) if isinstance(fm.get("path"), list) else []
                keys, attrs = title_keys(title, folder.name, path)
                if folder.name == "commentaires_dont_rep_rj":
                    mm = RJ_TITLE_RE.match(title.strip())
                    if mm:
                        keys.append(rj_key(*mm.groups()))
                dom = path[1] if len(path) > 1 else ""
                m = {"title": title, "folder": folder.name, "path": path, "date": fm.get("document_date") or "",
                     "region": region_of(title, path), "default_family": DOMAIN_FAMILY.get(dom), "keys": keys,
                     "twin": canonical(title, folder.name, "twin"), "stype": SOURCE_TYPE.get(folder.name, "other"), **attrs}
                self.ids.append(did)
                self.meta[did] = m
                for k in keys:
                    self.key_index[k].append(did)
                if "family" in attrs:
                    self.art_by_family[attrs["family"]].add(attrs["num"])
                bodies.append((did, body[:MAX_CHARS]))
        self.stats["load_s"] = round(time.perf_counter() - t0, 1)

        def sort_key(n):
            m = re.match(r"(\d+)(?:/(\d+))?(\D*)", n)
            return (int(m.group(1)), int(m.group(2) or 0), m.group(3)) if m else (10**9, 0, n)
        self.family_order = {f: sorted(s, key=sort_key) for f, s in self.art_by_family.items()}
        return bodies

    # ── extraction with positions ──────────────────────────────────────
    def mentions(self, did: str, body: str) -> list[tuple[str, int, str]]:
        """[(target doc, mention position, edge type)] for every resolved reference in ``body``."""
        m = self.meta[did]
        own_fam = m.get("family") or m.get("default_family")
        region = m.get("region")
        st = self.stats
        out: list[tuple[str, int, str]] = []

        def link(key: str, pos: int, typ: str, fam: str) -> None:
            targets = self.key_index.get(key)
            if targets:
                st[f"{fam}:resolved"] += 1
                out.extend((t, pos, typ) for t in targets)
            else:
                st[f"{fam}:unresolved"] += 1
                if len(self.examples[f"{fam}_unresolved"]) < 8:
                    self.examples[f"{fam}_unresolved"].append(f"{did}: {key}")

        for pos, items, tail in iter_article_refs(body):
            st["art:mentions"] += 1
            kind, val = classify_tail(tail)
            if kind == "external":
                st["art:unresolved:external"] += 1; continue
            if kind == "ar":
                fam_docs = self.key_index.get(f"ar:tva:{val}") if own_fam == "ctva" else self.key_index.get(f"ar:other:{val}")
                if fam_docs:
                    out.extend((t, pos, "cite_ar") for t in fam_docs); st["art:resolved:ar"] += 1
                else:
                    st["art:unresolved:ar"] += 1
                continue
            if kind == "family":
                fam = val
            else:
                if val in ("loi", "décret", "ordonnance", "wet", "decreet", "arrêté", "besluit") and not m.get("family"):
                    st["art:unresolved:same_law"] += 1; continue
                fam = own_fam
                if fam is None:
                    st["art:unresolved:no_default_code"] += 1; continue
                if kind == "same" and val == "":
                    st["art:bare"] += 1
            if fam not in self.art_by_family:
                st["art:unresolved:family_absent"] += 1; continue
            targets = expand_items(items, lambda n: self._art_docs(fam, n, region), lambda a, b: self._art_range(fam, a, b, region))
            if not targets:
                st["art:unresolved:no_such_article"] += 1; continue
            st["art:resolved"] += 1
            out.extend((t, pos, "cite_art") for t in targets)
        for mm in CIRC_TEXT_RE.finditer(body):
            st["circ:mentions"] += 1
            g = mm.groups()
            if g[0]:
                key = f"c:{g[0]}/C/{g[1]}"
            elif g[2]:
                key = f"c:{g[2]}/{g[3]}"
            elif g[4]:
                key = "c:ci." + g[4].lower() + "." + g[5]
            else:
                key = f"c:{g[6]}@{g[7]}"
            link(key, mm.start(), "cite_circ", "circ")
        for mm in ET_TEXT_RE.finditer(body):
            st["circ:mentions"] += 1
            link("c:et." + mm.group(1).replace(",", "."), mm.start(), "cite_circ", "circ")
        das: dict[str, int] = {}
        for mm in DA_TEXT_RE.finditer(body):
            das.setdefault(mm.group(1), mm.start())
        if m["folder"].startswith("decisions_anticipees"):
            for mm in DA_LIST_RE.finditer(body):
                if f"da:{mm.group(1)}" in self.key_index:
                    das.setdefault(mm.group(1), mm.start())
        for x, pos in das.items():
            st["da:mentions"] += 1
            link(f"da:{x}", pos, "cite_da", "da")
        for mm in JUR_TEXT_RE.finditer(body):
            st["jur:mentions"] += 1
            link(f"jur:{norm_court(mm.group('court'))}@{norm_date(mm.group('date'))}", mm.start(), "cite_jur", "jur")
        for mm in CASS_TEXT_RE.finditer(body):
            st["jur:mentions"] += 1
            link(f"jur:cass@{norm_date(mm.group(1))}", mm.start(), "cite_jur", "jur")
        seen_case: set[str] = set()
        for mm in CASE_RE.finditer(body):
            if mm.group(1) in seen_case:
                continue
            seen_case.add(mm.group(1))
            st["jur:mentions"] += 1
            link(f"case:{mm.group(1)}", mm.start(), "cite_jur", "jur")
        for mm in QP_TEXT_RE.finditer(body):
            st["qp:mentions"] += 1
            link(f"qp:{mm.group(1)}@{mm.group(2)}", mm.start(), "cite_qp", "qp")
        if own_fam == "ctva":
            for mm in AR_TEXT_RE.finditer(body):
                st["ar:mentions"] += 1
                link(f"ar:tva:{mm.group(1)}", mm.start(), "cite_ar", "ar")
        for mm in RJ_TEXT_RE.finditer(body):
            st["rj:mentions"] += 1
            link(rj_key(*mm.groups()), mm.start(), "cite_rj", "rj")
        return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--exclude-mined", action="store_true",
                    help="drop every sentence whose citing document is the source_doc of a mined C question → cache/C_reception_nomined.json")
    args = ap.parse_args()
    excluded: set[str] = set()
    if args.exclude_mined:
        excluded = {q.meta["source_doc"] for q in load_questions_mined("C") if q.meta.get("source_doc")}
    g = ReceptionC()
    bodies = g.load()
    # exp-20 normalisation needs the article numbers that have N/k sub-articles
    rec20.SLASH_STEMS.clear()
    for nums in g.art_by_family.values():
        for n in nums:
            if "/" in n:
                a, b = n.split("/", 1)
                rec20.SLASH_STEMS.setdefault(a, set()).add(b)
    print(f"loaded {len(g.ids)} docs ({g.stats['load_s']}s); keys {sum(len(v) for v in g.key_index.values())}; "
          f"rj keys {sum(1 for k in g.key_index if k.startswith('rj:'))}; excluded sources {len(excluded)}", flush=True)
    st = g.stats
    per_doc: dict[str, list[dict]] = collections.defaultdict(list)
    t0 = time.perf_counter()
    for i, (did, body) in enumerate(bodies):
        if did in excluded:
            st["docs_excluded_mined_source"] += 1
            continue
        m = g.meta[did]
        body = rec20.normalise_body(body)
        ments = g.mentions(did, body)
        if not ments:
            continue
        spans = sentence_spans(body)
        starts = [s for s, _ in spans]
        seen_here: set[tuple[str, int]] = set()
        for dst, pos, typ in ments:
            if dst == did:
                st["skip:self"] += 1; continue
            if g.meta[dst]["twin"] == m["twin"]:
                st["skip:twin"] += 1; continue
            k = bisect.bisect_right(starts, pos) - 1
            if k < 0:
                continue
            a, b = spans[k]
            if (dst, a) in seen_here:
                continue
            seen_here.add((dst, a))
            sent = rec20.clean_sentence(body, a, b, pos)
            if len(sent) < 40 or len(_LETTERS.findall(sent)) < 0.5 * len(sent):
                st["sentence_dropped"] += 1; continue
            per_doc[dst].append({"t": sent, "src": did, "type": m["stype"], "date": m["date"], "title": m["title"], "nl": rec20.is_dutch(sent), "edge": typ})
            st[f"pairs:{typ}"] += 1
            st[f"pairs_from:{m['stype']}"] += 1
        if (i + 1) % 5000 == 0:
            print(f"  {i+1}/{len(bodies)} docs, {sum(len(v) for v in per_doc.values())} pairs ({time.perf_counter()-t0:.0f}s)", flush=True)
    st["extract_s"] = round(time.perf_counter() - t0, 1)

    # cap per target: round-robin over source types (TYPE_ORDER), inside a type over documents (FR first, newest first)
    out: dict[str, dict] = {}
    sizes = []
    for dst, rows in per_doc.items():
        by_type: dict[str, dict[str, list[dict]]] = collections.defaultdict(lambda: collections.defaultdict(list))
        seen_text: set[str] = set()
        for r in rows:
            k = fold(r["t"].lower())
            if k in seen_text:
                continue
            seen_text.add(k)
            by_type[r["type"]][r["src"]].append(r)
        queues = []
        for stype in sorted(by_type, key=lambda t: TYPE_ORDER.index(t) if t in TYPE_ORDER else 99):
            docs = sorted(by_type[stype], key=lambda d: (not by_type[stype][d][0]["nl"], by_type[stype][d][0]["date"]), reverse=True)
            queues.append([by_type[stype][d] for d in docs])
        picked: list[dict] = []
        titles: list[str] = []
        seen_titles: set[str] = set()
        while len(picked) < CAP_SENTENCES and any(queues):
            for q in queues:
                if not q or len(picked) >= CAP_SENTENCES:
                    continue
                docq = q.pop(0)
                r = docq.pop(0)
                picked.append(r)
                if r["title"] not in seen_titles and len(titles) < CAP_TITLES:
                    seen_titles.add(r["title"]); titles.append(r["title"])
                if docq:
                    q.append(docq)
            queues = [q for q in queues if q]
        out[dst] = {"sentences": [{"t": r["t"], "src": r["src"], "type": r["type"], "nl": r["nl"]} for r in picked], "titles": titles,
                    "n_raw": len(rows), "types": sorted(set(r["type"] for r in rows)), "folder": g.meta[dst]["folder"]}
        sizes.append(len(picked))

    # ── coverage ──────────────────────────────────────────────────────
    sizes.sort()
    total_by_folder = collections.Counter(g.meta[d]["folder"] for d in g.ids)
    cov_by_folder = collections.Counter(v["folder"] for v in out.values())
    coverage = {f: {"docs": total_by_folder[f], "with_reception": cov_by_folder.get(f, 0),
                    "pct": round(100 * cov_by_folder.get(f, 0) / total_by_folder[f], 1),
                    "median_sentences": (lambda s: s[len(s) // 2] if s else 0)(sorted(len(v["sentences"]) for v in out.values() if v["folder"] == f)),
                    "at_cap": sum(1 for v in out.values() if v["folder"] == f and len(v["sentences"]) >= CAP_SENTENCES)}
                for f in sorted(total_by_folder, key=lambda f: -total_by_folder[f])}
    st["docs_with_reception"] = len(out)
    st["docs_total"] = len(g.ids)
    st["statute_docs_with_reception"] = sum(1 for v in out.values() if v["folder"] in STATUTE_FOLDERS)
    st["sentences_kept"] = sum(sizes)
    st["sentences_median"] = sizes[len(sizes) // 2] if sizes else 0
    st["docs_at_cap"] = sum(1 for s in sizes if s >= CAP_SENTENCES)
    st["sentences_dutch_kept"] = sum(1 for v in out.values() for r in v["sentences"] if r["nl"])
    st["kept_by_source_type"] = dict(collections.Counter(r["type"] for v in out.values() for r in v["sentences"]).most_common())
    st["top_targets"] = [f"{g.meta[d]['title'][:50]} ({v['n_raw']})" for d, v in sorted(out.items(), key=lambda kv: -kv[1]["n_raw"])[:10]]
    st["excluded_source_docs"] = len(excluded)
    # question-target coverage
    def q_cov(questions, label):
        rows = []
        for q in questions:
            have = [e for e in q.expected if e in out]
            rows.append({"qid": q.qid, "split": q.split, "source": q.meta.get("source"), "n_expected": len(q.expected), "n_with_reception": len(have),
                         "n_sentences": max((len(out[e]["sentences"]) for e in have), default=0), "folders": sorted({e.split("/")[0] for e in q.expected})})
        by = collections.defaultdict(lambda: [0, 0])
        for r in rows:
            key = r["source"] or "human"
            by[key][1] += 1
            by[key][0] += 1 if r["n_with_reception"] else 0
        st[f"qcov:{label}"] = {k: f"{v[0]}/{v[1]}" for k, v in by.items()}
        return rows
    qrows = {"human": q_cov(load_questions_c(), "human"), "mined": q_cov(load_questions_mined("C"), "mined")}
    out_name = "C_reception_nomined.json" if args.exclude_mined else "C_reception.json"
    (CACHE / out_name).write_text(json.dumps({"docs": out, "stats": st, "coverage": coverage, "question_coverage": qrows,
                                              "cap_sentences": CAP_SENTENCES, "cap_titles": CAP_TITLES}, ensure_ascii=False))
    print(json.dumps({k: v for k, v in st.items()}, ensure_ascii=False, indent=1))
    print("\ncoverage by target folder:")
    for f, c in coverage.items():
        print(f"  {f:55s} {c['with_reception']:6d} / {c['docs']:6d} ({c['pct']:5.1f} %)  median {c['median_sentences']:3d}  at cap {c['at_cap']}")
    for k, v in g.examples.items():
        print(f"\n{k}:")
        for e in v[:5]:
            print("  ", e[:150])
    for d in list(out)[:0]:
        pass
    show = [d for d in g.ids if d.startswith("circulaires/circulaire_2025_c_9") or d.startswith("code_et_legislation/article_44_code_de_la_tva")][:2]
    for d in show:
        if d in out:
            print(f"\n{d}: {out[d]['n_raw']} raw, {len(out[d]['sentences'])} kept, types {out[d]['types']}")
            for r in out[d]["sentences"][:5]:
                print(f"   [{r['type']}] {r['t'][:160]}")
    print(f"\nwrote cache/{out_name}", flush=True)


if __name__ == "__main__":
    main()
