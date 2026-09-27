"""Regex grammar for Belgian legal references, shared by the question miner (no LLM, no model).

Two layers, both moved verbatim from experiment 11 (``refparse.py`` and ``graph_c.py``) so that the
mined question sets stay reproducible after that folder is gone:

**In-text article references** – :func:`iter_article_refs` yields, for every "article(s) / art."
mention, the article numbers it names (ranges kept as ``[a, 'à', b]``) and the *tail* that follows the
consumed span; :func:`classify_tail` turns the tail into ``("same", kind)`` (own code / no qualifier),
``("family", fam)`` (an explicitly named code: ``cir92``, ``ctva``, ``cenr`` …), ``("ar", n)``
(numbered TVA royal decree) or ``("external", "")`` (a law, decree, treaty or a code outside the
corpus).  The span parser consumes only reference tokens (numbers, §/alinéa markers, ordinals,
connectors), so "article 7, § 1er, 2°, c, excéder …" stops before "excéder" and "article 3, 2° à 8" is
not a range.  :func:`expand_items` resolves items and ranges through callbacks.

**Document title keys** – :func:`title_keys` maps a ``myfin_docs`` title + folder + taxonomy path to
the keys under which the document can be cited (``art:<fam>:<num>``, ``art:<fam>:<region>:<num>``,
``c:2019/C/40``, ``c:ci.rh.…``, ``c:et.…``, ``da:2018.0775``, ``jur:…``, ``qp:…``, ``ar:…``) plus parsed
attributes (``family``, ``num``, ``region``); :func:`region_of` and :data:`DOMAIN_FAMILY` give a
document's region and default code family; ``CIRC_TEXT_RE`` / ``ET_TEXT_RE`` / ``DA_TEXT_RE`` find
circulars, E.T. circulars and rulings cited in running text.
"""
from __future__ import annotations

import re
import unicodedata


# ── article references (experiment 11 refparse.py) ───────────────────────────
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


AMEND_PRE_RE = re.compile(
    r"(?:modifi|ins[ée]r|remplac|abrog|compl[ée]t|r[ée]tabli|introduit|supprim|renum[ée]rot|gewijzigd|ingevoegd|vervangen|opgeheven)\S*\s+"
    r"(?:par\s+(?:l['’]|les\s+)?|bij\s+)$", re.I)


def iter_article_refs(text: str, tail_len: int = 90):
    """Yield (mention_start, items, tail) for every article mention in ``text``.
    A mention preceded by "modifié / inséré / remplacé par l'" is an amendment note that
    cites the *amending* act, so its tail is rewritten as external."""
    for m in ART_RE.finditer(text):
        items, end = parse_span(text, m.end())
        if not items:
            continue
        nxt = text[end: end + 2]
        if nxt[:1] == "." and nxt[1:2].isdigit():      # 'article 3.86' style numbers we do not model
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


# ── document titles and in-text document citations (experiment 11 graph_c.py) ─

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


# ── in-text document citations ───────────────────────────────────────────────
CIRC_TEXT_RE = re.compile(r"circulaires?\s+(?:n[°o]\.?\s*)?(?:(?:AGFisc|AAFisc|AAF|AFER|AFZ|AOIF)\s*(?:N[°o]\.?)?\s*)?"
                          r"(?:(\d{4})\s*/\s*C\s*/\s*(\d+)|(\d+)\s*/\s*(\d{4})|Ci\.\s?(RH|D)\.?\s?([\d.]+/[\d.]+)|(\d+)\s+(?:dd\.|du)\s+\d{2}\.\d{2}\.(\d{4}))", re.I)
ET_TEXT_RE = re.compile(r"\bE\.?\s?T\.?\s?(\d{2,3}[.,]\d{3})\b")
DA_TEXT_RE = re.compile(r"(?:d[ée]cisions? anticip[ée]es?|voorafgaande beslissing(?:en)?|\bDA|\bVB|ruling)\s*(?:n[°o]s?\.?|nrs?\.?)?\s*\??\s*(\d{3,4}\.\d{3,4})", re.I)
