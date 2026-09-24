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

RESULTS_PLACEHOLDER

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

ASSESSMENT_PLACEHOLDER
