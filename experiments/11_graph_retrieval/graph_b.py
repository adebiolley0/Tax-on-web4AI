#!/usr/bin/env python3
"""Citation / structure graph for corpus B (5,853 legal articles of the default subset).

Built without any LLM (see refparse.py for the reference grammar):
* ``cite``    – in-text references resolved to article ids of the same code, or of the named
                code ("du Code de la TVA" → ctva, "AR/CIR 92" → arcir92, "arrêté royal n° 1" →
                artva:AR1 …). Amendment notes ("art. 119, § 2, L 17.03.2019") and references to
                laws / codes outside the corpus are counted as unresolved:external.
* ``seq``     – previous / next article of the same code (file order).
* ``heading`` – group: articles under the same heading path (same Section / Chapter leaf).

  uv run python graph_b.py [--tag B_raw]      → cache/<tag>_graph.json + stats on stdout
"""
from __future__ import annotations

import argparse
import collections
import json
import time

from common11 import CACHE  # noqa: E402
from cleanup import clean_article, region_of_code  # noqa: E402  (08_corpus_b_cleanup)
from refparse import iter_article_refs, classify_tail, expand_items  # noqa: E402

FAMILY_OF_CODE = {"cir92": "cir92", "arcir92": "cir92", "ctva": "ctva", "artva": "ctva", "vcf": "vcf", "avcf": "vcf",
                  "crecouv": "crecouv", "cbpf": "cbpf", "ue282": "ue282", "agbxl2019": "agbxl2019",
                  "ar1927": "cenr", "ar1936_bxl": "csucc", "ar1936_vla": "csucc", "ar1940": "cenr"}
AR_CODES = {"arcir92", "artva", "avcf", "ar1927", "ar1936_bxl", "ar1936_vla", "ar1940", "agbxl2019"}
REGIONAL_FAMILIES = {"csucc", "cenr", "cta"}


class GraphB:
    def __init__(self, docs: list[dict]):
        self.docs = docs
        self.ids = [d["id"] for d in docs]
        self.idset = set(self.ids)
        self.by_code: dict[str, list[str]] = collections.defaultdict(list)
        for d in docs:
            self.by_code[d["meta"]["code"]].append(d["id"])
        self.pos = {i: k for lst in self.by_code.values() for k, i in enumerate(lst)}
        self.codes = list(self.by_code)
        self.stats: collections.Counter = collections.Counter()
        self.unresolved_examples: list[str] = []
        self.edges: list[tuple[str, str, str, float]] = []
        self.groups: dict[str, list[list[str]]] = {}

    # ── resolution ─────────────────────────────────────────────────────
    def _codes_of_family(self, family: str, region: str) -> list[str]:
        if family in REGIONAL_FAMILIES:
            if region in ("wal", "bxl", "vla"):
                return [c for c in self.codes if c == f"{family}_{region}"]
            return [c for c in self.codes if c.startswith(family + "_")]
        return [c for c in self.codes if c == family]

    def _targets(self, src_code: str, tail: str) -> list[str] | None:
        """Codes (or 'artva:ARn' prefixes) a reference may point to."""
        kind, val = classify_tail(tail)
        region = region_of_code(src_code).split(",")[0]
        if kind == "external":
            return None
        if kind == "ar":
            return [f"artva:AR{val}"] if src_code in ("artva", "ctva") else None
        if kind == "family":
            fam = val
            if fam == "cir92" and src_code in ("cir92", "arcir92"):
                return ["cir92"]
            if fam == "arcir92":
                return ["arcir92"] if "arcir92" in self.codes else None
            return self._codes_of_family(fam, region) or None
        # same
        if val in ("arrêté", "besluit"):
            return [src_code] if src_code in AR_CODES else None
        if val in ("loi", "décret", "ordonnance", "wet", "decreet"):
            return None                       # our nodes are codes, "la même loi" is external
        if val == "code" and src_code in AR_CODES:  # "du Code" inside an AR → the parent code
            fam = FAMILY_OF_CODE.get(src_code, src_code)
            return self._codes_of_family(fam, region) if fam in REGIONAL_FAMILIES else [fam]
        return [src_code]

    def _resolve_one(self, code: str, num: str, ar: str | None) -> list[str]:
        num = num.replace("er", "")
        key = f"{ar}:{num}" if ar else f"{code}:{num}"
        if key in self.idset:
            return [key]
        if code == "artva" and not ar:            # bare 'article 5' inside an AR TVA → any AR having it
            return []
        if "/" not in num and num.isdigit() and 3 <= len(num) <= 5:   # flattened superscript 14515 → 145/15
            for k in range(1, len(num)):
                c = f"{code}:{num[:k]}/{num[k:]}"
                if c in self.idset and num[k] != "0":
                    return [c]
        return []

    def _expand_range(self, code: str, a: str, b: str, ar: str | None) -> list[str]:
        ia, ib = self._resolve_one(code, a, ar), self._resolve_one(code, b, ar)
        if not ia or not ib:
            return ia + ib
        lst = self.by_code[ia[0].split(":")[0]]
        pa, pb = self.pos[ia[0]], self.pos[ib[0]]
        if pa > pb or pb - pa > 40:
            return ia + ib
        return lst[pa: pb + 1]

    # ── build ──────────────────────────────────────────────────────────
    def extract_citations(self) -> None:
        cite = collections.Counter()
        for d in self.docs:
            src, code = d["id"], d["meta"]["code"]
            own_ar = src.rsplit(":", 1)[0] if code == "artva" else None
            text = clean_article(d["text"])
            for _, items, tail in iter_article_refs(text):
                self.stats["mentions"] += 1
                targets = self._targets(code, tail)
                if targets is None:
                    self.stats["unresolved:external"] += 1
                    if len(self.unresolved_examples) < 30:
                        self.unresolved_examples.append(f"{src}: {items} | {tail[:60]!r}")
                    continue
                resolved: set[str] = set()
                for tcode in targets:
                    ar = tcode if ":" in tcode else (own_ar if tcode == "artva" else None)
                    tc = tcode.split(":")[0]
                    resolved |= expand_items(items, lambda n: self._resolve_one(tc, n, ar),
                                             lambda a, b: self._expand_range(tc, a, b, ar))
                if not resolved:
                    self.stats["unresolved:no_such_article"] += 1
                    if len(self.unresolved_examples) < 30:
                        self.unresolved_examples.append(f"?? {src}: {items} -> {targets} | {tail[:50]!r}")
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
        for lst in self.by_code.values():
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
        deg = [G.in_degree(n) + G.out_degree(n) for n in G.nodes]
        comps = sorted((len(c) for c in nx.connected_components(G.to_undirected())), reverse=True)
        sd = sorted(deg)
        rep = {
            "n_nodes": len(self.ids), "n_cite_edges": G.number_of_edges(),
            "cite_isolated_pct": round(100 * sum(1 for x in deg if x == 0) / len(deg), 1),
            "cite_deg_mean": round(sum(deg) / len(deg), 2), "cite_deg_median": sd[len(sd) // 2],
            "cite_deg_p90": sd[int(0.9 * len(sd))], "cite_deg_max": max(deg),
            "cite_out_nodes": sum(1 for n in G.nodes if G.out_degree(n)), "cite_in_nodes": len(indeg),
            "largest_components": comps[:5], "n_components": len(comps),
            "top_cited": [f"{k} ({v})" for k, v in indeg.most_common(12)],
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
    for e in g.unresolved_examples:
        print("  ", e[:140])
