# Experiment 05 – LlamaIndex structure-aware retrievers

**Question.** Do LlamaIndex's "structure-aware" retrieval patterns – hierarchical
nodes + `AutoMergingRetriever`, `SentenceWindowNodeParser` +
`MetadataReplacementPostProcessor`, and the hybrid `BM25Retriever` +
`QueryFusionRetriever` (reciprocal rank fusion) – beat plain chunk retrieval on French
legal text (Fisconet+ circulaires/FAQs in corpus A, code articles in corpus B)? And how
much friction does the framework add when used *retriever-only* (no LLM, no cloud)?

Everything runs locally: `Settings.llm = None` (→ `MockLLM`), embeddings via
`HuggingFaceEmbedding("intfloat/multilingual-e5-small")` on CPU, the default in-memory
`SimpleVectorStore`. No query engine / synthesis is used; the retrievers' node lists are
mapped back to `doc_id` (first occurrence wins) and scored with the shared
`rag_eval` harness (MRR, nDCG@5, hit@k, recall@10).

## Setup

Standalone uv project (not a workspace member; the root `pyproject` excludes `experiments/*`).

```bash
cd experiments/05_llamaindex
uv sync
# nltk >= 3.9.2 refuses hard-linked data files (see "Workarounds"); make a plain copy once:
cp -rL .venv/lib/python3.12/site-packages/llama_index/core/_static/nltk_cache .nltk_data

uv run python run_llamaindex.py --corpus A                       # all 5 patterns (+ leaf-only hierarchical)
uv run python run_llamaindex.py --corpus B --patterns sentence_splitter,hierarchical_automerge,fusion_rrf
uv run python run_llamaindex.py --corpus A --limit_docs 8        # smoke test (no save, no cache)
uv run python run_llamaindex.py --leaderboard --corpus A
```

Indices are persisted with `StorageContext.persist()` under `.index_cache/<corpus>/<pattern>`
(SimpleVectorStore + SimpleDocumentStore as JSON) so a crash does not re-embed; `--rebuild`
ignores the cache. Results go to `experiments/results/05_llamaindex/*.json` and
`experiments/results/leaderboard.jsonl`.

### Installed versions (uv, 2026-09-24)

| package | version |
|---|---|
| llama-index-core | 0.14.25 |
| llama-index-embeddings-huggingface | 0.8.0 |
| llama-index-retrievers-bm25 | 0.8.0 (wraps bm25s 0.3.11, PyStemmer 2.2.0.3) |
| sentence-transformers | 6.1.0 |
| transformers | 5.17.0 |
| torch | 2.14.0+cpu (pytorch-cpu index) |
| nltk | 3.10.3 |

Note that Context7 was unavailable (quota); import paths and constructor arguments were
verified by introspecting the installed packages (`inspect.signature`) and reading the
source (`llama_index/core/settings.py`, `llms/utils.py`, `retrievers/fusion_retriever.py`,
`retrievers/auto_merging_retriever.py`, `node_parser/text/sentence.py`,
`llama_index/retrievers/bm25/base.py`).

## What is built

Common: one `Document` per rag_eval `Doc`, `id_ = doc_id`, `metadata = {doc_id, title}`
(A) or `{doc_id, code, title, heading_path}` (B). `doc_id`/`code` are put in
`excluded_embed_metadata_keys` and `excluded_llm_metadata_keys`; `title` (A) and
`title` + `heading_path` (B) are left *in* the embedded text – LlamaIndex prepends
`key: value` lines to every chunk, which is exactly the "contextual chunk header"
(`article_ctx` / `fixed1500_title`) the other experiments use.

| run name | pipeline |
|---|---|
| `llamaindex__sentence_splitter_400__e5-small` | `SentenceSplitter(chunk_size=400, chunk_overlap=50)` → `VectorStoreIndex` → `as_retriever(similarity_top_k=50)` |
| `llamaindex__hierarchical_leaf_128__e5-small` | `HierarchicalNodeParser.from_defaults(chunk_sizes=[2048,512,128])`, all nodes in a `SimpleDocumentStore`, only `get_leaf_nodes()` embedded; plain top-50 leaf retrieval (control run, no merging) |
| `llamaindex__hierarchical_automerge_2048_512_128__e5-small` | same index → `AutoMergingRetriever(leaf_retriever, storage_context, simple_ratio_thresh=0.5)` |
| `llamaindex__sentence_window_3__e5-small` | `SentenceWindowNodeParser(window_size=3)` → `VectorStoreIndex` (one node per sentence, `window` excluded from the embedding) → top-50 → `MetadataReplacementPostProcessor("window")` |
| `llamaindex__bm25` | `BM25Retriever.from_defaults(docstore=…, stemmer=Stemmer("french"), language="french", similarity_top_k=50)` over the sentence_splitter nodes |
| `llamaindex__fusion_rrf__e5-small` | `QueryFusionRetriever([vector_top50, bm25_top50], mode="reciprocal_rerank", num_queries=1, llm=None, use_async=False, similarity_top_k=50)` |

`chunk_size` is counted with the **embedding model's own tokenizer** (`Settings.tokenizer`
set to the e5 XLM-R tokenizer) so that 400 tokens really is 400 e5 tokens under the
512 `max_length`; 400 e5 tokens ≈ 1 400–1 800 characters of French, i.e. comparable to
the `fixed1500` chunker of experiments 01–03.

Embedding: `HuggingFaceEmbedding(model_name="intfloat/multilingual-e5-small",
query_instruction="query: ", text_instruction="passage: ", max_length=512, device="cpu",
normalize=True, embed_batch_size=32)`. `torch.set_num_threads(2)` (shared 4-core box).

## Results

### Corpus A – 91 Fisconet+ documents, 29 questions, document-level ground truth

| run | nodes embedded | index build s | query mean ms | MRR | nDCG@5 | hit@1 | hit@5 | recall@10 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `llamaindex__bm25` | 1075 | 0.3 | 5.4 | 0.669 | 0.677 | 0.586 | 0.724 | 0.862 |
| `llamaindex__fusion_rrf__e5-small` | 1075 | 316.9 | 711.0 | 0.605 | 0.676 | 0.448 | 0.759 | 0.862 |
| `llamaindex__hierarchical_leaf_128__e5-small` | 4415 | 451.3 | 582.7 | 0.540 | 0.589 | 0.345 | 0.724 | 0.828 |
| `llamaindex__sentence_splitter_400__e5-small` | 1075 | 316.9 | 376.5 | 0.530 | 0.616 | 0.345 | 0.690 | 0.862 |
| `llamaindex__hierarchical_automerge_2048_512_128__e5-small` | 4415 | 451.3 | 529.7 | 0.509 | 0.564 | 0.345 | 0.690 | 0.828 |
| `llamaindex__sentence_window_3__e5-small` | 7481 | 1545.1 | 1702.1 | 0.469 | 0.552 | 0.310 | 0.690 | 0.828 |

Like-for-like references (same model, same 29 questions; experiments 04/06 use the
harness `fixed1500_title` chunker, 01 uses a hand-built accent-stripping analyser):

| experiment | run | MRR | nDCG@5 | hit@1 | hit@5 | recall@10 |
|---|---|---:|---:|---:|---:|---:|
| 04_lancedb | `lancedb__e5-small__vector` | 0.541 | 0.629 | 0.379 | 0.759 | 0.862 |
| 06_txtai | `txtai__e5-small__dense` | 0.541 | 0.629 | 0.379 | 0.759 | 0.862 |
| 04_lancedb | `lancedb__e5-small__fts_fr` | 0.645 | 0.690 | 0.517 | 0.759 | 0.862 |
| 06_txtai | `txtai__e5-small__bm25` | 0.565 | 0.640 | 0.379 | 0.759 | 0.862 |
| 04_lancedb | `lancedb__e5-small__hybrid_rrf` | 0.598 | 0.672 | 0.448 | 0.793 | 0.966 |
| 06_txtai | `txtai__e5-small__hybrid_w0.7` | 0.607 | 0.671 | 0.448 | 0.793 | 0.897 |
| 01_bm25 | `fixed1500+title|max|stem+stop+qstop+noaccent` | 0.672 | 0.704 | 0.552 | 0.793 | 0.897 |
| 01_bm25 | `doc|stem+stop+qstop+noaccent` | 0.695 | 0.734 | 0.586 | 0.897 | 0.897 |

Timings: 2 torch threads on a 4-core VM with load average 11–15 (three other experiments
embedding at the same time); `query mean ms` includes the ~130 ms query embedding.

Observations (A):

* **Plain `SentenceSplitter` (0.530) ≈ the harness's own chunker (0.541).** LlamaIndex's
  splitter is a fair baseline; the small gap is chunk boundaries (400 e5 tokens vs 1 500
  chars, paragraph separator `\n\n\n` vs heading-aware splitting).
* **Hierarchical leaves without merging (0.540) ≈ baseline; `AutoMergingRetriever`
  makes it worse (0.509).** Merging changes the rank of the expected document on 7 of 29
  questions: better on 2 (Q4, Q29), worse on 5 (Q6, Q19, Q25, Q26, Q30), because a merged
  parent takes the *mean* score of its retrieved children, which drags a document whose
  best leaf was rank 1 below documents that were retrieved as a single, high-scoring leaf.
  Small leaves also crowd the candidate list: with top-50 128-token leaves the expected
  document disappears from the list entirely on Q12/Q14/Q27, where 400-token chunks still
  found it at ranks 9–17 (hence recall@10 0.828 vs 0.862).
* **`SentenceWindowNodeParser` is the worst dense variant (0.469)** and the most expensive
  index (7 481 single-sentence nodes, 1 545 s, 123 MB JSON). Single sentences of legal French
  ("Ce montant est indexé conformément à l'article 178.") are poor retrieval units; the
  window only helps the *reader* after retrieval, not the ranking, and our metric is the
  ranking.
* **`BM25Retriever` with `Stemmer("french")` + French stopwords is the best single
  retriever (0.669)**, within noise of the hand-tuned BM25 of experiment 01 (0.672 on the
  same chunk granularity, 0.695 at whole-document level). Query latency 5 ms.
* **`QueryFusionRetriever` RRF (0.605)** lands between its two inputs, as RRF does when
  one input (dense, 0.530) is much weaker than the other; it improves hit@5 (0.759) but
  loses hit@1 vs BM25 alone (0.448 vs 0.586). LanceDB's hybrid RRF (experiment 04) shows
  the same pattern (0.598).

### Corpus B – 5 853 code articles (default subset), 40 questions, article-level ground truth

| run | nodes embedded | index build s | query mean ms | MRR | nDCG@5 | hit@1 | hit@5 | recall@10 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `llamaindex__sentence_splitter_400__e5-small` | 10609 | 3780.4 | 354.7 | 0.479 | 0.423 | 0.375 | 0.575 | 0.725 |
| `llamaindex__fusion_rrf__e5-small` | 10609 | 2.5 | 1105.4 | 0.420 | 0.364 | 0.250 | 0.575 | 0.750 |
| `llamaindex__bm25` | 10609 | 2.5 | 3.0 | 0.352 | 0.307 | 0.225 | 0.475 | 0.575 |

`llamaindex__hierarchical_leaf_128` / `llamaindex__hierarchical_automerge_2048_512_128` on B:
the parser produced **62 072 nodes, 46 975 leaves to embed** (4.4× the plain index, because
the `title + heading_path` header of 16–95 e5 tokens is repeated inside every 128-token
leaf). Embedding was still running when this README was written; the job
(`run_llamaindex.py --corpus B`) writes its results to
`experiments/results/05_llamaindex/B__llamaindex__hierarchical_*.json` and the shared
leaderboard on completion – run `uv run python run_llamaindex.py --leaderboard --corpus B`
to see them.

Like-for-like references (same model, same 40 questions; 04/06 use the harness
`article_ctx` chunker, 2 000 chars + heading context):

| experiment | run | MRR | nDCG@5 | hit@1 | hit@5 | recall@10 |
|---|---|---:|---:|---:|---:|---:|
| 04_lancedb | `lancedb__e5-small__vector` | 0.361 | 0.328 | 0.225 | 0.550 | 0.700 |
| 06_txtai | `txtai__e5-small__dense` | 0.369 | 0.344 | 0.250 | 0.550 | 0.650 |
| 04_lancedb | `lancedb__e5-small__fts_fr` | 0.357 | 0.313 | 0.225 | 0.500 | 0.600 |
| 04_lancedb | `lancedb__e5-small__hybrid_rrf` | 0.435 | 0.386 | 0.300 | 0.575 | 0.650 |
| 06_txtai | `txtai__e5-small__hybrid_w0.7` | 0.332 | 0.292 | 0.225 | 0.425 | 0.475 |
| 01_bm25 | `article+ctx|max|stem+stop+qstop+noaccent` | 0.338 | 0.306 | 0.200 | 0.500 | 0.600 |
| 02_dense_sweep | `e5-small__article_ctx` | (not run) |

Observations (B):

* **Plain `SentenceSplitter(400)` (0.479) beats every other e5-small run on B (0.36–0.37)
  and the best BM25 of experiment 01 (0.338).** The difference is not the framework but
  chunk sizing in *model tokens*: 25.8 % of the harness `article_ctx` chunks
  (2 103 / 8 148) exceed e5's 512-token window once `passage: ` and the heading context
  are prepended, and 28 of the 39 expected articles contain a truncated chunk.
* **`BM25Retriever` (0.352)** matches experiment 01's tuned BM25 (0.338) – so on B the
  lexical side is the weak input and RRF fusion (0.420) is pulled *below* dense alone,
  the mirror image of corpus A. Query latency: BM25 3 ms, fusion ~1.1 s (two retrievers +
  query embedding under load).


## Workarounds and pitfalls

1. **`Settings.llm` is lazy and defaults to OpenAI.** Nothing in this experiment needs an
   LLM, but `QueryFusionRetriever.__init__` reads `Settings.llm` even with
   `num_queries=1`; the getter instantiates `OpenAI()` and raises
   `Could not load OpenAI model … OPENAI_API_KEY`. `Settings.llm = None` resolves to a
   `MockLLM` (logged as "LLM is explicitly disabled") and must be set before any retriever
   is constructed. The same applies to `Settings.embed_model` (default `OpenAIEmbedding`):
   set it explicitly *and* pass `embed_model=` to `VectorStoreIndex` /
   `load_index_from_storage`, otherwise a persisted index reloads with OpenAI embeddings.
2. **Default token counter is tiktoken `cl100k_base`** (OpenAI's tokenizer; the BPE file is
   bundled offline in `_static/tiktoken_cache`, so no download). `chunk_size=400` would
   then be 400 GPT tokens, not 400 e5 tokens. Set `Settings.tokenizer`.
3. **Metadata is silently part of every chunk.** `SentenceSplitter.split_text_metadata_aware`
   subtracts the token length of the metadata string from `chunk_size` (and raises if it
   does not fit). On corpus B the `title + heading_path` header is 16–95 e5 tokens
   (p50 = 59), so the 128-token hierarchical leaves keep only ~35–110 tokens of article
   text. That is by design (every leaf stays self-describing) but it is not obvious from
   the API, and it is why the leaf count is high.
4. **nltk 3.10 "pathsec" vs uv hardlinks.** `SentenceSplitter` and
   `SentenceWindowNodeParser` use nltk's punkt sentence tokenizer, loaded from the
   `nltk_cache` bundled in `llama_index-core`. uv installs packages with hardlinks, and
   nltk ≥ 3.9.2 refuses to open any file with `st_nlink > 1`
   (`PermissionError: Security Violation [pathsec.open]: refusing multiply-linked file`).
   Fix: copy the data (`cp -rL … .nltk_data`) and point `NLTK_DATA` at the copy (the runner
   does this automatically when `.nltk_data` exists). Alternatives: `UV_LINK_MODE=copy`, or
   let `nltk.download()` fetch to `~/nltk_data`.
5. **`BM25Retriever` tokenisation is fixed.** It tokenises `node.get_content(MetadataMode.EMBED)`
   with bm25s' regex `(?u)\b\w\w+\b`, lower-cases, removes `language` stopwords and stems
   with the PyStemmer passed in. `language="french"` (or `"fr"`) is accepted by bm25s; the
   default is English stopwords + English stemmer, which silently degrades French. There is
   no hook for accent stripping or a custom analyser any more (the `tokenizer=` argument is
   deprecated), so the accent-insensitive variant that won experiment 01 cannot be
   reproduced inside the framework.
6. **Retriever output order.** `VectorIndexRetriever` and `QueryFusionRetriever` return
   nodes sorted by score; `AutoMergingRetriever` re-sorts after merging (parent score =
   mean of the retrieved children's scores). The runner re-sorts (stably) anyway before
   mapping to `doc_id`.
7. **Throughput.** `HuggingFaceEmbedding` adds only ~5–30 % over calling
   `SentenceTransformer.encode` directly (default `embed_batch_size=10` is worth raising).
   All absolute timings below were measured with load average ≈ 11 on a 4-core VM shared
   with experiments 02/04/06, so they are pessimistic by roughly 3×.

## Assessment

**Does structure-aware retrieval help on legal articles? No – not with these three
patterns, on either corpus.**

* *Hierarchical + auto-merging* is designed for long narrative documents where a query
  hits several adjacent small leaves. Legal articles are short (corpus B median 685 chars)
  and already the natural retrieval unit; circulaires (corpus A) are long but the
  questions are answered by one paragraph, so merging rarely triggers and, when it does,
  the averaged parent score demotes the document. On A it cost 0.02–0.03 MRR against the
  un-merged leaves and the plain splitter, at 4× the number of vectors. On B the 128-token
  leaves are dominated by the `title + heading_path` header (16–95 e5 tokens) so the parser
  emits 47k leaves for 5.9k articles – 4.4× the plain index – with no evidence from A that merging would pay for it (result pending, see Results).
* *Sentence window* trades ranking quality for reader context: single French legal
  sentences are weak embedding units (A: 0.469 vs 0.530), the index is 7× larger and the
  slowest to build. It is the wrong tool when the consumer is an LLM tool call that can
  simply fetch the whole article afterwards.
* *BM25 + RRF fusion* is the one pattern worth keeping, but it is not "structure-aware":
  it is the same hybrid every other experiment built. RRF lands between its inputs
  (A: 0.605 between 0.530 dense and 0.669 BM25; B: 0.420 between 0.479 dense and 0.352
  BM25), so it only helps when the two retrievers are of comparable strength. Weighted
  fusion (`retriever_weights=`) or a reranker would be needed to beat the better input.

**What did help is boring:** counting `chunk_size` in the *embedding model's* tokens.
LlamaIndex's plain `SentenceSplitter(400)` with the e5 tokenizer scores 0.479 MRR on B
versus 0.36–0.37 for the same model in experiments 04/06 with the harness's 2 000-char
`article_ctx` chunks. Checking the harness chunks with the e5 tokenizer: 25.8 % of them
(2 103 / 8 148) exceed 512 tokens once `passage: ` and the heading context are prepended,
and 28 of the 39 expected articles contain a truncated chunk. That truncation, not the
framework, explains most of the gap, and it is a bug to fix in the shared chunker
(chunk by model tokens, or cap at ~1 400 chars for 512-token models).

**Code and complexity.** The retriever-only path is ~250 lines including caching,
timing and evaluation; each pattern is 3–6 lines of framework code. The cost is not the
lines but the defaults: two silent OpenAI dependencies (`Settings.llm`,
`Settings.embed_model`), an OpenAI tokenizer for chunk sizing, metadata injected into
every embedded chunk, an English stemmer + stopwords in `BM25Retriever`, and an nltk data
loader that breaks under uv. All were found by reading source, not documentation. Persisted
indices are JSON (`SimpleVectorStore`): 123 MB for 7.5k sentence nodes, 24 s to reload the
10.6k-node B index, and the whole vector store is loaded in memory – fine for a demo, not
for the production corpus.

**Fit for the FastMCP tool.** Poor as a dependency: this venv has 88 packages against 45
for experiment 03 (same torch / sentence-transformers / bm25s stack), i.e. the three
`llama-index-*` packages add 43 transitive dependencies (nltk, tiktoken, pydantic,
aiohttp, SQLAlchemy, dataclasses-json, tenacity, httpx, …) to obtain a `SentenceSplitter`,
a numpy cosine loop and a thin wrapper around bm25s – all of which the harness already
has in fewer than 200 lines with no hidden network calls. The pieces that would carry
over are conceptual, not code: chunk in model tokens, keep BM25 with a French stemmer,
fuse with a weight rather than plain RRF, and treat "structure" as *metadata for
filtering and citation* (code, article, heading path) rather than as a retrieval
hierarchy. If LlamaIndex were adopted anyway, use it only for the ingestion transforms
and export nodes to LanceDB (experiment 04); the `QueryFusionRetriever` should not be
constructed in a process where `OPENAI_API_KEY` might be set, because with
`num_queries > 1` it *will* send the user's tax question to OpenAI.

