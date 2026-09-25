# 61 — PDF / HTML parsing tools for legal documents (docling, marker, unstructured, pymupdf4llm, OCR-VLMs, trafilatura)

**Idea**

Decide, per source type, whether a layout model (Docling layout + TableFormer, marker/surya, unstructured `hi_res`, MinerU) or an OCR-VLM (Nougat, olmOCR) should replace our `pymupdf` + regex PDF parser or the BeautifulSoup `html_to_markdown` used for Fisconet+, and fix a target pipeline per source.

**Why it fits this project**

- The 34 MyMinfin PDFs are native text; exp 00 recovers article ids, heading paths, the French column of bilingual editions and DROIT FUTUR versions in 21 s for 11.6k pages. Only tariff tables (flattened) and some footnote/running-header residue are lost.
- Fisconet+ HTML (21k docs) has DOM defects, not layout defects: SharePoint `<span>` residue, split words ("Arti cle"), two-column NL/FR tables, TOC-only pages.
- The retrieval unit is the article with its heading path (+0.04–0.08 MRR, exp 01/02); no layout model knows "Article 145^33 CIR 92" — regex does.
- CPU-only 4-core box; the LLM reads the parent article, so tables must survive verbatim (topic 38).

**Evidence**

- Docling (arXiv 2408.09869): DocLayNet layout + TableFormer, 0.60–0.94 pages/s at 4 CPU threads → **11.6k pages ≈ 3.5–5.5 h vs 21 s**; TableFormer TEDS 98.5/95.0 (arXiv 2203.01017). Docling scores only 50.3 % on olmOCR-bench (marker README), i.e. weak reading order on born-digital multi-column PDFs.
- marker (README, 2026-09): olmOCR-bench 76.0 % overall, 83.5 % born-digital, tables 73.4 %; CPU "fast" mode 23.7 pages/s but that is text-layer extraction (pdftext), what we already have; weights under a modified OpenRAIL-M licence (free < $5M funding) — awkward for a public-service tool.
- olmOCR: 7B VLM, ≥12 GB VRAM, 82.4 on its own bench. MinerU: 8 GB+ VRAM recommended, CPU "functional but slower", custom licence. Nougat (arXiv 2308.13418): 350M model trained on arXiv, hallucinates outside scientific layouts (own knowledge, unverified on legal text). Wrong tools for native-text codes.
- unstructured: `fast` is rule-based (pdfminer), "≈100× faster than image-to-text models"; `hi_res` = detectron2/yolox layout (own knowledge). Nothing over pymupdf here.
- pymupdf4llm: multi-column, header/footer suppression, page chunks; exp 00 measured 20× slower, wrong heading levels, kept dot leaders.
- camelot vs pdfplumber: camelot ahead on 8/10 text PDFs (camelot wiki); `stream` handles rule-less tariff tables; seconds per page.
- HTML: trafilatura evaluation (Aug 2026, 990 docs) F1 0.924 vs readability-lxml 0.826, justext 0.862 — boilerplate-removal scores on web pages. Fisconet+ bodies come isolated from the REST API, so the gain is nil and recall < 1.0 would drop NL/FR tables.

**How we would implement it**

1. **Coordinated-code PDFs**: keep `pymupdf` + regex. Add a targeted table pass on pages matching `Tableau|%|EUR`: `page.find_tables()` then camelot `stream` fallback; emit markdown plus row sentences (topic 38). Footnote pass: small-font spans at page bottom → `[^n]` attached to the article. +2–5 min total.
2. **Bilingual two-column editions**: keep the bbox clip; sanity-check the FR/NL word-count ratio per file and render with Docling only for files that fail.
3. **Fisconet+ HTML**: no readability/trafilatura. Extend `html_to_markdown`: unwrap `<span>`/`<font>`, join split words only when the join exists in the corpus vocabulary and only inside modification-history blocks, turn two-column NL|FR tables (language-detected cells) into an FR block plus a `lang=nl` sibling (topic 62), repair `colspan` in other pipe tables.
4. **Scanned PDFs** (old circulars, annexes): Docling with OCR or marker, capped at a few hundred pages.
5. Gate with a `parse_report.json` diff: article count, heading-path coverage, chars per code must not regress.

**Expected gain and cost**

≈0 MRR from swapping parsers on native PDFs; +0.02–0.05 overall and +0.1–0.2 on tariff questions from the table pass (topic 38 estimate); HTML hygiene mainly helps BM25 (split words) — small, free. Cost: 1–2 days of regex/table work, minutes of CPU; a full Docling run is ~5 h per rebuild with no measured benefit.

**Risks / open questions**

- `find_tables` misses rule-less tables; camelot `stream` needs per-table tuning.
- Word joining can merge legitimate tokens; keep it scoped.
- No Belgian-legal PDF benchmark; olmOCR-bench (English, mixed) is a proxy.
- Docling reading order on bilingual two-column pages untested by us; marker/MinerU licences.

**Verdict**

**skip** (layout models) / **try-now** (targeted table + HTML cleaning passes) — the text layer is already clean, so the value is in tables and DOM hygiene, not a 1,000× slower layout stack.

**Sources**

- https://arxiv.org/abs/2408.09869 — Docling report (speed figures via topic 38 notes)
- https://arxiv.org/abs/2203.01017 — TableFormer
- https://github.com/datalab-to/marker — benchmarks, CPU mode, licence
- https://github.com/opendatalab/MinerU — hardware / licence
- https://github.com/allenai/olmocr — olmOCR-bench, VRAM
- https://arxiv.org/abs/2308.13418 — Nougat (not re-read)
- https://docs.unstructured.io/open-source/concepts/partitioning-strategies
- https://pymupdf.readthedocs.io/en/latest/pymupdf4llm/
- https://github.com/camelot-dev/camelot/wiki/Comparison-with-other-PDF-Table-Extraction-libraries-and-tools
- https://trafilatura.readthedocs.io/en/latest/evaluation.html
- local: `experiments/00_pdf_parsing/README.md`, `experiments/09_corpus_c/README.md`, `experiments/ideas/38_tables_and_tariffs.md`
