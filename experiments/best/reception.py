#!/usr/bin/env python3
"""Reception field for corpus B (exp 20, +0.115 MRR lexical on 304 mined questions, p < 0.001): for every statute
article, the sentences of corpus-C documents (circulars, commentary, rulings, parliamentary answers, FAQ, case law,
notices) that cite it, plus the titles of the citing documents — doc2query without an LLM, aligned by explicit
citations.

Citations are found with the exp-11 regex reference grammar (:func:`iter_article_refs` / :func:`classify_tail`),
resolved to corpus-B article ids (``cir92:145/33``; regional code families → the citing document's region or all
three regions) and the sentence around each mention is kept (capped at 40 sentences / 10 titles per article,
round-robin over source types and documents, newest first).

    python reception.py                    → index/B_reception.json           (54 s over myfin_docs)
    python reception.py --exclude-mined    → index/B_reception_nomined.json   (leak-free: no sentence from a mined
                                                                                question's source document; evaluation only)
"""
from __future__ import annotations

import bisect
import collections
import json
import re
import time
import unicodedata
from pathlib import Path

from rag_eval import Doc
from rag_eval.corpora import REPO_ROOT, _parse_front_matter

from config import INDEX, RECEPTION

MYFIN = REPO_ROOT / "myfin_docs"
MAX_CHARS = 200_000
CAP_SENTENCES, CAP_TITLES, MAX_SENT = 40, 10, 600
SOURCE_TYPES = {
    "circulaires": "circ", "commentaires_dont_rep_rj": "com", "decisions_anticipees_l_24_12_2002": "ruling",
    "decisions_anticipees_art_345_cir_92": "ruling", "decisions_anticipees_ar_03_05_1999": "ruling",
    "questions_parlementaires": "qp", "faq": "faq", "jurisprudence_belge": "jur", "jurisprudence_europeenne": "jur",
    "avis": "avis", "communications": "avis", "informations_et_communications": "avis", "forfaits": "forfait",
}
FAM_CODES = {"cir92": ["cir92"], "arcir92": ["arcir92"], "ctva": ["ctva"], "crecouv": ["crecouv"], "cbpf": ["cbpf"], "vcf": ["vcf"]}
REGIONAL = ("csucc", "cenr", "cta")
DOMAIN_FAMILY = {"Impôts sur les revenus": "cir92", "Taxe sur la valeur ajoutée": "ctva", "Droits de succession": "csucc",
                 "Droits d'enregistrement, d'hypothèque et de greffe": "cenr", "Taxes assimilées aux impôts sur les revenus": "cta",
                 "Droits et taxes divers": "cdtd", "Perception et Recouvrement": "crecouv", "Secteur bancaire": "loibanc"}
REGION_WORDS = [("wal", r"r[ée]gion wallonne|wallon|waals"), ("bxl", r"bruxelles-capitale|bruxellois|brussels?\b"),
                ("vla", r"r[ée]gion flamande|flamand|vlaams|vlaanderen|autorit[ée] flamande"), ("fed", r"l[ée]gislation f[ée]d[ée]rale")]


def fold(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))


def region_of(title: str, path: list[str]) -> str | None:
    txt = fold((title + " | " + " | ".join(path)).lower())
    for r, rx in REGION_WORDS:
        if re.search(rx, txt):
            return r
    return None


# ── exp-11 reference grammar ─────────────────────────────────────────────────────────────────────────────────
SUFFIX = r"(?:bis|ter|quater|quinquies|sexies|septies|octies|novies|decies|undecies|duodecies)?"
ART_RE = re.compile(r"(?<![\w/])(?:articles?|art\.?|artikel(?:en)?)\s*(?=\d)", re.I)
TOKEN_RE = re.compile(rf"""[ \t]*(?:
    (?P<num>\d+(?:\.\d+)+|\d+(?:[/^]\d+)?{SUFFIX})(?P<ord>er\b|°|e\b|ème\b)?
  | (?P<mark>§+|al\.|alin[ée]as?\b|n[°o]s?\b|par\.|points?\b|litt?\.|lettres?\b|tirets?\b|phrases?\b|
      premi[eè]re?\b|deuxi[eè]me\b|troisi[eè]me\b|quatri[eè]me\b|derni[eè]re?\b|second\b|liminaire\b|
      paragra(?:ph|f)e?s?\b|lid\b|leden\b)
  | (?P<conn>,|\bet\b|\bou\b|\bà\b|\bjusqu['’]à\b|\ben\b|\btot\b|\ben\s+met\b|-|\+)
  | (?P<letter>[a-h]\)|[a-h](?=\s*,)|[ivx]+\)(?=\s*[,;.]))
  | (?P<incl>inclus\b|compris\b|nouveau\b|ancien\b)
)""", re.X | re.I)
SAME_RE = re.compile(
    r"^\s*,?\s*(?:du|de la|de l['’]|de ce|de cet|de cette|dudit|de ladite|van (?:dit|dezelfde|hetzelfde))\s*"
    r"(?:même|présent[e]?|zelfde)\s+(?P<kind>Code|arrêté|décret|loi|ordonnance|Wetboek|besluit|wet|decreet)", re.I)
BARE_CODE_RE = re.compile(
    r"^\s*,?\s*(?:du|de ce|de l['’]|de la|dudit)\s*(?:Code|Wetboek)\b"
    r"(?!\s+(?:des|de|du|d['’]|civil|pénal|judiciaire|wallon|flamand|bruxellois|de la|rural|forestier|électoral|consulaire))", re.I)
EXTERNAL_RE = re.compile(
    r"^\s*,?\s*(?:"
    r"(?:L|LP|Lprog|LS|AR|AGW|AGF|AGBC|AGRBC|D|DP|Décr\.?|AM|O|Ord\.?|A\.R\.|L\.|Loi|Décret|Arrêté|Ordonnance)\s+(?:du\s+)?\d{1,2}[./]\d{1,2}[./]\d{2,4}"
    r"|(?:de la|du|de l['’]|de cette|de cet|de ladite|dudit|de la même|du même|de la présente|du présent|van de|van het|van dezelfde)\s*"
    r"(?:loi|décret|arrêté(?!\s+royal\s+n)|ordonnance|Loi-programme|loi-programme|Constitution|Traité|directive|règlement|convention|accord|protocole|"
    r"wet\b|decreet|besluit|verordening|richtlijn|"
    r"Code\s+(?:des sociétés|civil|pénal|judiciaire|de droit économique|de commerce|de la démocratie|wallon|de la nationalité|d['’]instruction|"
    r"de la route|forestier|rural|électoral|de droit international|consulaire|de la navigation|de la sécurité|du bien-être|de l['’]environnement|"
    r"flamand de l['’]aménagement|bruxellois de l['’]aménagement|de droit pénal|des impôts sur les revenus 1964|du logement|de l['’]eau|de l['’]énergie)"
    r"|Wetboek\s+(?:van vennootschappen|van strafrecht|van economisch recht|van koophandel))"
    r")", re.I)
CODE_HINTS: list[tuple[re.Pattern, str]] = [(re.compile(
    r"^\s*[,(]?\s*(?:(?:du|de la|de l['’]|de|van het|van de)\s*)?(?:même\s+)?(?:" + p + ")", re.I), fam) for p, fam in [
    (r"(?:AR\s*/\s*CIR|A\.R\.\s*/\s*C\.I\.R\.)\s*(?:92|1992)?\b|arrêté royal d['’]exécution du Code des impôts sur les revenus|(?:KB|K\.B\.)\s*/\s*WIB\s*92", "arcir92"),
    (r"Code de la (?:TVA|T\.V\.A\.|taxe sur la valeur ajoutée)|\bC\.?\s?T\.?V\.?A\.?\b|Code TVA|(?:BTW|Btw)[- ]?Wetboek|W\.?BTW\b", "ctva"),
    (r"Code des impôts sur les revenus(?:\s*1992)?|\bCIR\s*(?:92|1992)?\b|\bC\.\s?I\.\s?R\.(?:\s*92)?|\bWIB\s*(?:92|1992)?\b|Wetboek van de inkomstenbelastingen", "cir92"),
    (r"Code des droits de succession|\bC\.?\s?succ\.?\b|Wetboek (?:der |van )?successierechten|\bW\.?Succ\.?\b", "csucc"),
    (r"Code des droits d['’]enregistrement|\bC\.?\s?enr\.?\b|Wetboek (?:der |van )?registratierechten|\bW\.?Reg\.?\b", "cenr"),
    (r"Code des taxes assimilées aux impôts sur les revenus|\bCTA\b|\bC\.T\.A\.|Wetboek van de met de inkomstenbelastingen gelijkgestelde belastingen|\bWGB\b|\bWIGB\b", "cta"),
    (r"Code des droits et taxes divers|\bC\.?\s?D\.?T\.?D\.?\b|Wetboek diverse rechten en taksen|\bWDRT\b", "cdtd"),
    (r"Code du recouvrement(?: amiable et forcé)?|\bCRAF\b|Invorderingswetboek", "crecouv"),
    (r"Code bruxellois de la procédure fiscale|\bC\.?\s?B\.?\s?P\.?\s?F\.?\b", "cbpf"),
    (r"Codex|Code flamand de la fiscalité|\bVCF\b|Vlaamse Codex Fiscaliteit", "vcf"),
    (r"Loi bancaire|\bLB\b", "loibanc"),
    (r"Code des taxes assimilées au timbre", "ctat"),
]]
AR_RE = re.compile(r"^\s*[,(]?\s*(?:(?:du|de l['’])\s*)?(?:arrêté royal|A\.?R\.?|koninklijk besluit|K\.?B\.?)\s*n[°o]\.?\s*(\d+)", re.I)
AMEND_PRE_RE = re.compile(
    r"(?:modifi|ins[ée]r|remplac|abrog|compl[ée]t|r[ée]tabli|introduit|supprim|renum[ée]rot|gewijzigd|ingevoegd|vervangen|opgeheven)\S*\s+"
    r"(?:par\s+(?:l['’]|les\s+)?|bij\s+)$", re.I)


def parse_span(text: str, pos: int) -> tuple[list[str], int]:
    """Consume reference tokens from ``pos``; return (items, end): article numbers and 'à' range markers."""
    items: list[str] = []
    skip = range_skip = last_ok = False
    while True:
        m = TOKEN_RE.match(text, pos)
        if not m:
            break
        if m.group("num"):
            if skip or m.group("ord") or range_skip:
                range_skip = False
                last_ok = False
            else:
                items.append(m.group("num").replace("^", "/"))
                last_ok = True
        elif m.group("mark"):
            skip = True
            last_ok = False
        elif m.group("conn"):
            c = m.group("conn").lower()
            if c == ",":
                skip = False
                range_skip = False
            elif c in ("à", "jusqu'à", "jusqu’à", "tot", "en met"):
                if last_ok and not skip:
                    items.append("à")
                else:
                    range_skip = True
            last_ok = last_ok and c != ","
            if c in ("et", "ou", "en"):
                last_ok = False
        elif m.group("letter") or m.group("incl"):
            last_ok = False
        pos = m.end()
    while items and items[-1] == "à":
        items.pop()
    return items, pos


def iter_article_refs(text: str, tail_len: int = 90):
    """Yield (mention_start, items, tail) for every "article(s) / art." mention; amendment notes are marked external."""
    for m in ART_RE.finditer(text):
        items, end = parse_span(text, m.end())
        if not items:
            continue
        nxt = text[end: end + 2]
        if nxt[:1] == "." and nxt[1:2].isdigit():
            continue
        tail = text[end: end + tail_len]
        if AMEND_PRE_RE.search(text[max(0, m.start() - 40): m.start()]):
            tail = " de la loi (amendement)" + tail
        yield m.start(), items, tail


def classify_tail(tail: str) -> tuple[str, str]:
    m = SAME_RE.match(tail)
    if m:
        return "same", m.group("kind").lower()
    m = AR_RE.match(tail)
    if m:
        return "ar", m.group(1)
    for rx, fam in CODE_HINTS:
        if rx.match(tail):
            return "family", fam
    if EXTERNAL_RE.match(tail):
        return "external", ""
    if BARE_CODE_RE.match(tail):
        return "same", "code"
    return "same", ""


def expand_items(items: list[str], resolve, expand_range) -> set[str]:
    out: set[str] = set()
    i = 0
    while i < len(items):
        if i + 2 < len(items) and items[i + 1] == "à" and items[i] != "à" and items[i + 2] != "à":
            out.update(expand_range(items[i], items[i + 2]))
            i += 3
            continue
        if items[i] != "à":
            out.update(resolve(items[i]))
        i += 1
    return out


# ── sentence splitting (exp 20) ──────────────────────────────────────────────────────────────────────────────
_ABBR = {w.lower() for w in (
    "art arts n nr nrs no al par p pp cf etc M MM Mme Mlle ch vol éd ed c Ci RH E T AR L LP AGFisc AAF AFER R D S V Q W B K "
    "St Ste min max env resp réf ref op cit ibid suiv ss s préc i e ex dd d v vs Cass Civ Comm Trib").split()}
_SENT_END = re.compile(r"[.;!?]+[\"»)\]]?\s+(?=[«\"(]?[A-ZÀ-ÜÉÈ0-9])")
_WORD_BEFORE = re.compile(r"([A-Za-zÀ-ÿ]+|\d+)$")
_NEWLINE_BREAK = re.compile(r"\n\s*\n")


def _is_boundary(text: str, m: re.Match) -> bool:
    if m.group(0)[0] != ".":
        return True
    w = _WORD_BEFORE.search(text, max(0, m.start() - 12), m.start())
    if not w:
        return True
    tok = w.group(1)
    return not (tok.lower() in _ABBR or (tok.isdigit() and len(tok) <= 2) or (len(tok) == 1 and tok.isupper()))


def _split_para(text: str, a: int, b: int) -> list[tuple[int, int]]:
    out, start = [], a
    for m in _SENT_END.finditer(text, a, b):
        if not _is_boundary(text, m):
            continue
        end = m.start() + len(m.group(0).rstrip())
        if end > start:
            out.append((start, end))
        start = m.end()
    if b > start:
        out.append((start, b))
    return out


def sentence_spans(text: str) -> list[tuple[int, int]]:
    spans, pos = [], 0
    for para in _NEWLINE_BREAK.finditer(text):
        spans.extend(_split_para(text, pos, para.start()))
        pos = para.end()
    spans.extend(_split_para(text, pos, len(text)))
    return spans


# ── body normalisation + resolution ──────────────────────────────────────────────────────────────────────────
_WS = re.compile(r"\s+")
_LETTERS = re.compile(r"[A-Za-zÀ-ÿ]")
_SP_SUFFIX = re.compile(r"(?<=\d)\s+(bis|ter|quater|quinquies|sexies|septies|octies|novies|decies|undecies|duodecies)\b", re.I)
_SP_ORD = re.compile(r"(?<=\d)\s+(er|ère|e|ème)\b")
_SP_ABBR = re.compile(r"\b([A-Z])\s+\.(?=\s*[A-Z]\b|\s*$|\s*[,;)])")
_SP_SUP = re.compile(r"(?<=\d)\s*\^\s*(?=\d)")
_NL_WORDS = re.compile(r"\b(het|een|van|wordt|niet|zijn|voor|worden|bij|deze|die|dat|met|belasting)\b")
_FR_WORDS = re.compile(r"\b(le|la|les|des|une|est|pour|dans|par|qui|que|ce|cette|sont|impôt)\b")
_SP_SLASH = re.compile(r"(?i)\b(articles?|art\.)\s+(\d{1,3})\s+(\d{1,2})(?![\d°/%]|\s*(?:er|e|ème|bis|ter|quater|à|et|ou)\b|\s*\.\d)")
SLASH_STEMS: dict[str, set[str]] = {}       # article numbers that have N/k sub-articles in corpus B (set by build_reception)


def _slash(m: re.Match) -> str:
    return f"{m.group(1)} {m.group(2)}/{m.group(3)}" if m.group(3) in SLASH_STEMS.get(m.group(2), ()) else m.group(0)


def normalise_body(body: str) -> str:
    """Undo PDF-style spacing that defeats the grammar: "36 bis" → "36bis", "1 er" → "1er", "C . T . A ." → "C.T.A."."""
    body = body.replace("|", " ")
    body = _SP_SLASH.sub(_slash, body)
    body = _SP_SUFFIX.sub(lambda m: m.group(1).lower(), body)
    body = _SP_ORD.sub(lambda m: m.group(1), body)
    for _ in range(3):
        body = _SP_ABBR.sub(r"\1.", body)
    body = re.sub(r"(?<=\b[A-Z]\.)\s+(?=[A-Z]\.(?:\s|$))", "", body)
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


# ── build ────────────────────────────────────────────────────────────────────────────────────────────────────
def build_reception(docs_b: list[Doc], excluded_docs: set[str] | None = None, verbose: bool = True) -> dict:
    """{article id → {"sentences": [{"t", "src", "type", "nl"}], "titles": [...], "n_raw", "types"}} + "__stats__"."""
    excluded_docs = excluded_docs or set()
    R = Resolver([d.doc_id for d in docs_b])
    SLASH_STEMS.clear()
    for d in docs_b:
        art = d.meta.get("article") or ""
        if "/" in art:
            a, b = art.split("/", 1)
            SLASH_STEMS.setdefault(a, set()).add(b)
    per_article: dict[str, list[dict]] = collections.defaultdict(list)
    st: collections.Counter = collections.Counter()
    t0 = time.perf_counter()
    for folder, stype in SOURCE_TYPES.items():
        fdir = MYFIN / folder
        if not fdir.is_dir():
            continue
        for p in sorted(fdir.glob("*.md")):
            fm, body = _parse_front_matter(p.read_text(encoding="utf-8", errors="replace"))
            body = body.strip()
            if body.startswith("# "):
                body = body.split("\n", 1)[1] if "\n" in body else ""
            body = normalise_body(body[:MAX_CHARS])
            did = f"{folder}/{p.stem}"
            if did in excluded_docs:
                st["docs_excluded"] += 1
                continue
            title = fm.get("title", p.stem)
            path = fm.get("path", []) if isinstance(fm.get("path"), list) else []
            own_fam = DOMAIN_FAMILY.get(path[1] if len(path) > 1 else "")
            region = region_of(title, path)
            date = fm.get("document_date") or ""
            st[f"docs:{stype}"] += 1
            spans = starts = None
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
                    if (t, a) in seen_here:
                        continue
                    seen_here.add((t, a))
                    per_article[t].append({"t": sent, "src": did, "type": stype, "date": date, "title": title, "nl": is_dutch(sent)})
    st["extract_s"] = round(time.perf_counter() - t0, 1)

    out = {}
    for art, rows in per_article.items():          # cap: round-robin over source types, then over documents (newest first)
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
        out[art] = {"sentences": [{"t": r["t"], "src": r["src"], "type": r["type"], "nl": r["nl"]} for r in picked],
                    "titles": titles, "n_raw": len(rows), "types": sorted(set(r["type"] for r in rows))}
    st["articles_with_reception"] = len(out)
    st["articles_total"] = len(docs_b)
    st["sentences_kept"] = sum(len(v["sentences"]) for v in out.values())
    st["excluded_source_docs"] = len(excluded_docs)
    if verbose:
        print(f"  reception: {st['resolved']} resolved mentions, {len(out)}/{len(docs_b)} articles, {st['sentences_kept']} sentences "
              f"({st['extract_s']} s; {st['excluded_source_docs']} source documents excluded)", flush=True)
    return {"articles": out, "stats": dict(st), "cap_sentences": CAP_SENTENCES, "cap_titles": CAP_TITLES}


def reception_path(exclude_mined: bool = False) -> Path:
    return INDEX / ("B_reception_nomined.json" if exclude_mined else "B_reception.json")


def load_reception(path: Path | None = None, exclude_mined: bool = False) -> dict:
    """The per-article reception table (``{article id → …}``) as :class:`lexical.LexicalIndex` expects it."""
    path = Path(path) if path else reception_path(exclude_mined)
    arts = json.loads(path.read_text())["articles"]
    arts["__source__"] = path.name
    return arts


def reception_text(entry: dict, variant: str = RECEPTION["variant"]) -> str:
    text = "\n".join(s["t"] for s in entry["sentences"])
    if variant == "sent+title":
        text += "\n" + "\n".join(entry["titles"])
    return text


def reception_tokens(reception: dict, tok, unit_doc: np.ndarray, doc_ids: list[str]) -> list[list[str]]:
    """Tokens of the reception field per lexical unit (every unit of an article carries the article's reception)."""
    per_art = {art: tok(reception_text(v)) for art, v in reception.items() if not art.startswith("__")}
    return [per_art.get(doc_ids[int(d)], []) for d in unit_doc]


def mined_source_docs() -> set[str]:
    from rag_eval import load_questions_mined
    out: set[str] = set()
    for c in ("B", "C"):
        out |= {q.meta["source_doc"] for q in load_questions_mined(c) if q.meta.get("source_doc")}
    return out


import numpy as np  # noqa: E402  (after the pure-python grammar; used by reception_tokens)

if __name__ == "__main__":
    import argparse
    from corpus import load_b
    ap = argparse.ArgumentParser()
    ap.add_argument("--exclude-mined", action="store_true", help="leak-free variant for the mined evaluation sets")
    a = ap.parse_args()
    INDEX.mkdir(parents=True, exist_ok=True)
    rec = build_reception(load_b(), mined_source_docs() if a.exclude_mined else set())
    out = reception_path(a.exclude_mined)
    out.write_text(json.dumps(rec, ensure_ascii=False))
    print("saved", out, json.dumps({k: v for k, v in rec["stats"].items() if not k.startswith(("docs:", "unresolved"))}))
