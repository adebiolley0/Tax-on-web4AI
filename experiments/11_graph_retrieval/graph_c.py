#!/usr/bin/env python3
"""Citation / structure graph for corpus C (21,259 Fisconet+ documents), built without an LLM.

Node = document (``folder/stem``, the ids of the harness). Edges / groups:

* ``cite_art``  – in-text article references ("art. 145/33, CIR 92", "article 44 du Code de la TVA",
                  "art. 18, AR/CIR 92", bare "article 22" resolved with the document's default code
                  inferred from its taxonomy path) → the *Code et législation* article documents
                  (all yearly editions; regional editions filtered by the citing document's region).
* ``cite_circ`` – "circulaire 2023/C/76", "circulaire n° 50/2013", "AGFisc N° 17/2016", "Ci.RH.…", "E.T. …"
* ``cite_da``   – "décision anticipée n° 2023.0887" / "DA 2023.0887"
* ``cite_jur``  – "arrêt de la Cour de cassation du 22.05.2025", "jugement du tribunal de première
                  instance de Liège du 24.03.2016", "C-11/07" (CJUE); Dutch titles are normalised too.
* ``cite_qp``   – "question parlementaire n° 552 … du 04.12.2025"
* ``cite_ar``   – "arrêté royal n° 20" (TVA royal decrees)
* ``cite_toc``  – the *found_via* table of contents when it is itself a document of the corpus
* groups: ``found_via`` (the navigation node a document was listed under), ``path`` (taxonomy leaf),
  ``edition`` (yearly editions of the same article / versions), ``twin`` (edition + regional twins).
* ``linked_document_nl`` is reported but useless: the NL twins are not in the (French) corpus.

  uv run python graph_c.py            → cache/C_graph.json + cache/C_docs_meta.json + stats
"""
from __future__ import annotations

import collections
import json
import re
import time
import unicodedata
from pathlib import Path

from common11 import CACHE  # noqa: E402
from rag_eval.corpora import CORPUS_C_DIR, _parse_front_matter  # noqa: E402
from refparse import iter_article_refs, classify_tail, expand_items  # noqa: E402

MAX_CHARS = 200_000
REGION_WORDS = [("wal", r"r[ée]gion wallonne|wallon|waals"), ("bxl", r"bruxelles-capitale|bruxellois|brussels?\b"),
                ("vla", r"r[ée]gion flamande|flamand|vlaams|vlaanderen|autorit[ée] flamande"), ("fed", r"l[ée]gislation f[ée]d[ée]rale")]
DOMAIN_FAMILY = {"Impôts sur les revenus": "cir92", "Taxe sur la valeur ajoutée": "ctva", "Droits de succession": "csucc",
                 "Droits d'enregistrement, d'hypothèque et de greffe": "cenr", "Taxes assimilées aux impôts sur les revenus": "cta",
                 "Droits et taxes divers": "cdtd", "Perception et Recouvrement": "crecouv", "Secteur bancaire": "loibanc"}
CITY_NL = {"gent": "gand", "antwerpen": "anvers", "brussel": "bruxelles", "brugge": "bruges", "leuven": "louvain", "luik": "liege",
           "bergen": "mons", "namen": "namur", "mechelen": "malines", "dendermonde": "termonde", "tongeren": "tongres",
           "kortrijk": "courtrai", "ieper": "ypres", "oudenaarde": "audenarde", "veurne": "furnes", "nijvel": "nivelles",
           "aarlen": "arlon", "doornik": "tournai", "hoei": "huy", "marche-en-famenne": "marche", "marche": "marche"}


def fold(s: str) -> str:
    s = unicodedata.normalize("NFKD", s.lower())
    return "".join(c for c in s if not unicodedata.combining(c))


def region_of(title: str, path: list[str]) -> str | None:
    txt = fold(title + " | " + " | ".join(path))
    for r, rx in REGION_WORDS:
        if re.search(rx, txt):
            return r
    return None


# ── title → keys ─────────────────────────────────────────────────────────────
ART_TITLE_RE = re.compile(r"^Article\s+(?P<num>\d+(?:[\^/]\d+)?(?:bis|ter|quater|quinquies|sexies|septies|octies|novies|decies)?(?:/\d+)?)"
                          r"(?:\s+à\s+\S+)?\s*(?:,|\s+du|\s+de\s+la|\s+de\s+l')?\s*(?P<label>.*)$", re.I)
LABEL_FAMILY = [
    (re.compile(r"AR\s*/\s*CIR", re.I), "arcir92"), (re.compile(r"\bCIR\b", re.I), "cir92"),
    (re.compile(r"Code de la TVA", re.I), "ctva"), (re.compile(r"droits d['’]enregistrement", re.I), "cenr"),
    (re.compile(r"droits de succession", re.I), "csucc"), (re.compile(r"taxes assimilées aux impôts", re.I), "cta"),
    (re.compile(r"Droits et Taxes Divers", re.I), "cdtd"), (re.compile(r"AR\s*/\s*C\.DTD", re.I), "arcdtd"),
    (re.compile(r"Recouvrement", re.I), "crecouv"), (re.compile(r"C\.B\.P\.F", re.I), "cbpf"),
    (re.compile(r"Loi bancaire", re.I), "loibanc"), (re.compile(r"L\.R\.I\.C\.G", re.I), "lricg"),
    (re.compile(r"AR 31\.03\.1936", re.I), "ar1936"),
]
CIRC_KEYS = [
    (re.compile(r"(\d{4})\s*/\s*C\s*/\s*(\d+)", re.I), lambda m: f"c:{m.group(1)}/C/{m.group(2)}"),
    (re.compile(r"(?:AGFisc|AAFisc|AAF|AFER|AFZ|AOIF)\s*(?:N[°o]\.?)?\s*(\d+)\s*/\s*(\d{4})", re.I), lambda m: f"c:{m.group(1)}/{m.group(2)}"),
    (re.compile(r"n[°o]\.?\s*(\d+)\s*/\s*(\d{4})", re.I), lambda m: f"c:{m.group(1)}/{m.group(2)}"),
    (re.compile(r"Ci\.\s?(RH|D)\.?\s?([\d.]+/[\d.]+)", re.I), lambda m: "c:ci." + m.group(1).lower() + "." + m.group(2).replace(" ", "")),
    (re.compile(r"E\.?\s?T\.?\s?(\d{2,3}[.,]\d{3})", re.I), lambda m: "c:et." + m.group(1).replace(",", ".")),
    (re.compile(r"n[°o]\.?\s*(\d+)\s+(?:dd\.|du)\s+(\d{2})\.(\d{2})\.(\d{4})", re.I), lambda m: f"c:{m.group(1)}@{m.group(4)}"),
]
DA_TITLE_RE = re.compile(r"(?:n[°o]|nr\.)\s*\??\s*(\d{3,4}\.\d{3,4})")
JUR_TITLE_RE = re.compile(r"^(?:Arr[êe]t|Jugement|Arrest|Vonnis|Ordonnance)\s+(?:de la|du|de l['’]|van (?:het|de))\s+(?P<court>.+?)\s+(?:du|d\.d\.|dd\.|van)\s+(?P<date>\d{1,2}\.\d{1,2}\.\s?\d{4})", re.I)
CASE_RE = re.compile(r"\b(C-\d{1,4}/\d{2})\b")
QP_TITLE_RE = re.compile(r"(?:Question parlementaire|Parlementaire vraag)\s+(?:orale\s+|mondelinge\s+)?(?:n[°o]|nr\.)\s*(\S+)\s+(?:de|van)\s+.+?\s+(?:du|d\.d\.)\s+(\d{2}\.\d{2}\.\d{4})", re.I)
AR_TITLE_RE = re.compile(r"Arr[êe]t[ée] royal n[°o]\s*(\d+)", re.I)
YEAR_RE = re.compile(r"\s*[-–]?\s*\(?\s*revenus\s+\d{4}\s*\)?|\s*[-–]?\s*version\s+\d+", re.I)
REGION_TITLE_RE = re.compile(r"\s*[-–,]?\s*\(?(?:Région wallonne|Région de Bruxelles-Capitale|Région flamande|Législation fédérale|Autorité flamande)\s*[-–]?\s*\)?", re.I)
RJ_REGION_RE = re.compile(r"-(?:BR|VL|WA|AL|HM|PR)(?=/|\b)")


def norm_court(court: str) -> str:
    c = fold(court)
    if "cassation" in c or "cassatie" in c:
        return "cass"
    if "constitutionnelle" in c or "grondwettelijk" in c or "arbitrage" in c:
        return "cc"
    if "justice" in c or "justitie" in c or "union europ" in c:
        return "cjue"
    if "droits de l'homme" in c or "rechten van de mens" in c:
        return "cedh"
    m = re.search(r"(?:de|d'|te|van)\s+([a-z' -]+?)\s*$", c)
    city = (m.group(1).strip() if m else c.split()[-1]).replace("'", "")
    city = CITY_NL.get(city, city)
    if "appel" in c or "beroep" in c:
        return f"ca:{city}"
    if "premiere instance" in c or "eerste aanleg" in c or "tribunal" in c or "rechtbank" in c:
        return f"tpi:{city}"
    if "travail" in c or "arbeid" in c:
        return f"ctrav:{city}"
    return f"other:{city}"


def norm_date(d: str) -> str:
    p = re.split(r"[./ ]+", d.strip())
    p = [x for x in p if x]
    if len(p) != 3:
        return d
    return f"{int(p[0]):02d}.{int(p[1]):02d}.{p[2]}"


def title_keys(title: str, folder: str, path: list[str]) -> tuple[list[str], dict]:
    """Keys under which a document can be cited + parsed attributes (family, num, edition …)."""
    keys: list[str] = []
    attrs: dict = {}
    t = title.strip()
    m = ART_TITLE_RE.match(t)
    if m and folder in ("code_et_legislation", "arretes_royaux", "legislation_et_reglementation_regionale_et_locale"):
        num = m.group("num").replace("^", "/")
        fam = next((f for rx, f in LABEL_FAMILY if rx.search(m.group("label"))), None)
        if fam:
            reg = region_of(m.group("label"), path) or "fed"
            attrs.update(family=fam, num=num, region=reg)
            keys.append(f"art:{fam}:{num}")
            if fam in ("cenr", "csucc", "cta", "ar1936", "cir92", "arcir92"):
                keys.append(f"art:{fam}:{reg}:{num}")
    if folder == "circulaires" or "circulaire" in fold(t):
        for rx, fn in CIRC_KEYS:
            mm = rx.search(t)
            if mm:
                keys.append(fn(mm))
    if folder.startswith("decisions_anticipees"):
        mm = DA_TITLE_RE.search(t)
        if mm:
            keys.append(f"da:{mm.group(1)}")
    if folder in ("jurisprudence_belge", "jurisprudence_europeenne", "sans_type"):
        mm = JUR_TITLE_RE.match(t)
        if mm:
            keys.append(f"jur:{norm_court(mm.group('court'))}@{norm_date(mm.group('date'))}")
        for c in CASE_RE.findall(t):
            keys.append(f"case:{c}")
    if folder == "questions_parlementaires":
        mm = QP_TITLE_RE.search(t)
        if mm:
            keys.append(f"qp:{mm.group(1)}@{mm.group(2)}")
    if folder == "arretes_royaux":
        mm = AR_TITLE_RE.search(t)
        if mm:
            dom = path[1] if len(path) > 1 else ""
            keys.append(f"ar:{'tva' if 'valeur ajout' in fold(dom) or 'tva' in fold(t) else 'other'}:{mm.group(1)}")
    return keys, attrs


def canonical(title: str, folder: str, level: str) -> str:
    t = YEAR_RE.sub("", title).replace("*", "").strip(" -–")
    if level == "twin":
        t = REGION_TITLE_RE.sub("", t)
        t = RJ_REGION_RE.sub("", t)
        t = re.sub(r"^(\d{3,4}) - .*$", r"forfait \1", t)
        t = re.sub(r"^Numéro (\d{3,4})/\d{4}$", r"forfait \1", t)
    return f"{folder}|{fold(t)}"


# ── in-text references ───────────────────────────────────────────────────────
CIRC_TEXT_RE = re.compile(r"circulaires?\s+(?:n[°o]\.?\s*)?(?:(?:AGFisc|AAFisc|AAF|AFER|AFZ|AOIF)\s*(?:N[°o]\.?)?\s*)?"
                          r"(?:(\d{4})\s*/\s*C\s*/\s*(\d+)|(\d+)\s*/\s*(\d{4})|Ci\.\s?(RH|D)\.?\s?([\d.]+/[\d.]+)|(\d+)\s+(?:dd\.|du)\s+\d{2}\.\d{2}\.(\d{4}))", re.I)
ET_TEXT_RE = re.compile(r"\bE\.?\s?T\.?\s?(\d{2,3}[.,]\d{3})\b")
DA_TEXT_RE = re.compile(r"(?:d[ée]cisions? anticip[ée]es?|voorafgaande beslissing(?:en)?|\bDA|\bVB|ruling)\s*(?:n[°o]s?\.?|nrs?\.?)?\s*\??\s*(\d{3,4}\.\d{3,4})", re.I)
DA_LIST_RE = re.compile(r"(?<=[\s,(])(\d{4}\.\d{3,4})(?=[\s,.;)])")
JUR_TEXT_RE = re.compile(r"(?:arr[êe]t|jugement|arrest|vonnis)s?\s+(?:de la|du|de l['’]|van (?:het|de)|rendu par (?:la|le))?\s*"
                         r"(?P<court>(?:cour|tribunal|hof|rechtbank)[^,;.\n()]{0,60}?)\s*,?\s+(?:du|d\.d\.|dd\.|van|en date du)\s+(?P<date>\d{1,2}[./]\d{1,2}[./]\d{4})", re.I)
CASS_TEXT_RE = re.compile(r"\bCass\.?,?\s+(\d{1,2}\.\d{1,2}\.\d{4})")
QP_TEXT_RE = re.compile(r"questions?(?:\s+parlementaires?)?\s+(?:orale\s+|écrite\s+)?n[°o]\.?\s*(\S+)\s+(?:de|du|van)\s+[^\n]{0,80}?(\d{2}\.\d{2}\.\d{4})", re.I)
AR_TEXT_RE = re.compile(r"(?:arr[êe]t[ée] royal|A\.?R\.?|koninklijk besluit|K\.?B\.?)\s*n[°o]\.?\s*(\d+)\b", re.I)


class GraphC:
    def __init__(self):
        self.ids: list[str] = []
        self.meta: dict[str, dict] = {}
        self.key_index: dict[str, list[str]] = collections.defaultdict(list)
        self.edges: collections.Counter = collections.Counter()      # (src, dst, type) → count
        self.groups: dict[str, list[list[str]]] = {}
        self.stats: collections.Counter = collections.Counter()
        self.examples: dict[str, list[str]] = collections.defaultdict(list)
        self.art_by_family: dict[str, set[str]] = collections.defaultdict(set)   # family → nums
        self.family_order: dict[str, list[str]] = {}

    # ── loading ────────────────────────────────────────────────────────
    def load(self) -> list[tuple[str, str]]:
        """Read myfin_docs once; returns [(doc_id, body)] and fills meta / key index."""
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
                dom = path[1] if len(path) > 1 else ""
                m = {"title": title, "folder": folder.name, "path": path, "found_via": fm.get("found_via"),
                     "guid": fm.get("guid"), "linked_nl": fm.get("linked_document_nl"), "language": fm.get("language"),
                     "region": region_of(title, path), "default_family": DOMAIN_FAMILY.get(dom), "keys": keys, **attrs}
                self.ids.append(did)
                self.meta[did] = m
                for k in keys:
                    self.key_index[k].append(did)
                if "family" in attrs:
                    self.art_by_family[attrs["family"]].add(attrs["num"])
                bodies.append((did, body[:MAX_CHARS]))
        self.stats["load_s"] = round(time.perf_counter() - t0, 1)
        # article order per family for range expansion (numeric-ish sort)
        def sort_key(n):
            m = re.match(r"(\d+)(?:/(\d+))?(\D*)", n)
            return (int(m.group(1)), int(m.group(2) or 0), m.group(3)) if m else (10**9, 0, n)
        self.family_order = {f: sorted(s, key=sort_key) for f, s in self.art_by_family.items()}
        return bodies

    # ── resolution ─────────────────────────────────────────────────────
    def _art_docs(self, fam: str, num: str, region: str | None) -> list[str]:
        num = num.replace("er", "")
        if fam in ("cenr", "csucc", "cta") and region in ("wal", "bxl", "vla"):
            r = self.key_index.get(f"art:{fam}:{region}:{num}")
            if r:
                return r
        r = self.key_index.get(f"art:{fam}:{num}")
        if r:
            return r
        if "/" not in num and num.isdigit() and 3 <= len(num) <= 5:      # flattened superscript
            for k in range(1, len(num)):
                r = self.key_index.get(f"art:{fam}:{num[:k]}/{num[k:]}")
                if r and num[k] != "0":
                    return r
        return []

    def _art_range(self, fam: str, a: str, b: str, region: str | None) -> list[str]:
        order = self.family_order.get(fam, [])
        if a in order and b in order:
            ia, ib = order.index(a), order.index(b)
            if 0 <= ib - ia <= 40:
                out = []
                for n in order[ia: ib + 1]:
                    out += self._art_docs(fam, n, region)
                return out
        return self._art_docs(fam, a, region) + self._art_docs(fam, b, region)

    def _add(self, src: str, dst: str, typ: str) -> None:
        if src != dst:
            self.edges[(src, dst, typ)] += 1

    # ── extraction ─────────────────────────────────────────────────────
    def extract(self, did: str, body: str) -> None:
        m = self.meta[did]
        own_fam = m.get("family") or m.get("default_family")
        region = m.get("region")
        st = self.stats
        # article references
        for _, items, tail in iter_article_refs(body):
            st["art:mentions"] += 1
            kind, val = classify_tail(tail)
            if kind == "external":
                st["art:unresolved:external"] += 1; continue
            if kind == "ar":
                fam_docs = self.key_index.get(f"ar:tva:{val}") if own_fam == "ctva" else self.key_index.get(f"ar:other:{val}")
                if fam_docs:
                    for t in fam_docs:
                        self._add(did, t, "cite_ar")
                    st["art:resolved:ar"] += 1
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
                st["art:unresolved:family_absent"] += 1
                if len(self.examples["family_absent"]) < 10:
                    self.examples["family_absent"].append(f"{did}: {items} {fam} {tail[:40]!r}")
                continue
            targets = expand_items(items, lambda n: self._art_docs(fam, n, region), lambda a, b: self._art_range(fam, a, b, region))
            if not targets:
                st["art:unresolved:no_such_article"] += 1
                if len(self.examples["no_such_article"]) < 12:
                    self.examples["no_such_article"].append(f"{did}: {items} {fam} {tail[:40]!r}")
                continue
            st["art:resolved"] += 1
            for t in targets:
                self._add(did, t, "cite_art")
        # circulars
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
            self._link(did, key, "cite_circ", "circ")
        for mm in ET_TEXT_RE.finditer(body):
            st["circ:mentions"] += 1
            self._link(did, "c:et." + mm.group(1).replace(",", "."), "cite_circ", "circ")
        # rulings
        das = {mm.group(1) for mm in DA_TEXT_RE.finditer(body)}
        if m["folder"].startswith("decisions_anticipees"):
            das |= {x for x in DA_LIST_RE.findall(body) if f"da:{x}" in self.key_index}
        for x in das:
            st["da:mentions"] += 1
            self._link(did, f"da:{x}", "cite_da", "da")
        # court decisions
        for mm in JUR_TEXT_RE.finditer(body):
            st["jur:mentions"] += 1
            self._link(did, f"jur:{norm_court(mm.group('court'))}@{norm_date(mm.group('date'))}", "cite_jur", "jur")
        for mm in CASS_TEXT_RE.finditer(body):
            st["jur:mentions"] += 1
            self._link(did, f"jur:cass@{norm_date(mm.group(1))}", "cite_jur", "jur")
        for c in set(CASE_RE.findall(body)):
            st["jur:mentions"] += 1
            self._link(did, f"case:{c}", "cite_jur", "jur")
        # parliamentary questions
        for mm in QP_TEXT_RE.finditer(body):
            st["qp:mentions"] += 1
            self._link(did, f"qp:{mm.group(1)}@{mm.group(2)}", "cite_qp", "qp")
        # royal decrees by number (outside article references)
        if own_fam == "ctva":
            for mm in AR_TEXT_RE.finditer(body):
                st["ar:mentions"] += 1
                self._link(did, f"ar:tva:{mm.group(1)}", "cite_ar", "ar")

    def _link(self, src: str, key: str, typ: str, fam: str) -> None:
        targets = self.key_index.get(key)
        if targets:
            self.stats[f"{fam}:resolved"] += 1
            for t in targets:
                self._add(src, t, typ)
        else:
            self.stats[f"{fam}:unresolved"] += 1
            if len(self.examples[f"{fam}_unresolved"]) < 8:
                self.examples[f"{fam}_unresolved"].append(f"{src}: {key}")

    # ── structure ──────────────────────────────────────────────────────
    def add_structure(self) -> None:
        guid_to_id = {m["guid"]: d for d, m in self.meta.items() if m.get("guid")}
        fv: dict[str, list[str]] = collections.defaultdict(list)
        pth: dict[tuple, list[str]] = collections.defaultdict(list)
        ed: dict[str, list[str]] = collections.defaultdict(list)
        tw: dict[str, list[str]] = collections.defaultdict(list)
        nl_in = 0
        for d in self.ids:
            m = self.meta[d]
            if m.get("found_via"):
                fv[m["found_via"]].append(d)
                if m["found_via"] in guid_to_id:
                    self._add(d, guid_to_id[m["found_via"]], "cite_toc")
            if m.get("path"):
                pth[tuple(m["path"])].append(d)
            ed[canonical(m["title"], m["folder"], "edition")].append(d)
            tw[canonical(m["title"], m["folder"], "twin")].append(d)
            if m.get("linked_nl") in guid_to_id:
                nl_in += 1
        self.groups = {"found_via": [v for v in fv.values() if len(v) > 1],
                       "path": [v for v in pth.values() if len(v) > 1],
                       "edition": [v for v in ed.values() if len(v) > 1],
                       "twin": [v for v in tw.values() if len(v) > 1]}
        self.stats["found_via_ids_that_are_docs"] = sum(1 for g in fv if g in guid_to_id)
        self.stats["linked_nl_in_corpus"] = nl_in
        for name, gs in self.groups.items():
            sizes = sorted(map(len, gs), reverse=True)
            self.stats[f"groups:{name}"] = len(gs)
            self.stats[f"groups:{name}_docs"] = sum(sizes)
            self.stats[f"groups:{name}_max"] = sizes[0] if sizes else 0
            self.stats[f"groups:{name}_median"] = sizes[len(sizes) // 2] if sizes else 0
        self.canonical = {"edition": {d: canonical(self.meta[d]["title"], self.meta[d]["folder"], "edition") for d in self.ids},
                          "twin": {d: canonical(self.meta[d]["title"], self.meta[d]["folder"], "twin") for d in self.ids}}

    def report(self) -> dict:
        import networkx as nx
        G = nx.DiGraph()
        G.add_nodes_from(self.ids)
        cite = [(s, t) for (s, t, ty) in self.edges if ty.startswith("cite")]
        G.add_edges_from(cite)
        deg = [G.in_degree(n) + G.out_degree(n) for n in G.nodes]
        sd = sorted(deg)
        indeg = collections.Counter(t for s, t in cite)
        comps = sorted((len(c) for c in nx.connected_components(G.to_undirected())), reverse=True)
        by_type = collections.Counter(ty for (_, _, ty) in self.edges)
        by_folder_out = collections.Counter(s.split("/")[0] for (s, t, ty) in self.edges if ty.startswith("cite"))
        rep = {"n_nodes": len(self.ids), "n_cite_edges": len(cite), "edges_by_type": dict(by_type),
               "cite_isolated_pct": round(100 * sum(1 for x in deg if x == 0) / len(deg), 1),
               "cite_deg_mean": round(sum(deg) / len(deg), 2), "cite_deg_median": sd[len(sd) // 2],
               "cite_deg_p90": sd[int(0.9 * len(sd))], "cite_deg_p99": sd[int(0.99 * len(sd))], "cite_deg_max": max(deg),
               "nodes_with_out_cites": sum(1 for n in G.nodes if G.out_degree(n)),
               "nodes_with_in_cites": len(indeg), "largest_components": comps[:5], "n_components": len(comps),
               "top_cited": [f"{self.meta[k]['title'][:50]} ({v})" for k, v in indeg.most_common(12)],
               "cite_edges_by_source_folder": dict(by_folder_out.most_common())}
        rep.update(self.stats)
        return rep


def build() -> tuple[GraphC, dict]:
    g = GraphC()
    bodies = g.load()
    t0 = time.perf_counter()
    for did, body in bodies:
        g.extract(did, body)
    g.stats["extract_s"] = round(time.perf_counter() - t0, 1)
    g.add_structure()
    rep = g.report()
    edges = [(s, t, ty, float(n)) for (s, t, ty), n in g.edges.items()]
    (CACHE / "C_graph.json").write_text(json.dumps({"nodes": g.ids, "edges": edges, "groups": g.groups,
                                                    "canonical": g.canonical, "stats": rep}, ensure_ascii=False))
    (CACHE / "C_docs_meta.json").write_text(json.dumps(
        {d: {k: v for k, v in m.items() if k in ("title", "folder", "path", "region", "default_family", "family", "num")}
         for d, m in g.meta.items()}, ensure_ascii=False))
    return g, rep


if __name__ == "__main__":
    g, rep = build()
    print(json.dumps(rep, ensure_ascii=False, indent=1))
    for k, v in g.examples.items():
        print(f"\n{k}:")
        for e in v:
            print("  ", e[:150])
