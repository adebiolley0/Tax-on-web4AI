"""A lightweight 'structure prior': multiplicative boosts from question cues to document metadata.

* region: the question names a region or a city (exp-08 ``detect_region``) → documents of that
  region ×(1+γ), documents of another region ×(1-γ), federal / unknown unchanged.
* domain: a few regexes on the question (TVA, succession, enregistrement, taxes assimilées,
  droits et taxes divers, impôts sur les revenus) → documents whose taxonomy domain (corpus C
  ``path[1]``) or code family (corpus B) matches ×(1+γ). Nothing is penalised for a missing cue.
"""
from __future__ import annotations

import re

import numpy as np

from cleanup import detect_region, region_of_code  # noqa: E402  (08_corpus_b_cleanup)

TOPIC_CUES = [
    ("tva", r"\btva\b|taxe sur la valeur|assujetti|facture"),
    ("succ", r"succession|h[ée]rit|d[ée]c[èe]s|d[ée]c[ée]d|\blegs?\b|testament|l[ée]gu"),
    ("enr", r"enregistrement|droits de vente|abattement|ach[èe]te|acquisition|achat|donation|donner"),
    ("ta", r"taxe de (?:mise en )?circulation|immatricul|remorque|chevaux fiscaux|\bcv\b"),
    ("div", r"comptes?-titres|op[ée]rations de bourse|\btob\b|\btact\b"),
    ("ir", r"pr[ée]compte|imp[ôo]t des soci[ée]t[ée]s|\bisoc\b|\bipp\b|frais professionnels|d[ée]duction|r[ée]mun[ée]ration|"
           r"pension|revenus|droits d['’]auteur|avantage|salari|employeur|soci[ée]t[ée]|b[ée]n[ée]fice|dividende|int[ée]r[êe]ts"),
]
DOMAIN_OF_C = {"Taxe sur la valeur ajoutée": "tva", "Droits de succession": "succ",
               "Droits d'enregistrement, d'hypothèque et de greffe": "enr", "Taxes assimilées aux impôts sur les revenus": "ta",
               "Droits et taxes divers": "div", "Impôts sur les revenus": "ir"}
DOMAIN_OF_B = {"cir92": {"ir"}, "arcir92": {"ir"}, "ctva": {"tva"}, "artva": {"tva"}, "ue282": {"tva"},
               "csucc": {"succ"}, "cenr": {"enr"}, "cta": {"ta"}, "vcf": {"succ", "enr", "ta"}, "avcf": {"succ", "enr", "ta"},
               "ar1927": {"enr"}, "ar1940": {"enr"}, "ar1936": {"succ"}, "cbpf": {"ir", "ta"}, "crecouv": {"ir", "tva"},
               "agbxl2019": {"enr"}}


def question_cues(question: str) -> tuple[str | None, set[str]]:
    q = question.lower()
    return detect_region(question), {k for k, rx in TOPIC_CUES if re.search(rx, q)}


def doc_attrs_b(doc_ids: list[str]) -> tuple[list[str | None], list[set[str]]]:
    regions, domains = [], []
    for d in doc_ids:
        code = d.split(":")[0]
        r = region_of_code(code).split(",")[0]
        regions.append(None if r == "fed" else r)
        domains.append(DOMAIN_OF_B.get(code.split("_")[0], set()))
    return regions, domains


def doc_attrs_c(doc_ids: list[str], meta: dict) -> tuple[list[str | None], list[set[str]]]:
    regions, domains = [], []
    for d in doc_ids:
        m = meta.get(d, {})
        r = m.get("region")
        regions.append(r if r in ("wal", "bxl", "vla") else None)
        p = m.get("path") or []
        dom = DOMAIN_OF_C.get(p[1]) if len(p) > 1 else None
        domains.append({dom} if dom else set())
    return regions, domains


def boost_matrix(questions, regions: list[str | None], domains: list[set[str]], gamma_region: float, gamma_domain: float) -> np.ndarray:
    n = len(regions)
    reg_arr = np.array([r or "" for r in regions])
    dom_masks = {k: np.array([k in ds for ds in domains]) for k, _ in TOPIC_CUES}
    out = np.ones((len(questions), n), dtype=np.float32)
    for i, q in enumerate(questions):
        qr, cues = question_cues(q.question)
        if qr and gamma_region:
            out[i][reg_arr == qr] *= 1 + gamma_region
            out[i][(reg_arr != qr) & (reg_arr != "")] *= 1 - gamma_region
        if cues and gamma_domain:
            m = np.zeros(n, dtype=bool)
            for c in cues:
                m |= dom_masks[c]
            out[i][m] *= 1 + gamma_domain
    return out
