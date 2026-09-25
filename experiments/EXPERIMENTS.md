# RAG experiments for Belgian tax law — log, results and recommendation

*Branch `claude/belgian-tax-rag-planning-g6luoo`, September 2026. All numbers are reproducible from the
per-experiment folders; the machine-readable log is `experiments/results/leaderboard.jsonl`
(`uv run python -m rag_eval.results A|B|C` prints a leaderboard from any experiment venv).*

## 1. Question, constraints, method

**Question.** What is the best way to build (agentic) RAG on a medium-size corpus of French legal text,
with quick prototyping now and growth to ~100k documents, behind the project's FastMCP server?

**Constraints.** Open-weight embedding models only; no LLM available in this branch (DeepSeek comes
later), so everything below is *retrieval* quality; CPU-only box (4 cores, 16 GB, no Docker daemon).

**Method.** One shared harness (`experiments/common`, package `rag_eval`) with three corpora and
human-verified ground truth, and one metric set at *document* level (a document = a Fisconet+ document
for A/C, a legal *article* for B):

| corpus | content | size | questions | ground truth |
|---|---|---|---|---|
| **A** | the repo's 91 Fisconet+ markdown docs (circulaires, FAQs, rulings, PQs, code excerpts) | 1.2 M chars | 31 → **29** (Q13/Q15 flagged invalid, see §3.0) | doc ids from `questions.json` |
| **B** | the 30 unilingual legal-code PDFs of `myfin_pdfs/`, parsed into **9,824 articles** (§3.1); default subset 5,853 articles | 8.4 M chars | **40 new** (`experiments/data/corpus_b/questions_b.json`) | article ids, verified in the text |
| **C** | the 21,259 Fisconet+ documents of `myfin_docs/` (24 document types) | 238 M chars | **64 new** (`experiments/data/corpus_c/questions_c.json`) | file ids, verified in the text; several acceptable ids where yearly/regional editions coexist |

Metrics: MRR (rank of the first expected document), nDCG@5 (secondary documents weighted 0.5),
hit@1/5, recall@10. Questions are natural French questions of a taxpayer, company or accountant,
deliberately using everyday vocabulary rather than statute wording (that is what makes B and C hard).

Each experiment lives in its own standalone `uv` project under `experiments/` (own venv, CPU-only torch),
with a README documenting setup, API notes and results:

| folder | what |
|---|---|
| `00_pdf_parsing` | PDF → article corpus (Corpus B) |
| `01_bm25` | lexical baselines (bm25s, French normalisation, unit / aggregation / k1,b grid) |
| `02_dense_sweep` | 15 open-weight embedding models × chunking (numpy cosine, cached embeddings) |
| `03_hybrid_rerank` | dense + BM25 fusion (RRF / convex) and cross-encoder rerankers |
| `04_lancedb` | embedded store prototype: LanceDB (vector + French FTS + hybrid + reranker plug-in + SQL filters) |
| `05_llamaindex` | LlamaIndex structure-aware retrievers (hierarchical/auto-merging, sentence-window, BM25, fusion) |
| `06_txtai` | txtai all-in-one embeddings DB (hybrid, SQL filters, reranker pipeline) |
| `07_frameworks_assessment` | paper assessment of Onyx, RAGFlow, LightRAG/GraphRAG, Dify, AnythingLLM, Kotaemon, Verba |
| `08_corpus_b_cleanup` | amendment-preamble stripping, region metadata + city→region query filter |
| `09_corpus_c` | the 21k-document corpus: BM25, static + e5 dense, fusion, reranking at scale |

## 2. Headline results

MRR at document level; best configuration per family. Full tables in each README.

| approach | A (29 q) | B (40 q) | C (64 q) |
|---|---:|---:|---:|
| Repo's previous best (MiniLM 384d + ColBERT rerank, Qdrant grid, 31 q) | 0.50 | – | – |
| MiniLM dense, 1,500-char chunks (the docker-compose default) | 0.48 | – | – |
| **BM25, French-normalised** (stem + stopwords + question-word list + accent fold) | 0.695 | 0.338 | 0.577 |
| BM25 after corpus-B preamble cleanup (exp 08) | – | 0.377 | – |
| potion static embeddings (1 s to encode A) | 0.46 | – | 0.315 |
| potion + BM25 convex 0.3 | – | – | 0.595 |
| e5-small dense (118M), token-safe chunks | 0.543 | 0.438 (0.466 cleaned; 0.486 with 128-token leaves, exp 05) | 0.433 |
| e5-base dense (278M), title-prefixed / cleaned token-safe chunks | 0.641 | 0.469 | – |
| bge-m3 dense (568M), title-prefixed chunks | 0.678 (R@10 0.966) | too slow on CPU | too slow on CPU |
| e5-large / Solon-large / arctic-l-v2 (whole doc, 512 tokens) | 0.677 / 0.674 / 0.675 | – | – |
| bge-m3 + BM25 convex 0.5 | 0.691 | – | – |
| e5-small hybrid RRF | 0.598 (LanceDB) | 0.457 | 0.567 |
| e5-small + BM25 convex 0.5 | – | 0.381 (BM25 leg too weak on B) | 0.621 |
| e5-small hybrid RRF + mMARCO-MiniLM rerank @30 | 0.639 (LanceDB) | **0.522** | – |
| BM25 + mMARCO-MiniLM rerank @30 | – | – | 0.593 |
| BM25 + bge-reranker-v2-m3 @30 | – | – | 0.696 (H@1 0.594) |
| **e5-small hybrid + bge-reranker-v2-m3 @30** | **0.703** (RRF, LanceDB; nDCG@5 0.797, H@5 0.931) | 0.517 (RRF) | **0.703** (convex 0.5; H@1 0.609, R@10 0.891) |
| bge-m3 + BM25 convex 0.5 + bge-reranker-v2-m3 @30 | 0.681 (nDCG@5 0.782, H@5 0.931) | – | – |

Reranker cost on this 4-core CPU: 20–24 s per query for 30 candidates of ≤1,024 tokens (bge-reranker-v2-m3),
2 s with mMARCO-MiniLM. All heavy runs were executed one at a time by `experiments/run_queue.sh` (`queue.log`).

## 3. What was learned, experiment by experiment

### 3.0 Validation data hygiene (before anything else)
* Two of the repo's 31 questions had **wrong ground truth**: Q13's document is a 1984 VAT circular on the
  second-hand margin scheme (not benefits in kind) and Q15's is a 1.3k-char fragment of a court-decision
  preamble. No retriever can get them right; they are flagged `skip: true` in `questions.json` and the harness
  excludes them. Q24's document is in Dutch with a French summary (kept: a legitimate cross-lingual case).
* Corpus B and C questions were written *after* reading the documents, with an evidence quote per question,
  and every id is validated against the corpus.

### 3.1 PDF parsing (`00_pdf_parsing`)
* The 34 MyMinfin PDFs are native text: `pymupdf` + regex beats layout models (21 s for 11.6k pages).
  `pymupdf4llm` was not needed (mis-detected heading levels, kept TOC dot leaders, 20× slower).
* Structure recovered: article headings (`Article 185, CIR 92`, `Art. 2.7.4.1.1.`, superscripts
  `145^33 → 145/33`), heading path (LIVRE/TITRE/CHAPITRE/Section), French column of bilingual editions,
  AR TVA decree prefixes (`artva:AR1:5`), "DROIT FUTUR" versions tagged with their date.
* Known losses: tariff tables flattened; Flemish codes are concordance tables; customs code numbering overlaps.

### 3.2 Lexical baseline (`01_bm25`)
* **Normalisation is worth +0.25 MRR on A** (plain 0.45 → 0.70): stopwords +0.13, French Snowball stemming
  +0.05, an extra list of question words (*quel, comment, puis-je…*) +0.04; accent folding neutral.
  Default k1=1.5, b=0.75 best; `lucene` = `bm25+`.
* On A whole documents beat chunks (docs are short, single-topic); on B article-level units with the heading
  path prefixed are best (+0.04); "sum of top-3 chunks" aggregation hurts (monster articles absorb everything).
* Failure modes on B (16/40 questions rank > 10): layman ↔ statute vocabulary (dominant), region given as a
  city while three near-identical regional codes exist, length pathologies, amendment-history preambles,
  tables flattened to numbers, doctrinal labels absent from statute text (RDT, TVA vs "la taxe").

### 3.3 Embedding models (`02_dense_sweep`)
* On B, token-safe 1,200-char article chunks lift e5-small from 0.361 to 0.438 (+0.08) — the single most
  important chunking result; e5-base on the same cleaned chunks gives 0.469.
* Quality tracks model size: MiniLM 0.48 < e5-small 0.54 < e5-base 0.64 < bge-m3 / e5-large / Solon / arctic
  ≈ 0.68 on A. Only the 560M-class models reach tuned BM25; bge-m3 has the best recall@10 (0.97).
* A title / heading-path prefix on every chunk is a free +0.02–0.04.
* **Chunk in model tokens.** 27 % of the 2,000-char corpus-B article chunks exceeded 512 tokens once the
  heading prefix was added; capping at 1,200 chars leaves 0.3 % and is the fix for every 512-token encoder.
* CPU economics: a 560M model costs ~1 h per 1,000 chunks here; e5-small is the largest model that can
  index the 21k-document corpus C (201k chunks) on this box. Static embeddings (potion, model2vec) index
  the same corpus in 10 minutes and, fused with BM25, beat BM25 alone.
* Concurrency kills throughput: several torch jobs on 4 cores spin on OpenMP locks (10-40× slowdowns
  measured); one job at a time with all threads (`run_queue.sh`) is the only sane mode on this hardware.
* gte-multilingual-base and the Belgian ModernBERT embed model do not load on transformers 5.x.

### 3.4 Fusion and reranking (`03_hybrid_rerank`, `04_lancedb`)
* RRF never beats the stronger leg; convex fusion of min-max-normalised scores does (+0.013 on A with
  bge-m3; +0.02 on C with potion) but the weight is corpus-dependent (0.5 on A, 0.3 on C).
* A multilingual cross-encoder on the top-30 candidates is the biggest single quality lever after
  normalisation: bge-reranker-v2-m3 lifts e5-small hybrid from 0.598 to **0.703** on A and from 0.621 to
  **0.703** on the 21k-document corpus C (hit@1 0.48 → 0.61); over plain BM25 candidates on C it gives
  0.577 → 0.696. When the first stage is already strong (bge-m3 convex on A, 0.691) the reranker no longer
  raises MRR (0.681) but still improves nDCG@5 (0.758 → 0.782) and hit@5. Cost: 20–24 s/query on this CPU
  (≈0.7 s per pair), sub-second on a GPU. The small mMARCO MiniLM reranker is inconsistent: it lowers MRR on
  A, but is the best option on B (0.522 vs 0.517 for bge) where candidates are short article chunks.
* Fusion choice depends on the legs: convex (min-max) wins when both legs are decent (A, C), RRF wins when
  one leg is weak (B: BM25 0.34 vs dense 0.44 → convex 0.38, RRF 0.457). Validate per corpus.
* Candidate depth 30 is enough (recall@10 of the hybrid candidates is already 0.83–0.97).

### 3.5 Structure-aware retrieval (`05_llamaindex`)
* Hierarchical auto-merging and sentence-window retrievers **do not help** on legal articles (A: 0.51 and
  0.47 vs 0.53 for a plain splitter); merged parents average children scores and demote the right document.
* The one thing that helped on B was accidental: 128-token leaves are token-safe and score 0.486, the best
  dense number on B — again a chunk-length effect, not structure.
* Framework friction: hidden OpenAI defaults (`Settings.llm`, `Settings.embed_model`), tiktoken chunk
  counting, metadata silently subtracted from chunk size, nltk/uv hard-link incompatibility, 120 MB JSON
  vector store. Verdict: not worth adopting for the MCP tool.

### 3.6 Embedded engines (`04_lancedb`, `06_txtai`)
* **LanceDB** (0.39): zero server, DB = directory, native BM25 FTS with `language="French"` (+0.11 MRR over
  the default English stemmer on A), hybrid with RRF, reranker plug-in contract of ~25 lines, SQL `where`
  filters with prefilter on vector/FTS/hybrid, 7–30 ms brute-force queries at 8k rows, IVF-PQ only loses
  recall at this size. Gotchas: tantivy removed, deprecated `create_fts_index`, `list_tables()` object,
  versions pile up until `optimize()`, shipped CrossEncoderReranker unusable on CPU with big models.
* **txtai** (9.13): one object, save/load, SQL over metadata, but fusion mode is an implicit side effect of
  `scoring.normalize` (convex default is worse than dense alone on B; RRF/BB25 fix it), no French stemmer
  (−0.04…−0.10 MRR vs bm25s), reranker pipeline untunable (batch 1, no truncation). Fine for prototyping,
  needs care.
* Both are fit to sit in-process behind FastMCP; LanceDB is the better default for this project.

### 3.7 Hosted frameworks on paper (`07_frameworks_assessment`)
* **Onyx**: 11 containers (Postgres, OpenSearch, Redis, MinIO, two model servers…), 10–16 GB RAM, Docker
  only; its search API and MCP tool run the full Onyx LLM pipeline and return merged 512-token sections
  without scores; self-hosted embedding list stops at e5-base; English keyword analyzer; tag-only filters.
  **Not a fit** for an LLM-free, article-cited retrieval tool.
* **RAGFlow** is the only platform with an LLM-free retrieval API and MCP tool, but needs Docker, ≥16 GB,
  ES/Infinity + MySQL + Redis + MinIO and an external embedding server; French tokenisation unverified.
  Keep as the "platform with UI" fallback.
* **LightRAG** is pip-installable and can return raw context, but its graph indexing costs one LLM call
  per chunk and adds nothing to article-precise citation — an experiment for later, with DeepSeek.
* GraphRAG (maintenance mode, LLM-driven), Verba (archived), Kotaemon (dormant), Dify (restricted
  licence, big stack), AnythingLLM (no hybrid/reranker) are out.

### 3.8 Corpus cleanup and region filters (`08_corpus_b_cleanup`)
* Stripping amendment-history preambles: BM25 on B 0.346 → 0.372 (hit@1 0.20 → 0.275); with token-safe
  chunks it also helps dense retrieval (e5-small 0.438 → 0.466, e5-base 0.469).
* City→region mapping + region filter is correct (fixes the "other region's twin article" cases) but
  nearly neutral until the vocabulary gap is closed by a reranker; it is cheap metadata filtering in any store.

### 3.9 The 21k-document corpus (`09_corpus_c`)
* French-normalised BM25 is already strong (0.577; questions on documents with descriptive titles are easy).
* Static potion embeddings alone are weak (0.315) but potion + BM25 convex 0.3 gives 0.595 at ~zero cost.
* The corpus needs ingestion-policy work that no retriever can compensate: Dutch bodies flagged `fr`
  (≈ half of the rulings), yearly triplication of CIR 92 articles and regional quadruplication of codes,
  topic-less titles (rulings, PQs, Rép. RJ), non-tax noise, abrogated texts, TOC-only documents.
* e5-small (3.3 h to encode 201k chunks on 4 cores) alone is weaker than BM25 here (0.433 vs 0.577) —
  the questions were written from documents with descriptive titles, which favours lexical search — but
  convex fusion 0.5 gives 0.621 and the cross-encoder on top gives **0.703** (hit@1 0.61, recall@10 0.89).
  Reranking BM25 candidates alone already reaches 0.696: on a corpus this size, French BM25 + reranker is a
  legitimate no-embedding baseline, and the dense leg mainly adds recall for paraphrased questions.

## 4. Recommendation

**Stack for the MCP server (prototype now, scales to 100k docs):**

1. **Parsing / metadata**: keep the Fisconet+ markdown + the article parser; add per-document
   `language` (detect NL bodies), `region`, `income_year` / `valid_from`, `document_type`, `code`, `article`
   and drop or collapse yearly duplicates. Strip amendment preambles (exp 08). Chunk at ≤ 1,200 chars with
   title + heading path prefixed.
2. **Lexical leg**: bm25s (or LanceDB's French FTS) with French Snowball stemming, French stopwords + a
   question-word list. This alone is the baseline to beat and costs nothing.
3. **Dense leg**: `intfloat/multilingual-e5-base` (best quality/cost on CPU: 0.64 on A, 240 s per 1k chunks)
   or `BAAI/bge-m3` when a GPU is available (0.68, best recall). For very large corpora on CPU, static
   `potion-multilingual-128M` + BM25 is a credible fast tier.
4. **Fusion**: convex fusion of min-max scores (weight ~0.3–0.5, validated per corpus), RRF as fallback.
5. **Reranker**: `BAAI/bge-reranker-v2-m3` on the top-30 (the largest measured gain; 2–4 s/query on CPU,
   sub-second on GPU). Skip small rerankers.
6. **Store**: LanceDB embedded (directory next to the MCP server; SQL metadata filters for region /
   document type / year; no service to run). Qdrant stays a valid choice for the server deployment later —
   the MCP `search`/`fetch` contract does not change.
7. **Agentic layer (when DeepSeek is available)**: tools `search(query, region?, document_type?, year?)`
   returning chunks with exact `code:article` ids and scores, `fetch(id)` returning the full article,
   and query rewriting (layman → legal vocabulary, region/city detection) driven by the LLM — the
   vocabulary gap is the dominant failure mode on B and C and is exactly what an LLM-side rewrite fixes.

**Not recommended**: Onyx / RAGFlow as the retrieval backbone; LlamaIndex hierarchical or sentence-window
retrievers; MiniLM-class embeddings; running several embedding jobs concurrently on a small CPU box.

## 5. Reproducing

```bash
cd experiments/00_pdf_parsing && uv sync && uv run python parse_pdfs.py       # corpus B
cd ../01_bm25 && uv sync && uv run python run_bm25.py A && uv run python run_bm25.py B
cd ../02_dense_sweep && uv sync && uv run python run_sweep.py --corpus A --models e5-base --chunkers fixed1500_title
cd ../03_hybrid_rerank && uv sync && uv run python run_hybrid.py --corpus A --model e5-base --chunker fixed1500_title --rerankers bge-reranker-v2-m3
cd ../09_corpus_c && uv sync && uv run python run_corpus_c.py --runs bm25_doc,bm25_chunk
cd .. && ./run_queue.sh                                                          # everything CPU-heavy, sequentially
```
