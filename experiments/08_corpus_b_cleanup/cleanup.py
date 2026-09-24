"""Corpus B enrichment used by later experiments.

* :func:`clean_article` – strips amendment-history preambles
  ("Art. 185, § 3 … est applicable à partir de … Numac …"), "[montants indexés …]"
  markers and "(modifié par l'art. … (M.B., …))" notes that flatten IDF and
  dilute embeddings.
* :func:`region_of_code` – region metadata per code id.
* :func:`detect_region` – query-time region detection from region words and
  Belgian city / commune names.
"""
from __future__ import annotations

import re
import unicodedata

_PREAMBLE_LINE = re.compile(
    r"^(?:\(?\s*(?:Art\.|Article|L'art\.|Les art\.|L'article)\s.*?(?:applicable|en vigueur|abrog|remplac|ins[ée]r|modifi|r[ée]tabli|compl[ée]t)"
    r"|\(?\s*(?:al\.|alin[ée]a|§)\s.*?(?:applicable|en vigueur|abrog|remplac|ins[ée]r|modifi)"
    r"|\(\s*(?:modifi|remplac|ins[ée]r|abrog|compl[ée]t|r[ée]tabli)|\[.*?(?:index|Numac|Toute modification).*?\]"
    r"|\(?\s*Le texte de l.AR n°)",
    re.IGNORECASE)
_NOTE_TAIL = re.compile(r"(?:Numac\s*:?\s*\d+\)?|M\.B\.,?\s*\d{2}\.\d{2}\.\d{4}[^)]*\)?)\s*$")


def clean_article(text: str) -> str:
    lines = text.split("\n")
    out: list[str] = []
    head = True
    for ln in lines:
        s = ln.strip()
        if head and (_PREAMBLE_LINE.match(s) or _NOTE_TAIL.search(s) or not s):
            continue          # drop leading amendment notes
        head = False
        if re.match(r"^\[.*(?:index|Numac|Toute modification).*\]$", s):
            continue          # bracketed indexation markers anywhere
        out.append(ln)
    cleaned = "\n".join(out).strip()
    return cleaned if len(cleaned) >= 15 else text


_REGION = {
    "wal": {"csucc_wal", "cenr_wal", "cta_wal", "cir92_wal", "arcir92_wal"},
    "bxl": {"csucc_bxl", "cenr_bxl", "cta_bxl", "cbpf", "agbxl2019", "cir92_bxl", "arcir92_bxl"},
    "vla": {"csucc_vla", "cenr_vla", "cta_vla", "vcf", "avcf", "ar1936_vla", "cir92_vla", "arcir92_vla"},
}


def region_of_code(code: str) -> str:
    for r, codes in _REGION.items():
        if code in codes:
            return r
    if code == "ar1936_bxl":
        return "bxl,wal"
    return "fed"


def _fold(s: str) -> str:
    s = unicodedata.normalize("NFKD", s.lower())
    return "".join(c for c in s if not unicodedata.combining(c))


CITY_REGION = {
    # Wallonia
    "namur": "wal", "liege": "wal", "charleroi": "wal", "mons": "wal", "tournai": "wal", "arlon": "wal",
    "wavre": "wal", "nivelles": "wal", "verviers": "wal", "la louviere": "wal", "mouscron": "wal", "huy": "wal",
    "dinant": "wal", "bastogne": "wal", "marche-en-famenne": "wal", "ottignies": "wal", "louvain-la-neuve": "wal",
    "eupen": "wal", "waterloo": "wal", "braine-l'alleud": "wal", "seraing": "wal", "chatelet": "wal",
    # Brussels-Capital (19 communes)
    "bruxelles": "bxl", "brussel": "bxl", "schaerbeek": "bxl", "ixelles": "bxl", "uccle": "bxl", "anderlecht": "bxl",
    "etterbeek": "bxl", "forest": "bxl", "saint-gilles": "bxl", "molenbeek": "bxl", "molenbeek-saint-jean": "bxl",
    "woluwe-saint-lambert": "bxl", "woluwe-saint-pierre": "bxl", "jette": "bxl", "evere": "bxl", "auderghem": "bxl",
    "watermael-boitsfort": "bxl", "koekelberg": "bxl", "ganshoren": "bxl", "berchem-sainte-agathe": "bxl",
    "saint-josse": "bxl", "saint-josse-ten-noode": "bxl",
    # Flanders
    "anvers": "vla", "antwerpen": "vla", "gand": "vla", "gent": "vla", "bruges": "vla", "brugge": "vla",
    "louvain": "vla", "leuven": "vla", "hasselt": "vla", "malines": "vla", "mechelen": "vla", "courtrai": "vla",
    "kortrijk": "vla", "ostende": "vla", "oostende": "vla", "alost": "vla", "aalst": "vla", "genk": "vla",
    "roulers": "vla", "roeselare": "vla", "saint-nicolas": "vla", "sint-niklaas": "vla", "turnhout": "vla",
    "vilvorde": "vla", "vilvoorde": "vla", "hal": "vla", "halle": "vla", "tongres": "vla", "tongeren": "vla",
    "ypres": "vla", "ieper": "vla", "termonde": "vla", "dendermonde": "vla", "knokke": "vla", "zaventem": "vla",
}
_REGION_WORDS = {
    "wal": ["wallonie", "wallon", "wallonne", "region wallonne"],
    "bxl": ["bruxelles-capitale", "bruxellois", "bruxelloise", "region bruxelloise"],
    "vla": ["flandre", "flamand", "flamande", "region flamande", "vlaanderen", "vlaams"],
}


def detect_region(question: str) -> str | None:
    q = _fold(question)
    for r, words in _REGION_WORDS.items():
        if any(w in q for w in words):
            return r
    for city, r in sorted(CITY_REGION.items(), key=lambda kv: -len(kv[0])):
        if re.search(rf"(?<![a-z]){re.escape(city)}(?![a-z])", q):
            return r
    return None


def allowed_regions(detected: str | None) -> set[str] | None:
    """Regions whose documents may answer a question: the detected one plus federal."""
    if detected is None:
        return None
    return {detected, "fed"}
