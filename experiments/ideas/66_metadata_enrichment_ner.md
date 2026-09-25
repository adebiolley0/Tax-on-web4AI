# 66 — Metadata enrichment without an LLM

**Idea**

Build one deterministic enrichment pass over the 21k Fisconet+ documents that turns front matter + body text into a fixed set of typed fields (region, years, validity, amounts, article/law/ruling references, court, company forms, tax types, keyphrases), stored beside the index and exposed as `search` filters/boosts and `facet_counts`. Rules and gazetteers do almost all of it; a French NER model is only a gated add-on for fuzzy classes (organisations, court names in free text). Keyphrases (YAKE/KeyBERT) exist only to give topic-less titles ("Article 8", 7,745 of 8,061 code files) something searchable.

**Why it fits this project**

Front matter already gives `document_type` (24 types), `document_date/publication_date/effective_date`, `path` (depth 3–6; domains: enregistrement 6.7k, revenus 5.3k, succession 3.6k, taxes assimilées 1.3k, TVA 1.1k) and `linked_document_nl` — but no region, income year, amount or article field, and no keywords (0 files). Failure modes in exp 08/11 are exactly metadata-shaped: regional twins (6,381 docs in `twin` groups), yearly editions (3,610), NL bodies flagged `fr`. The MCP server (`mcp_server/src/tax_mcp/server.py`) already takes `document_type/tax_category/audience/language` filters; it needs values to filter on. CPU-only, no LLM; DeepSeek later just fills the same arguments. Generic French NER classes (PER/ORG/LOC/MISC) cover none of dates, amounts, articles, regions or tax types, so rules are not a fallback — they are the primary tool.

**Evidence**

- Local: exp 11 region/domain prior — B BM25 +0.04 val MRR, C flat (0.536 → 0.536); exp 08 city→region filter "correct but nearly neutral" until reranking (`EXPERIMENTS.md` §3.8). Cue coverage: 1,569/1,730 jurisprudence files contain a court name; company forms in rulings by regex (SA 3.2k, ASBL 546, SPRL 483, SRL 112 mentions).
- Version/date metadata is decisive: static RAG retrieves the date-applicable French tax article 0 % of the time, rule-extracted `date_debut/date_fin` multi-version index 98.3 % (https://arxiv.org/html/2608.09393).
- Query-conditioned field weighting: mFAR MRR 0.602 vs BM25 0.462 on STaRK (https://arxiv.org/abs/2410.20056). Partition-based ANN beats HNSW for low-selectivity filters (https://arxiv.org/abs/2602.11443); OLAP-style hierarchical routing with controlled fallback when metadata is incomplete (https://arxiv.org/abs/2601.03748, abstract only).
- French NER: spaCy `fr_core_news_lg` 3.8 ENTS_F 84.2, WikiNER, LGPL-LR, 545 MB; `Jean-Baptiste/camembert-ner` F1 0.891 (ORG 0.82), MIT; flair `ner-french` F1 90.6, non-commercial; `wikineural-multilingual-ner` CC-BY-NC-SA — all PER/ORG/LOC/MISC only. GLiNER `gliner_multi-v2.1` 209M Apache-2.0 zero-shot any label; legal zero-shot F1 ≈ 60 (idea 22, unverified). French court-decision NER with contextual dictionaries F1 96.5 (https://arxiv.org/abs/1909.03453).
- Keyphrases: unsupervised YAKE/TextRank/KeyBERT ≤ 11.6 % exact F1@6 on an inflected language (SlovKE, https://arxiv.org/abs/2603.15523) — usable as a BM25 field, not as displayed metadata.
- Tooling: `dateparser` (BSD, French, "search dates in text" limited); HeidelTime (French TIMEX3, Java, GPL-3).

**How we would implement it**

1. `ingestion/enrich.py` (pure regex/gazetteer, unit-tested on 200 hand-checked docs): `region` (title suffixes "- Région wallonne", Rép. RJ -BR/-VL/-WA, SPW/VLABEL/Bruxelles Fiscalité, exp 08 cities), `income_years[]`/`assessment_years[]` ("revenus 2025", "ex. d'imp. 2026"), `valid_from/valid_to` (idea 41 grammar), `amounts[] {value, unit, indexed, year}`, `percentages[]`, `article_refs[] {code, article}` (exp 11 `refparse.py`), `law_refs[]` (date + type + numac), `ruling_no`, `court {name, city}`, `decision_date`, `company_forms[]`, `tax_types[]` (gazetteer: IPP/ISoc/INR/IPM/TVA/PrM/PrP/enregistrement/succession/circulation…), `body_language` (langdetect on first 2k chars).
2. Taxonomy propagation: `domain = path[1]`, `subdomain = path[2]`, `leaf = path[-1]`, plus `found_via` parent's title as `context_title`; children inherit the parent's `region`/`tax_types` when their own are empty.
3. Keyphrases for topic-less titles only: YAKE (fr, n ≤ 3, top 10) and KeyBERT with `multilingual-e5-small` (already cached) top 10 → `keyphrases` BM25 field with weight 0.5; `title_enriched = context_title + article + keyphrases`.
4. Schema in LanceDB/SQLite: scalar columns above + `facets` JSON; `search(query, document_type?, region?, tax_type?, domain?, income_year?, in_force_on?, court?, code?, article?)` → hits + `facet_counts`; explicit filter relaxed to a boost when < k hits.
5. GLiNER gate: run on 300 jurisprudence/QP docs with labels {juridiction, organisation, forme de société}; adopt only if it beats the gazetteer on the audit.

**Expected gain and cost**

Global MRR +0.01–0.03 (metadata questions are ~15 % of sets); the real payoff is zero twin/edition traps on cued questions, working `search` filters, and structured `fetch` output. Cost: 2–3 days rules + audit, ~5 min per full run (YAKE seconds/doc-batch; KeyBERT ~1 h on 21k titles' first chunk); GLiNER audit +1 day, ~1–2 s/doc CPU.

**Risks / open questions**

Publication vs entry-into-force vs income-year semantics; base vs indexed amounts; NL-only regional docs; keyphrases from bilingual/abrogated text add noise; gazetteers miss renamed bodies (SPF Finances/AGFisc); hard filters kill recall if a field is empty — always fallback. No French legal NER benchmark exists to validate GLiNER.

**Verdict**

try-now — the fields are rule-extractable with existing parsers, the store and MCP filters already expect them, and NER is optional; measure on the cued subset and the twin-trap rate, not global MRR.

**Sources**

- `myfin_docs/README.md`, `experiments/11_graph_retrieval/README.md`, `experiments/08_corpus_b_cleanup/cleanup.py`, `experiments/EXPERIMENTS.md`
- https://arxiv.org/html/2608.09393 · https://arxiv.org/abs/2410.20056 · https://arxiv.org/abs/2602.11443 · https://arxiv.org/abs/2601.03748
- https://github.com/explosion/spacy-models/releases/tag/fr_core_news_lg-3.8.0 · https://huggingface.co/Jean-Baptiste/camembert-ner · https://huggingface.co/flair/ner-french · https://huggingface.co/Babelscape/wikineural-multilingual-ner
- https://huggingface.co/urchade/gliner_multi-v2.1 · https://arxiv.org/abs/2311.08526 · https://huggingface.co/knowledgator/gliner-multitask-large-v0.5 · https://arxiv.org/abs/1909.03453
- https://github.com/MaartenGr/KeyBERT · https://github.com/LIAAD/yake · https://arxiv.org/abs/2603.15523 · https://github.com/scrapinghub/dateparser · https://github.com/HeidelTime/heideltime
