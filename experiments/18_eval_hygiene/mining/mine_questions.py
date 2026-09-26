#!/usr/bin/env python3
"""Mine a large document-labelled question set from Fisconet+ Q&A sources — no LLM, regex only
(experiments/ideas/73_larger_test_set_mining.md, round-3 evaluation hygiene part b).

Sources (all in ``myfin_docs/``) and labels:

* **PQ** – parliamentary questions: the ``QUESTION`` block gives the query (interrogative sentences, with
  the first context sentence prepended); the ``RÉPONSE`` block gives the labels: the statute articles it
  cites ("art. 46bis … C. enr.", "article 5 du C.T.A.", bare "article 131" resolved with the PQ's
  taxonomy domain) → corpus B article ids and corpus C ``code_et_legislation`` documents; circulars and
  rulings it cites by number → corpus C documents. The PQ document itself is **never** a target and is
  listed under ``exclude`` (dropped from the ranking at evaluation time: the question text is copied
  from it, so it would otherwise be the trivial rank-1 hit).
* **FAQ** – the 16 FAQ circulars + the 7 ``faq/`` documents: every numbered question heading is a query;
  corpus C target = every FAQ document that contains the same heading (all coexisting versions /
  errata are accepted, as questions_c.json does for editions); corpus B target = the articles cited in
  the answer paragraphs under that heading. These questions are verbatim in their C target
  (BM25-easy) and are reported as a separate slice.
* **RUL** – SDA rulings with an "Objet de la demande" section: the objet paragraph (with the
  "La demande vise à obtenir la confirmation que" boiler-plate stripped) is the query; corpus C target =
  the ruling itself (verbatim slice; cited articles as secondary), corpus B target = the articles the
  objet cites.

Filters: French only; interrogatives ≥ 25 chars; statistics / policy questions dropped by regex
(``combien``, ``statistiques``, ``recettes``, ``envisage``, ``comptez-vous`` …); answers citing nothing
resolvable are dropped; cited articles must exist in the target corpus; ≤ 8 distinct cited articles per
question; near-duplicate questions (3-gram Jaccard ≥ 0.6) collapsed; one question per PQ / ruling,
≤ 25 per FAQ edition group; every document of the 133 human questions (A, B, C sets) is excluded as a
source or a target (leak check, counts reported); each code family capped at 25 % of a set
(newest first, round-robin over target articles).  Ids are stable hashes; split = harness md5 rule.

  cd experiments/13_lexical_upgrades && uv run python ../18_eval_hygiene/mining/mine_questions.py
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import random
import re
import sys
import time
import unicodedata
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXP_DIR = HERE.parents[1]
sys.path.insert(0, str(EXP_DIR / "11_graph_retrieval"))
sys.path.insert(0, str(EXP_DIR / "common"))

from rag_eval.corpora import (CORPUS_A_MANIFEST, CORPUS_B_JSONL, CORPUS_C_DIR, DATA_DIR, QUESTIONS_B,  # noqa: E402
                              QUESTIONS_C, _parse_front_matter, question_split)
from refparse import classify_tail, expand_items, iter_article_refs  # noqa: E402
from graph_c import CIRC_TEXT_RE, DA_TEXT_RE, DOMAIN_FAMILY, ET_TEXT_RE, region_of, title_keys  # noqa: E402

OUT_B = DATA_DIR / "corpus_b" / "questions_b_mined.json"
OUT_C = DATA_DIR / "corpus_c" / "questions_c_mined.json"
REGIONS = ("wal", "bxl", "vla")
REGIONAL_FAMILIES = ("cenr", "csucc", "cta")
B_FAMILY_CODES = {"cir92": ["cir92"], "arcir92": ["arcir92"], "ctva": ["ctva"], "vcf": ["vcf"], "crecouv": ["crecouv"],
                  "cbpf": ["cbpf"], "cenr": ["cenr_{r}"], "csucc": ["csucc_{r}"], "cta": ["cta_{r}"]}
SUFFIX = r"bis|ter|quater|quinquies|sexies|septies|octies|novies|decies|undecies|duodecies"
MAX_Q_CHARS = 700
MAX_ARTICLES = 8
MIN_INTERROGATIVE = 25
FAQ_CAP = 25
CAP_FRAC = 0.30       # with only 5-6 code families present a 25 % cap would discard two thirds of corpus B
DUP_JACCARD = 0.6


# ── text helpers ──────────────────────────────────────────────────────────────
def fold(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", s.lower()) if not unicodedata.combining(c))


def norm_text(t: str) -> str:
    """Undo PDF flattening that breaks the reference grammar: '183 bis' → '183bis', '1 er' → '1er',
    'C . T . A .' → 'C.T.A.', 'C. enr .' → 'C. enr.', '145 /33' → '145/33'."""
    t = re.sub(rf"(\d)\s+({SUFFIX})\b", r"\1\2", t)
    t = re.sub(r"(\d)\s+er\b", r"\1er", t)
    t = re.sub(r"(\d)\s*/\s*(\d)", r"\1/\2", t)
    t = t.replace("\u00ad", "")
    # flattened superscripts of the PDF parse: 'articles 145 8 à 145 16', 'article 201 20, 3°' → 145/8 à 145/16, 201/20
    t = re.sub(rf"((?:art(?:icle)?s?\.?|\bà|\bet|,)\s+)(\d{{2,3}})\s+(\d{{1,2}}(?:{SUFFIX})?)\b(?!\s*[°%/.,]?\d)(?!\s*[°%])", r"\1\2/\3", t, flags=re.I)
    for _ in range(3):
        t = re.sub(r"\b([A-Za-z]{1,5})\s+\.(?=\s|$)", r"\1.", t)
    t = re.sub(r"\b([A-Z])\.\s+(?=[A-Z]\.)", r"\1.", t)      # 'C. T. A.' → 'C.T. A.' → 'C.T.A.'
    t = re.sub(r"\b([A-Z])\.\s+(?=[A-Z]\.)", r"\1.", t)
    return t


EXTRA_HINTS = [(re.compile(p, re.I), fam) for p, fam in [
    (r"^\s*[,(]?\s*(?:du|de la|de l['’]|de)?\s*(?:Code\s+enreg\.?|C\.?\s?enreg\.?|CDE\b|Code des droits d['’]enregistrement)", "cenr"),
    (r"^\s*[,(]?\s*(?:du|de la|de l['’]|de)?\s*(?:Code\s+succ\.?|CDS(?:RF|RW|RB)?\b|Code des droits de succession)", "csucc"),
    (r"^\s*[,(]?\s*(?:du|de la|de l['’]|de)?\s*(?:CTVA\b|Code belge de la TVA|Code de la T\.?V\.?A\.?)", "ctva"),
    (r"^\s*[,(]?\s*(?:du|de la|de l['’]|de)?\s*(?:CIR\s?(?:92|1992)|C\.I\.R\.)", "cir92"),
    (r"^\s*[,(]?\s*(?:du|de la|de l['’]|de)?\s*(?:CDTD\b|C\.?\s?D\.?\s?T\.?\s?D\.?\b)", "cdtd"),
]]


BARE_SKIP_RE = re.compile(r"^\s*,?\s*(?:pr[ée]cit|susvis|susmentionn|ci-dessus|vis[ée] ci|de la pr[ée]sente|dudit arr|de cet arr|de l['’]arr|du projet|de la proposition|"
                          r"of the|van (?:de|het)|de la directive|du r[èe]glement|du trait[ée])", re.I)


def classify(tail: str) -> tuple[str, str]:
    kind, val = classify_tail(tail)
    if kind == "same" and val == "":
        for rx, fam in EXTRA_HINTS:
            if rx.match(tail):
                return "family", fam
    return kind, val


STAT_RES = [re.compile(p) for p in [
    r"\bcombien\b", r"\bnombre\b", r"\bstatistiq", r"\bchiffres?\b", r"\bventil", r"\brecettes?\b", r"\bbudget",
    r"\bpar (region|province|annee|arrondissement|commune|bureau)\b", r"\bdonnees\b", r"\bderni[eè]res? annees\b",
    r"\bpourcentage\b", r"\bproportion\b", r"\bevolution\b", r"\bmontant total\b", r"\ba combien s'elev",
    r"\bcou?t\b", r"\bcoute", r"\beffectifs?\b", r"\bpersonnel\b", r"\bdelai moyen\b", r"\bmoyenne\b", r"\bpart\b",
    r"\bestimation\b", r"\bestim(?:ez|e)-vous\b", r"\bquel est le (?:montant|nombre|total)\b", r"\bannee(?:s)? 20\d\d\b",
    r"\b(?:en|pour|depuis) (?:19|20)\d\d\b", r"\bdossiers\b", r"\bcontroles?\b", r"\btableau\b", r"\bapercu\b",
    r"\bcalcul(?:ee|e)?s? par (?:region|annee)\b",
]]
POLICY_RES = [re.compile(p) for p in [
    r"\benvisag", r"\bcompte-t-(?:il|elle)\b", r"\bcomptez-vous\b", r"\bavez-vous\b", r"\bintention", r"\bpr[eê]ts? [àa]\b",
    r"\bdispos[eé]e?s? [àa]\b", r"\bmesures?\b", r"\binitiatives?\b", r"\bprevoyez-vous\b", r"\bpartagez-vous\b",
    r"\bopinion\b", r"\bposition\b", r"\bvision\b", r"\bjugez-vous\b", r"\bpensez-vous\b", r"\btrouvez-vous\b",
    r"\bconcertation", r"\bnegociation", r"\bne serait-il pas\b", r"\bne faudrait-il pas\b", r"\bn'est-il pas\b",
    r"\bopportun", r"\bsouhaitable\b", r"\breform", r"\bplanning\b", r"\bcalendrier\b", r"\bou en est\b",
    r"\bavancement\b", r"\bpourquoi\b", r"\bgouvernement\b", r"\bministre[- ]president\b", r"\bpolitique\b",
    r"\bproposition de loi\b", r"\bprojet de loi\b", r"\bmodifier la (?:loi|legislation)\b", r"\badapter\b",
    r"\bsupprim", r"\babolir\b", r"\bharmonis", r"\bfaites-vous\b", r"\bpouvez-vous (?:me )?(?:communiquer|fournir|transmettre)\b",
    r"\bquelles? (?:sont|est) (?:votre|vos)\b", r"\bselon vous\b", r"\bvotre (?:avis|analyse|point de vue|sentiment|appreciation)\b",
    r"\bplaidez-vous\b", r"\bsoutenez-vous\b", r"\bregrettez-vous\b", r"\bdeplorez-vous\b", r"\bvoulez-vous\b",
    r"\bcollaborat", r"\bcampagne\b", r"\bsensibilis", r"\bcommunication\b", r"\binformer\b",
    r"\bapplication informatique\b", r"\blogiciel\b", r"\bsite (?:web|internet)\b", r"\bplateforme\b",
    r"\bpromess", r"\bpromis\b", r"\bconfirmez-vous\b", r"\bces informations\b", r"\bcette information\b", r"\bau courant\b", r"\bexpliqu", r"\braisons?\b", r"\bjustifi", r"\b[eê]tes-vous\b", r"\bseriez-vous\b",
    r"\bsera(?:-t-(?:il|elle))?\s+(?:publi|adopt|disponible|mis|pris|pr[eê]t)", r"\bconfirmer (?:que|qu')\s*(?:le|la|les|des) (?:promesse|d[ée]claration)",
    r"\bministre (?:a-t-il|a-t-elle|est-il|est-elle) (?:effectivement|d[ée]j[àa])\b", r"\bd[ée]lai(?:s)? (?:de traitement|d'attente)\b",
]]


def is_policy(sent: str) -> str | None:
    s = fold(sent)
    for rx in STAT_RES:
        if rx.search(s):
            return "stat"
    for rx in POLICY_RES:
        if rx.search(s):
            return "policy"
    return None


ENUM_RE = re.compile(r"^(?:\(?[a-h0-9]{1,2}[.)]\s*)+")
SENT_SPLIT = re.compile(r"(?<=[.?!;:])\s+(?=[A-ZÀ-Ü0-9«\"(\-])")


def split_sentences(block: str) -> list[str]:
    block = re.sub(r"\s+", " ", block).strip()
    out = []
    for s in SENT_SPLIT.split(block):
        s = ENUM_RE.sub("", s.strip()).strip()
        if s:
            out.append(s)
    return out


def shingles(text: str, n: int = 3) -> set[str]:
    w = re.findall(r"[a-z0-9]+", fold(text))
    return {" ".join(w[i: i + n]) for i in range(max(1, len(w) - n + 1))}


def jaccard(a: set, b: set) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def qid(prefix: str, source: str, source_doc: str, key: str = "") -> str:
    """Stable id: hash of the source document (+ the normalised heading for FAQ questions), independent
    of the query text so that text-cleaning changes do not move questions between splits."""
    h = hashlib.sha1(f"{source_doc}\n{key}".encode()).hexdigest()[:8]
    return f"{prefix}-{source.upper()}-{h}"


# ── corpus indexes ────────────────────────────────────────────────────────────
class CorpusC:
    """Front matter of all myfin_docs + full bodies of the three source folders; title keys as in
    experiment 11 (art:<fam>:<num>, art:<fam>:<region>:<num>, c:<circ>, da:<num> …)."""
    SOURCE_FOLDERS = ("questions_parlementaires", "circulaires", "faq", "decisions_anticipees_l_24_12_2002")

    def __init__(self):
        self.meta: dict[str, dict] = {}
        self.body: dict[str, str] = {}
        self.key_index: dict[str, list[str]] = collections.defaultdict(list)
        self.fam_nums: dict[str, set[str]] = collections.defaultdict(set)
        self.guid_to_id: dict[str, str] = {}
        t0 = time.perf_counter()
        for folder in sorted(p for p in CORPUS_C_DIR.iterdir() if p.is_dir()):
            keep_body = folder.name in self.SOURCE_FOLDERS
            for p in sorted(folder.glob("*.md")):
                raw = p.read_text(encoding="utf-8", errors="replace")
                fm, body = _parse_front_matter(raw)
                did = f"{folder.name}/{p.stem}"
                title = fm.get("title", p.stem)
                path = fm.get("path", []) if isinstance(fm.get("path"), list) else []
                keys, attrs = title_keys(title, folder.name, path)
                dom = path[1] if len(path) > 1 else ""
                m = {"title": title, "folder": folder.name, "path": path, "date": fm.get("document_date") or "",
                     "language": fm.get("language"), "guid": fm.get("guid"), "region": region_of(title, path),
                     "domain": dom, "default_family": DOMAIN_FAMILY.get(dom), **attrs}
                self.meta[did] = m
                if fm.get("guid"):
                    self.guid_to_id[fm["guid"]] = did
                for k in keys:
                    self.key_index[k].append(did)
                if "family" in attrs:
                    self.fam_nums[attrs["family"]].add(attrs["num"])
                if keep_body:
                    body = body.strip()
                    if body.startswith("# "):
                        body = body.split("\n", 1)[1] if "\n" in body else ""
                    self.body[did] = body
        self.family_order = {f: sorted(s, key=num_key) for f, s in self.fam_nums.items()}
        print(f"corpus C index: {len(self.meta)} docs, {len(self.body)} source bodies, {len(self.key_index)} keys "
              f"in {time.perf_counter() - t0:.0f}s", flush=True)

    def art_docs(self, fam: str, num: str, region: str | None) -> tuple[list[str], list[str]]:
        """(expected, secondary): regional editions when the region is known (others secondary), else all."""
        num = num.replace("er", "")
        all_ = list(self.key_index.get(f"art:{fam}:{num}", []))
        if not all_ and "/" not in num and num.isdigit() and 3 <= len(num) <= 5:       # flattened superscript
            for k in range(1, len(num)):
                r = self.key_index.get(f"art:{fam}:{num[:k]}/{num[k:]}")
                if r and num[k] != "0":
                    all_ = list(r); break
        if fam in REGIONAL_FAMILIES and region in REGIONS:
            reg = [d for d in all_ if self.meta[d].get("region") == region]
            if reg:
                return reg, [d for d in all_ if d not in reg]
        return all_, []

    def art_range(self, fam: str, a: str, b: str, region: str | None) -> tuple[list[str], list[str]]:
        order = self.family_order.get(fam, [])
        a, b = a.replace("er", ""), b.replace("er", "")
        if a in order and b in order and 0 <= order.index(b) - order.index(a) <= MAX_ARTICLES:
            e, s = [], []
            for n in order[order.index(a): order.index(b) + 1]:
                x, y = self.art_docs(fam, n, region); e += x; s += y
            return e, s
        return [], []


def num_key(n: str):
    m = re.match(r"(\d+)(?:/(\d+))?(\D*)", n)
    return (int(m.group(1)), int(m.group(2) or 0), m.group(3)) if m else (10 ** 9, 0, n)


class CorpusB:
    def __init__(self):
        self.ids: set[str] = set()
        self.by_code_art: dict[tuple[str, str], str] = {}
        self.code_order: dict[str, list[str]] = collections.defaultdict(list)
        with CORPUS_B_JSONL.open(encoding="utf-8") as fh:
            for line in fh:
                r = json.loads(line)
                self.ids.add(r["id"])
                if "@" in r["id"]:
                    continue                           # 'droit futur' variants
                self.by_code_art[(r["code"], r["article"])] = r["id"]
                self.code_order[r["code"]].append(r["article"])
        for c in self.code_order:
            self.code_order[c] = sorted(set(self.code_order[c]), key=num_key)
        print(f"corpus B index: {len(self.ids)} articles, {len(self.code_order)} codes", flush=True)

    def codes_for(self, fam: str, region: str | None) -> list[str]:
        pats = B_FAMILY_CODES.get(fam)
        if not pats:
            return []
        regs = [region] if region in REGIONS else list(REGIONS)
        return [p.format(r=r) for p in pats for r in (regs if "{r}" in p else [""])]

    def art_ids(self, fam: str, num: str, region: str | None) -> list[str]:
        num = num.replace("er", "")
        out = []
        for code in self.codes_for(fam, region):
            i = self.by_code_art.get((code, num))
            if i:
                out.append(i)
        return out

    def art_range(self, fam: str, a: str, b: str, region: str | None) -> list[str]:
        out = []
        a, b = a.replace("er", ""), b.replace("er", "")
        for code in self.codes_for(fam, region):
            order = self.code_order.get(code, [])
            if a in order and b in order and 0 <= order.index(b) - order.index(a) <= MAX_ARTICLES:
                out += [self.by_code_art[(code, n)] for n in order[order.index(a): order.index(b) + 1]]
        return out

    def ar_ids(self, ar_num: str, num: str) -> list[str]:
        i = self.by_code_art.get(("artva", f"AR{ar_num}:{num}"))
        if not i:
            i = f"artva:AR{ar_num}:{num}" if f"artva:AR{ar_num}:{num}" in self.ids else None
        return [i] if i else []


# ── citation extraction ───────────────────────────────────────────────────────
class Cites:
    def __init__(self):
        self.b_expected: list[str] = []
        self.c_expected: list[str] = []
        self.c_secondary: list[str] = []
        self.articles: list[tuple[str, str]] = []     # (family, num) distinct
        self.bare = 0
        self.explicit = 0
        self.evidence: list[str] = []
        self._b_x: list[str] = []; self._c_x: list[str] = []; self._c_s: list[str] = []; self._arts_x: list = []; self._ev_x: list[str] = []
        self.fam_counts: collections.Counter = collections.Counter()    # explicitly named code families (resolvable or not)

    def add(self, lst: list, items):
        for x in items:
            if x not in lst:
                lst.append(x)


def extract_cites(text: str, default_family: str | None, region: str | None, B: CorpusB, C: CorpusC,
                  allow_bare: bool = True, with_docs: bool = True) -> Cites:
    text = norm_text(text)
    out = Cites()
    for pos, items, tail in iter_article_refs(text):
        kind, val = classify(tail)
        if kind == "external":
            continue
        snippet = re.sub(r"\s+", " ", text[max(0, pos - 10): pos + 70])
        if kind == "ar":
            if default_family == "ctva":
                ids = expand_items(items, lambda n: B.ar_ids(val, n), lambda a, b: [])
                if ids:
                    out.add(out.b_expected, ids); out.add(out._b_x, ids); out.explicit += 1
                    out.evidence.append(snippet); out._ev_x.append(snippet)
                    for n in items:
                        if n != "à" and ("artva", n) not in out.articles:
                            out.articles.append(("artva", n)); out._arts_x.append(("artva", n))
            continue
        if kind == "family":
            fam = val
            out.explicit += 1
            out.fam_counts[fam] += 1
        else:
            if val in ("loi", "décret", "ordonnance", "wet", "decreet", "arrêté", "besluit"):
                continue
            if not allow_bare or default_family is None:
                continue
            if BARE_SKIP_RE.match(tail):                      # "article 3 précité" → refers to an earlier (external) act
                continue
            fam = default_family
            out.bare += 1
        nums = [n for n in items if n != "à"]
        b_ids = expand_items(items, lambda n: B.art_ids(fam, n, region), lambda a, b: B.art_range(fam, a, b, region))
        c_exp, c_sec = [], []
        if with_docs:
            def _res(n):
                e, s = C.art_docs(fam, n, region); c_sec.extend(s); return e
            def _rng(a, b):
                e, s = C.art_range(fam, a, b, region); c_sec.extend(s); return e
            c_exp = expand_items(items, _res, _rng)
        if not b_ids and not c_exp:
            continue
        out.add(out.b_expected, sorted(b_ids))
        out.add(out.c_expected, sorted(c_exp))
        out.add(out.c_secondary, sorted(set(c_sec)))
        for n in nums:
            if (fam, n) not in out.articles:
                out.articles.append((fam, n))
        out.evidence.append(snippet)
        if kind == "family":                             # explicit-only copies (used when bare refs are discarded)
            out.add(out._b_x, sorted(b_ids)); out.add(out._c_x, sorted(c_exp)); out.add(out._c_s, sorted(set(c_sec)))
            for n in nums:
                if (fam, n) not in out._arts_x:
                    out._arts_x.append((fam, n))
            out._ev_x.append(snippet)
    if with_docs:
        for mm in CIRC_TEXT_RE.finditer(text):
            g = mm.groups()
            key = (f"c:{g[0]}/C/{g[1]}" if g[0] else f"c:{g[2]}/{g[3]}" if g[2] else
                   "c:ci." + g[4].lower() + "." + g[5] if g[4] else f"c:{g[6]}@{g[7]}")
            docs = C.key_index.get(key)
            if docs:
                out.add(out.c_expected, docs); out.evidence.append(re.sub(r"\s+", " ", mm.group(0)))
        for mm in ET_TEXT_RE.finditer(text):
            docs = C.key_index.get("c:et." + mm.group(1).replace(",", "."))
            if docs:
                out.add(out.c_expected, docs); out.evidence.append(mm.group(0))
        for mm in DA_TEXT_RE.finditer(text):
            docs = C.key_index.get(f"da:{mm.group(1)}")
            if docs:
                out.add(out.c_expected, docs); out.evidence.append(mm.group(0))
    if out.explicit and out.bare:                    # bare refs are a fallback only: keep the explicit citations
        out.b_expected, out.c_expected, out.c_secondary, out.articles, out.evidence = out._b_x, out._c_x, out._c_s, out._arts_x, out._ev_x
        out.bare = 0
    out.c_secondary = [d for d in out.c_secondary if d not in out.c_expected]
    return out


# ── source miners ─────────────────────────────────────────────────────────────
Q_RE = re.compile(r"^QUESTIONS?\s*$", re.M)
R_RE = re.compile(r"^R[ÉE]PONSE\b.*$", re.M)
Q_END_RE = re.compile(r"^(?:QUESTIONS? EN RETOUR|R[ÉE]PONSE EN RETOUR|ANNEXE)\b", re.M)


def build_pq_query(block: str, stats: collections.Counter) -> tuple[str | None, str | None]:
    sents = split_sentences(block)
    inter, dropped = [], []
    for s in sents:
        if not s.endswith("?"):
            continue
        if len(s) < MIN_INTERROGATIVE:
            continue
        why = is_policy(s)
        if why:
            dropped.append(why); continue
        inter.append(s)
    if not inter:
        return None, ("policy" if dropped else "no_question")
    ctx = next((s for s in sents if not s.endswith("?") and len(s) >= 30), None)
    if ctx and len(ctx) > 350:
        ctx = ctx[:350].rsplit(" ", 1)[0] + " …"
    q = ((ctx + " ") if ctx else "") + " ".join(inter)
    if len(q) > MAX_Q_CHARS:                       # cut at a sentence boundary, keep ≥ 1 interrogative
        parts = ([ctx] if ctx else []) + inter
        q, acc = "", []
        for p in parts:
            if acc and len(" ".join(acc + [p])) > MAX_Q_CHARS:
                break
            acc.append(p)
        q = " ".join(acc)
        if not any(p.endswith("?") for p in acc):
            q = " ".join(acc[:-1] + [inter[0]]) if len(acc) > 1 else inter[0]
    return q, None


def mine_pq(C: CorpusC, B: CorpusB, stats: collections.Counter) -> list[dict]:
    rows = []
    for did, body in C.body.items():
        m = C.meta[did]
        if m["folder"] != "questions_parlementaires":
            continue
        stats["pq:docs"] += 1
        if m.get("language") != "fr":
            stats["pq:drop:not_fr"] += 1; continue
        q = Q_RE.search(body); r = R_RE.search(body)
        if not q or not r or r.start() < q.end():
            stats["pq:drop:no_question_answer_blocks"] += 1; continue
        qblock = body[q.end(): r.start()]
        ablock = body[r.end():]
        e = Q_END_RE.search(ablock)
        if e:
            ablock = ablock[: e.start()]
        query, why = build_pq_query(qblock, stats)
        if not query:
            stats[f"pq:drop:{why}"] += 1; continue
        cites = extract_cites(ablock, m.get("default_family"), m.get("region"), B, C)
        if not cites.b_expected and not cites.c_expected:
            stats["pq:drop:no_resolvable_citation"] += 1; continue
        if len(cites.articles) > MAX_ARTICLES:
            stats["pq:drop:too_many_articles"] += 1; continue
        rows.append({"source": "pq", "source_doc": did, "question": query, "date": m["date"], "domain": m.get("default_family") or fold(m["domain"]),
                     "region": m.get("region"), "cites": cites, "exclude": [did]})
        stats["pq:kept"] += 1
    return rows


HEAD_RE = re.compile(r"^\s*(?:#+\s*)?(\d{1,3})[.)]\s+(\S.*\?)\s*$")
SECTION_RE = re.compile(r"^\s*(?:#+\s*|[IVX]+\.\s+|[A-Z]\.\s+)\S")


def faq_headings(body: str) -> list[tuple[int, str, str]]:
    """(line_no, heading_text, answer_text) for the *body* occurrence of every numbered question heading
    (the table of contents lists the same headings first; the last occurrence is the one with an answer)."""
    lines = body.split("\n")
    occ: dict[str, list[int]] = collections.defaultdict(list)
    for i, ln in enumerate(lines):
        mm = HEAD_RE.match(ln)
        if mm:
            occ[norm_heading(mm.group(2))].append(i)
    heads = []
    positions = sorted(i for v in occ.values() for i in v)
    for key, idxs in occ.items():
        i = idxs[-1]
        mm = HEAD_RE.match(lines[i])
        nxt = next((j for j in positions if j > i), None)
        end = nxt if nxt is not None else len(lines)
        ans_lines = []
        for j in range(i + 1, end):
            if SECTION_RE.match(lines[j]) and not lines[j].lstrip().startswith("-"):
                break
            ans_lines.append(lines[j])
        heads.append((i, mm.group(2).strip(), "\n".join(ans_lines).strip()))
    heads.sort()
    return heads


def norm_heading(h: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", fold(h)).strip()


def mine_faq(C: CorpusC, B: CorpusB, stats: collections.Counter) -> list[dict]:
    docs = [d for d, m in C.meta.items() if d in C.body and (m["folder"] == "faq" or "faq" in fold(m["title"]))
            and m["folder"] in ("faq", "circulaires")]
    stats["faq:docs"] = len(docs)
    by_heading: dict[str, list[tuple[str, str, str]]] = collections.defaultdict(list)     # key → [(doc, heading, answer)]
    for did in sorted(docs):
        if C.meta[did].get("language") != "fr":
            continue
        for _, h, ans in faq_headings(C.body[did]):
            by_heading[norm_heading(h)].append((did, h, ans))
    rows = []
    for key, occs in by_heading.items():
        stats["faq:headings"] += 1
        did, h, ans = max(occs, key=lambda x: (C.meta[x[0]]["date"], x[0]))       # newest edition's answer
        h = re.sub(r"\s+", " ", h)
        if len(h) < MIN_INTERROGATIVE:
            stats["faq:drop:short"] += 1; continue
        why = is_policy(h)
        if why:
            stats[f"faq:drop:{why}"] += 1; continue
        m = C.meta[did]
        cites = extract_cites(ans, m.get("default_family"), m.get("region"), B, C, allow_bare=True, with_docs=False)
        c_docs = sorted({o[0] for o in occs})
        rows.append({"source": "faq", "source_doc": did, "question": h, "date": m["date"], "domain": m.get("default_family") or fold(m["domain"]),
                     "region": m.get("region"), "cites": cites, "c_docs": c_docs, "group": "|".join(c_docs), "exclude": [], "key": key})
        stats["faq:kept"] += 1
    return rows


OBJ_RE = re.compile(r"^.*Objet de la demande.*$", re.M)
OBJ_END_RE = re.compile(r"^\s*(?:#+\s*)?(?:II\b|2\.\s|B\.\s|D[ée]cision\b|DECISION\b|Motivation\b)", re.M)
OBJ_BOILER = re.compile(r"^(?:\d+(?:\.\d+)*\s*[.)]?\s*)?(?:la (?:pr[ée]sente )?demande (?:vise|tend|porte|a pour objet|consiste)[^:]{0,160}?:\s*|"
                        r"votre demande (?:porte|tend|vise)[^:]{0,120}?:\s*|"
                        r"(?:le|les) demandeurs? (?:souhaitent?|demandent?|sollicitent?) [^:]{0,120}?:\s*)", re.I)


OBJ_BOILER2 = re.compile(r"^(?:(?:la|votre|cette) (?:pr[ée]sente )?demande (?:vise|tend|a pour (?:but|objet))(?: [àa])? ?(?:obtenir|savoir|confirmer|ce que)?\s*"
                         r"(?:la confirmation|une d[ée]cision anticip[ée]e|une d[ée]cision|confirmation|l['’]accord)?[^:;]{0,70}?"
                         r"\b(?:que|si|selon laquelle|confirmant que|sur (?:la|le) (?:question|point) de savoir si|de savoir si|quant [àa] savoir si)\s+"
                         r"|(?:la|votre|cette) demande (?:porte|concerne|vise|tend) [^:;]{0,60}?\b(?:la question de savoir si|le point de savoir si|de savoir si|"
                         r"la confirmation (?:que|de ce que|des points suivants|du point suivant|selon laquelle)|les questions suivantes|les points suivants)\s*:?\s*"
                         r"|(?:le|les|la) (?:demandeurs?|demanderesses?|requ[ée]rants?) (?:souhaitent?|demandent?|sollicitent?|d[ée]sirent?) [^:;]{0,80}?\b(?:que|si)\s+)", re.I)


def clean_objet(objet: str) -> str:
    enum = re.compile(r"^(?:[-–•]\s*|\(?[ivx]{1,4}\)\s*|\(?[a-e]\)\s*|\d+(?:\.\d+)*\s*[.)]\s*|si\s+(?=[a-zà-ü]))")
    for _ in range(2):                      # "1. La demande vise à obtenir la confirmation que : 1.1. …" → strip enumerators and boiler-plate alternately
        for _ in range(3):
            objet = enum.sub("", objet).strip()
        objet = OBJ_BOILER.sub("", objet).strip()
        objet = OBJ_BOILER2.sub("", objet).strip()
    if objet and objet[0].islower():
        objet = objet[0].upper() + objet[1:]
    return objet


def mine_rulings(C: CorpusC, B: CorpusB, stats: collections.Counter) -> list[dict]:
    rows = []
    for did, body in C.body.items():
        m = C.meta[did]
        if not m["folder"].startswith("decisions_anticipees"):
            continue
        stats["rul:docs"] += 1
        o = OBJ_RE.search(body)
        if not o:
            stats["rul:drop:no_objet"] += 1; continue
        rest = body[o.end():]
        e = OBJ_END_RE.search(rest)
        objet = rest[: e.start()] if e else rest[:3000]
        objet = re.sub(r"\s+", " ", objet).strip()
        objet = clean_objet(objet)
        if len(objet) < 60 or objet.count(" ") < 10:
            stats["rul:drop:short_objet"] += 1; continue
        if re.search(r"\b(?:de|het|een|van|wordt|aanvraag)\b", objet[:200]) and not re.search(r"\b(?:la|le|les|des|du)\b", objet[:200]):
            stats["rul:drop:not_fr"] += 1; continue
        if len(objet) > MAX_Q_CHARS:
            cut = objet[:MAX_Q_CHARS]
            k = max(cut.rfind("; "), cut.rfind(". "), cut.rfind(" ; "))
            objet = (cut[: k + 1] if k > 200 else cut).strip()
        cites = extract_cites(objet, m.get("default_family"), m.get("region"), B, C, allow_bare=False)
        if len(cites.articles) > MAX_ARTICLES:
            stats["rul:drop:too_many_articles"] += 1; continue
        rows.append({"source": "ruling", "source_doc": did, "question": objet, "date": m["date"], "domain": m.get("default_family") or fold(m["domain"]),
                     "region": m.get("region"), "cites": cites, "exclude": []})
        stats["rul:kept"] += 1
    return rows


# ── assembling the two sets ───────────────────────────────────────────────────
def human_sets(C: CorpusC) -> tuple[set[str], set[str]]:
    hc: set[str] = set()
    for q in json.loads(QUESTIONS_C.read_text()):
        hc.update(q["expected"]); hc.update(q.get("secondary", []))
    man = json.loads(CORPUS_A_MANIFEST.read_text())
    for mrow in (man if isinstance(man, list) else man.values()):
        d = C.guid_to_id.get(mrow.get("guid") or "")
        if d:
            hc.add(d)
    hb: set[str] = set()
    for q in json.loads(QUESTIONS_B.read_text()):
        hb.update(q["expected"]); hb.update(q.get("secondary", []))
    return hc, hb


def strip_region(bid: str) -> str:
    return re.sub(r"_(wal|bxl|vla):", ":", bid)


def make_rows(rows: list[dict], corpus: str, hc: set[str], hb: set[str], stats: collections.Counter) -> list[dict]:
    hb_strip = {strip_region(x) for x in hb}
    out = []
    for r in rows:
        c = r["cites"]
        if c.bare and not c.explicit and r["source"] != "faq":
            stats[f"{corpus}:{r['source']}:drop:bare_refs_only"] += 1      # precision first: bare "article N" resolved by domain only
            continue
        if corpus == "B":
            exp, sec = list(c.b_expected), []
            if not exp:
                continue
            if c.fam_counts and c.fam_counts.most_common(1)[0][0] not in B_FAMILY_CODES:
                stats[f"{corpus}:{r['source']}:drop:dominant_code_not_in_B"] += 1   # e.g. CDTD answers citing CIR 92 in passing
                continue
            leak = any(x in hb or strip_region(x) in hb_strip for x in exp) or r["source_doc"] in hc
        else:
            if r["source"] == "pq":
                exp, sec = list(c.c_expected), list(c.c_secondary)
            elif r["source"] == "faq":
                exp, sec = list(r["c_docs"]), []
            else:
                exp, sec = [r["source_doc"]], list(c.c_expected) + list(c.c_secondary)
            if not exp:
                continue
            leak = r["source_doc"] in hc or any(x in hc for x in exp + sec)
        if leak:
            stats[f"{corpus}:{r['source']}:drop:human_leak"] += 1
            continue
        fam = strip_region(exp[0]).split(":")[0] if corpus == "B" else None
        if corpus == "C":
            fam = next((C_META[x].get("family") for x in exp if C_META[x].get("family")), None) or r["domain"]
        out.append({"id": qid("MB" if corpus == "B" else "MC", r["source"], r["source_doc"], r.get("key", "")),
                    "question": r["question"], "topic": fam, "source": r["source"], "source_doc": r["source_doc"],
                    "date": r["date"], "expected": exp, "secondary": sec, "exclude": list(r["exclude"]),
                    "notes": "cites: " + " | ".join(c.evidence[:6]) + (f" [bare refs resolved with default code {r['domain']}]" if c.bare and not c.explicit else ""),
                    "label_basis": "explicit" if c.explicit else ("bare" if c.bare else "document")})
    return out


def dedupe(rows: list[dict], stats: collections.Counter, tag: str) -> list[dict]:
    rows = sorted(rows, key=lambda r: (r["date"] or "", r["id"]), reverse=True)     # keep the newest
    keep, sh = [], []
    for r in rows:
        s = shingles(r["question"])
        if any(jaccard(s, t) >= DUP_JACCARD for t in sh):
            stats[f"{tag}:drop:near_duplicate"] += 1
            continue
        keep.append(r); sh.append(s)
    return keep


def cap_faq(rows: list[dict], stats: collections.Counter, tag: str) -> list[dict]:
    groups: dict[str, list[dict]] = collections.defaultdict(list)
    out = []
    for r in rows:
        if r["source"] != "faq":
            out.append(r); continue
        groups["|".join(r["expected"]) if tag == "C" else r["source_doc"]].append(r)
    for g, rs in groups.items():
        rs.sort(key=lambda r: r["id"])
        out += rs[:FAQ_CAP]
        stats[f"{tag}:faq:drop:cap_per_document"] += max(0, len(rs) - FAQ_CAP)
    return out


def cap_topics(rows: list[dict], stats: collections.Counter, tag: str) -> list[dict]:
    """No topic family above CAP_FRAC of the set: trim the largest families, keeping the newest question
    per target article in round-robin so the kept questions stay diverse."""
    while True:
        cnt = collections.Counter(r["topic"] for r in rows)
        n = len(rows)
        over = [f for f, c in cnt.items() if c > CAP_FRAC * n + 1]
        if not over:
            return rows
        f = max(over, key=lambda x: cnt[x])
        others = [r for r in rows if r["topic"] != f]
        n_other = len(others)
        cap = int(CAP_FRAC * n_other / (1 - CAP_FRAC))       # cap = frac · (cap + n_other)
        fam_rows = [r for r in rows if r["topic"] == f]
        by_target: dict[str, list[dict]] = collections.defaultdict(list)
        for r in sorted(fam_rows, key=lambda r: (r["date"] or "", r["id"]), reverse=True):
            by_target[strip_region(r["expected"][0])].append(r)
        kept = []
        queues = sorted(by_target.values(), key=lambda q: (q[0]["date"] or "", q[0]["id"]), reverse=True)
        while len(kept) < cap and any(queues):
            for q in queues:
                if q and len(kept) < cap:
                    kept.append(q.pop(0))
        stats[f"{tag}:drop:topic_cap[{f}]"] += len(fam_rows) - len(kept)
        rows = others + kept


C_META: dict[str, dict] = {}


def finalize(rows: list[dict]) -> list[dict]:
    rows = sorted(rows, key=lambda r: (r["source"], r["date"] or "", r["id"]), reverse=False)
    for r in rows:
        r["split"] = question_split(r["id"])
    return rows


def main():
    global C_META, CAP_FRAC
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", type=int, default=40)
    ap.add_argument("--seed", type=int, default=40)
    ap.add_argument("--cap-frac", type=float, default=CAP_FRAC)
    a = ap.parse_args()
    CAP_FRAC = a.cap_frac
    stats: collections.Counter = collections.Counter()
    C = CorpusC(); C_META = C.meta
    B = CorpusB()
    hc, hb = human_sets(C)
    print(f"human leak sets: {len(hc)} corpus-C docs (incl. corpus-A docs present in C), {len(hb)} corpus-B ids", flush=True)
    raw = mine_pq(C, B, stats) + mine_faq(C, B, stats) + mine_rulings(C, B, stats)
    print({k: v for k, v in sorted(stats.items())}, flush=True)
    sets = {}
    for corpus in ("B", "C"):
        rows = make_rows(raw, corpus, hc, hb, stats)
        stats[f"{corpus}:after_leak_check"] = len(rows)
        rows = dedupe(rows, stats, corpus)
        rows = cap_faq(rows, stats, corpus)
        rows = cap_topics(rows, stats, corpus)
        sets[corpus] = finalize(rows)
    (OUT_B).write_text(json.dumps(sets["B"], ensure_ascii=False, indent=1))
    (OUT_C).write_text(json.dumps(sets["C"], ensure_ascii=False, indent=1))
    # report
    rep = {"stats": dict(sorted(stats.items())), "sets": {}}
    for corpus, rows in sets.items():
        rep["sets"][corpus] = {"n": len(rows), "by_source": dict(collections.Counter(r["source"] for r in rows)),
                               "by_topic": dict(collections.Counter(r["topic"] for r in rows).most_common()),
                               "by_split": dict(collections.Counter(r["split"] for r in rows)),
                               "by_label_basis": dict(collections.Counter(r["label_basis"] for r in rows)),
                               "by_source_topic": {s: dict(collections.Counter(r["topic"] for r in rows if r["source"] == s).most_common())
                                                   for s in ("pq", "faq", "ruling")},
                               "n_expected_mean": round(sum(len(r["expected"]) for r in rows) / max(1, len(rows)), 2),
                               "date_deciles": sorted(r["date"][:4] for r in rows if r["date"])[:: max(1, len(rows) // 10)]}
    (HERE / "mining_report.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1))
    print(json.dumps(rep["sets"], ensure_ascii=False, indent=1))
    # held-out sample for hand checking
    pool = [("B", r) for r in sets["B"]] + [("C", r) for r in sets["C"]]
    rng = random.Random(a.seed)
    sample = rng.sample(pool, min(a.sample, len(pool)))
    lines = ["# 40 mined questions sampled uniformly from questions_b_mined ∪ questions_c_mined (seed 40)", "",
             "For each: the query, the labels, the citation evidence the regex extracted, and a `check:` line for the owner", ""]
    for i, (corpus, r) in enumerate(sample, 1):
        lines += [f"## {i}. `{r['id']}` (corpus {corpus}, source {r['source']}, split {r['split']}, topic {r['topic']})", "",
                  f"**Q:** {r['question']}", "", f"- source_doc: `{r['source_doc']}`" + (f" (excluded from ranking)" if r["exclude"] else ""),
                  f"- expected: " + ", ".join(f"`{x}`" for x in r["expected"][:8]) + (" …" if len(r["expected"]) > 8 else ""),
                  f"- secondary: " + (", ".join(f"`{x}`" for x in r["secondary"][:6]) + (" …" if len(r["secondary"]) > 6 else "") if r["secondary"] else "—"),
                  f"- evidence: {r['notes']}", "- check: [ ] correct  [ ] partly  [ ] wrong — note:", ""]
    (HERE / "sample40.md").write_text("\n".join(lines))
    print(f"wrote {OUT_B} ({len(sets['B'])}), {OUT_C} ({len(sets['C'])}), sample40.md ({len(sample)})")


if __name__ == "__main__":
    main()
