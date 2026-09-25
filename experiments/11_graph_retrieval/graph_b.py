#!/usr/bin/env python3
"""Citation / structure graph for corpus B (5,853 legal articles of the default subset).

Built without any LLM:
* ``cite``   – regex references inside the article text ("article 145/33", "art. 215, § 2",
               "articles 202 à 205", "l'article 44 du Code de la TVA", "article 5 de l'arrêté
               royal n° 1" …) resolved to article ids of the same code, or of the named code.
               Amendment notes ("art. 119, § 2, L 17.03.2019") and references to laws / other
               codes that are not in the corpus are counted as unresolved.
* ``seq``    – sequential neighbours (previous / next article of the same code, file order).
* ``heading`` (group) – articles under the same heading path (same Section) form a group.

  uv run python graph_b.py [--tag B_raw]      → cache/<tag>_graph.json + stats on stdout
"""
from __future__ import annotations

import argparse
import collections
import json
import re
import time

from common11 import CACHE  # noqa: E402
from cleanup import clean_article, region_of_code  # noqa: E402  (08_corpus_b_cleanup)

SUFFIX = r"(?:bis|ter|quater|quinquies|sexies|septies|octies|novies|decies|undecies|duodecies)?"
NUM_RE = re.compile(rf"(\d(?:\.\d+){{4}}|\d+(?:/\d+)?{SUFFIX})(er\b|°)?", re.I)
MARK_RE = re.compile(r"§|\bal\.|\balin[ée]as?\b|\bn°|\bpar\.", re.I)
ART_RE = re.compile(r"(?<![\w/])(?:articles?|art\.?)\s*(?=\d)", re.I)
SPAN_STOP = re.compile(
    r"[;:()\[\]]|\.\s|\s(?:du|de|des|d'|d’|est|sont|ne|n'|n’|qui|que|au|aux|pour|par|dans|en|sur|vis[ée]e?s?|"
    r"pr[ée]cit[ée]e?s?|ci-|tels?|telles?|ainsi|sans|selon|lorsque|si|ou|où|CIR|AR|L|LP|Lprog|D|AGW|AGF|Décr)\b",
    re.I)
EXTERNAL_RE = re.compile(
    r"^\s*,?\s*(?:(?:L|LP|Lprog|AR|AGW|AGF|AGBC|D|Décr\.?|AM|O)\s+\d{1,2}[./]\d{1,2}[./]\d{2,4}|loi|arrêté|décret|ordonnance|"
    r"Loi-programme|de la loi|du décret|de l'arrêté|de l’arrêté|de l'ordonnance|de la loi-programme|"
    r"du Code des sociétés|du Code civil|du Code pénal|du Code judiciaire|de la Constitution|du Code de droit économique|"
    r"du Code de commerce|du Code de la démocratie|du Code wallon|de la directive|du règlement|du Traité)", re.I)
CODE_HINTS = [  # (regex on the tail after the numbers, target family)
    (re.compile(r"Code de la (?:TVA|taxe sur la valeur ajoutée)|\bC\.?\s?TVA\b|Code TVA", re.I), "ctva"),
    (re.compile(r"Code des impôts sur les revenus|\bCIR\s*(?:92|1992)?\b|\bC\.?I\.?R\.?\b", re.I), "cir92"),
    (re.compile(r"Code des droits de succession|\bC\.?\s?succ", re.I), "csucc"),
    (re.compile(r"Code des droits d['’]enregistrement|\bC\.?\s?enr", re.I), "cenr"),
    (re.compile(r"Code des taxes assimilées|\bCTA\b", re.I), "cta"),
    (re.compile(r"Code du recouvrement|\bCRAF\b", re.I), "crecouv"),
    (re.compile(r"Code bruxellois de la procédure fiscale|\bC\.?B\.?P\.?F\b", re.I), "cbpf"),
    (re.compile(r"Codex|Code flamand de la fiscalité|\bVCF\b", re.I), "vcf"),
    (re.compile(r"arrêté royal n[°o]\s*(\d+)|\bAR\s*n[°o]\s*(\d+)", re.I), "artva"),
]
SAME_CODE_RE = re.compile(r"^\s*,?\s*(?:du|de ce|de la|de l')\s+(?:même|présent)\s+(?:Code|arrêté)|^\s*,?\s*du\s+Code\b", re.I)
FAMILY_OF_CODE = {"cir92": "cir92", "arcir92": "cir92", "ctva": "ctva", "artva": "ctva", "vcf": "vcf", "avcf": "vcf",
                  "crecouv": "crecouv", "cbpf": "cbpf", "ue282": "ue282", "agbxl2019": "agbxl2019",
                  "ar1927": "cenr", "ar1936_bxl": "csucc", "ar1936_vla": "csucc", "ar1940": "cenr"}
REGIONAL_FAMILIES = {"csucc", "cenr", "cta"}


def parse_numbers(span: str) -> list[str]:
    """Article numbers in a reference span, skipping paragraph / alinéa / n° markers and ranges."""
    out: list[str] = []
    pos = 0
    skip_next = False
    tokens = []
    for m in re.finditer(rf"({MARK_RE.pattern})|{NUM_RE.pattern}|(\bà\b)", span, re.I):
        tokens.append(m)
    for m in tokens:
        if m.group(1):            # § / al. / n° marker
            skip_next = True
            continue
        if m.group(4):            # 'à' → range
            out.append("à")
            continue
        num, tail = m.group(2), m.group(3)
        if skip_next or tail:     # '§ 2', 'alinéa 1er', '3°'
            skip_next = False
            continue
        out.append(num)
    return out


class GraphB:
    def __init__(self, docs: list[dict]):
        self.docs = docs
        self.ids = [d["id"] for d in docs]
        self.idset = set(self.ids)
        self.by_code: dict[str, list[str]] = collections.defaultdict(list)
        for d in docs:
            self.by_code[d["meta"]["code"]].append(d["id"])
        self.pos = {i: k for c, lst in self.by_code.items() for k, i in enumerate(lst)}
        self.codes = list(self.by_code)
        self.stats: collections.Counter = collections.Counter()
        self.unresolved_examples: list[str] = []
        self.edges: list[tuple[str, str, str, float]] = []
        self.groups: dict[str, list[list[str]]] = {}

    # ── resolution helpers ─────────────────────────────────────────────
    def _target_codes(self, src_code: str, tail: str) -> list[str] | None:
        """Codes a reference may point to, from the text after the number list."""
        region = region_of_code(src_code)
        fam = FAMILY_OF_CODE.get(src_code, src_code.split("_")[0])
        m = EXTERNAL_RE.match(tail)
        for rx, family in CODE_HINTS:
            mm = rx.search(tail[:90])
            if mm and (not m or mm.start() < m.start()):
                if family == "artva":
                    n = mm.group(1) or mm.group(2)
                    return [f"artva:AR{n}"]
                return self._family_codes(family, region)
        if m:
            return None
        if SAME_CODE_RE.match(tail) or not re.match(r"^\s*,?\s*(?:du|de la|de l['’])\s", tail):
            return self._family_codes(fam, region, own=src_code)
        return None

    def _family_codes(self, family: str, region: str, own: str | None = None) -> list[str]:
        if family in REGIONAL_FAMILIES:
            if region in ("wal", "bxl", "vla"):
                return [f"{family}_{region}"]
            return [c for c in self.codes if c.startswith(family + "_")]
        if own and own in self.codes and family == FAMILY_OF_CODE.get(own, own):
            if own in ("arcir92", "artva", "avcf"):
                return [own] if own != "artva" else [own]
            return [own]
        return [c for c in (family,) if c in self.codes] or [c for c in self.codes if c.startswith(family)]

    def _resolve_one(self, code: str, num: str, ar: str | None) -> str | None:
        num = num.replace("er", "")
        cands = [f"{code}:{num}"] if not ar else [f"{ar}:{num}"]
        for c in cands:
            if c in self.idset:
                return c
        if "/" not in num and num.isdigit() and len(num) >= 3:   # flattened superscript 14515 → 145/15
            for k in range(1, len(num)):
                c = f"{code}:{num[:k]}/{num[k:]}"
                if c in self.idset and num[k] != "0":
                    return c
        return None

    def _expand_range(self, code: str, a: str, b: str, ar: str | None) -> list[str]:
        ia, ib = self._resolve_one(code, a, ar), self._resolve_one(code, b, ar)
        if not ia or not ib:
            return [x for x in (ia, ib) if x]
        lst = self.by_code[ia.split(":")[0]]
        pa, pb = self.pos[ia], self.pos[ib]
        if pa > pb or pb - pa > 40:
            return [ia, ib]
        return lst[pa: pb + 1]

    # ── build ──────────────────────────────────────────────────────────
    def extract_citations(self) -> None:
        cite = collections.Counter()
        for d in self.docs:
            src, code = d["id"], d["meta"]["code"]
            text = clean_article(d["text"])
            for m in ART_RE.finditer(text):
                self.stats["mentions"] += 1
                rest = text[m.end(): m.end() + 200]
                stop = SPAN_STOP.search(rest)
                span = rest[: stop.start()] if stop else rest[:120]
                tail = rest[len(span):]
                nums = parse_numbers(span)
                if not nums:
                    self.stats["unresolved:no_number"] += 1
                    continue
                targets = self._target_codes(code, tail)
                if targets is None:
                    self.stats["unresolved:external"] += 1
                    if len(self.unresolved_examples) < 40:
                        self.unresolved_examples.append((m.group(0) + span + tail[:40]).replace("\n", " "))
                    continue
                resolved: set[str] = set()
                for tcode in targets:
                    ar = tcode if ":" in tcode else None          # artva:AR1
                    tc = tcode.split(":")[0]
                    i = 0
                    while i < len(nums):
                        if i + 2 < len(nums) and nums[i + 1] == "à":
                            resolved.update(self._expand_range(tc, nums[i], nums[i + 2], ar)); i += 3; continue
                        if nums[i] != "à":
                            r = self._resolve_one(tc, nums[i], ar)
                            if r:
                                resolved.add(r)
                        i += 1
                if not resolved:
                    self.stats["unresolved:no_such_article"] += 1
                    if len(self.unresolved_examples) < 40:
                        self.unresolved_examples.append(("?? " + m.group(0) + span + tail[:40]).replace("\n", " "))
                    continue
                self.stats["resolved_mentions"] += 1
                for t in resolved:
                    if t != src:
                        cite[(src, t)] += 1
        for (s, t), n in cite.items():
            self.edges.append((s, t, "cite", float(n)))
        self.stats["edges:cite"] = len(cite)

    def add_sequential(self) -> None:
        n = 0
        for code, lst in self.by_code.items():
            for a, b in zip(lst, lst[1:]):
                self.edges.append((a, b, "seq", 1.0)); n += 1
        self.stats["edges:seq"] = n

    def add_heading_groups(self) -> None:
        g: dict[tuple, list[str]] = collections.defaultdict(list)
        for d in self.docs:
            g[(d["meta"]["code"], tuple(d["meta"].get("heading_path") or []))].append(d["id"])
        groups = [v for v in g.values() if len(v) > 1]
        self.groups["heading"] = groups
        self.stats["groups:heading"] = len(groups)
        self.stats["groups:heading_mean_size"] = round(sum(map(len, groups)) / max(1, len(groups)), 1)
        self.stats["groups:heading_max_size"] = max(map(len, groups)) if groups else 0

    def report(self) -> dict:
        import networkx as nx
        G = nx.DiGraph()
        G.add_nodes_from(self.ids)
        G.add_edges_from((s, t) for s, t, ty, _ in self.edges if ty == "cite")
        indeg = collections.Counter(t for s, t, ty, _ in self.edges if ty == "cite")
        outdeg = collections.Counter(s for s, t, ty, _ in self.edges if ty == "cite")
        deg = [G.in_degree(n) + G.out_degree(n) for n in G.nodes]
        und = G.to_undirected()
        comps = sorted((len(c) for c in nx.connected_components(und)), reverse=True)
        top_cited = [f"{k} ({v})" for k, v in indeg.most_common(12)]
        rep = {
            "n_nodes": len(self.ids), "n_cite_edges": G.number_of_edges(),
            "cite_isolated_pct": round(100 * sum(1 for x in deg if x == 0) / len(deg), 1),
            "cite_deg_mean": round(sum(deg) / len(deg), 2), "cite_deg_median": sorted(deg)[len(deg) // 2],
            "cite_deg_p90": sorted(deg)[int(0.9 * len(deg))], "cite_deg_max": max(deg),
            "cite_out_nodes": len(outdeg), "cite_in_nodes": len(indeg),
            "largest_components": comps[:5], "n_components": len(comps),
            "top_cited": top_cited,
            "cross_code_cite_pct": round(100 * sum(1 for s, t, ty, _ in self.edges if ty == "cite" and s.split(":")[0] != t.split(":")[0]) / max(1, G.number_of_edges()), 1),
        }
        rep.update(self.stats)
        return rep


def build(tag: str = "B_raw") -> tuple[GraphB, dict]:
    docs = json.loads((CACHE / f"{tag}_docs.json").read_text())
    t0 = time.perf_counter()
    g = GraphB(docs)
    g.extract_citations()
    g.add_sequential()
    g.add_heading_groups()
    rep = g.report()
    rep["build_s"] = round(time.perf_counter() - t0, 1)
    (CACHE / f"{tag}_graph.json").write_text(json.dumps(
        {"nodes": g.ids, "edges": g.edges, "groups": g.groups, "stats": rep}, ensure_ascii=False))
    return g, rep


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="B_raw")
    a = ap.parse_args()
    g, rep = build(a.tag)
    print(json.dumps(rep, ensure_ascii=False, indent=1))
    print("\nunresolved examples:")
    for e in g.unresolved_examples[:40]:
        print("  ", e[:120])
