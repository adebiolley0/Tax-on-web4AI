# 38 — Tables and tariffs

**Idea**

Two layers. (1) *Retrieval*: parse each tariff table into cells and emit one **row sentence** per row, prefixed with article, version date, caption and headers ("Art. 48 C. succ. RW (23.12.2009) — Tableau I, ligne directe — tranche 25.000,01 à 150.000 EUR : taux 5 %, impôt sur tranches précédentes 875 EUR"), indexed as child chunks of the article. (2) *Answer*: the ~10 recurring tariff families (succession/donation/enregistrement × 3 regions, IPP brackets, ISoc, précompte, ATN/CO2, indexed amounts) become rows of a SQLite `rates` table with provenance; an MCP tool `lookup_rate(tax, region, relation, year, amount)` returns bracket, rate, computed tax and citing article, beside text retrieval for conditions and abattements.

**Why it fits this project**

18/40 corpus-B and 21/64 corpus-C questions ask for a rate, bracket or amount (regex count). B31 ("père domicilié à Namur… quel pourcentage") expects `csucc_wal:48`, a pure table. Corpus C (HTML→markdown) already carries **1,921 docs with pipe tables (~89.5k rows)**; Wallonia art. 48 arrives as a clean `a`/`b` table, but merged cells misalign (`Au-delà de 500.000,00 EUR | 15 % | 45.125,00 EUR |`) and several temporal versions (DROIT FUTUR 2028, 2009…) share one document. Only the PDF corpora (A/B, pymupdf) truly flatten tables. Row sentences and SQLite are CPU-cheap and LLM-free.

**Evidence**

- Extraction: TableFormer (Docling) TEDS 98.5 simple / 95.0 complex on PubTabNet (arXiv 2203.01017, 2022); Docling runs 0.60–0.94 pages/s at 4 threads on a Xeon (arXiv 2408.09869, Aug 2024) → 11.6k pages ≈ 3.5–5.5 h vs 21 s pymupdf. GMFT (Table Transformer, MIT) claims ~1.4 s/page CPU (README, unverified). Camelot beats pdfplumber 8/10 on text PDFs (camelot wiki, undated); ours are native text.
- Linearisation: plain DPR over linearised tables matches or beats table-specific retrievers on NQ-tables; structure "plays a negligible role in >70 % of cases"; row/column embeddings did not help (arXiv 2205.09843, 2022). Docling's default `TripletTableSerializer` emits `"row, col = value"` sentences joined by ". ". Element-based chunking keeping whole tables: page retrieval 84.4 % vs 68–73 % fixed-size; FinanceBench answers 53.2 % vs 35–48 % (arXiv 2402.05131, Feb 2024).
- LLM reading: HTML is the best table format for GPT-3.5/4, +6.76 % over NL+separators (arXiv 2305.13062, WSDM 2024) — keep the raw table for the answer prompt.
- Table QA: TAPEX 57.5 % WikiTableQuestions (arXiv 2107.07653), OmniTab (NAACL 2022): English, superseded. TableRAG (EMNLP 2025, arXiv 2506.10380), SQL over extracted tables + text: HeteQA 44.9 % vs NaiveRAG 35.9 % with DeepSeek-V3; WTQ 80.4 vs 75.4 — needs a strong LLM. TableRAG-NeurIPS 2024 (arXiv 2410.04739) targets million-token tables, irrelevant for <20-row tariffs.
- No direct evidence that row sentences lift BM25/dense recall on legal tariffs; the DPR result is the closest analogue.

**How we would implement it**

1. Corpus C: parse markdown pipe tables, repair merged cells by column count, attach caption + nearest heading + version date; one row-chunk per row with parent id (topic 05); keep the raw table in the parent for the LLM.
2. Corpus B PDFs: camelot (stream) only on pages containing `Tableau`/`%`, pdfplumber fallback, GMFT if both fail; no full Docling run.
3. `rates.sqlite` (tax, region, relation, bracket_lo/hi, rate, fixed_part, valid_from/to, guid, article) seeded from parsed rows, hand-verified; `lookup_rate` MCP tool computes the tax; router = amount regex + city→region gazetteer (topic 40) + tax keyword, text retrieval in parallel.
4. Evaluate on the ~39 tariff-like questions plus ~20 new "compute" questions with expected amounts.

**Expected gain and cost**

Retrieval: +0.02–0.05 MRR overall, +0.1–0.2 on the tariff subset (row chunks carry "ligne directe", "Région wallonne", the bracket words). Answer: compute questions go from unanswerable to deterministic on covered tables. Cost: 2–3 days serialiser + eval; 3–5 days rates DB, tool and curation; camelot pass ≤1 h; Docling ~5 h CPU only if needed.

**Risks / open questions**

Merged-cell repair; temporal keying (Wallonia 2028 reform vs current, decease-date rule); abattements (art. 54, 60ter) and indexation (topic 39) mean the tool gives a bracket rate, not full liability; curated DB drifts as decrees change; 89.5k row-chunks inflate the index (restrict to tariff tables); the dense leg may not benefit; Flemish VCF tariffs live in NL documents.

**Verdict**

try-now — row-wise serialisation of the existing markdown tables plus a curated `lookup_rate` for succession/donation/enregistrement/IPP; text-to-SQL over arbitrary tables is try-when-LLM.

**Sources**

- Local: `myfin_docs/code_et_legislation/article_48_du_code_des_droits_de_succession_region_wallonne_ca2f583c.md`; `experiments/data/corpus_b/questions_b.json` (B31); `experiments/EXPERIMENTS.md` §3.1–3.2
- https://arxiv.org/abs/2203.01017 — TableFormer
- https://arxiv.org/abs/2408.09869 — Docling technical report
- https://github.com/conjuncts/gmft — GMFT README (unverified)
- https://github.com/camelot-dev/camelot/wiki/Comparison-with-other-PDF-Table-Extraction-libraries-and-tools
- https://arxiv.org/abs/2205.09843 — table retrieval without table-specific models
- https://github.com/docling-project/docling-core — `hierarchical_chunker.py`, TripletTableSerializer
- https://arxiv.org/abs/2402.05131 — financial report chunking
- https://arxiv.org/abs/2305.13062 — Table Meets LLM
- https://arxiv.org/abs/2107.07653 — TAPEX; https://arxiv.org/abs/2207.03637 — OmniTab
- https://arxiv.org/abs/2506.10380 — TableRAG (EMNLP 2025); https://arxiv.org/abs/2410.04739 — TableRAG (NeurIPS 2024)
