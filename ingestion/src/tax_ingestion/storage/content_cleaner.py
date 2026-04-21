"""Pre-ingestion content cleaner for Belgian tax documents.

Removes sections that degrade semantic-search quality:
  * Commentary index sections (Législation, Circulaires, Jurisprudence,
    Questions parlementaires, Autres documents, Avis) — these are reference
    lists with one-line descriptions, not substantive text.
  * Table-of-contents blocks.
  * Boilerplate metadata (SPF header, "Réf. interne", Numac, etc.).
  * Royal decree preamble boilerplate (Vu …, Considérant que, signature).

The cleaner is intentionally conservative: it only strips patterns that are
demonstrably noise across the full Fisconet+ corpus.  Substantive content
inside circulars and FAQs is preserved.
"""

from __future__ import annotations

import re

# ── Section-level removal ────────────────────────────────────────────────
# These heading patterns mark the START of an index/reference section in
# "Commentaire de l'article …" pages.  Everything from the heading to the
# next same-level heading (or EOF) is noise.

_INDEX_SECTION_HEADINGS = [
    r"^#{1,3}\s*L[ée]gislation\s*$",
    r"^#{1,3}\s*Circulaires?\s*$",
    r"^#{1,3}\s*Jurisprudence\s*$",
    r"^#{1,3}\s*Questions?\s+parlementaires?\s*$",
    r"^#{1,3}\s*Autres?\s+documents?\s*$",
    r"^#{1,3}\s*Avis\s*$",
]

# Combined pattern: matches any index-section heading
_INDEX_HEADING_RE = re.compile(
    "|".join(_INDEX_SECTION_HEADINGS),
    re.MULTILINE | re.IGNORECASE,
)

# Any markdown heading (used to find the *next* heading after an index section)
_ANY_HEADING_RE = re.compile(r"^#{1,6}\s+\S", re.MULTILINE)


def _strip_index_sections(text: str) -> str:
    """Remove full index/reference sections (Législation, Circulaires, …).

    For each index heading found, remove everything from that heading up to
    (but not including) the next heading of same or higher level, or EOF.
    """
    while True:
        m = _INDEX_HEADING_RE.search(text)
        if not m:
            break

        start = m.start()
        # Determine the heading level (count leading '#')
        heading_line = text[start : text.index("\n", start) if "\n" in text[start:] else len(text)]
        level = len(heading_line) - len(heading_line.lstrip("#"))

        # Find the next heading at same or higher level
        rest = text[m.end():]
        end = len(text)
        for next_m in _ANY_HEADING_RE.finditer(rest):
            next_line = rest[next_m.start() : rest.index("\n", next_m.start()) if "\n" in rest[next_m.start():] else len(rest)]
            next_level = len(next_line) - len(next_line.lstrip("#"))
            if next_level <= level:
                end = m.end() + next_m.start()
                break

        text = text[:start] + text[end:]

    return text


# ── Table-of-Contents removal ────────────────────────────────────────────
# Fisconet circulars have a ToC block that looks like:
#   T able des matières         (or TABLE DES MATIERES, Table des matière s)
#   I. Introduction
#   II. Commentaire
#   A. Foo
#   B. Bar
#   III. Examples
#   ...
# The ToC ends when a real markdown heading (# …) or a blank-line
# followed by non-ToC text appears.

_TOC_START_RE = re.compile(
    r"^T\s*(?:ABLE|able)\s+[Dd][Ee][Ss]\s+[Mm][Aa][Tt][Ii][EeÈè][Rr][Ee][Ss]?\s*$",
    re.MULTILINE,
)

# A ToC line: Roman numeral + dot, or uppercase letter + dot, or just text
# that does NOT start with a markdown heading.
_TOC_LINE_RE = re.compile(
    r"^(?:"
    r"[IVXLC]+\.\s|"            # Roman numeral lines (I. II. III. …)
    r"[A-H]\.\s|"               # Lettered sub-items (A. B. C. …)
    r"\d+\.\s|"                 # Numbered items (1. 2. 3. …)
    r"[a-zà-ÿ]|"               # Lowercase continuation lines
    r"ANNEXE|"                  # Annexe markers
    r"\s*$"                     # Blank lines inside ToC
    r")"
)


def _strip_toc(text: str) -> str:
    """Remove Table-of-Contents blocks."""
    while True:
        m = _TOC_START_RE.search(text)
        if not m:
            break

        start = m.start()
        # Walk forward line by line to find where the ToC ends
        pos = m.end()
        lines = text[pos:].split("\n")
        consumed = 0
        for line in lines:
            stripped = line.strip()
            # ToC ends at a markdown heading or substantive paragraph
            if stripped.startswith("#"):
                break
            if _TOC_LINE_RE.match(stripped) or not stripped:
                consumed += len(line) + 1  # +1 for the newline
            else:
                # Non-ToC line that isn't a heading — might be the end of ToC
                # or a stray line.  If the next line also doesn't look like ToC,
                # end here.
                consumed += len(line) + 1
                break

        text = text[:start] + text[pos + consumed:]

    return text


# ── Boilerplate line patterns ────────────────────────────────────────────
# Individual lines (or small groups) that are metadata / boilerplate.

_BOILERPLATE_LINE_RES = [
    # Fisconet metadata header
    re.compile(r"^\*\*(?:Source|GUID|Date)\s*:\*\*.*$", re.MULTILINE),
    re.compile(r"^---\s*$", re.MULTILINE),

    # SPF administrative header
    re.compile(
        r"^SPF\s+Finances\s*,\s*(?:le\s+)?\d+\s*\.\s*\d+\s*\.\s*\d+.*$",
        re.MULTILINE | re.IGNORECASE,
    ),
    re.compile(
        r"^A?\s*dministration\s+g[ée]n[ée]rale\s+de\s+la\s+Fiscalit[ée].*$",
        re.MULTILINE | re.IGNORECASE,
    ),

    # "ANNEXE(S) : N" line at top of circulars
    re.compile(r"^ANNEXE\s*S?\s*:\s*\d+\s*$", re.MULTILINE),

    # Internal reference number
    re.compile(r"^R[ée]f\.\s*interne\s*:\s*[\d\s.]+$", re.MULTILINE),

    # Moniteur Belge publication line
    re.compile(r"^M\.B\.\s*,?\s*\d{1,2}\.\d{1,2}\.\d{4}.*$", re.MULTILINE),

    # Numac reference
    re.compile(r"^Numac\s*:\s*\d+\s*$", re.MULTILINE),

    # Royal decree signature block lines
    re.compile(r"^Donn[ée]\s+[àa]\s+Bruxelles.*$", re.MULTILINE),
    re.compile(r"^Par\s+le\s+Roi\s*:\s*$", re.MULTILINE),
    re.compile(r"^Le\s+Ministre\s+des\s+Finances\s*,?\s*$", re.MULTILINE),
    re.compile(r"^PHILIPPE\s*$", re.MULTILINE),
    re.compile(r"^A\s+tous\s*,\s*pr[ée]sents\s+et\s+[àa]\s+venir\s*,\s*Salut\s*\.?\s*$", re.MULTILINE),
]


def _strip_boilerplate_lines(text: str) -> str:
    """Remove individual boilerplate lines."""
    for pat in _BOILERPLATE_LINE_RES:
        text = pat.sub("", text)
    return text


# ── Royal decree preamble ────────────────────────────────────────────────
# "Vu le Code …; Vu la loi …; Vu l'urgence;" blocks and
# "Considérant que :" blocks in royal decrees.

_VU_BLOCK_RE = re.compile(
    r"(?:^Vu\s+(?:le|la|les|l['']).+?;\s*\n)+",
    re.MULTILINE,
)

_CONSIDERANT_BLOCK_RE = re.compile(
    r"^Consid[ée]rant\s+que\s*:.*?\n(?:(?:^[-–•].*\n|^\s+.*\n|^\s*\n)*)",
    re.MULTILINE,
)

_SUR_PROPOSITION_RE = re.compile(
    r"^Sur\s+(?:la\s+)?proposition\s+du\s+[Mm]inistre.*$",
    re.MULTILINE,
)
_NOUS_AVONS_RE = re.compile(
    r"^Nous\s+avons\s+arr[êe]t[ée]\s+et\s+arr[êe]tons\s*:?\s*$",
    re.MULTILINE,
)


def _strip_decree_preamble(text: str) -> str:
    """Remove royal decree formulaic preamble blocks."""
    text = _VU_BLOCK_RE.sub("", text)
    text = _CONSIDERANT_BLOCK_RE.sub("", text)
    text = _SUR_PROPOSITION_RE.sub("", text)
    text = _NOUS_AVONS_RE.sub("", text)
    return text


# ── Keyword/tag lines at document start ──────────────────────────────────
# Many Fisconet documents have a semicolon-separated keyword line right
# after the title, e.g.:
#   "impôt des personnes physiques ; biens immobiliers ; déduction …"
# These are tags, not prose.

_KEYWORD_LINE_RE = re.compile(
    r"^[a-zà-ÿ][a-zà-ÿ\s,'()°/^]+(?:\s*;\s*[a-zà-ÿ][a-zà-ÿ\s,'()°/^]+){2,}\s*$",
    re.MULTILINE,
)


def _strip_keyword_lines(text: str) -> str:
    """Remove semicolon-separated keyword/tag lines."""
    return _KEYWORD_LINE_RE.sub("", text)


# ── Final whitespace normalization ───────────────────────────────────────

def _normalize_whitespace(text: str) -> str:
    """Collapse runs of blank lines to at most two newlines."""
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


# ── Public API ───────────────────────────────────────────────────────────

def clean_for_indexing(text: str) -> str:
    """Clean a document's text before chunking for semantic search.

    Removes:
    - Index/reference sections (Législation, Circulaires, Jurisprudence,
      Questions parlementaires, Autres documents, Avis)
    - Table-of-contents blocks
    - Boilerplate metadata lines (SPF header, Numac, signatures, etc.)
    - Royal decree preamble boilerplate
    - Keyword/tag lines

    Preserves all substantive content: explanations, examples, legal
    provisions, and policy commentary.
    """
    text = _strip_index_sections(text)
    text = _strip_toc(text)
    text = _strip_boilerplate_lines(text)
    text = _strip_decree_preamble(text)
    text = _strip_keyword_lines(text)
    text = _normalize_whitespace(text)
    return text
