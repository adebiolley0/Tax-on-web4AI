"""Regex parser for legal references ("article 145/33", "art. 215, § 2", "articles 202 à 205",
"l'article 44 du Code de la TVA" …) shared by the corpus B and C graph builders. No LLM.

`iter_article_refs(text)` yields, for every "article(s) / art." mention, the list of article
numbers it names (ranges kept as ``[a, 'à', b]``) and the *tail* that follows the consumed
reference span, which `classify_tail(tail)` turns into one of

* ``("same", kind)``   – "du même Code" / "du présent arrêté" / no qualifier (own code)
* ``("family", fam)``  – an explicitly named code ("du Code de la TVA", "CIR 92", "AR/CIR 92" …)
* ``("ar", n)``        – "arrêté royal n° 20" (numbered TVA royal decrees)
* ``("external", "")`` – a law, decree, treaty or a code that is not in the corpus.

The span parser consumes only reference tokens (numbers, §/alinéa markers, ordinals, connectors),
so "article 7, § 1er, 2°, c, excéder les deux tiers du revenu …" stops before "excéder" and is
resolved to article 7 of the same code, and "article 3, 2° à 8" is not a range of articles.
"""
from __future__ import annotations

import re

SUFFIX = r"(?:bis|ter|quater|quinquies|sexies|septies|octies|novies|decies|undecies|duodecies)?"
ART_RE = re.compile(r"(?<![\w/.’'])(?:articles?|art\.?|artikel(?:en)?)\s*(?=\d)", re.I)
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
    r"^\s*,?\s*(?:du|de la|de l['’]|de ce|de cet|de cette|dudit|de ladite|van (?:dit|dezelfde|hetzelfde))\s+"
    r"(?:même|présent[e]?|zelfde)\s+(?P<kind>Code|arrêté|décret|loi|ordonnance|Wetboek|besluit|wet|decreet)", re.I)
BARE_CODE_RE = re.compile(
    r"^\s*,?\s*(?:du|de ce|de l['’]|de la|dudit)\s+(?:Code|Wetboek)\b"
    r"(?!\s+(?:des|de|du|d['’]|civil|pénal|judiciaire|wallon|flamand|bruxellois|de la|rural|forestier|électoral|consulaire))", re.I)
EXTERNAL_RE = re.compile(
    r"^\s*,?\s*(?:"
    r"(?:L|LP|Lprog|LS|AR|AGW|AGF|AGBC|AGRBC|D|DP|Décr\.?|AM|O|Ord\.?|A\.R\.|L\.|Loi|Décret|Arrêté|Ordonnance)\s+(?:du\s+)?\d{1,2}[./]\d{1,2}[./]\d{2,4}"
    r"|(?:de la|du|de l['’]|de cette|de cet|de ladite|dudit|de la même|du même|de la présente|du présent|van de|van het|van dezelfde)\s+"
    r"(?:loi|décret|arrêté(?!\s+royal\s+n)|ordonnance|Loi-programme|loi-programme|Constitution|Traité|directive|règlement|convention|accord|protocole|"
    r"wet\b|decreet|besluit|verordening|richtlijn|"
    r"Code\s+(?:des sociétés|civil|pénal|judiciaire|de droit économique|de commerce|de la démocratie|wallon|de la nationalité|d['’]instruction|"
    r"de la route|forestier|rural|électoral|de droit international|consulaire|de la navigation|de la sécurité|du bien-être|de l['’]environnement|"
    r"flamand de l['’]aménagement|bruxellois de l['’]aménagement|de droit pénal|des impôts sur les revenus 1964|du logement|de l['’]eau|de l['’]énergie)"
    r"|Wetboek\s+(?:van vennootschappen|van strafrecht|van economisch recht|van koophandel)"
    r")", re.I)
CODE_HINTS: list[tuple[re.Pattern, str]] = [(re.compile(
    r"^\s*[,(]?\s*(?:(?:du|de la|de l['’]|de|van het|van de)\s+)?(?:même\s+)?" + p, re.I), fam) for p, fam in [
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
AR_RE = re.compile(r"^\s*[,(]?\s*(?:(?:du|de l['’])\s+)?(?:arrêté royal|A\.?R\.?|koninklijk besluit|K\.?B\.?)\s*n[°o]\.?\s*(\d+)", re.I)


def parse_span(text: str, pos: int) -> tuple[list[str], int]:
    """Consume reference tokens from ``pos``; return (items, end). Items are article
    numbers (with '^' normalised to '/') and 'à' range markers."""
    items: list[str] = []
    skip = False           # inside a §/alinéa/n° scope (until the next comma)
    range_skip = False     # 'à' after a skipped number → the next number is skipped too
    last_ok = False
    while True:
        m = TOKEN_RE.match(text, pos)
        if not m:
            break
        if m.group("num"):
            if skip or m.group("ord") or range_skip:
                range_skip = False
                last_ok = False
                if m.group("ord") and not skip:
                    range_skip = False
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
    # drop trailing / dangling range markers
    while items and items[-1] == "à":
        items.pop()
    return items, pos


def iter_article_refs(text: str, tail_len: int = 90):
    """Yield (mention_start, items, tail) for every article mention in ``text``."""
    for m in ART_RE.finditer(text):
        items, end = parse_span(text, m.end())
        if not items:
            continue
        nxt = text[end: end + 2]
        if nxt[:1] == "." and nxt[1:2].isdigit():      # 'article 3.86' style numbers we do not model
            continue
        yield m.start(), items, text[end: end + tail_len]


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
    """Resolve a list of items with the given callbacks (ranges via expand_range)."""
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
