# 66 — Metadata enrichment without an LLM

**Idea**

One deterministic enrichment pass over the 21k Fisconet+ documents turns front matter + body into typed fields (region, years, validity, amounts, article/law/ruling references, court, company forms, tax types, keyphrases), stored beside the index and exposed as `search` filters/boosts and `facet_counts`. Rules and gazetteers do almost all of it; French NER is a gated add-on for fuzzy classes only. Keyphrases (YAKE/KeyBERT) give topic-less titles ("Article 8": 7,745 of 8,061 code files) something searchable.

**Why it fits this project**

Front matter already gives `document_type` (24 types), `document_date/publication_date/effective_date`, `path` (depth 3–6; domains: enregistrement 6.7k, revenus 5.3k, succession 3.6k, taxes assimilées 1.3k, TVA 1.1k) and `linked_document_nl` — but no region, year, amount, article or keyword field. Exp 08/11 failure modes are metadata-shaped: regional twins (6,381 docs), yearly editions (3,610), NL bodies flagged `fr`. `mcp_server/src/tax_mcp/server.py` already accepts `document_type/tax_category/audience/language` filters but has no values to filter on. CPU-only; DeepSeek later fills the same arguments. French NER (PER/ORG/LOC/MISC) covers none of dates, amounts, articles, regions or tax types, so rules are the primary tool, not a fallback.

**Evidence**

- Local: exp 11 region/domain prior — B BM25 +0.04 val MRR, C flat (0.536 → 0.536); exp 08 city→region filter "correct but nearly neutral" until reranking (§3.8). 1,569/1,730 jurisprudence files contain a court name; company forms are regex-visible (SA 3.2k, ASBL 546, SPRL 483 mentions).
- Version/date metadata is decisive: static RAG retrieves the date-applicable French tax article 0 % of the time, rule-extracted `date_debut/date_fin` multi-version index 98.3 % (https://arxiv.org/html/2608.09393).
- Query-conditioned field weighting: mFAR MRR 0.602 vs BM25 0.462 on STaRK (https://arxiv.org/abs/2410.20056). Partition-based ANN beats HNSW under selective filters (https://arxiv.org/abs/2602.11443); hierarchical routing needs controlled fallback when metadata is incomplete (https://arxiv.org/abs/2601.03748, abstract only).
- French NER: spaCy `fr_core_news_lg` 3.8 ENTS_F 84.2, WikiNER, LGPL-LR, 545 MB; `Jean-Baptiste/camembert-ner` F1 0.891 (ORG 0.82), MIT; flair `ner-french` F1 90.6, non-commercial; `wikineural-multilingual-ner` CC-BY-NC-SA — all PER/ORG/LOC/MISC only. GLiNER `gliner_multi-v2.1` 209M Apache-2.0 zero-shot any label; legal zero-shot F1 ≈ 60 (idea 22, unverified). French court-decision NER with contextual dictionaries F1 96.5 (https://arxiv.org/abs/1909.03453).
- Keyphrases: YAKE/TextRank/KeyBERT ≤ 11.6 % exact F1@6 on an inflected language (SlovKE, https://arxiv.org/abs/2603.15523) — a BM25 field, not displayed metadata.
- Tooling: `dateparser` (BSD, French; text search "limited"); HeidelTime (French TIMEX3, Java, GPL-3).

**How we would implement it**

1. `ingestion/enrich.py` (pure regex/gazetteer, unit-tested on 200 hand-checked docs): `region` (title suffixes "- Région wallonne", Rép. RJ -BR/-VL/-WA, SPW/VLABEL/Bruxelles Fiscalité, exp 08 cities), `income_years[]`/`assessment_years[]` ("revenus 2025", "ex. d'imp. 2026"), `valid_from/valid_to` (idea 41 grammar), `amounts[] {value, unit, indexed, year}`, `percentages[]`, `article_refs[] {code, article}` (exp 11 `refparse.py`), `law_refs[]` (date + type + numac), `ruling_no`, `court {name, city}`, `decision_date`, `company_forms[]`, `tax_types[]` (gazetteer: IPP/ISoc/INR/IPM/TVA/PrM/PrP/enregistrement/succession/circulation…), `body_language` (langdetect on first 2k chars).
2. Taxonomy propagation: `domain = path[1]`, `subdomain = path[2]`, `leaf = path[-1]`, plus the `found_via` parent's title as `context_title`; children inherit the parent's `region`/`tax_types` when empty.
3. Keyphrases for topic-less titles only: YAKE (fr, n ≤ 3, top 10) and KeyBERT with `multilingual-e5-small` (already cached) top 10 → `keyphrases` BM25 field with weight 0.5; `title_enriched = context_title + article + keyphrases`.
4. Schema in LanceDB/SQLite: scalar columns above + `facets` JSON; `search(query, document_type?, region?, tax_type?, domain?, income_year?, in_force_on?, court?, code?, article?)` → hits + `facet_counts`; explicit filter relaxed to a boost when < k hits.
5. GLiNER gate: 300 jurisprudence/QP docs, labels {juridiction, organisation, forme de société}; adopt only if it beats the gazetteer.

**Expected gain and cost**

Global MRR +0.01–0.03 (~15 % of questions carry a cue); the real payoff is no twin/edition traps on cued questions, working `search` filters and structured `fetch` output. Cost: 2–3 days rules + audit, minutes per full run (KeyBERT ~1 h on 21k first chunks); GLiNER audit +1 day, ~1–2 s/doc CPU.

**Risks / open questions**

Publication vs entry-into-force vs income-year semantics; base vs indexed amounts; NL-only regional docs; keyphrases from bilingual/abrogated text add noise; gazetteers miss renamed bodies; hard filters on empty fields kill recall — always fall back. No French legal NER benchmark validates GLiNER.

**Verdict**

try-now — the fields are rule-extractable with existing parsers, the MCP filters already expect them, NER is optional; measure on the cued subset and the twin-trap rate, not global MRR.

**Sources**

- `myfin_docs/README.md`, `experiments/11_graph_retrieval/README.md`, `experiments/08_corpus_b_cleanup/cleanup.py`, `experiments/EXPERIMENTS.md`
- https://arxiv.org/html/2608.09393 · https://arxiv.org/abs/2410.20056 · https://arxiv.org/abs/2602.11443 · https://arxiv.org/abs/2601.03748
- https://github.com/explosion/spacy-models/releases/tag/fr_core_news_lg-3.8.0 · https://huggingface.co/Jean-Baptiste/camembert-ner · https://huggingface.co/flair/ner-french · https://huggingface.co/Babelscape/wikineural-multilingual-ner
- https://huggingface.co/urchade/gliner_multi-v2.1 · https://arxiv.org/abs/2311.08526 · https://huggingface.co/knowledgator/gliner-multitask-large-v0.5 · https://arxiv.org/abs/1909.03453
- https://github.com/MaartenGr/KeyBERT · https://github.com/LIAAD/yake · https://arxiv.org/abs/2603.15523 · https://github.com/scrapinghub/dateparser · https://github.com/HeidelTime/heideltime
