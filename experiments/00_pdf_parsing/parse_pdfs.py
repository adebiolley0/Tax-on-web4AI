#!/usr/bin/env python3
"""Step 1 – parse the MyMinfin library PDFs (``myfin_pdfs/``) into an
article-level corpus (**Corpus B**).

Output (``experiments/data/corpus_b/``):
  * ``articles.jsonl``   – one record per article (id, code, article, title,
                           heading_path, text, source_file, page)
  * ``md/<code>.md``     – human-readable dump per code
  * ``parse_report.json``– per-code counts / anomalies

Design notes (see README.md):
  * Native-text PDFs → ``pymupdf`` ``get_text`` is enough (no OCR / layout model).
  * Bilingual two-column editions: only the French column is clipped.
  * Running headers/footers, dot-leader table-of-contents lines and bare page
    numbers are dropped.
  * Articles are detected from ``Article N`` / ``Art. N`` heading lines whose
    remainder is empty or a known qualifier (``, CIR 92``, ``(applicable …)``).
  * Structural headings (TITRE / CHAPITRE / Section / Sous-section …) are kept as
    a *heading path* attached to every article for contextual chunking.
"""
from __future__ import annotations

import json
import re
import sys
import time
from collections import Counter
from dataclasses import dataclass, field, asdict
from pathlib import Path

import pymupdf

REPO = Path(__file__).resolve().parents[2]
PDF_DIR = REPO / "myfin_pdfs"
OUT_DIR = REPO / "experiments" / "data" / "corpus_b"


@dataclass
class CodeSpec:
    file: str
    code: str
    title: str
    column: str | None = None       # None | "left" | "right"  (French column)
    form: str = "Article"           # dominant article-heading form: "Article" | "Art."
    default: bool = True            # part of the default Corpus B subset


SPECS: list[CodeSpec] = [
    CodeSpec("cir_92_revenus_de_2026_exercice_d_imposition_2027_federal.pdf", "cir92",
             "Code des impôts sur les revenus 1992 (CIR 92) – dispositions fédérales, revenus 2026 / ex. imp. 2027"),
    CodeSpec("cir_92_revenus_de_2026_exercice_d_imposition_2027_region_de_bruxelles_capitale.pdf", "cir92_bxl",
             "CIR 92 – édition Région de Bruxelles-Capitale, revenus 2026", default=False),
    CodeSpec("cir_92_revenus_de_2026_exercice_d_imposition_2027_region_flamande.pdf", "cir92_vla",
             "CIR 92 – édition Région flamande, revenus 2026", default=False),
    CodeSpec("cir_92_revenus_de_2026_exercice_d_imposition_2027_region_wallonne.pdf", "cir92_wal",
             "CIR 92 – édition Région wallonne, revenus 2026", default=False),
    CodeSpec("ar_cir_92_revenus_2026_exercice_d_imposition_2027_federal.pdf", "arcir92",
             "Arrêté royal d'exécution du CIR 92 (AR/CIR 92) – dispositions fédérales, revenus 2026"),
    CodeSpec("ar_cir_92_revenus_2026_exercice_d_imposition_2027_region_de_bruxelles_capitale.pdf", "arcir92_bxl",
             "AR/CIR 92 – édition Région de Bruxelles-Capitale", default=False),
    CodeSpec("ar_cir_92_revenus_2026_exercice_d_imposition_2027_region_flamande.pdf", "arcir92_vla",
             "AR/CIR 92 – édition Région flamande", default=False),
    CodeSpec("ar_cir_92_revenus_2026_exercice_d_imposition_2027_region_wallonne.pdf", "arcir92_wal",
             "AR/CIR 92 – édition Région wallonne", default=False),
    CodeSpec("code_de_la_tva_unilingue.pdf", "ctva", "Code de la taxe sur la valeur ajoutée (Code TVA)"),
    CodeSpec("arretes_royaux_de_la_tva_unilingue.pdf", "artva", "Arrêtés royaux d'exécution du Code TVA"),
    CodeSpec("reglement_dexecution_ue_n_282_2011_du_conseil_en_matiere_de_tva_bilingue.pdf", "ue282",
             "Règlement d'exécution (UE) n° 282/2011 du Conseil (TVA)", column="left"),
    CodeSpec("code_des_droits_de_succession_region_wallonne.pdf", "csucc_wal", "Code des droits de succession – Région wallonne"),
    CodeSpec("code_des_droits_de_succession_region_de_bruxelles_capitale.pdf", "csucc_bxl", "Code des droits de succession – Région de Bruxelles-Capitale"),
    CodeSpec("code_des_droits_de_succession_region_flamande.pdf", "csucc_vla", "Code des droits de succession – Région flamande (tables de concordance vers le VCF)"),
    CodeSpec("code_des_droits_d_enregistrement_d_hypotheque_et_de_greffe_region_wallonne.pdf", "cenr_wal", "Code des droits d'enregistrement, d'hypothèque et de greffe – Région wallonne"),
    CodeSpec("code_des_droits_d_enregistrement_d_hypotheque_et_de_greffe_region_de_bruxelles_capitale.pdf", "cenr_bxl", "Code des droits d'enregistrement, d'hypothèque et de greffe – Région de Bruxelles-Capitale"),
    CodeSpec("code_des_droits_d_enregistrement_d_hypotheque_et_de_greffe_region_flamande.pdf", "cenr_vla", "Code des droits d'enregistrement, d'hypothèque et de greffe – Région flamande (concordance VCF)"),
    CodeSpec("code_des_taxes_assimilees_aux_impots_sur_les_revenus_region_wallonne.pdf", "cta_wal", "Code des taxes assimilées aux impôts sur les revenus – Région wallonne"),
    CodeSpec("code_des_taxes_assimilees_aux_impots_sur_les_revenus_region_de_bruxelles_capitale.pdf", "cta_bxl", "Code des taxes assimilées aux impôts sur les revenus – Région de Bruxelles-Capitale"),
    CodeSpec("code_des_taxes_assimilees_aux_impots_sur_les_revenus_region_flamande.pdf", "cta_vla", "Code des taxes assimilées aux impôts sur les revenus – Région flamande"),
    CodeSpec("code_du_recouvrement_amiable_et_force_des_creances_fiscales_et_non_fiscales.pdf", "crecouv",
             "Code du recouvrement amiable et forcé des créances fiscales et non fiscales", form="Art."),
    CodeSpec("code_bruxellois_de_procedure_fiscale_c_b_p_f.pdf", "cbpf", "Code bruxellois de procédure fiscale (CBPF)", column="left", form="Art."),
    CodeSpec("arrete_du_gouvernement_de_la_region_de_bruxelles_capitale_portant_execution_de_l_ordonnance_du_6_mars_2019_rel.pdf", "agbxl2019",
             "Arrêté du Gouvernement de la Région de Bruxelles-Capitale portant exécution de l'ordonnance du 6 mars 2019 (CBPF)", column="left", form="Art."),
    CodeSpec("code_flamand_de_la_fiscalite_codex.pdf", "vcf", "Code flamand de la fiscalité (Vlaamse Codex Fiscaliteit) – traduction française", column="right", form="Art."),
    CodeSpec("arrete_du_gouvernement_flamand_portant_execution_du_code_flamand_de_la_fiscalite_du_13_decembre_2013.pdf", "avcf",
             "Arrêté du Gouvernement flamand portant exécution du Code flamand de la fiscalité", column="right", form="Art."),
    CodeSpec("arrete_royal_du_3_mars_1927_portant_execution_du_code_des_droits_et_taxes_divers.pdf", "ar1927", "Arrêté royal du 3 mars 1927 portant exécution du Code des droits et taxes divers"),
    CodeSpec("arrete_royal_du_31_03_1936_portant_reglement_general_des_droits_de_succession_region_de_bruxelles_capitale_et.pdf", "ar1936_bxl", "Arrêté royal du 31 mars 1936 portant règlement général des droits de succession – Bruxelles-Capitale et Wallonie"),
    CodeSpec("arrete_royal_du_31_03_1936_portant_reglement_general_des_droits_de_succession_region_flamande.pdf", "ar1936_vla", "Arrêté royal du 31 mars 1936 portant règlement général des droits de succession – Région flamande"),
    CodeSpec("arrete_royal_du_11_01_1940_relatif_a_l_execution_du_code_des_droits_d_enregistrement_d_hypotheque_et_de_greffe.pdf", "ar1940", "Arrêté royal du 11 janvier 1940 relatif à l'exécution du Code des droits d'enregistrement"),
    CodeSpec("code_des_douanes_de_l_union_version_integree_avec_les_textes_des_da_tda_et_ia_version_a_jour_au_20_03_2021.pdf", "cdu",
             "Code des douanes de l'Union (règlement (UE) n° 952/2013) – version intégrée DA/TDA/IA", default=False),
    # Skipped on purpose: the two bilingual CIR 92 / AR-CIR 92 "édition 2026" volumes duplicate the
    # unilingual editions above; memento_fiscal_2025.pdf has no legal value (manifest ingest=false).
]

# ── line-level filters ────────────────────────────────────────────────────
_NOISE_LINE = re.compile(
    r"^(?:www\.fisconetplus\.be|WWW\.FISCONETPLUS\.BE|SPF Finances \(AG ?ESS\)|Service Public F[ée]d[ée]ral FINANCES|"
    r"C\.TVA - Mise à j\. .*|AR\.TVA - Mise à j\. .*|Mise à jour jusqu.*|Règlement d.exécution \(UE\) n° 282/2011\s*|"
    r"\d{1,4}|- \d{1,4} -|Expertise et Support Strat[ée]giques?|Réservé pour un(?:e)? (?:usage futur|utilisation ultérieure)\.?)\s*$")
_TOC_LINE = re.compile(r"\.{4,}\s*\d*\s*$|^[. ]{6,}$")
_ART_RE = re.compile(
    r"^(?P<form>Article|Art\.)\s+(?P<num>\d+(?:[./^]\d+)*"
    r"(?:\s?(?:bis|ter|quater|quinquies|sexies|septies|octies|nonies|decies|undecies|duodecies|terdecies|quaterdecies|quindecies|sexdecies)"
    r"(?:/\d+)*)?)\.?(?P<rest>.*)$")
_REST_OK = re.compile(
    r"^\s*$|^\s*,\s*(?:CIR 92|AR/CIR 92|C\.TVA|AR n°)\b.*$|^\s*\((?:applicable|abrogé|Abrogé|ancien|nouveau|inséré|remplacé)[^)]*\)?\s*$"
    r"|^\s*\(abrog[ée]s?\)\s*$|^\s*-\s*\(?(?:abrog[ée]|Abrog[ée])\)?\.?\s*$")
_HEAD_RE = re.compile(
    r"^(?P<lvl>LIVRE|Livre|PARTIE|Partie|TITRE|Titre|CHAPITRE|Chapitre|SECTION|Section|Sous-section|SOUS-SECTION)\s+"
    r"(?P<num>[IVXLC0-9]+(?:er|re|e|bis|ter|quater|quinquies)?(?:[./][0-9IVX]+)?)?\s*[.:–\-]*\s*(?P<txt>.*)$")
_LEVEL = {"LIVRE": 0, "PARTIE": 0, "TITRE": 1, "CHAPITRE": 2, "SECTION": 3, "SOUS-SECTION": 4}
_DECREE_RE = re.compile(r"^Arrêté royal n° (?P<n>\S+), du (?P<date>\d{1,2}(?:er)? \S+ \d{4}),?\s*(?P<txt>.*)$")
_FUTURE_RE = re.compile(r"^DROIT FUTUR\s*\((?:à partir du|applicable à partir du)?\s*(?P<date>[\d.]+)\)")


def page_lines(page: pymupdf.Page, column: str | None) -> list[str]:
    w = page.rect.width
    clip = None
    if column == "left":
        clip = pymupdf.Rect(0, 0, w * 0.5, page.rect.height)
    elif column == "right":
        clip = pymupdf.Rect(w * 0.5, 0, w, page.rect.height)
    txt = page.get_text("text", clip=clip) if clip else page.get_text("text")
    out = []
    for raw in txt.split("\n"):
        line = raw.replace(" ", " ").rstrip()
        s = line.strip()
        if not s or _NOISE_LINE.match(s) or _TOC_LINE.search(s):
            continue
        out.append(s)
    return out


def join_wrapped(lines: list[str]) -> str:
    """Re-flow PDF line wraps into paragraphs (conservative)."""
    paras: list[str] = []
    buf = ""
    for ln in lines:
        starts_block = bool(re.match(r"^(§\s*\d|\d+°|[a-z]\)|\(\d+\)|[-–•]\s|Art\.|Article|[A-Z]\.\s|[IVX]+\.\s|\d+\.\s|\[)", ln))
        if buf and not starts_block and not re.search(r"[.;:!?»)\]]$", buf) and (ln[:1].islower() or ln[:1] in "«(" or buf.endswith(",")):
            buf = f"{buf} {ln}"
        elif buf and not starts_block and not re.search(r"[.;:!?»)\]]$", buf) and len(buf) > 60:
            buf = f"{buf} {ln}"
        else:
            if buf:
                paras.append(buf)
            buf = ln
    if buf:
        paras.append(buf)
    return "\n".join(paras)


@dataclass
class Article:
    id: str
    code: str
    code_title: str
    article: str
    title: str
    heading_path: list[str]
    text: str
    source_file: str
    page: int
    n_chars: int = 0


def parse_code(spec: CodeSpec) -> tuple[list[Article], dict]:
    doc = pymupdf.open(PDF_DIR / spec.file)
    path: list[str | None] = [None] * 5
    articles: list[Article] = []
    cur_num: str | None = None
    cur_lines: list[str] = []
    cur_page = 0
    cur_path: list[str] = []
    cur_future: str | None = None   # date of a "DROIT FUTUR" block applying to the next article
    cur_decree: str | None = None   # AR n° (artva only)
    report = Counter()

    def flush():
        nonlocal cur_lines
        if cur_num is not None:
            text = join_wrapped(cur_lines)
            if len(text.strip()) < 15:
                report["dropped_empty"] += 1
            else:
                short = {"cir92": "CIR 92", "arcir92": "AR/CIR 92", "ctva": "Code TVA", "artva": "AR TVA",
                         "vcf": "Code flamand de la fiscalité", "cbpf": "CBPF", "crecouv": "Code du recouvrement",
                         "cdu": "Code des douanes de l'Union", "ue282": "Règlement UE 282/2011"}.get(spec.code.split("_")[0], spec.title)
                if spec.code.startswith(("cir92_", "arcir92_")):
                    short += " (" + {"bxl": "Bruxelles", "vla": "Flandre", "wal": "Wallonie"}[spec.code.split("_")[1]] + ")"
                elif "_" in spec.code and spec.code.split("_")[0] in ("csucc", "cenr", "cta"):
                    short = spec.title
                art_id = f"{spec.code}:{cur_num}"
                title = f"{short} – Article {cur_num}"
                if cur_decree:
                    art_id = f"{spec.code}:AR{cur_decree}:{cur_num}"
                    title = f"AR TVA n° {cur_decree} – Article {cur_num}"
                if cur_future:
                    art_id += f"@{cur_future}"
                    title += f" (droit futur à partir du {cur_future})"
                articles.append(Article(
                    id=art_id, code=spec.code, code_title=spec.title, article=cur_num,
                    title=title, heading_path=list(cur_path), text=text,
                    source_file=spec.file, page=cur_page, n_chars=len(text)))
        cur_lines = []

    pending_future: str | None = None
    for pno in range(doc.page_count):
        for line in page_lines(doc[pno], spec.column):
            fm = _FUTURE_RE.match(line)
            if fm:
                pending_future = fm.group("date")
                continue
            if spec.code == "artva":
                dm = _DECREE_RE.match(line)
                if dm and len(line) < 200:
                    flush(); cur_num = None
                    cur_decree = dm.group("n")
                    path = [None] * 5
                    path[0] = f"Arrêté royal n° {cur_decree} du {dm.group('date')} {dm.group('txt')}".strip()
                    report["decrees"] += 1
                    continue
            m = _ART_RE.match(line)
            if m and m.group("form") == spec.form and _REST_OK.match(m.group("rest")) and len(line) < 110:
                flush()
                cur_num = m.group("num").replace(" ", "").replace("^", "/")
                cur_page = pno + 1
                cur_path = [p for p in path if p]
                cur_future, pending_future = pending_future, None
                report["headings"] += 1
                continue
            h = _HEAD_RE.match(line)
            if h and len(line) < 90 and (h.group("txt") or h.group("num")) and not h.group("txt")[:1].islower():
                lvl = _LEVEL[h.group("lvl").upper()]
                path[lvl] = line
                for i in range(lvl + 1, 5):
                    path[i] = None
                if cur_num is None:
                    continue
            if cur_num is None:
                report["preamble_lines"] += 1
                continue
            cur_lines.append(line)
    flush()

    # dedupe ids (TOC remnants / repeated headings): keep the longest body
    best: dict[str, Article] = {}
    for a in articles:
        if a.id not in best or a.n_chars > best[a.id].n_chars:
            if a.id in best:
                report["duplicates"] += 1
            best[a.id] = a
        else:
            report["duplicates"] += 1
    # keep original order of first occurrence
    seen = set(); ordered = []
    for a in articles:
        if a.id in seen:
            continue
        seen.add(a.id); ordered.append(best[a.id])
    report.update({"pages": doc.page_count, "articles": len(ordered),
                   "chars": sum(a.n_chars for a in ordered)})
    return ordered, dict(report)


def main(only: list[str] | None = None) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "md").mkdir(exist_ok=True)
    all_articles: list[Article] = []
    full_report: dict = {}
    t0 = time.perf_counter()
    for spec in SPECS:
        if only and spec.code not in only:
            continue
        t1 = time.perf_counter()
        arts, rep = parse_code(spec)
        rep["seconds"] = round(time.perf_counter() - t1, 1)
        rep["default_subset"] = spec.default
        full_report[spec.code] = rep
        all_articles.extend(arts)
        with (OUT_DIR / "md" / f"{spec.code}.md").open("w", encoding="utf-8") as fh:
            fh.write(f"# {spec.title}\n\n")
            for a in arts:
                fh.write(f"\n\n## {a.title}\n<!-- id={a.id} page={a.page} path={' > '.join(a.heading_path)} -->\n\n{a.text}\n")
        print(f"{spec.code:12s} pages={rep['pages']:5d} articles={rep['articles']:5d} chars={rep['chars']:9,d} "
              f"dups={rep.get('duplicates',0)} empty={rep.get('dropped_empty',0)} {rep['seconds']}s")
    if not only:
        with (OUT_DIR / "articles.jsonl").open("w", encoding="utf-8") as fh:
            for a in all_articles:
                fh.write(json.dumps(asdict(a), ensure_ascii=False) + "\n")
        (OUT_DIR / "parse_report.json").write_text(json.dumps(full_report, indent=1, ensure_ascii=False))
    print(f"total articles={len(all_articles)} chars={sum(a.n_chars for a in all_articles):,} in {time.perf_counter()-t0:.0f}s")


if __name__ == "__main__":
    main(sys.argv[1:] or None)
