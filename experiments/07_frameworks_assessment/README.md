# 07 – RAG framework assessment (paper study)

**Date of assessment: 2026-09-24.** Docker is not available on the dev box, so nothing below was
run; every statement comes from the official docs / GitHub sources listed in *Sources* (fetched on
that date). Anything I could not confirm from a primary source is marked **unverified**.

**Project context used for the verdict**

* Corpus: French legal text — today ~9.8k article-level units (`experiments/data/corpus_b/articles.jsonl`,
  already parsed with `heading_path`, code id, article id) plus ~90 Fisconet+ markdown documents;
  target ~100k documents (codes, circulaires, rulings, jurisprudence, QP).
* Consumer: a FastMCP server (`mcp_server.py`) exposing `search` / `fetch` tools. The MCP tool must
  return **raw chunks with exact article citations**; the answering LLM (DeepSeek, OpenAI-compatible)
  sits on the client side, not inside the retrieval stack.
* Constraints: open-weight embeddings only (bge-m3 / multilingual-e5 already benchmarked in
  `02_dense_sweep`, bm25s + French Snowball in `01_bm25`, hybrid + `bge-reranker-v2-m3` in
  `03_hybrid_rerank`); metadata filters needed (region, document type, date, code).

---

## TL;DR ranking for this project

| Rank | Candidate | Verdict |
|---|---|---|
| 1 | **Library route: own pipeline on LanceDB (embedded) — optionally via LlamaIndex/Haystack — with bge-m3 dense + BM25 + bge-reranker-v2-m3** | Fits every constraint: no services, French-aware lexical search, exact-article citations, metadata filters, direct in-process call from FastMCP. Grow to Qdrant server or pgvector at 100k docs if needed. |
| 2 | **RAGFlow** | Strongest "batteries included" retrieval API (raw chunk retrieval, hybrid, metadata filter, MCP tool `ragflow_retrieval`), but heavy (16 GB RAM, ES/Infinity + MySQL + Redis + MinIO), embedding model must be served externally (slim image only since v0.22), Chinese/English-centric tokenisation for French is unverified. Needs Docker. |
| 3 | **LightRAG** (naive/mix mode, `/query/data`) | Lightweight, pip-installable, retrieval-only endpoint exists. But its value is the LLM-built knowledge graph, which costs one LLM extraction pass over 100k legal documents and adds entities/relations we do not need for article-precise citation. Worth a later experiment, not the backbone. |
| 4 | **Onyx** | Good product, wrong shape: a full enterprise "knowledge assistant" (11 containers, OpenSearch 2 GB heap, two model servers, 10–16 GB RAM), whose search API and MCP tool run through its own LLM pipeline (query expansion + document selection) and return sections without scores. Its self-hosted embedding list is small (multilingual-e5-base/small; custom models via "Custom Model" only). No control over chunking/citation granularity. |
| 5 | **Dify / AnythingLLM / Kotaemon** | Dify has a real retrieval API with hybrid + rerank + metadata filters but a restricted licence and a large stack; AnythingLLM is one container with a `vector-search` endpoint but no hybrid search; Kotaemon is nearly dormant. |
| — | **Microsoft GraphRAG** | In maintenance mode, expensive LLM indexing, global-summary use case. Not applicable. |
| — | **Verba** | Archived 2026-06-08. Excluded. |

---

## Comparison table

Legend: ✔ yes, ✘ no, ~ partial, ? unverified.

| | **Onyx** | **RAGFlow** | **LightRAG** | **GraphRAG (MS)** | **Dify** | **AnythingLLM** | **Kotaemon** | **Library route** (LlamaIndex / Haystack / txtai + LanceDB / Qdrant / pgvector) |
|---|---|---|---|---|---|---|---|---|
| Licence | MIT + `ee/` dirs under Onyx Enterprise License | Apache-2.0 | MIT | MIT | Apache-2.0 + extra conditions (no multi-tenant SaaS, keep logo) | MIT | Apache-2.0 | MIT (LlamaIndex, LangChain), Apache-2.0 (Haystack, txtai, LanceDB, Qdrant) |
| Latest version seen | v4.8.1 (Sep 2026); ~32k stars | v0.27.2 (2026-09-10); ~91k stars | 1.5.7 (PyPI 2026-09-02); ~40k stars | 3.2.0 (PyPI 2026-09-23); ~36k stars; **maintenance mode** | 157k stars (release not checked) | 66k stars, v1.11.x | 25.8k stars; last commits Mar–May (year rendered inconsistently, see §5) | llama-index 0.14.25 (2026-09-21), langchain 1.4.2 (2026-09-18), haystack-ai 3.2.0 (2026-09-24), txtai 9.13 |
| Required services (self-host) | Postgres, **OpenSearch** (Vespa removed in 4.0), Redis, MinIO, nginx, api_server, background, web, 2 model servers, code-interpreter (11 containers) | Elasticsearch **or** Infinity, MySQL, Redis, MinIO, ragflow server (+ optional sandbox) | None by default (in-memory/JSON files); optional Postgres / Neo4j / Qdrant / Milvus / Mongo / OpenSearch | None (parquet + LanceDB files); needs LLM API | Postgres, Redis, vector DB (Weaviate default), sandbox, plugin daemon, nginx, api/worker/web (?) | 1 container (LanceDB embedded) | Gradio app; Chroma/LanceDB/Qdrant/Milvus + ES/LanceDB docstore | None with LanceDB / sqlite-vec / Qdrant local mode; Postgres for pgvector; Qdrant server when scaling |
| Min RAM / CPU (docs) | Standard: 4 vCPU / 10 GB / 32 GB disk (16 GB preferred); local model servers 2 CPU + 4 GB each; OpenSearch heap 2 GB | 4 cores / **16 GB** / 50 GB; `vm.max_map_count ≥ 262144` for ES | Library: whatever the embedding model needs (bge-m3 ≈ 2–3 GB) | Library; cost is LLM tokens, not RAM | 2 cores / 4 GB (docs) + vector DB | not stated; small | Python 3.10+, not stated | bge-m3 fp32 ≈ 2.3 GB RAM; LanceDB index for 100k×1024-d ≈ 0.4 GB |
| Chunking | 512-token chunks (`DOC_EMBEDDING_CONTEXT_SIZE=512`), optional 150-token mini-chunks (multipass), title/contextual summaries optional | `chunk_token_num` default 512 (1–2048), templates naive/book/paper/qa/table…; **can push pre-made chunks via API** | `CHUNK_SIZE=1200` tokens, overlap 100; fixed / recursive / semantic / paragraph strategies | `chunks.size`/`overlap` (tokens or sentence) | configurable, parent-child chunks (?) | configurable | configurable | fully ours (article = unit, heading_path prefix, as in experiments 01–03) |
| Hybrid BM25 + dense | ✔ OpenSearch, `HYBRID_ALPHA=0.5`; text analyzer default `english` (`OPENSEARCH_TEXT_ANALYZER`, French value ?) | ✔ "multiple recall + fused re-ranking", `vector_similarity_weight` (default 0.3) + `term_similarity`; Snowball stemmer 16 languages since v0.26.4 (French ?) | ~ naive mode is dense-only; KG modes add entity/relation retrieval; no BM25 (?) | ✘ vector + graph | ✔ `hybrid_search` (weights or rerank) | ✘ not documented | ✔ full-text + vector | ✔ LanceDB FTS(BM25)+vector+RRF; Qdrant sparse (fastembed `Qdrant/bm25`) + dense; Haystack BM25+embedding retrievers; txtai sparse+dense weights; pgvector + `tsvector('french')` |
| Reranker | optional cross-encoder (`DEFAULT_CROSS_ENCODER_MODEL_NAME`, e.g. mxbai-rerank-xsmall) or cloud | ✔ any rerank provider (Xinference `/v1/rerank`, Cohere, Bedrock…) | ✔ `enable_rerank`; bindings cohere / jina / aliyun (Jina-format endpoint; local via TEI ?) | ✘ | ✔ `reranking_model` | ✘ (?) | ✔ Cohere etc. | ✔ any HF cross-encoder (bge-reranker-v2-m3) |
| Default embedding / swappable to bge-m3 or multilingual-e5 | default `nomic-ai/nomic-embed-text-v1`; suggested self-hosted list: e5-base/small-v2, **multilingual-e5-base/small**; "Custom Model" for other HF names (sentence-transformers, `trust_remote_code=False`); bge-m3 ? (not in list) | no bundled models since v0.22 → bring Ollama (`bge-m3` in docs) / Xinference / TEI / OpenAI-compatible; `embedding_model="name@factory"` per dataset | user-supplied; README recommends **`BAAI/bge-m3`** locally; server bindings openai / ollama / jina / …; Python API accepts any `EmbeddingFunc` | via LiteLLM model config (any OpenAI-compatible embedding endpoint) | Ollama / OpenAI-compatible / HF providers | native embedder or Ollama / OpenAI-compatible | OpenAI / Ollama / llama-cpp | ✔ direct sentence-transformers (already done in `02_dense_sweep`) |
| Raw chunks without LLM (API) | ~ `POST /api/search` (v4.0+) returns `SearchResult{citation_id,title,content,link,source_type,updated_at}` **but the pipeline obtains an LLM and runs query expansion + document selection**; `skip_query_expansion` only skips expansion; no scores. `POST /admin/search` is LLM-free keyword-only (admin explorer) | ✔ `POST /api/v1/retrieval` → chunks with `content, document_id, similarity, vector_similarity, term_similarity, positions, highlight`, no LLM | ✔ `only_need_context=true` and `POST /query/data` → entities/relationships/chunks/references; naive mode needs no KG; *but* keyword extraction for KG modes calls the LLM | ✘ query modes are LLM-driven | ✔ `retrieve-chunks` endpoint (records with content, document, score) | ✔ `POST /v1/workspace/:slug/vector-search` → `results[{text,score,metadata,distance}]` | ~ internal API, no stable endpoint | ✔ trivially — it *is* our code |
| External OpenAI-compatible LLM (DeepSeek) | ✔ "OpenAI-compatible" provider, LiteLLM proxy, OpenRouter… | ✔ DeepSeek is a built-in provider; OpenAI-API-compatible too | ✔ `LLM_BINDING=openai`, `LLM_BINDING_HOST=<url>`; DeepSeek named in README | ✔ via LiteLLM | ✔ DeepSeek listed | ✔ DeepSeek listed | ✔ | n/a (LLM stays outside retrieval) |
| Metadata filters | tags (`tag_key/tag_value`), `sources`, `document_sets`, `time_cutoff`; `metadata` on ingestion is stored as string/list tags | ✔ `metadata_condition{logic, conditions[]}`; "metadata filters pushed to index" (v0.27.1) | ~ workspaces for isolation; no per-chunk filter in `QueryParam` (?) | ✘ | ✔ typed metadata fields (string/number/time) + `metadata_filtering_conditions` | ~ per-workspace only (?) | collections | ✔ SQL `where` (LanceDB), payload filters (Qdrant), `WHERE` (pgvector), SQL (txtai) |
| MCP exposure | ✔ built-in MCP server (`/mcp`, tool `search_indexed_documents`, community code path) | ✔ MCP server (port 9382 or in-process `/mcp`), tools `ragflow_retrieval`, `ragflow_list_datasets`, `ragflow_list_chats` | ✘ (wrap REST) | ✘ | ~ Dify is an MCP *client*; server side ? | ✔ "MCP-compatibility" (as client ?) | MCP tools (client) | ✔ our FastMCP server calls the library directly |
| Effort to load 10k pre-parsed articles | Ingestion API (`POST /onyx-api/ingestion`, doc with `sections[{text,link}]`, `metadata`); async; must re-chunk at 512 tokens; ~1 script | REST: create dataset → create empty docs → `POST …/chunks` per chunk (one call per chunk, ?) or upload text files and let it chunk; ~1 script + model provider setup | `ainsert(texts, ids=…, file_paths=…)` or `POST /documents/texts`; naive mode cheap, KG mode = LLM call per chunk | `graphrag index` over txt/jsonl; LLM call per text unit | REST create-by-text per document | REST upload + `update-embeddings` | UI / scripts | ~50 lines: embed with bge-m3, `table.add(rows)`, build FTS index |

---

## 1. Onyx (onyx-dot-app/onyx, docs.onyx.app)

**What it is.** "The knowledge/context layer for your team and AI agents": an enterprise chat/agent
product with 50+ connectors, Slack/Discord bots, Chrome extension, MCP client *and* server.
MIT for everything outside the `ee/` directories (Onyx Enterprise License). Core RAG is stated to
be free forever; RBAC, audit, white-labelling are Enterprise; some features moved to a "Business"
tier in v4.0.

**Architecture / services (Standard mode, `deployment/docker_compose/docker-compose.yml`):**
`api_server`, `background`, `web_server`, `inference_model_server`, `indexing_model_server`,
`relational_db` (postgres 15), `opensearch` (3.6.0, `OPENSEARCH_JAVA_OPTS=-Xms2g -Xmx2g`),
`nginx`, `cache` (redis 7.4), `minio`, `code-interpreter`. **Vespa was removed entirely in v4.0.0
(2026-05-26)** in favour of OpenSearch; older installs must migrate. "Lite" mode (Postgres only,
< 1 GB RAM) disables the vector DB and RAG entirely, so it is irrelevant here.

**Resources (docs, Resourcing page):** Standard minimum 4 vCPU / 10 GB RAM / 32 GB + 2.5× data on
disk; preferred 8 vCPU / 16 GB. Each local model server needs 2 CPU + 4 GB (much less if using cloud
embeddings).

**Retrieval stack (from `backend/…/configs`):** chunks of `DOC_EMBEDDING_CONTEXT_SIZE=512` tokens,
optional multipass with 150-token mini-chunks and 4× "large chunks"; hybrid OpenSearch retrieval
with `HYBRID_ALPHA=0.5`, `NUM_RETURNED_HITS=50`, `DOC_TIME_DECAY=0.5`, `TITLE_CONTENT_RATIO=0.10`;
optional contextual RAG (LLM-generated document/chunk summaries, off by default); optional
cross-encoder reranking (no default model; `mixedbread-ai/mxbai-rerank-xsmall-v1` is the dev
example) or cloud rerankers; LLM-based "multilingual expansion" (rephrase query into other
languages). OpenSearch keyword analyzer defaults to `english` (`OPENSEARCH_TEXT_ANALYZER`);
whether a `french` analyzer is a supported value is **unverified**.

**Embeddings.** Default `nomic-ai/nomic-embed-text-v1` (768-d). Suggested self-hosted list in
`backend/onyx/configs/embedding_configs.py`: `intfloat/e5-base-v2`, `e5-small-v2`,
`intfloat/multilingual-e5-base` (768), `intfloat/multilingual-e5-small` (384). Cloud: OpenAI, Cohere
(embed-v4.0), Google Gemini embedding, Voyage (deprecated), LiteLLM, Azure. A "Custom Model" entry
lets you type another Hugging Face name; the model server loads it with
`SentenceTransformer(..., trust_remote_code=False)`, so `BAAI/bge-m3` should load (plain
XLM-R architecture) but the 1024-d / 8192-token settings and prefixes must be configured by hand —
**unverified** that the UI accepts it. `multilingual-e5-large` is not in the list either.

**API without LLM?** Only partially. `POST /api/search` (added v4.0, also used by the CLI and by the
MCP tool `search_indexed_documents`) returns `SearchResult[{citation_id, title, content, link,
source_type, updated_at}]` — text sections, **no relevance score** — and the handler resolves an LLM
(`get_default_llm()` fallback) because "the agentic search flow requires multiple LLM calls":
query expansion (skippable with `skip_query_expansion`), scope decision, and *document selection*.
The LLM-free endpoint `POST /admin/search` is a keyword-only retrieval meant for the admin explorer
(filters: source_type, document_set, created/updated ranges, tags). So an MCP tool wrapping Onyx
would in practice pay one or more DeepSeek calls per search and would not get scores or exact chunk
boundaries back.

**External LLM.** Yes: OpenAI, Anthropic, Azure, Bedrock, Vertex, OpenRouter, LiteLLM proxy,
Bifrost, Ollama, LM Studio and a generic "OpenAI-compatible" provider (base URL + model). DeepSeek
would go through the latter or LiteLLM.

**Metadata filters.** Ingestion `metadata` (string or list[string]) is stored as tags; search filters
are `sources`, `document_sets`, `tags[{tag_key, tag_value}]`, `time_cutoff`. No numeric/range
filters on custom metadata.

**Loading 10k articles.** `POST /onyx-api/ingestion` with
`{id, semantic_identifier, sections:[{text, link}], source, metadata, doc_updated_at}`; async
indexing; requires API key with `manage:connectors`. Straightforward (one script), but Onyx
re-chunks at 512 tokens; a long article becomes several chunks and the search result returns
"merged sections", so citation granularity is Onyx's, not ours.

**MCP.** Onyx ships an MCP server (`https://<host>/mcp`, bearer PAT/API key) with tools for
knowledge-base search, web search and URL fetch; the search tool lives in `backend/onyx/mcp_server/`
(community path) and returns `{"results":[{title,url,source_type,content,updated_at}]}`.

**Maturity.** Very active (10k commits, releases every ~2 weeks, v4.8.x in Sep 2026).

**Fit verdict.** See §7.

## 2. RAGFlow (infiniflow/ragflow)

* **Licence / maturity:** Apache-2.0; ~91k stars; v0.27.2 (2026-09-10), releases monthly. Python ≥ 3.13
  on the server side.
* **Services:** Elasticsearch (default) or Infinity (InfiniFlow's own engine; not supported on
  linux/arm64), MySQL, Redis, MinIO, the ragflow server; gVisor only for the code sandbox. The
  image is ~2 GB compressed / ~7 GB unpacked. **Since v0.22.0 only the slim image is shipped: no
  embedding models are bundled**; you must attach a model provider (Ollama — docs suggest `bge-m3` —,
  Xinference, LocalAI, HuggingFace/TEI, OpenAI-compatible…).
* **Resources:** CPU ≥ 4 cores, RAM ≥ 16 GB, disk ≥ 50 GB, Docker ≥ 24, `vm.max_map_count ≥ 262144`
  for ES. GPU optional.
* **Retrieval:** per-dataset `embedding_model` (`name@factory`) and `chunk_method` (naive, book,
  paper, qa, table, …) with `parser_config.chunk_token_num` default 512; keyword + vector "multiple
  recall with fused re-ranking" (`vector_similarity_weight` default 0.3, `similarity_threshold`
  0.2, `knn_top_k` 1024); any rerank provider. Tokenisation is historically Chinese/English-centric;
  v0.26.4 added a "language-aware Snowball stemmer supporting 16 languages" — **French coverage
  unverified** (no hit for "french" in `rag/nlp` via GitHub code search).
* **API without LLM:** yes. `POST /api/v1/retrieval {question, dataset_ids, document_ids,
  metadata_condition{logic, conditions[]}, …}` → `chunks[{id, content, document_id,
  document_keyword, similarity, vector_similarity, term_similarity, positions, highlight}]`.
  Pre-parsed chunks can be pushed with `POST /api/v1/datasets/{ds}/documents/{doc}/chunks
  {content, important_keywords, questions}`.
* **External LLM:** DeepSeek is a first-class provider; OpenAI-API-compatible too.
* **Metadata:** document-level metadata with `metadata_condition` filters; v0.27.1 "metadata filters
  pushed to index for faster retrieval".
* **MCP:** ships an MCP server (`mcp/server`, port 9382, or in-process `POST /mcp` with the Go
  backend) exposing `ragflow_retrieval(dataset_ids, document_ids, question)`, `ragflow_list_datasets`,
  `ragflow_list_chats`. The retrieval tool is the retrieval API, no LLM.
* **Loading 10k articles:** create dataset (embedding model + naive chunking) → either upload
  `.md/.txt` per article and let RAGFlow chunk, or create documents and push one chunk per article via
  the chunks endpoint (one HTTP call per chunk; batching **unverified**).
* **Fit:** functionally the closest "ready-made" match (raw retrieval + hybrid + filters + MCP), but
  the stack is 5 services / 16 GB and needs Docker, and French lexical quality is unproven. Keep as
  the "if we want a UI + document parsing later" option.

## 3. LightRAG (HKUDS) and Microsoft GraphRAG

**LightRAG** — MIT, `lightrag-hku` 1.5.7 (2026-09-02), ~40k stars, EMNLP 2025 paper.
* Pip library + optional `lightrag-server` (REST + WebUI, API-key auth). Default storages are
  in-memory/JSON (`JsonKVStorage`, `NanoVectorDBStorage`, `NetworkXStorage`); production options
  Postgres (unified, incl. new `PGTableGraphStorage` without Apache AGE), Neo4j, Memgraph, Milvus,
  Qdrant, MongoDB, OpenSearch.
* Chunking `CHUNK_SIZE=1200` tokens / overlap 100 (fixed, recursive, semantic, paragraph);
  `TOP_K=40` entities/relations, `CHUNK_TOP_K=20`.
* Embeddings: `EMBEDDING_BINDING` openai / ollama / lollms / azure_openai / bedrock / gemini / jina
  (no built-in sentence-transformers binding in the server; the Python API takes any embedding
  function); README recommends `BAAI/bge-m3` for local use. Rerank `RERANK_BINDING` cohere / jina /
  aliyun with `BAAI/bge-reranker-v2-m3` as example (serve it behind a Jina-compatible endpoint, e.g.
  TEI — **unverified**).
* LLM: `LLM_BINDING=openai` + `LLM_BINDING_HOST` → DeepSeek works; separate model roles EXTRACT /
  QUERY / KEYWORD / VLM.
* Retrieval without generation: `QueryParam.only_need_context`, `only_need_prompt`, and the server's
  `POST /query/data` (entities, relationships, chunks, references); `include_references=True`
  returns `{reference_id, file_path}`. Mode `naive` skips the graph entirely; `mix` (default) is
  KG + vector. Note that KG modes call the LLM for keyword extraction even when only context is
  requested.
* Indexing cost: every chunk goes through LLM entity/relation extraction (except in naive-only
  use); 100k legal docs ≈ hundreds of thousands of DeepSeek calls. Metadata filtering per chunk is
  not part of `QueryParam` (workspaces only) — **unverified**.
* Insert pre-parsed text: `rag.ainsert(texts, ids=[…], file_paths=[…])` or `POST /documents/texts`.
* Fit: an interesting *experiment* (cross-reference graph between articles, circulaires and rulings)
  on top of a working baseline, not the baseline.

**Microsoft GraphRAG** — MIT, 3.2.0 (2026-09-23), README: "largely in maintenance mode … won't be
accepting new PRs or implementing new features". Indexing = LLM extraction of entities/relations/
claims + Leiden communities + community reports ("can be an expensive operation … start small").
Models via LiteLLM (any OpenAI-compatible endpoint), vector store LanceDB (default) / Azure AI Search /
CosmosDB, input txt/csv/json/jsonl/parquet. Query modes (global/local/DRIFT/basic) are LLM-driven;
no retrieval-only API, no metadata filters, `--language` only for prompt tuning. Not suitable.

## 4. Batteries-included alternatives (brief)

* **Dify** (langgenius) — 157k stars. Licence is Apache-2.0 **plus**: no multi-tenant operation
  without written permission and no removal of the Dify logo in the web console. Docker Compose stack
  (Postgres, Redis, vector DB — Weaviate default —, sandbox, plugin daemon, nginx, api/worker/web;
  exact list **unverified** here), docs say ≥ 2 cores / 4 GB. Knowledge base has a real retrieval
  API ("Retrieve chunks from a knowledge base": `search_method` keyword / semantic / full_text /
  hybrid, reranking, weights, `top_k`, score threshold, typed metadata fields + filtering
  conditions; **field names taken from search summaries, unverified**). DeepSeek supported. Dify acts
  as MCP *client*; as a server, unverified. Verdict: capable, but a workflow-builder product with
  licence strings attached; over-scoped.
* **AnythingLLM** (Mintplex) — MIT, 66k stars, single container or desktop app, LanceDB default
  (also pgvector, Qdrant, Chroma, Milvus…), built-in native embedder or Ollama / OpenAI-compatible,
  40+ LLM providers incl. DeepSeek. Developer API has `POST /v1/workspace/:slug/vector-search` →
  `results[{text, score, metadata, distance}]` (verified in `server/endpoints/api/workspace/index.js`).
  No hybrid/BM25, no reranker, no per-document metadata filters documented → weak for legal text.
* **Kotaemon** (Cinnamon) — Apache-2.0, 25.8k stars, Gradio UI, hybrid full-text + vector + rerank,
  citations with PDF highlights, GraphRAG option. Activity is thin: v0.12.0 (May) and three commits in
  Mar–May; the fetch rendered the year once as 2025 and once as 2026, so treat as **low activity,
  year unverified**. No stable retrieval API. Not recommended.
* **Verba** (Weaviate) — **archived 2026-06-08**, read-only. Excluded.

## 5. Lightweight library route

**Frameworks** (all pip, all accept any sentence-transformers model, all give raw nodes/documents
with scores and metadata, all run in-process inside FastMCP):

* **LlamaIndex** 0.14.25 (MIT). Vector-store matrix lists metadata filtering + hybrid for LanceDB,
  Qdrant, Chroma, Postgres, Milvus, Elasticsearch, OpenSearch. Qdrant hybrid: `enable_hybrid=True`
  with fastembed sparse (`Qdrant/bm25` default, SPLADE optional), relative-score fusion with
  `alpha`, `sparse_top_k`/`similarity_top_k`. LanceDB store: `query_type="hybrid"` + LanceDB rerankers
  (page redirected/404 today — **unverified from the LlamaIndex side**, verified from LanceDB docs).
* **Haystack** 3.2.0 (Apache-2.0). Hybrid tutorial: `InMemoryBM25Retriever` +
  `InMemoryEmbeddingRetriever` → `SentenceTransformersSimilarityRanker` (cross-encoder, e.g.
  bge-reranker); `DocumentJoiner` with RRF is the alternative. Document stores: in-memory, pgvector,
  Qdrant, Elasticsearch/OpenSearch, … ; metadata filters are a JSON DSL.
* **LangChain** 1.4.2 (MIT). Vector-store wrappers for all of the below; hybrid depends on the store;
  mostly useful if we want its agent tooling, which we do not (MCP client side handles that).
* **txtai** 9.x (Apache-2.0). Embedded "embeddings database" (SQLite + FAISS/HNSW), built-in
  sparse+dense hybrid with weights, SQL filtering, any HF model, reranking, FastAPI server whose
  `/search` returns raw results, and MCP support. Compact single-dependency option; smaller
  community than the two above.

**Embedded / light stores**

| Store | Server? | BM25 / hybrid | French lexical | Filters | Scale notes |
|---|---|---|---|---|---|
| **LanceDB** (Apache-2.0) | No, file-based | native FTS (BM25) + vector + RRF / cross-encoder / Cohere rerankers ("always set `.limit()`") | FTS tokenizer language options — **unverified** (the project's bm25s + PyStemmer pipeline can be kept for lexical scoring instead) | SQL `where`, pre- or post-filter | fine for 100k×1024-d (~0.4 GB vectors); IVF-PQ/HNSW indexes |
| **Qdrant** (Apache-2.0) | Python local mode `QdrantClient(path=…)` for "development, prototyping and testing"; server (binary or Docker) "when you need to scale" | dense + sparse vectors (fastembed `Qdrant/bm25`, SPLADE) with RRF / score fusion in `query_points` | sparse BM25 via fastembed tokenizer (language handling unverified); bge-m3 sparse weights can be stored as sparse vectors | rich payload filters, multi-tenancy | 100k easy; server needs Docker or the single binary — the repo already has Qdrant skills under `.cursor/skills/` |
| **pgvector** 0.8.6 (PostgreSQL licence) | Postgres server | vector (HNSW/IVFFlat) + `to_tsvector('french')` full-text; hybrid via SQL/RRF | ✔ built-in French stemmer/stopwords | SQL `WHERE`, joins with the document tables | best long-term single store if we already run Postgres; no Docker needed if Postgres is installed natively |
| **Chroma** (Apache-2.0) | embedded `PersistentClient` or server | vector only; `where_document $contains/$regex` are filters, **not BM25 ranking** | ✘ | metadata `where` | fine for 100k, but no lexical ranking → would need external BM25 |
| **sqlite-vec** (MIT/Apache) | No (SQLite extension) | vector KNN (brute-force; ANN files exist, status unverified) + SQLite FTS5 for BM25 | FTS5 has no French stemmer (unicode61 only) | SQL | "pre-v1, expect breaking changes"; OK for 10k, marginal at 100k×1024-d brute force |

**Effort for 10k articles:** one script — reuse `02_dense_sweep` encoding (bge-m3), write
`{id, code, article, heading_path, region, doc_type, date, text, vector}` rows to LanceDB,
`create_fts_index("text")`, and the MCP `search` tool does `table.search(query, query_type="hybrid")
.where("doc_type = 'code' AND region = 'federal'").limit(50)` → bge-reranker-v2-m3 → top-k with
`{id, code, article, heading_path, snippet, score}`. That is the exact article-level citation the
project needs, with no daemon.

---

## 6. Recommendation

1. **Now (prototype, 10k articles): library route, embedded store.** Put bge-m3 (already the
   strongest open-weight multilingual candidate in the project's sweep; MIT, 1024-d, 8192 tokens,
   100+ languages, dense+sparse) + the existing bm25s/French-Snowball lexical index + bge-reranker-v2-m3
   behind a small `retrieval` package, persisted in **LanceDB** (no server, SQL filters, native hybrid)
   — or, if we prefer one engine for lexical scoring too, **Qdrant in local mode** with bge-m3 sparse
   vectors. Wrap it in the existing FastMCP `search`/`fetch` tools. Everything stays LLM-free and
   returns exact `code:article` ids. Whether to go through LlamaIndex/Haystack or write ~200 lines
   directly is a taste question; the evaluation harness in `experiments/common` already speaks plain
   Python, so direct code + LanceDB is the least friction. Haystack is the better of the two
   frameworks if we want pluggable pipelines with typed components.
2. **Growth to 100k docs:** same code, switch the store to Qdrant server or pgvector (Postgres +
   `tsvector('french')`) when a single-process file store becomes a bottleneck or when we need
   multi-process writers. Both keep hybrid + filters + scores. Nothing in the MCP contract changes.
3. **Keep RAGFlow as the fallback "platform" option** if the project later wants document parsing,
   a UI for accountants and a hosted MCP endpoint out of the box; it is the only platform here whose
   retrieval API and MCP tool are LLM-free and metadata-filterable. Budget 16 GB RAM + Docker + an
   external embedding server (Ollama/TEI with bge-m3), and validate French tokenisation first.
4. **LightRAG (naive + mix) as an experiment (08+)** once the baseline is stable, to see whether an
   entity/citation graph (article ↔ circulaire ↔ ruling) improves multi-hop questions; index only a
   subset because of the LLM extraction cost.
5. **Skip Onyx, GraphRAG, Verba, Kotaemon, AnythingLLM** for this use-case; Dify only if a
   no-code workflow UI becomes a requirement (and the licence conditions are acceptable).

## 7. Why Onyx is *not* a good fit here

* **Shape mismatch.** Onyx is an end-user knowledge assistant (chat UI, connectors, agents, bots).
  We need a retrieval engine callable from *our* MCP server. Onyx's own MCP server and `/api/search`
  both run "the full Onyx search pipeline (LLM query expansion, hybrid retrieval, document selection,
  context expansion)" and return text sections **without scores**; `skip_query_expansion` removes
  only one LLM step, and the endpoint still resolves a default LLM. A DeepSeek key would therefore be
  consumed *inside* the retriever, and we lose control over ranking and citation boundaries.
* **Chunking and citations are Onyx's.** 512-token chunks and "merged sections" replace our
  article-level units; there is no way to return `CIR 92 art. 145/33 §2` as the unit of citation
  other than by encoding it into `link`/`semantic_identifier`.
* **Footprint.** 11 containers, OpenSearch with a 2 GB heap, two model servers (2 CPU / 4 GB each
  for local embeddings), 10–16 GB RAM, Docker/Kubernetes only. That is an order of magnitude more
  infrastructure than the problem needs, and it cannot be started on the current box at all.
* **Embedding choice is constrained.** The curated self-hosted list stops at
  `multilingual-e5-base/small`; bge-m3 / multilingual-e5-large are "Custom Model" territory with no
  documentation, and the keyword analyzer defaults to English.
* **Metadata filters are tag-based** (string equality, time cutoff, source, document set) — enough
  for `region`/`doc_type`, but no ranges or numeric filters and no per-chunk structure.
* What Onyx does well — connectors, permissions, SSO, agents, a polished UI, an MCP endpoint that
  enforces per-user ACLs — is not on this project's critical path. If a hosted assistant UI for
  accountants is ever needed, Onyx (or RAGFlow) could sit *on top of* our index via its ingestion
  API, but it should not be the index.

---

## Sources (read on 2026-09-24)

Onyx
* https://github.com/onyx-dot-app/onyx
* https://docs.onyx.app/deployment/getting_started/resourcing
* https://docs.onyx.app/deployment/getting_started/quickstart
* https://docs.onyx.app/deployment/local/opensearch
* https://docs.onyx.app/changelog
* https://docs.onyx.app/admins/advanced_configs/search_configs
* https://docs.onyx.app/admins/ai_models/overview
* https://docs.onyx.app/developers/core_concepts
* https://docs.onyx.app/developers/guides/index_files_ingestion_api
* https://docs.onyx.app/developers/api_reference/search/search
* https://docs.onyx.app/overview/onyx_anywhere/mcp_server
* https://docs.onyx.app/overview/miscellaneous/open_source_statement
* https://raw.githubusercontent.com/onyx-dot-app/onyx/main/LICENSE
* https://raw.githubusercontent.com/onyx-dot-app/onyx/main/deployment/docker_compose/docker-compose.yml
* https://raw.githubusercontent.com/onyx-dot-app/onyx/main/backend/shared_configs/configs.py
* https://raw.githubusercontent.com/onyx-dot-app/onyx/main/backend/onyx/configs/app_configs.py
* https://raw.githubusercontent.com/onyx-dot-app/onyx/main/backend/onyx/configs/chat_configs.py
* https://raw.githubusercontent.com/onyx-dot-app/onyx/main/backend/onyx/configs/embedding_configs.py
* https://raw.githubusercontent.com/onyx-dot-app/onyx/main/web/src/lib/searchSettings/constants.ts
* https://raw.githubusercontent.com/onyx-dot-app/onyx/main/backend/model_server/encoders.py
* https://raw.githubusercontent.com/onyx-dot-app/onyx/main/backend/onyx/server/features/search/api.py
* https://raw.githubusercontent.com/onyx-dot-app/onyx/main/backend/onyx/server/query_and_chat/query_backend.py
* https://raw.githubusercontent.com/onyx-dot-app/onyx/main/backend/onyx/mcp_server/tools/search.py
* https://github.com/onyx-dot-app/onyx/releases (fetch rendered release years inconsistently; versions/months cross-checked with the changelog)

RAGFlow
* https://github.com/infiniflow/ragflow
* https://raw.githubusercontent.com/infiniflow/ragflow/main/README.md
* https://github.com/infiniflow/ragflow/releases
* https://ragflow.io/docs/
* https://ragflow.io/docs/http_api_reference
* https://ragflow.io/docs/deploy_local_llm
* https://ragflow.io/docs/supported_models
* https://ragflow.io/docs/faq
* GitHub code search `ragflow_retrieval repo:infiniflow/ragflow` (mcp/client/client.py, docs/develop/mcp/mcp_client_example.md, internal/mcp/server.go, docker/entrypoint.sh)

LightRAG / GraphRAG
* https://github.com/HKUDS/LightRAG and https://raw.githubusercontent.com/HKUDS/LightRAG/main/README.md
* https://raw.githubusercontent.com/HKUDS/LightRAG/main/env.example
* https://raw.githubusercontent.com/HKUDS/LightRAG/main/lightrag/api/routers/query_routes.py
* https://github.com/HKUDS/LightRAG/releases ; https://pypi.org/project/lightrag-hku/
* https://microsoft.github.io/graphrag/ ; https://microsoft.github.io/graphrag/config/yaml/ ; https://microsoft.github.io/graphrag/index/overview/ ; https://microsoft.github.io/graphrag/prompt_tuning/auto_prompt_tuning/
* https://github.com/microsoft/graphrag ; https://github.com/microsoft/graphrag/releases ; https://pypi.org/project/graphrag/

Batteries-included alternatives
* https://github.com/Cinnamon/kotaemon ; https://github.com/Cinnamon/kotaemon/releases ; https://github.com/Cinnamon/kotaemon/commits/main
* https://github.com/weaviate/Verba
* https://github.com/langgenius/dify ; https://raw.githubusercontent.com/langgenius/dify/main/LICENSE ; https://docs.dify.ai/api-reference/datasets/retrieve-chunks-from-a-knowledge-base (search summary only) ; https://docs.dify.ai/en/guides/knowledge-base/knowledge-request-rate-limit
* https://github.com/Mintplex-Labs/anything-llm ; https://docs.anythingllm.com/features/api ; https://raw.githubusercontent.com/Mintplex-Labs/anything-llm/master/server/endpoints/api/workspace/index.js

Libraries and stores
* https://pypi.org/project/llama-index/ ; https://developers.llamaindex.ai/python/framework/module_guides/storing/vector_stores/ ; https://developers.llamaindex.ai/python/examples/vector_stores/qdrant_hybrid/
* https://pypi.org/project/langchain/
* https://pypi.org/project/haystack-ai/ ; https://haystack.deepset.ai/tutorials/33_hybrid_retrieval
* https://github.com/neuml/txtai ; https://github.com/neuml/txtai/releases
* https://docs.lancedb.com/search/hybrid-search
* https://github.com/qdrant/qdrant-client
* https://docs.trychroma.com/docs/overview/introduction ; https://docs.trychroma.com/docs/querying-collections/full-text-search
* https://github.com/asg017/sqlite-vec
* https://github.com/pgvector/pgvector

Models
* https://huggingface.co/BAAI/bge-m3
* https://huggingface.co/intfloat/multilingual-e5-large

Local project files consulted: `AGENTS.md`, `experiments/00_pdf_parsing/README.md`,
`experiments/01_bm25/README.md`, `experiments/02_dense_sweep/*.py`, `experiments/03_hybrid_rerank/run_hybrid.py`,
`experiments/results/leaderboard.jsonl`.
