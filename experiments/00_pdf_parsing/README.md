# 00 – PDF parsing → Corpus B (article-level legal codes)

**Goal:** turn the 34 MyMinfin library PDFs (`myfin_pdfs/`, 11,614 pages) into a clean,
article-level corpus that the retrieval experiments can index.

```bash
cd experiments/00_pdf_parsing && uv sync && uv run python parse_pdfs.py          # ~20 s
# outputs: experiments/data/corpus_b/{articles.jsonl, md/<code>.md, parse_report.json}
```

## What was tried

| Parser | Verdict |
|---|---|
| `pymupdf` `get_text("text")` (+ column clip) | **Chosen.** PDFs are native text (no OCR needed); 21 s for all files. |
| `pymupdf4llm.to_markdown` | Produces markdown headings but mis-detects heading levels on these layouts, keeps TOC dot leaders and running headers, and is ~20× slower. Not needed since article structure is recovered by regex anyway. |
| docling / marker (layout models) | Not tried: CPU-only box, 11k pages → hours, and the text layer is already clean. Would only matter for scanned PDFs or tables (succession tariff tables are the one place it could help). |

## Cleaning rules (see `parse_pdfs.py`)

* **Bilingual two-column editions** – only the French column is clipped
  (FR is *left* for CBPF / AG Bruxelles 2019 / Règlement UE 282; *right* for the Flemish Codex and its executing decree).
* The two bilingual "édition 2026 version coordonnée" CIR 92 / AR-CIR 92 volumes are skipped (duplicates of the
  unilingual editions). `memento_fiscal_2025.pdf` is skipped (no legal value, manifest `ingest=false`).
* Dropped lines: running headers/footers (`www.fisconetplus.be`, `SPF Finances (AGESS)`, `C.TVA - Mise à j.`…),
  bare page numbers, dot-leader table-of-contents lines.
* **Article detection**: `Article N` / `Art. N` lines whose remainder is empty or a known qualifier
  (`, CIR 92`, `(applicable à partir du …)`, `(abrogé)`). The dominant form is set per code
  (`Art.` for CBPF, VCF, recouvrement…). Superscript numbering (`Article 145^33`) → `145/33`.
* **AR TVA** is a collection of ~60 royal decrees each restarting at Article 1 → ids are `artva:AR<n>:<article>`.
* **"DROIT FUTUR (à partir du …)"** blocks (succession / enregistrement codes) → the following article gets
  id suffix `@<date>` and a "(droit futur …)" title, so current and future law never collide.
* Structural headings (LIVRE / TITRE / CHAPITRE / Section / Sous-section) are tracked as a `heading_path`
  attached to every article → used as contextual chunk header by the experiments.
* Wrapped PDF lines are re-flowed into paragraphs conservatively (sentence punctuation / enumerations preserved).

## Result

9,824 articles, 18.4 M characters. Default Corpus B subset (`default_subset=true` in `parse_report.json`)
excludes the three regional CIR 92 / AR-CIR 92 re-editions (near-duplicates of the federal edition) and the
EU customs code (three overlapping numbering schemes): **~7,400 articles / ~8.4 M chars**.

Known limitations
* Tariff tables (succession/registration duties) are flattened to text lines; numbers survive but table
  structure is lost.
* The Flemish succession / registration codes are mostly concordance tables pointing to the VCF; they are kept
  because that is what the Flemish edition legally is.
* Customs code (`cdu`): Code / DA / IA share article numbers; only the longest body per number is kept.
