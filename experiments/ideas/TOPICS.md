# Idea research topics (100 subagents, research only — no testing)

Theme A — Retrieval models and representations
01 Learned sparse retrieval (SPLADE-v3, opensearch neural sparse, BGE-M3 sparse) for French legal text
02 Late-interaction / multi-vector retrieval (ColBERTv2, PLAID, PyLate, colbert-xm, jina-colbert-v2) at 100k docs on CPU
03 Static and tiny embeddings (model2vec/potion, static-similarity) and distillation from large embedders
04 Long-context embedders and late chunking (jina v3, bge-m3 8k, nomic) for long articles and circulars
05 Multi-granularity indexing: article, paragraph (§/alinéa), sentence — which unit for legal QA
06 Contextual retrieval / chunk context augmentation (Anthropic-style) and doc2query for legal chunks
07 Matryoshka / binary / int8 quantised embeddings and their effect on legal retrieval quality
08 Cross-encoder rerankers: Qwen3-Reranker, jina-reranker-v3, bge-reranker, monoT5/RankT5, listwise LLM rerankers (RankGPT/RankZephyr)
09 French and legal-domain language models for embeddings (CamemBERT-based, Solon, legal-french, CroissantLLM, EuroBERT)
10 Cross-lingual retrieval FR/NL/DE for Belgian law (translate-train, multilingual embedders, NL bodies with FR summaries)
11 Query-document asymmetry: instruction-tuned embedders (e5-instruct, gte-Qwen, NV-Embed) and prompts for legal questions
12 Retrieval-oriented fine-tuning with synthetic data (InPars, Promptagator, GPL) generated later by DeepSeek
13 Knowledge distillation from a cross-encoder into a bi-encoder (Margin-MSE) for domain adaptation
14 Numeric and amount-aware retrieval (thresholds like 25.000 €, percentages, dates) — tokenisation and matching strategies
15 Hybrid fusion theory: RRF, CombSUM/CombMNZ, learned fusion, score calibration, "when to fuse" results

Theme B — Indexing structures and databases beyond vector DBs
16 Inverted-index engines embedded in Python (Tantivy, Xapian, Lucene via PyLucene, Whoosh) with French analyzers
17 SQLite FTS5 + sqlite-vec / DuckDB FTS + VSS as a zero-dependency hybrid store for an MCP server
18 Postgres: pgvector + tsvector('french') + pg_search/ParadeDB as one store with SQL filters
19 Elasticsearch/OpenSearch/Vespa/Manticore: what they add (BM25F, ranking DSL, learned sparse native) vs cost
20 Graph databases (Neo4j, Kuzu, Memgraph, FalkorDB, TigerGraph) — storing a legal citation/hierarchy graph and graph-native ranking
21 RDF/SPARQL and legal ontologies (ELI, Akoma Ntoso, LKIF, FIBO-like tax ontologies) for Belgian tax law
22 Knowledge graphs built without an LLM: rule/regex extraction of citations, definitions, amounts, dates, entities
23 Graph-RAG family (Microsoft GraphRAG, LightRAG, HippoRAG 2, KAG, Graphiti, nano-graphrag): what they need and evidence on legal QA
24 Hierarchical / tree indexes (RAPTOR, tree-of-summaries, table-of-contents routing) for codes with titles/chapters/sections
25 Temporal/versioned indexing: point-in-time law (income year, "droit futur"), bitemporal storage and retrieval-time filtering
26 Deduplication and canonicalisation at scale (MinHash/SimHash, near-duplicate clustering of yearly/regional editions)
27 Metadata/faceted search and query routing (document type, region, tax domain) — learned vs rule-based routers
28 Search engines with built-in rerankers/hybrid for prototyping (Meilisearch, Typesense, Weaviate embedded, Marqo, Infinity, LanceDB, Milvus Lite)
29 Learned index structures and ANN choices (HNSW vs IVF vs DiskANN vs brute force) at 100k–1M chunks on CPU
30 Sparse-dense unified engines (Vespa, Infinity, OpenSearch neural sparse) vs two-index fusion — tradeoffs

Theme C — Legal-domain structure and knowledge modelling
31 Statute cross-reference graphs: PageRank/HITS priors, citation-network retrieval in legal IR literature
32 Article hierarchy exploitation: heading paths, parent-child scoring, "legal breadcrumb" embeddings
33 Definitions and defined terms in tax law (art. 2 CIR 92 etc.): a definitions index and query expansion via definitions
34 Layman-to-legal vocabulary mapping: building a bilingual lexicon (everyday ↔ statute terms) from FAQs, circulars, forum data
35 Case law retrieval specifics (fact patterns, summaries, headnotes) — how COLIEE/CLERC/LePaRD approaches transfer
36 Rulings (décisions anticipées) retrieval: extracting the scheme/fact pattern and ruling outcome as structured fields
37 Administrative commentary (ComIR/Rép. RJ numbered paragraphs) as a bridge between statute and practice — indexing strategies
38 Tables and tariffs (succession/registration rates, brackets) — table linearisation, table QA, structured extraction
39 Amount/threshold indexation over years — a parametric layer (index tables) alongside text retrieval
40 Regionalisation of Belgian tax (federal/Wallonia/Brussels/Flanders) — modelling jurisdiction as a first-class filter
41 Temporal validity of provisions (entry into force, abrogation, "applicable à partir de") — extraction and use at query time
42 Cross-document consistency: linking circulars ↔ articles ↔ rulings ↔ case law ↔ parliamentary questions (typed edges)
43 Tax-form-centric retrieval: mapping declaration codes (codes 1250, 1370 …) to provisions — a code→law index
44 Procedural knowledge (deadlines, appeals, payment plans) as workflows/checklists rather than text chunks
45 Multi-hop legal questions (article → exception → regional variant) — decomposition and iterative retrieval evidence

Theme D — Query understanding and agentic patterns
46 Query rewriting and expansion with an LLM (HyDE, Query2Doc, RAG-Fusion, step-back prompting) — evidence on legal QA
47 Agentic RAG architectures (ReAct search agents, Self-RAG, CRAG, Adaptive-RAG, FLARE): what actually improves precision
48 Tool design for an MCP retrieval server (search/fetch/cite/neighbours/filters): best practices from MCP and tool-use research
49 Query classification and routing (jurisdiction, tax type, document type, intent) with small classifiers
50 Clarification and slot-filling dialogues for tax questions (region, year, taxpayer type) before retrieval
51 Iterative retrieval with citation following (expand from the first hit along cross-references) — algorithms and evidence
52 Reranking with LLMs vs cross-encoders: listwise, pairwise, setwise; cost/quality on CPU with small models
53 Answer verification, citation grounding and attribution (ALCE, self-checking, NLI-based faithfulness) for legal answers
54 Long-context LLM instead of retrieval for a single code (whole CIR 92 in context) — evidence and cost
55 Caching, memoisation and query logs: learning from usage (click models, implicit feedback) in a legal assistant
56 Multi-query / decomposition strategies for compound questions (deductions + regional credit + procedure)
57 Structured retrieval via text-to-SQL/Cypher over extracted facts (rates, thresholds) combined with text RAG
58 Retrieval evaluation without labels: LLM-as-judge, pseudo-labels, and how to avoid circular bias
59 Personalisation and taxpayer profile (salaried/self-employed/company, region) as retrieval context
60 Safety and refusal design for tax advice: scope detection, uncertainty communication, legal disclaimers

Theme E — Data, ingestion and quality
61 PDF/HTML parsing tools for legal documents (docling, marker, unstructured, pymupdf4llm, Nougat) — quality vs cost on codes
62 Language identification and handling of Dutch bodies with French summaries (translation with open models, dual indexing)
63 Boilerplate removal and section classification (amendment history, preambles, ToC) with small classifiers or rules
64 Change tracking and incremental re-indexing (Fisconet+ change feeds, content hashing, versioned chunk ids)
65 Document quality scoring and filtering (index pages, stubs, TOC-only, abrogated texts) — automatic detection
66 Metadata enrichment without an LLM: NER for dates/amounts/articles/regions, taxonomy from Fisconet+ tree
67 Web sources beyond Fisconet+ (finances.belgium.be, Moniteur belge/Justel, regional tax portals, Juridat) and their structure
68 Legal text normalisation (abbreviations CIR 92/WIB 92, article numbering variants 145/33 vs 145³³, accents) for matching
69 Synthetic question generation for evaluation and training (with DeepSeek later): templates, coverage, quality control
70 Data licensing and provenance for Belgian legal sources (Fisconet+, Justel, BSARD/LLeQA) — what can be used how

Theme F — Evaluation and training data
71 Legal retrieval benchmarks (BSARD, LLeQA, LegalBench-RAG, COLIEE, CLERC, LePaRD, ECtHR) — protocols and metrics to adopt
72 Small-sample evaluation statistics: confidence intervals, paired tests, bootstrap for 30–60 question sets
73 Building a larger Belgian tax QA test set cheaply (FAQs of SPF Finances, parliamentary questions as natural queries)
74 Hard-negative mining and contrastive fine-tuning with few labels (sample efficiency evidence)
75 Learning-to-rank with few queries: feature engineering, regularisation, cross-validation practices from LETOR literature
76 Cross-encoder distillation into small models (MiniLM-class) for CPU deployment — recipes and results
77 Evaluating chunking strategies rigorously (chunk-level vs doc-level metrics, attribution to spans)
78 Retrieval metrics for RAG (context precision/recall, RAGAS, ARES, nugget-based evaluation) beyond MRR
79 Measuring and reducing overfitting of retrieval pipelines to a small dev set (nested CV, held-out corpora)
80 Human-in-the-loop labelling tools and active learning for legal relevance judgments

Theme G — Systems, MCP, deployment, latency
81 CPU inference optimisation for embedders/rerankers (ONNX Runtime, OpenVINO, int8/int4, token pruning, batching)
82 Serving architecture for a FastMCP retrieval server (in-process embedded store vs sidecar; async; warm models; caching)
83 GPU-less deployment options and cost (small cloud CPU, Apple silicon, edge) for a 100k-document legal index
84 Incremental index updates and zero-downtime reindexing in embedded stores (LanceDB versions, SQLite, Tantivy)
85 Observability for RAG (tracing retrieval, logging queries, quality dashboards) with open tools (Phoenix, Langfuse)
86 Security/privacy for a tax assistant (PII in queries, local-only inference, prompt injection via retrieved documents)
87 Streaming and progressive retrieval UX (fast lexical first, dense/rerank refinement) for an assistant
88 Multi-tenant / multi-corpus routing (personal vs corporate tax, regions) and index partitioning
89 Reproducibility and experiment management for retrieval research (config tracking, result stores, MLflow/W&B alternatives)
90 Cost model: tokens, CPU seconds, storage per 100k documents for each candidate architecture

Theme H — Creative and unconventional ideas
91 Retrieval over a compiled "rule base": formalising tax rules (Catala, OpenFisca-Belgium) and using retrieval to point at rules
92 Question-to-form-field mapping: using the tax return structure (Tax-on-web codes) as the primary navigation index
93 Analogical retrieval: retrieving rulings/cases with similar fact patterns via structured fact embeddings
94 Legal "diff" retrieval: what changed between income years — indexing changes and amendments as first-class documents
95 Pre-computed answer graph: clustering historical questions (FAQs, parliamentary questions) as an index of intents
96 Crowd/expert feedback loops (accountants correcting citations) as training signal — design and incentives
97 Compression-based retrieval (NCD, gzip distance) and other model-free baselines revisited for legal text
98 Small on-device LLMs (Qwen3-0.6B/1.7B, Gemma-3n, Phi-4-mini) as query rewriters/rerankers on CPU — feasibility
99 Multi-agent RAG: specialist agents per tax domain/region debating or voting on citations — evidence vs hype
100 "Explain the citation": generating human-readable provenance chains (statute → circular → ruling) as a product feature
