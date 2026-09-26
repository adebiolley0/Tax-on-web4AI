"""Experiment 19 – "canonical-work hybrid" (ideas/README.md §3.1) on corpus C: shared rules.

Everything here is rule-based and written once from the corpus profile (folder / title / path
patterns), never from the validation questions:

* :func:`doc_metadata` – document type, year / income year, region (fed / vla / wal / bxl), tax
  domain from the taxonomy path, body language (idea 66 / 40);
* :func:`quality_flags` – index / TOC / navigation / empty / non-French documents (idea 65);
* :func:`zone_text` – boilerplate zoning: repeated title line, separators, signature blocks,
  publication stamps, portal residue (idea 63);
* :func:`work_groups` – canonicalisation of yearly / version editions into works: title rule
  (exp 13 ``group_key`` + extra patterns), exact body hash, MinHash near-duplicates within the same
  (folder, region, language) (ideas 26 / 21);
* :func:`question_facets` – region / year / tax-domain / document-type cues of a question
  (ideas 27 / 49 / 40), reusing ``detect_region`` of exp 08 and the doc-type cue grammar of exp 13.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

from rag_eval.corpora import DATA_DIR

EXP = "19_canonical_hybrid"
EXP_DIR = Path(__file__).resolve().parent
CACHE = EXP_DIR / "cache"
RUNS = EXP_DIR / "runs"
RESULTS = DATA_DIR.parent / "results"
EXP13 = DATA_DIR.parent / "13_lexical_upgrades"
EXP14_CACHE = DATA_DIR.parent / "14_ltr_fusion" / "cache"
EXP17_CACHE = DATA_DIR.parent / "17_lex_rerank" / "cache"
for _p in (EXP13, DATA_DIR.parent / "08_corpus_b_cleanup"):
    sys.path.insert(0, str(_p.resolve()))

TOP_LEG = 2000            # chunks kept per leg per question (z-scoring population + candidate pool)
RERANK_DEPTH = 20
FUSION_W = 0.5            # fixed convex weight (dense) after z-scoring – not tuned
FACET_BOOST = 1.2
MIN_AFTER_HARD_FILTER = 10
RERANKER_HF = "BAAI/bge-reranker-v2-m3"
RERANK_MAX_LEN = 512
E5_HF = "intfloat/multilingual-e5-small"
E5_EXTRA = "seq512|d_prefix='passage: '|C/fixed1200_title"     # exp 09 / 14 cache key extra

# the round-2 best on C (exp 17: exp-13 lexical → bge-reranker-v2-m3 @20) and other references
REFS = {
    "round2_best": (RESULTS / "17_lex_rerank" / "C__lex13_bge_20.json", "exp 17: exp-13 lexical → bge @20 (round-2 best)"),
    "round1_bar": (RESULTS / "09_corpus_c" / "C__bm25__fixed1200_title__bm25_bge-reranker-v2-m3_30.json", "exp 09: BM25 tok03 → bge @30 (round-1 bar)"),
    "lex13": (RESULTS / "13_lexical_upgrades" / "C__combo__fields_tok01_num_cues.json", "exp 13 lexical only"),
}


def fold(s: str) -> str:
    s = unicodedata.normalize("NFKD", s.lower())
    return "".join(c for c in s if not unicodedata.combining(c))


def sha1(s: str) -> str:
    return hashlib.sha1(s.encode("utf-8")).hexdigest()


# ── metadata ────────────────────────────────────────────────────────────────
DOMAIN_OF_PATH1 = {
    "impots sur les revenus": "IR", "taxe sur la valeur ajoutee": "TVA",
    "droits d'enregistrement, d'hypotheque et de greffe": "ENR", "droits de succession": "SUCC",
    "taxes assimilees aux impots sur les revenus": "ASSIM", "droits et taxes divers": "DIVERS",
    "perception et recouvrement": "RECOUV", "entites federees": "FEDERE", "douanes": "DOUANE", "accises": "DOUANE",
    "organisations internationales et missions diplomatiques": "INTL",
}
_YEAR = re.compile(r"\b((?:19|20)\d\d)\b")
_REV_YEAR = re.compile(r"revenus?\s+(?:de\s+)?(20\d\d)", re.I)
_EX_YEAR = re.compile(r"(?:exercice d'imposition|ex\.?\s*d'imp\.?|aanslagjaar)\s*(20\d\d)", re.I)
_REGION_WORDS = {
    "wal": r"region wallonne|wallon(?:ne)?s?\b|wallonie|\bwal\b|c\. ?enr\. ?wal|c\. ?succ\. ?wal",
    "bxl": r"bruxelles[- ]capitale|bruxellois(?:e)?s?\b|region de bruxelles|brussels? hoofdstedelijk|\bc\.b\.p\.f\.|\bcbpf\b",
    "vla": r"region flamande|flamand(?:e)?s?\b|vlaams(?:e)?\b|vlaanderen|flandre|vlabel|codex fiscaliteit|\bvcf\b|\bcff\b",
}
_NL_STOP = set("de het een van en in is dat op te zijn voor met die niet aan er ook als bij dan nog worden wordt door over deze naar uit om hij zij wij werd heeft hebben kan moet".split())
_FR_STOP = set("le la les des du de et en un une est dans pour par sur au aux que qui ne pas ce cette ces son sa ses avec sont ont été être il elle nous vous".split())


def body_language(text: str) -> str:
    w = re.findall(r"[a-zàâçéèêëîïôûùüÿœ]+", text.lower()[:6000])
    nl = sum(1 for x in w if x in _NL_STOP)
    fr = sum(1 for x in w if x in _FR_STOP)
    if nl > 10 and nl > 1.5 * fr:
        return "nl"
    if fr >= nl and fr > 3:
        return "fr"
    return "?"


def region_of_doc(doc_id: str, title: str, path: list[str]) -> str | None:
    m = re.search(r"_(wa|br|vl)_", doc_id)
    if m:
        return {"wa": "wal", "br": "bxl", "vl": "vla"}[m.group(1)]
    t = fold(title)
    for r, rx in _REGION_WORDS.items():
        if re.search(rx, t):
            return r
    p = fold(" | ".join(path or []))
    if "entites federees" in p or "regionale" in p:
        for r, rx in _REGION_WORDS.items():
            if re.search(rx, p):
                return r
    return None


def domain_of_doc(title: str, path: list[str]) -> str:
    path = path or []
    p0 = fold(path[0]) if path else ""
    p1 = fold(path[1]) if len(path) > 1 else ""
    if p0 == "finances":
        return "FIN"
    if p0 == "droit externe":
        return "EXT"
    dom = DOMAIN_OF_PATH1.get(p1, "OTHER")
    if dom == "FEDERE":                      # regional codes: infer the tax from the title
        t = fold(title)
        if "succession" in t:
            return "SUCC"
        if "enregistrement" in t or "hypoth" in t:
            return "ENR"
        if "circulation" in t or "vehicule" in t:
            return "ASSIM"
        if "precompte immobilier" in t or "revenu cadastral" in t:
            return "IR"
    return dom


def doc_metadata(doc) -> dict:
    title, path = doc.title, doc.meta.get("path") or []
    m = _YEAR.search(title)
    date = str(doc.meta.get("document_date") or "")
    year = int(m.group(1)) if m else (int(date[:4]) if re.match(r"^(19|20)\d\d", date) else None)
    rv = _REV_YEAR.search(title) or re.search(r"_revenus_(20\d\d)", doc.doc_id)
    ex = _EX_YEAR.search(title)
    return {"folder": doc.meta["folder"], "title": title, "year": year,
            "rev_year": int(rv.group(1)) if rv else None, "ex_year": int(ex.group(1)) if ex else None,
            "region": region_of_doc(doc.doc_id, title, path), "domain": domain_of_doc(title, path),
            "lang": body_language(doc.text), "n_chars": len(doc.text)}


# ── quality filter (idea 65) ────────────────────────────────────────────────
def quality_flags(doc, meta: dict, zoned_text: str) -> dict:
    lines = [l.strip() for l in zoned_text.split("\n") if l.strip()]
    n = len(lines)
    short_lines = sum(1 for l in lines if len(l) < 80)
    longest = max((len(l) for l in lines), default=0)
    t = fold(doc.title)
    head = fold(" ".join(lines[:5]))
    toc = ("table des matieres" in t or "inhoudstafel" in t or "apercu documentaire" in t
           or (("table des matieres" in head or "sommaire" in head) and n >= 8 and short_lines / n > 0.9 and longest < 250))
    empty = len(zoned_text) < 150
    nl = meta["lang"] == "nl"
    return {"toc": toc, "empty": empty, "nl": nl, "drop": bool(toc or empty or nl),
            "reason": "toc" if toc else ("empty" if empty else ("nl" if nl else ""))}


# ── boilerplate zoning (idea 63) ────────────────────────────────────────────
_ZONE_LINE = re.compile("|".join([
    r"^[-_=*•.·—–]{3,}$",                                    # separators
    r"^\(\s*(?:\.\.\.|…)\s*\)$",                             # (...) / (…)
    r"^\[\s*Top\s*\]$", r"^\[\s*Historique[^\]]*\]$",        # portal navigation residue
    r"^\|(?:\s*-{3,}\s*\|)+$",                               # markdown table separator rows
    r"^Date de publication\s*:.*$", r"^Publicatiedatum\s*:.*$",
    r"^R[ée]pertoire RJ\s*[–-].*$", r"^Texte int[ée]gral$", r"^R[ée]sum[ée]$", r"^Samenvatting$", r"^Volledige tekst$",
    r"^(?:PHILIPPE|ALBERT(?: II)?|BAUDOUIN)(?:,\s*Roi des Belges,?)?$", r"^(?:FILIP|ALBERT(?: II)?),\s*Koning der Belgen,?$",
    r"^A tous, pr[ée]sents et [àa] venir, Salut\.?$", r"^Aan allen die nu zijn en hierna wezen zullen, Onze Groet\.?$",
    r"^Par le Roi\s*:?$", r"^Van Koningswege\s*:?$", r"^Au nom du Ministre\s*:?$", r"^Nous avons arr[êe]t[ée] et arr[êe]tons\s*:?$",
    r"^Arr[êe]te\s*:$", r"^Scell[ée] du sceau de l.Etat\s*:?$", r"^Sur la proposition (?:du|de la|de notre|des) .{0,120}$",
    r"^Les Chambres ont adopt[ée] et Nous sanctionnons ce qui suit\s*:?$", r"^Apr[èe]s d[ée]lib[ée]ration,?$",
    r"^(?:Le|La|De) (?:Vice-Premi(?:er|ère) Ministre et )?Ministre(?:-Pr[ée]sident)?(?: (?:des|de la|de l'|du) [A-Za-zéèêÉ' ,-]{3,60})?,?$",
    r"^Le Directeur g[ée]n[ée]ral,?$", r"^Le Ministre-Pr[ée]sident,?$", r"^Le Secr[ée]taire d.Etat[^,]{0,60},?$",
    r"^[A-Z]\.\s?(?:[A-Z][A-Z' -]{2,28})$",                  # signatures: 'V. VAN PETEGHEM', 'D. REYNDERS'
    r"^La d[ée]cision est publi[ée]e uniquement dans la langue dans laquelle la demande a [ée]t[ée] introduite\.?$",
    r"^De beslissing wordt enkel gepubliceerd in de taal waarin de aanvraag werd ingediend\.?$",
    r"^(?:Communication|Information) importante$", r"^Belangrijke (?:mededeling|informatie)$",
]), re.I)


def zone_text(title: str, text: str) -> tuple[str, int]:
    """Strip boilerplate lines; returns (zoned text, number of removed lines)."""
    out, removed = [], 0
    t_norm = re.sub(r"\s+", " ", fold(title.strip().rstrip("*"))).strip()
    for i, ln in enumerate(text.split("\n")):
        s = re.sub(r"\s+", " ", ln.strip())
        if not s:
            out.append("")
            continue
        if (i < 4 and re.sub(r"\s+", " ", fold(s.rstrip("*"))) == t_norm) or _ZONE_LINE.match(s):
            removed += 1
            continue
        out.append(ln)
    z = re.sub(r"\n{3,}", "\n\n", "\n".join(out)).strip()
    return z, removed


# ── canonicalisation (ideas 26 / 21) ────────────────────────────────────────
_EDITION_PATTERNS = [
    re.compile(r"\s*\((?:revenus|ex\.? d'imp\.?|exercice d'imposition|aanslagjaar|inkomsten)\s*(?:de\s+)?20\d\d(?:\s*/\s*\d\d)?\)\*{0,2}", re.I),
    re.compile(r"\s*\(version\s*\d+\)", re.I),
    re.compile(r"\s*-\s*revenus\s*(?:de\s+)?20\d\d\s*-\s*exercice d'imposition\s*20\d\d", re.I),
    re.compile(r"\s*-\s*revenus\s*(?:de\s+)?20\d\d\b", re.I),
    re.compile(r"\s*\(?\b[ée]dition\s+20\d\d\)?", re.I),
    re.compile(r"\s*-\s*exercice d'imposition\s*20\d\d", re.I),
]
_NUM_YEAR = re.compile(r"^num[ée]ro\s+(\d+)/20\d\d$", re.I)


def edition_key(doc_id: str, title: str, folder: str) -> str | None:
    """Documents that are yearly / version editions of one text share a key (None = own work)."""
    t = title.strip().rstrip("*").strip()
    t2 = t
    for rx in _EDITION_PATTERNS:
        t2 = rx.sub("", t2)
    t2 = t2.strip(" -–")
    m = _NUM_YEAR.match(t2)
    if m:
        return f"{folder}::forfait::{m.group(1)}"
    if folder == "forfaits":
        m2 = re.match(r"^(\d+)\s*-", t2)
        if m2:
            return f"{folder}::forfait::{m2.group(1)}"
    if t2 != t or folder == "faq":
        return f"{folder}::{fold(t2.lower())}"
    return None


_REGION_TITLE = re.compile(r"\s*[-–(]\s*(?:r[ée]gion (?:wallonne|flamande|de bruxelles[- ]capitale)|f[ée]d[ée]ral|wallonie|flandre|bruxelles)\s*\)?\s*$", re.I)
_RJ_REGION = re.compile(r"-(wa|br|vl)/", re.I)


def twin_key(doc_id: str, title: str, folder: str) -> str:
    """Edition key with the region tokens removed as well (regional twins): diagnostic only."""
    k = edition_key(doc_id, title, folder) or f"{folder}::{fold(title.strip().rstrip('*').lower())}"
    k = _REGION_TITLE.sub("", k)
    k = _RJ_REGION.sub("-XX/", k)
    return re.sub(r",?\s*\((?:region (?:wallonne|flamande|de bruxelles[- ]capitale)|federal)\)", "", k, flags=re.I)


_TOK = re.compile(r"\w+")


def norm_body_tokens(text: str) -> list[str]:
    return _TOK.findall(fold(text.lower()))


class MinHasher:
    def __init__(self, n_perm: int = 128, shingle: int = 5, bands: int = 32, seed: int = 0, max_tokens: int = 20000):
        rng = np.random.default_rng(seed)
        self.p = (1 << 31) - 1                                   # Mersenne prime: a*h < 2^62 fits int64
        self.a = rng.integers(1, self.p, n_perm, dtype=np.int64)
        self.b = rng.integers(0, self.p, n_perm, dtype=np.int64)
        self.n_perm, self.shingle, self.bands, self.max_tokens = n_perm, shingle, bands, max_tokens
        self.rows = n_perm // bands

    def signature(self, tokens: list[str]) -> np.ndarray | None:
        k = self.shingle
        tokens = tokens[: self.max_tokens]
        if len(tokens) < k + 15:
            return None
        sh = {int(hashlib.blake2b(" ".join(tokens[i:i + k]).encode(), digest_size=4).hexdigest(), 16)
              for i in range(len(tokens) - k + 1)}
        h = np.fromiter(sh, dtype=np.int64, count=len(sh)) % self.p
        return ((self.a[:, None] * h[None, :] + self.b[:, None]) % self.p).min(axis=1)

    def band_keys(self, sig: np.ndarray) -> list[tuple[int, bytes]]:
        return [(bi, sig[bi * self.rows:(bi + 1) * self.rows].tobytes()) for bi in range(self.bands)]


class UnionFind:
    def __init__(self, n: int):
        self.p = list(range(n))

    def find(self, x: int) -> int:
        while self.p[x] != x:
            self.p[x] = self.p[self.p[x]]
            x = self.p[x]
        return x

    def union(self, a: int, b: int) -> None:
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.p[max(ra, rb)] = min(ra, rb)


def work_groups(docs, metas: list[dict], zoned_texts: list[str], jaccard: float = 0.9) -> tuple[list[int], dict]:
    """Union of three tiers → work id per doc (index of the group). Tiers: (1) edition title key,
    (2) exact hash of the normalised body, (3) MinHash near-duplicates (5-token shingles, 128 perms,
    32 bands × 4 rows, estimated Jaccard ≥ ``jaccard``). Tiers 2-3 only within the same
    (folder, region, language) so regional twins and FR/NL pairs are never merged."""
    n = len(docs)
    uf = UnionFind(n)
    stats = Counter()
    by_key: dict[str, int] = {}
    for i, (d, m) in enumerate(zip(docs, metas)):
        k = edition_key(d.doc_id, d.title, m["folder"])
        if k:
            k = f"{k}|{m['region']}|{m['lang']}"
            if k in by_key:
                uf.union(i, by_key[k]); stats["title_pairs"] += 1
            else:
                by_key[k] = i
    scope = [f"{m['folder']}|{m['region']}|{m['lang']}" for m in metas]
    by_hash: dict[str, int] = {}
    toks = []
    for i, z in enumerate(zoned_texts):
        tk = norm_body_tokens(z)
        toks.append(tk)
        if len(tk) >= 20:
            h = sha1(scope[i] + "|" + " ".join(tk))
            if h in by_hash:
                uf.union(i, by_hash[h]); stats["hash_pairs"] += 1
            else:
                by_hash[h] = i
    mh = MinHasher()
    sigs: list[np.ndarray | None] = [mh.signature(tk) for tk in toks]
    buckets: dict[tuple, list[int]] = defaultdict(list)
    for i, s in enumerate(sigs):
        if s is None:
            continue
        for bk in mh.band_keys(s):
            buckets[(scope[i],) + bk].append(i)
    cand: set[tuple[int, int]] = set()
    for members in buckets.values():
        if 1 < len(members) <= 50:
            for a in range(len(members)):
                for b in range(a + 1, len(members)):
                    cand.add((members[a], members[b]))
    for a, b in cand:
        if uf.find(a) == uf.find(b):
            continue
        est = float((sigs[a] == sigs[b]).mean())
        if est >= jaccard:
            uf.union(a, b); stats["minhash_pairs"] += 1
    stats["minhash_candidates"] = len(cand)
    roots = [uf.find(i) for i in range(n)]
    ids: dict[int, int] = {}
    work = [ids.setdefault(r, len(ids)) for r in roots]
    return work, dict(stats)


# ── question facets (ideas 27 / 49 / 40) ────────────────────────────────────
_Q_REGION_EXPLICIT = {
    "wal": r"region wallonne|wallonie|wallon(?:ne)?s?\b",
    "bxl": r"region (?:de )?bruxelles|bruxelles[- ]capitale|bruxellois(?:e)?s?\b",
    "vla": r"region flamande|flandre|flamand(?:e)?s?\b|vlaanderen|vlaams",
}
_Q_DOMAIN = [
    ("TVA", r"\btva\b|valeur ajoutee|assujetti|\bfactur|taux reduit|regime de la marge|regime (?:particulier )?agricole"),
    ("SUCC", r"succession|\bherit|\bdeces\b|decede|\blegs?\b|legataire|testament|legue|avoirs herites"),
    ("ENR", r"droits? d'enregistrement|enregistr|donation|abattement|droits de vente|hypothec|tontine|usufruit|revend"),
    ("IR", r"impot des personnes physiques|\bipp\b|impot des societes|\bisoc\b|precompte|frais professionnels|droits d'auteur|dividende|depenses non admises|deduction|revenus? (?:de |des |d')|avantage de toute nature|impatri|prime beneficiaire|\bforfait|pension|remuneration|voiture de societe|fiche fiscale|chercheurs?|travailleurs? occasionnels?"),
    ("ASSIM", r"taxe de circulation|mise en circulation|immatricul|\bvehicule|remorque|cv fiscaux|jeux et paris|eurovignette"),
    ("DIVERS", r"comptes?[- ]titres|operations? de bourse|\btob\b|\btact\b|taxe annuelle|embarquement|droit pour .{0,30}nationalite|demande de nationalite"),
    ("RECOUV", r"recouvrement|dette fiscale|responsabilite solidaire|omis de payer|saisie|redevable solidaire|paiement de l'impot"),
]
_Q_DOCTYPE = [
    (r"\bcirculaire", ("circulaires",)),
    (r"\bruling|decision anticipee|service des decisions anticipees|\bsda\b", ("decisions_anticipees_l_24_12_2002", "decisions_anticipees_art_345_cir_92", "decisions_anticipees_ar_03_05_1999")),
    (r"question parlementaire|le ministre|\bdepute|\bparlement", ("questions_parlementaires",)),
    (r"\barret\b|\bjugement|\btribunal|cour d'appel|cour de cassation|cour constitutionnelle|\bjuge\b|jurisprudence", ("jurisprudence_belge", "sans_type")),
    (r"cour de justice|\bcjue\b|\bcjce\b", ("jurisprudence_europeenne",)),
    (r"convention (?:preventive|fiscale|belgo)|double imposition|\bcpdi\b|frontalier|avenant|accord amiable", ("conventions_preventives_de_la_double_imposition", "traites_et_accords_internationaux")),
    (r"arrete royal|\bar/cir|\bar cir", ("arretes_royaux",)),
    (r"\bforfait", ("forfaits",)),
    (r"\bfaq\b", ("faq",)),
    (r"commentaire|\bcom\.?ir|repertoire", ("commentaires_dont_rep_rj",)),
    (r"\bdirective\b|reglement (?:ue|europeen)", ("reglementation_europeenne",)),
    (r"\bdecret\b|\bordonnance\b|code flamand|vlaamse codex|\bcff\b|\bvcf\b|vlaamse belastingdienst|vlabel", ("legislation_et_reglementation_regionale_et_locale",)),
    (r"\bcir\s*92|\barticle\s+\d|\bart\.\s*\d|code (?:de la tva|des droits|du recouvrement|civil)", ("code_et_legislation",)),
]


def question_facets(question: str) -> dict:
    from cleanup import detect_region                       # exp 08 (region words + Belgian cities)
    q = fold(question.lower())
    region = detect_region(question)
    explicit = next((r for r, rx in _Q_REGION_EXPLICIT.items() if re.search(rx, q)), None)
    years = sorted({int(y) for y in re.findall(r"\b(20[0-3]\d)\b", q)})
    domains = [d for d, rx in _Q_DOMAIN if re.search(rx, q)]
    folders: list[str] = []
    for rx, fs in _Q_DOCTYPE:
        if re.search(rx, q):
            folders += [f for f in fs if f not in folders]
    return {"region": region, "region_explicit": explicit, "years": years, "domains": domains, "folders": folders}


def doc_matches(meta: dict, facets: dict) -> dict:
    """Which facets of the question a document matches (each is a ×FACET_BOOST)."""
    out = {}
    if facets["region"] and meta["region"] == facets["region"]:
        out["region"] = True
    if facets["years"]:
        ys = {meta["year"], meta["rev_year"], meta["ex_year"]} - {None}
        if meta["rev_year"]:
            ys.add(meta["rev_year"] + 1)                     # 'revenus 2026' answers 'exercice 2027' too
        if any(y in ys for y in facets["years"]):
            out["year"] = True
    if facets["domains"] and meta["domain"] in facets["domains"]:
        out["domain"] = True
    if facets["folders"] and meta["folder"] in facets["folders"]:
        out["doctype"] = True
    return out


# ── stats / helpers ─────────────────────────────────────────────────────────
def per_question_ranks(result_json: Path) -> dict[str, int | None]:
    r = json.loads(result_json.read_text())
    return {qid: v["rank"] for qid, v in r["per_question"].items()}


def split_metrics_from_ranks(ranks: dict[str, int | None], questions) -> dict:
    out = {}
    for sp in ("train", "val", "all"):
        qs = [q for q in questions if sp == "all" or q.split == sp]
        rr = [1.0 / ranks[q.qid] if ranks.get(q.qid) else 0.0 for q in qs]
        out[sp] = {"n": len(qs), "mrr": float(np.mean(rr)),
                   "hit@1": float(np.mean([1.0 if ranks.get(q.qid) == 1 else 0.0 for q in qs])),
                   "recall@10": float(np.mean([1.0 if ranks.get(q.qid) and ranks[q.qid] <= 10 else 0.0 for q in qs]))}
    return out


def paired_tests(rr_new: np.ndarray, rr_ref: np.ndarray, seed: int = 0, n_boot: int = 20000) -> dict:
    """Paired t, sign test, Wilcoxon, bootstrap CI on reciprocal-rank differences. Uses
    rag_eval.stats when present (another agent may add it), else scipy inline."""
    try:
        from rag_eval import stats as rs  # type: ignore
        if hasattr(rs, "paired_tests"):
            return rs.paired_tests(rr_new, rr_ref)
    except Exception:
        pass
    from scipy import stats
    d = rr_new - rr_ref
    n = len(d)
    wins, losses = int((d > 1e-12).sum()), int((d < -1e-12).sum())
    out = {"n": n, "mean_diff": float(d.mean()), "wins": wins, "losses": losses, "ties": n - wins - losses}
    if n > 1 and d.std() > 0:
        t = stats.ttest_rel(rr_new, rr_ref)
        out["t"] = float(t.statistic); out["p_t"] = float(t.pvalue)
        try:
            out["p_wilcoxon"] = float(stats.wilcoxon(rr_new, rr_ref, zero_method="wilcox").pvalue)
        except ValueError:
            out["p_wilcoxon"] = None
    else:
        out["t"] = None; out["p_t"] = None; out["p_wilcoxon"] = None
    out["p_sign"] = float(stats.binomtest(wins, wins + losses, 0.5).pvalue) if wins + losses else None
    rng = np.random.default_rng(seed)
    boots = np.array([d[rng.integers(0, n, n)].mean() for _ in range(n_boot)])
    out["ci95"] = [float(np.quantile(boots, 0.025)), float(np.quantile(boots, 0.975))]
    return out
