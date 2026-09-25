# 10 — Alternatives to the current retrieval stack: a critical, evidence-based survey

*Desk research only (no code, no runs). Written 2026-09-25 for the Belgian tax-law RAG project: French legal
text (codes/articles, circulaires, rulings, court decisions, PQs), 21k documents now, ~100k later, retrieval
exposed through the FastMCP server, open-weight models only, 4-core CPU box, and **no LLM available for the
experiments yet** (DeepSeek comes later). Every number below was read from the cited source (Sources § 7);
statements that could only be checked through search snippets or secondary summaries are marked **[unverified]**.*

**Where we stand (from `EXPERIMENTS.md`):** tuned French BM25 alone reaches MRR 0.736 on the 91-doc corpus A
(0.695 in the table; the higher number is the best grid point) and 0.577 on the 21k-doc corpus C; e5-small +
BM25 fusion + bge-reranker-v2-m3 gives 0.70 on A and C. Failure modes: layman-vs-statute vocabulary,
near-duplicate regional/yearly editions of the same article, flattened tables, topic-less titles.

**One-paragraph verdict.** The legal-IR literature is unusually consistent with what we measured: zero-shot
dense models rarely beat a well-tuned BM25 on statute/case retrieval (BSARD, bBSARD, LLeQA, CLERC, CJEU
paragraphs), hybrid + reranking is the best *zero-shot* configuration, and the only thing that reliably moves
the needle by a large margin is **in-domain training** (BSARD MRR@100 26 → 47–50, LLeQA R@10 23 → 61 with a
110M CamemBERT). Graph-RAG frameworks need an LLM at index time and, once evaluation biases are removed, do not
beat plain hybrid RAG on factual QA; the graph that *does* help on statutes is the cheap one we can build without
an LLM (legislative hierarchy + cross-references), used as a feature/expansion, not as a KG store. The shortlist in
§ 6 therefore prioritises (1) structure/metadata/duplicate handling, (2) small in-domain fine-tuning with the
Belgian datasets that already exist (BSARD, LLeQA), (3) learned-sparse and late-interaction retrievers that run
on CPU, and (4) cheap query expansion — in that order.

---

## 1. Alternatives to a semantic vector database

### 1.1 Inverted-index engines (all run BM25 the way we already do; the question is fields, ops and scale)

| engine | what it is | French support | embedded? | evidence / notes |
|---|---|---|---|---|
| **Tantivy** (`tantivy-py`) | Rust library "inspired by Lucene": BM25 ("the same as Lucene"), phrase queries, facets, multi-field with per-field boosts, block-WAND, MIT | stemming for 17 Latin languages incl. French; custom tokenizers | yes (library, not server) | README claims ≈2× Lucene search latency on its own benchmark, "your mileage WILL vary". Sensible production engine for a single box at 100k docs. |
| **Lucene / Elasticsearch / OpenSearch** | JVM server | French analyzer (elision, stemmer) | no (JVM + service) | ES ≥ 7.13 `combined_fields` = Lucene `CombinedFieldsQuery` = **BM25F** (term-centric multi-field scoring); only BM25 similarity supported **[unverified — ES docs seen via search only]**. OpenSearch adds the neural-sparse plugin (§ 1.2). Overkill for one box unless we want ES-native BM25F + collapse. |
| **Vespa** | C++/Java engine: WAND-accelerated BM25, phased ranking, native ColBERT embedder and late-interaction tensor ranking, pyvespa | yes (linguistics per language) | no (needs the Vespa container/JVM stack) | Best "all retrieval paradigms in one engine" option, but not embeddable; a single-node deployment is still a service to operate. Not recommended before 100k+ docs and a real ops budget. |
| **DuckDB FTS** | `create_fts_index(...)` builds an inverted index in DuckDB; `match_bm25(k, b, conjunctive, fields)` | `stemmer='french'`, custom stop-word table, `strip_accents`, `lower`, `ignore` regex | yes | Limitation from the docs: the FTS index is **not updated when the table changes**; you drop and recreate it. Fine for a batch-rebuilt corpus, awkward for incremental crawls. |
| **SQLite FTS5 + sqlite-vec** | FTS5 inverted index + brute-force/quantised vector search, RRF in pure SQL | FTS5's `unicode61` tokenizer folds diacritics; the built-in `porter` stemmer is English-only, so French stemming needs a custom tokenizer **[unverified]** | yes (single file) | Willison (2024-10-04) shows RRF / FTS-first / re-order-by-semantics patterns in SQL; the point he stresses is that FTS and vector scores are incomparable, hence rank fusion. Simplest possible deployment for an MCP server; French normalisation would have to be done in Python before indexing (as our `bm25s` pipeline already does). |
| **LanceDB** (exp 04) | vector + FTS + hybrid + SQL filters | French FTS worked in exp 04 | yes | Already prototyped (MRR 0.703 with reranker on A). Stays a valid choice. |

Takeaway: none of these changes ranking quality by itself — BM25 is BM25. They matter for **fields/boosting,
filters, collapsing and ops**. For our scale, Tantivy (via `tantivy-py` or LanceDB) or DuckDB FTS is enough; ES/Vespa
buy BM25F and multi-stage ranking that we can also implement in Python over 21k–100k docs.

**BM25F / field boosting.** BM25F (Robertson et al., 2004) sums per-field term frequencies with field weights
before saturation instead of summing per-field BM25 scores; ES `combined_fields` and DuckDB `fields=` expose it.
There is no strong recent benchmark literature on BM25F gains for legal text; the relevant evidence for *us* is
indirect: (a) exp 02's title-prefix trick (+0.10 MRR for e5-base on A) shows title tokens carry signal, and (b) the
Summary-Augmented-Chunking paper (§ 3.6) shows that "Document-Level Retrieval Mismatch" — retrieving from the
wrong but structurally similar document — is halved by injecting document-level context into each chunk. A
pseudo-title field (code + article number + chapter heading + document type + year + region) with a separate
weight is the no-LLM version of that.

### 1.2 Learned sparse retrieval (SPLADE family)

* **SPLADE-v3** (Naver, 2024-03): MS MARCO MRR@10 40.2, BEIR-13 mean nDCG@10 **51.7** (SPLADE++SD 50.7); the
  *inference-free* `SPLADE-v3-Doc` (no query encoder, documents only) drops to 47.0 and `-Lexical` (no query
  expansion) to 49.1 — "even a minimal amount of computation on the query side is important". All SPLADE-v3
  checkpoints are **English BERT/DistilBERT**; they do not apply to French text.
* **CPU cost** (Lassance & Clinchant, SIGIR 2022): with L1 query regularisation, separate encoders and a BERT-tiny
  query encoder, efficient-SPLADE reaches "less than 4 ms difference" from BM25 on PISA single-core with < 10 %
  MRR@10 loss; a DistilBERT query encoder alone costs ≈45 ms average CPU latency vs 0.7 ms for BERT-tiny. Document
  encoding remains a full transformer pass over the corpus (one-off).
* **Multilingual options that cover French**
  * `opensearch-neural-sparse-encoding-multilingual-v1` (model card 2024-11-07; OpenSearch v3 blog 2025-09-25):
    160M BERT-based, Apache-2.0, 15 languages incl. French, **inference-free**: documents are encoded by the
    model, queries are "just a tokenizer and a weight look-up table" (IDF). MIRACL fr nDCG@10 **0.558** (card:
    BM25 0.115 in their setup); average over languages 0.629 vs 0.305 BM25; a pruned variant (ratio 0.1) keeps
    0.626 with a smaller index. Usable outside OpenSearch with plain `transformers` (the card gives the code):
    store the sparse doc vectors in a scipy matrix and dot-product at query time — zero query-side model cost.
  * **BGE-M3 sparse head** (paper table, MIRACL fr nDCG@10): BM25 45.8 (their own BM25), mE5-large 54.5, M3 dense
    57.8, **M3 sparse 35.5**, M3 multi-vector 59.0, dense+sparse 57.6, all three 60.7. The sparse head alone is
    *worse than BM25 on French*; it only helps in fusion. And bge-m3 was "too slow on CPU" in exp 02 for corpus B/C.
  * **MILCO** (ICLR 2026, arXiv v2 2026-03-19): 560M LSR model on the bge-m3-unsupervised backbone with an
    English-pivot "LexEcho" head; reports MIRACL fr nDCG@10 **81.2** vs BM25 45.8, M3-sparse 65.4 and OpenSearch
    multilingual 55.8 (the M3-sparse number disagrees with the BGE-M3 paper's 35.5 — different evaluation setup;
    treat both with caution). Checkpoints "released at the same repository" **[unverified: not checked on HF]**;
    560M on CPU means the same cost problem as bge-m3.
  * **French legal SPLADE**: `maastrichtlawtech/splade-legal-french` (CamemBERT-base, 110M, MIT, trained on LLeQA
    after pre-finetuning on mMARCO-fr). See § 3.3 for its numbers: strong in-domain (R@100 0.687 on LLeQA test vs
    BM25 0.537), but its CPU latency in the authors' table is **0.61 s/query** vs 0.14 s for BM25 (the SPLADE query
    encoder is a full CamemBERT).
* **Caveat on "BM25 on French MIRACL"**: the three sources above report BM25 fr nDCG@10 as 0.115, 0.183 (MIRACL
  paper, Anserini French analyzer) and 0.458 (BGE-M3 paper). The spread is the analyzer, not the corpus — exactly
  the lesson of exp 01 (French normalisation moved BM25 from 0.48 to 0.70 on A). Any published "×3 over BM25" claim
  for French should be read as "over an untuned BM25".

### 1.3 Late interaction (ColBERT)

* **ColBERTv2 / PLAID**: BEIR average nDCG@10 49.6 vs BM25 44.0 (as tabulated in the Jina-ColBERT-v2 paper);
  PLAID makes CPU retrieval practical (the French legal ColBERT below runs at 0.14 s/query on CPU with PLAID, same
  as BM25, but with a 6.7× text-size index).
* **jina-colbert-v2** (2024-09): Jina-XLM-RoBERTa backbone, 89 languages, Matryoshka token dims 64–128, 8k
  context; BEIR 53.1; MIRACL fr **54.1**; mMARCO-fr MRR@10 **33.5** vs ColBERT-XM 26.9. Weights on HF are
  **CC-BY-NC-4.0** to the best of my knowledge **[unverified — check the model card before any commercial use]**.
* **ColBERT-XM** (Maastricht, 2024-02, COLING 2025): XMOD modular backbone trained on **English only** (6.4M
  triples), zero-shot mMARCO-fr MRR@10 26.9 vs BM25 15.5, mE5-base 30.3, mColBERT 28.9, mT5 cross-encoder 30.2.
  Open (MIT) and cheap to extend; slightly below mE5-base on French.
* **French legal ColBERT**: `maastrichtlawtech/colbert-legal-french` (CamemBERT-base, MIT, LLeQA-trained): LLeQA
  test R@10 0.432 / R@100 0.679 vs BM25 0.367 / 0.537 (in-domain), but zero-shot (mMARCO-fr only) it was *below*
  BM25 (R@10 0.148). Late interaction is not magic on statutes without in-domain data.
* **Tooling**: **PyLate** (LightOn) trains ColBERT models with the sentence-transformers API and ships PLAID /
  FastPLAID indexes; **pylate-rs** does CPU/WASM *encoding only* (model init 0.07 s vs 2.06 s), retrieval needs
  `fast-plaid`. A CPU-native multi-vector index ("TACHIOM") was mentioned in search results **[unverified]**. For
  21k docs the pragmatic use is **late-interaction re-ranking of the top-100** from BM25/hybrid (MaxSim over
  pre-computed token vectors is milliseconds), replacing part of the 20 s cross-encoder budget.

### 1.4 Pseudo-relevance feedback (RM3 / Rocchio)

* Lin (2019, "The Neural Hype and Comparisons Against Weak Baselines") showed most neural rankers of the time did
  not beat Anserini's BM25+RM3 on Robust04; Waseda's Anserini runs found BM25PRF with default parameters beats
  vanilla BM25 on Robust04 and that tuning did not help further **[both from search snippets]**. RM3 is a free,
  CPU-only, no-model technique, and it directly targets the vocabulary gap (it adds statute words from the top-k
  feedback documents to a layman query).
* Risks for us: (a) queries are short natural-language questions, so PRF depends on the first-pass top-k being
  right — on corpus C hit@1 is 0.59 with reranking, ~0.5 for BM25 alone; (b) the corpus is full of near-duplicate
  editions, so PRF will reinforce the duplicate cluster (harmless if we collapse duplicates first, § 4.2); (c) no
  French-specific RM3 evidence was found (MIRACL/mMARCO papers publish BM25 and hybrid only). `bm25s` has no RM3;
  Pyserini has RM3/Rocchio but needs Java; a Rocchio expansion over `bm25s` term vectors is ~50 lines.

### 1.5 Document expansion (doc2query / doc2query--)

* doc2query-- (ECIR 2023): filtering generated queries with a relevance model improves docT5query effectiveness by
  up to 16 %, cuts query time 23 % and index size 33 %. On **BSARD**, docT5query lifted BM25 R@100 from 49.3 to
  51.7 (G-DSR paper, Table 2) — a real but small gain, far below in-domain dense (77–84).
* For French there is `doc2query/msmarco-french-mt5-base-v1` (mT5-base, ~580M) and a 14-language variant
  **[model cards seen via search only]**. It is a seq2seq generator, not an LLM, so it *is* testable now, but
  generating 20–40 queries for each of ~150k chunks with mT5-base on 4 CPU cores is days of compute; feasible on a
  subset (e.g. the 9.8k corpus-B articles). Expectation: modest; the BSARD number is the best prior.

### 1.6 Learning to rank (LambdaMART)

* LightGBM/XGBoost `lambdarank` is the standard; XGBoost's LTR docs recommend `rank:ndcg` or `rank:pairwise` with
  the `mean` pair method for **small datasets** to maximise effective pairs. I found no study quantifying
  LambdaMART with ~100 labelled queries; with our 133 questions the honest use is a **few-feature model (≤10
  features: BM25 score, dense score, late-interaction score, title-field match, doc type, year/region match,
  duplicate-group size, citation in-degree) with leave-one-question-out CV**, and only to *combine* signals, not
  to learn text relevance. Treat it as a tuned fusion, which "Know When to Fuse" (§ 3.3) shows is what makes fusion
  of in-domain models work at all.

---

## 2. Graph databases and graph-based retrieval

### 2.1 Property-graph / RDF stores (if we need one at all)

| store | status (2026) | embedded? | notes |
|---|---|---|---|
| **Kuzu** | GitHub repo **archived 2025-10-10** after Apple acqui-hired the team (gdotv, 2026-05-28); existing releases still work | yes | Do not start new work on it. Community fork **LadybugDB** (multi-label nodes, Arrow/DuckDB/Parquet integration) is gdotv's pick to carry it forward. |
| **FalkorDBLite** | `pip install falkordblite`, Python ≥ 3.12 | "embedded": it spawns a local Redis+FalkorDB subprocess over a Unix socket | Cypher; API mirrors `falkordb-py` **[docs via search only]**. |
| **pyoxigraph** | active | yes (RocksDB or in-memory) | Full SPARQL 1.1 (query/update/federated), Turtle/N-Triples/JSON-LD I/O **[docs via search only]**. The natural fit if we ever model the legal corpus as RDF (ELI/Fisconet identifiers). |
| **DuckPGQ** | DuckDB extension, SQL/PGQ | yes | Mentioned as the DuckDB-side successor for embedded graph queries **[unverified]**. |
| **Neo4j / Memgraph / FalkorDB server** | servers | no | Fine, but a service to run; nothing in our workload needs Cypher at scale. |

For the graph we actually need (article → parent chapter/title/book; article → cited article; circulaire →
articles it comments; yearly/regional edition → canonical article) a **pandas/NetworkX adjacency** or two SQL
tables in DuckDB/SQLite is sufficient at 100k nodes; PageRank over 100k nodes takes seconds in NetworkX/scipy.

### 2.2 The graph-RAG family — what needs an LLM at index time

| method | LLM at index time | LLM at query time | designed for |
|---|---|---|---|
| Microsoft GraphRAG (2024-04) | yes: entity/relation extraction per chunk + community summaries (thousands of calls; the "global" mode also spends ~2M tokens per query) **[cost figures from secondary sources]** | yes | query-focused *summarisation* over a whole corpus, not fact lookup |
| LightRAG | yes (entity/relation extraction; ~400 s to index six regulations with GPT-4o in the legal benchmark) | yes | local/global/hybrid/mix modes |
| HippoRAG 2 (2025-06) | yes: OpenIE triples with an LLM (9.2M tokens, ≈100 min for 11.6k passages) | light (PPR + dense) | multi-hop / associative recall |
| RAPTOR | yes: recursive cluster summaries | no | long documents / thematic questions |
| KG-RAG / citation-graph retrieval on legal text (G-DSR, CuSINeS, QABISAR, Hier-SPCNet, CRAwLeR) | **no LLM** for the graph (structure and cross-references are parsed); some train a GNN or use an LLM only to *generate* eval queries | no | statute / case retrieval |

### 2.3 Evidence that graph retrieval beats hybrid + reranker (it mostly does not, on factual QA)

* **RAG vs GraphRAG, systematic evaluation** (Han et al., v3 2026-03-04; Llama-3.1-8B): single-hop **NQ F1 RAG
  64.78 vs Community-GraphRAG-local 63.01**; HotpotQA RAG 60.04 vs HippoRAG2 63.01; MultiHop-RAG RAG 67.02 vs
  Community-GraphRAG-local 69.01. Index construction on MultiHop-RAG: RAG 135 s, Community-GraphRAG 5,560 s,
  KG-GraphRAG 7,702 s. Conclusion: "complementary behaviours rather than a consistent winner"; graph helps
  multi-hop/summary, hurts detail-oriented factual queries. Also documents strong position bias in LLM-judge
  summarisation comparisons.
* **HippoRAG 2 paper** (own numbers, GPT-4o-mini reader): average F1 59.8 vs NV-Embed-v2 dense 57.0 (BM25 39.5);
  NQ 63.3 vs 61.9 (+1.4), PopQA 56.2 vs 55.7; the gains are on 2Wiki (71.0 vs 61.5) and MuSiQue (48.6 vs 45.7),
  i.e. multi-hop; query time 1.2 s with 9.9 GB GPU memory.
* **"How significant are the real performance gains?"** (Zeng et al., 2025-06): after removing position/length/
  trial bias and using graph-text-grounded questions, LightRAG's reported 66.70 % win rate vs NaiveRAG on the
  Agriculture set becomes **39.06 %**, and "NaiveRAG performs better than LightRAG"; tie rates > 20 %; swapping
  answer order alone moves win rates by > 30 points. Microsoft's own fine-grained GraphRAG (FGRAG) is best "below
  10 % in win rate" over NaiveRAG — attributed to concise entity contexts and **PageRank re-ranking**, "a
  high-quality knowledge graph and proper re-ranking … are beneficial".
* **Legal KG-RAG benchmark** (Ongris et al., CEUR Vol-4079, 2025; EU directives + Indonesian regulations, GPT-4o,
  Ragas answer accuracy): **Naive RAG 0.82** (86.5 % good answers, 1.76 s/query, 5.9 s indexing) vs LightRAG-Mix
  0.86 (9.3 s/query, 397 s indexing), LlamaIndex-Hybrid 0.85, HippoRAG 2 0.78, LightRAG-Local 0.65, Nano-GraphRAG
  0.65, LlamaIndex property-graph 0.57. "KG-only systems often underperform due to their inability to fully capture
  the semantics of the text"; the hybrids that win are the ones that keep the text index.
* **GraphRAG-Bench** (2025-06): college-textbook reasoning; the authors report that a pure "knowledge graph
  performs suboptimally" versus text-preserving structures and that KG construction costs the most tokens.

Honest reading for our use case (single-hop statutory/procedural questions, factual, citation-critical): **no
published evidence that GraphRAG/LightRAG/HippoRAG beats hybrid + cross-encoder; several controlled evaluations
show ties or losses at 10–50× the indexing cost, all requiring an LLM.** Plan it only for the later "global"
questions ("what changed in 2024 for company cars?") once DeepSeek is available, and only as HippoRAG-2-style
(text-preserving) rather than KG-only.

### 2.4 Graphs that *do* help on statutes, without an LLM

* **G-DSR** (Louis et al., EACL 2023, BSARD test): BM25 R@100 49.3 / mAP 16.8; docT5query 51.7; DPR (mMARCO-fr
  pre-finetuned) 77.9 / 45.4; dense statute retriever DSR 77.1; **G-DSR (GNN over the legislative hierarchy
  code→book→title→chapter→section→article) 84.3 / mAP 47.1**; the GNN also improved rank-aware metrics of the
  best DSR "by ∼12 %", i.e. it works as a re-ranker. The graph is parsed from the codes; the GNN is trained on the
  886 BSARD training questions (GPU, but a 262M model).
* **CuSINeS** (LREC-COLING 2024): using the hierarchy + sequential position of articles to schedule hard negatives
  raises DSR R@100 77.1 → 82.6 and DSR+GNN 80.2 → 83.2. **QABISAR** (2024-12): query–article bipartite graph +
  distillation, 83.7 R@100. All three say the same thing: *statute structure is a strong training signal.*
* **Hier-SPCNet** (IPM 2022, Indian case similarity): precedent citation network augmented with statutes; best
  network+text hybrid is +11.8 % over the best text-only method in correlation with expert judgements.
* **Reference-network statute retrieval** (Vuong et al., Applied Intelligence 2025, COLIEE 2021/2022): models
  articles as a reference network with a local window to trade recall against noise **[paywalled; abstract via
  search only]**.
* **CRAwLeR** (2026-06; Danish/Polish statutes): cross-reference-aware chunk retrieval benchmark; with
  Anthropic-style contextualisation BM25 R@10 0.392/0.470 vs BGE-M3 0.551/0.587; the remaining errors are
  attributed to the contextualising LLM, and "labelled context chunks routinely outrank" the target — i.e. the
  referenced article often ranks above the article that answers. Directly relevant to our "near-duplicate/
  related-article" confusions: retrieving the *neighbourhood* and letting the reader see both is the practical
  answer.

Implication: parse `art. 90, 1°`, `article 171 CIR 92`, `§ 2, alinéa 3`, code/book/title headings and the
"commente l'article …" references of circulaires now (regex; the corpus already has these strings), store a
small adjacency, and use it for (a) neighbour expansion of the top-k, (b) an in-degree/PageRank prior feature,
(c) duplicate-edition grouping. A trained GNN (G-DSR) is a later, GPU step.

---

## 3. Legal-domain IR evidence

### 3.1 BSARD — the Belgian, French statutory dataset (most relevant; same jurisdiction and language)

* Louis & Spanakis (ACL 2022): 22,633 articles from 32 Belgian codes, 1,108 citizen questions labelled by jurists;
  median article 495 words, 25 % > 1,026 words. Test set: TF-IDF R@100 40.1 / MRR@100 13.0; **BM25 51.3 /
  24.6**; word2vec siamese 49.4 / 21.5; zero-shot CamemBERT siamese 4.2 / 2.0 (!); fine-tuned siamese CamemBERT
  71.6 / 43.5; fine-tuned two-tower CamemBERT (hierarchical article encoder) **74.8 / 42.5**. The paper names the
  lexical gap between layman questions and statute wording as the reason BM25 stalls — our failure mode #1.
* BM25 needs tuning here too: Louis et al. used k1 = 2.5, b = 0.2 on BSARD (long articles, low length
  normalisation) — the same direction as our exp 01 grid.
* **bBSARD** (Lotfi et al., COLING 2025) French test subset, R@100 / MRR@100 / nDCG@10: BM25 **51.8 / 26.0 /
  21.5**; word2vec 49.9 / 21.5 / 17.3 (but R@500 71.1 > BM25 65.5); mE5-small 46.3 / 23.5 / 18.5; mE5-base 47.6 /
  26.3 / 21.9; mGTE 57.5 / 30.1 / 24.1; mE5-large 55.3 / 34.3 / 28.1; **BGE-M3 60.8 / 31.4 / 25.4**;
  jina-embeddings-v3 64.1 / 34.5 / 27.1; E5-mistral-7B 69.4 / 40.2 / 34.8; bge-multilingual-gemma2 (9B) 71.4 /
  43.7 / 36.4; voyage-3 77.7 / 54.6 / 46.0; text-embedding-3-large 75.5 / 46.5 / 40.5; **fine-tuned CamemBERT-base
  (111M) 77.1 / 47.0 / 44.3; fine-tuned FlauBERT-base 78.2 / 49.8 / 46.7**. Conclusions in the paper: "BM25 remains
  a competitive baseline compared to many zero-shot dense models" (it beats every open model ≤ 300M on MRR), and
  fine-tuning a small language-specific encoder on the ~900 training questions matches or beats proprietary
  embeddings. This is the single strongest datapoint for our shortlist: **e5-small/e5-base zero-shot ≈ BM25 on
  Belgian French statutes; a 110M French encoder fine-tuned in-domain doubles MRR.**
* Graph/structure results on BSARD: § 2.4 (G-DSR 84.3 R@100, CuSINeS, QABISAR).
* Licence: BSARD and LLeQA are **CC-BY-NC-SA** (evaluation/research only, per the lexfr-embed README).

### 3.2 LLeQA (French, Belgian, long-form legal QA; AAAI 2024)

1,868 expert-annotated questions with answers grounded in ~27k statutory articles. Dev-set retrieval: BM25 R@5
17.4 / R@10 22.8 / MRR@10 22.0; mE5-base 15.4 / 21.7 / 25.8; mE5-large 16.5 / 26.7 / 28.3; **fine-tuned
CamemBERT-base bi-encoder 48.6 / 60.6 / 60.0**. Same lesson as BSARD, larger effect.

### 3.3 "Know When to Fuse" (Louis et al., 2024-09; French legal hybrid retrieval) — the paper closest to exp 03

* Zero-shot on LLeQA test (models trained on mMARCO-fr or general multilingual data), R@10 / R@500:
  **BM25 (k1 2.5, b 0.2) 0.367 / 0.672**; mE5-small 0.174 / 0.611; mE5-base 0.157 / 0.653; mE5-large 0.194 /
  0.695; BGE-M3 dense 0.325 / 0.734; DPR-fr 0.146; SPLADE-fr 0.107; ColBERT-fr 0.148; monoBERT-fr cross-encoder
  0.290. "Surprisingly, BM25 outperforms all neural models in this specialized context." Best zero-shot fusions
  (normalised score fusion with tuned weights): BM25+SPLADE 0.372, BM25+ColBERT 0.397, BM25+DPR+ColBERT 0.407 —
  i.e. **+4 points R@10 over BM25**, the same order as our fusion gains on C (0.577 → 0.621).
* In-domain (fine-tuned on LLeQA train), test R@10 / R@100: BM25 0.367 / 0.537; SPLADE-LEX 0.434 / 0.687;
  **DPR-LEX 0.558 / 0.801**; ColBERT-LEX 0.432 / 0.679; monoBERT-LEX 0.473 / 0.746. Pre-finetuning on mMARCO-fr
  before LLeQA adds +1–3 % recall for bi-encoders.
* Fusion **after** in-domain training: "around 70 % of these combinations lead to deteriorated performance"; only
  27/88 improve and 23 of those need in-domain-tuned weights. Our RRF-everything habit should be re-tested once
  any component is fine-tuned.
* CPU latency (s/query, LLeQA index): BM25 0.142, DPR 0.057, SPLADE 0.609 (query encoder), ColBERT+PLAID 0.142,
  monoBERT re-ranking 1k candidates **184.7** (GPU 4.5). Index size vs text: BM25 0.2×, SPLADE 1.1×, DPR 2.9×,
  ColBERT 6.7×.

### 3.4 CLERC (US case law, 2024) and CJEU paragraphs (2025)

* CLERC/doc: BM25 R@10 11.7 / R@1k 48.3 / nDCG@10 5.4 beats every zero-shot neural model (E5-v2 8.4 / 42.3;
  Contriever 9.3 / 41.4; **ColBERTv2 2.2 / 17.6**; jina-colbert-v1 2.2 / 16.1); fine-tuned DPR 18.6 / 63.1;
  fine-tuned LegalBERT-DPR 23.2 / 68.5. "Zero-shot models are particularly bad due to distribution shifts."
* Mori et al. (2025-06, CJEU passage retrieval): BM25 R@5 63.6 / MRR 0.579 beats off-the-shelf dense models in 4
  of 7 metrics (only OpenAI ada-2 wins R@1/MAP/MRR); a fine-tuned legal SBERT wins overall; BM25 is better "in more
  nuanced scenarios where repetition and verbatim quotes are less prevalent and in longer queries".

### 3.5 Reasoning-focused legal retrieval (Bar Exam QA / Housing Statute QA, 2025-03)

Query–gold lexical similarity is 0.07–0.09 (vs 0.26 on NQ); BM25 R@10 5.0 vs E5-large-v2 7.0 on Bar Exam QA; a
structured legal-reasoning query expansion adds +6.3 R@10 to BM25 (LLM-generated). This is the extreme end of our
vocabulary-gap problem: when the question is a fact pattern, nothing lexical works and expansion is the lever.

### 3.6 LegalBench-RAG, SAC, COLIEE, LePaRD, MLEB, Swiss

* **LegalBench-RAG** (2024-08): 6,858 expert-annotated query→span pairs over 79M characters (US contracts,
  privacy policies, MAUD). Reported findings (from the paper's own summary and secondary write-ups; the full
  results tables were not re-read here **[unverified]**): recursive-character chunking beats fixed-size, and a
  generic Cohere reranker *hurt* — "the need for rerankers specifically trained on legal language".
* **Summary-Augmented Chunking** (NLLP 2025, on LegalBench-RAG): defines Document-Level Retrieval Mismatch (DRM),
  observed at > 20 % with plain chunking; prepending a document-level summary to every chunk roughly halves DRM and
  raises span precision/recall; a *generic* summary beat a legal-expert-guided one. Adding BM25 to the dense
  retriever reduced DRM (19.3 → 18.2 %) but lowered span precision (11.0 → 8.2 %). Needs an LLM for summaries —
  but the mechanism (global document context in every chunk) is exactly what a metadata/pseudo-title prefix gives.
* **COLIEE 2025** (overview, 2026-04): statute retrieval (Task 3) won by "initial-stage candidate retrieval →
  LLM-based cross-encoder re-ranking → multi-LLM verification"; case retrieval (Task 1) best F1 only 0.36,
  "multi-stage retrieval pipelines combining traditional IR with neural re-ranking" dominate. BM25 first stage is
  still the norm.
* **LePaRD** (ACL 2024): 4M+ judicial citations; best recall only 59 % on the 10k-passage version;
  classification-style retrieval worked best **[abstract via search only]**.
* **LLM-based embedders for prior-case retrieval** (2025-07): 7B-class embedders beat BM25 on four PCR datasets
  (English/Indian/Chinese-style long cases) — not Swiss, not French, and not CPU-feasible for us.
* **Swiss**: the Swiss Federal Supreme Court dataset (EMNLP 2025 findings) is a *summarisation* corpus (20k
  rulings, DE/FR/IT); I found no Swiss/French *retrieval* benchmark with published BM25-vs-dense numbers.
* **MLEB** (Isaacus, 2025-10): English-only (US/UK/AU/IE/SG/EU); no French track exists.
* **MTEB-French** (2024): includes BSARD and Syntec (collective-agreement articles) as retrieval tasks; among open
  models multilingual-e5, bge-m3, Solon-embeddings and sentence-croissant "stand out"; the strongest predictor of
  performance is having been trained for sentence similarity, not language specialisation.

### 3.7 French legal models with open weights

| model | type | training | licence |
|---|---|---|---|
| `maastrichtlawtech/dpr-legal-french` | bi-encoder, CamemBERT-base 110M | mMARCO-fr → LLeQA | MIT |
| `maastrichtlawtech/splade-legal-french` | learned sparse, CamemBERT-base | mMARCO-fr → LLeQA | MIT |
| `maastrichtlawtech/colbert-legal-french` | late interaction, CamemBERT-base | mMARCO-fr → LLeQA | MIT |
| `maastrichtlawtech/monobert-legal-french` | cross-encoder, CamemBERT-base | LLeQA | MIT |
| `maastrichtlawtech/legal-camembert-base`, `legal-distilcamembert` (68M) | MLM backbones on French legal text | — | (see cards) |
| `antoinelouis/colbert-xm`, `antoinelouis/splade-max-camembert-base-mmarcoFR`, `antoinelouis/dpr-*-mmarcoFR` | general French/multilingual retrievers | mMARCO-fr / English | MIT |
| `ghislaindelabie/lexfr-embed` | WIP: BGE-M3/Qwen3-0.6B + LoRA on LegalKit + DILA jurisprudence, evaluated on BSARD | — | Apache-2.0 code; no results published yet |

No French legal **reranker** other than `monobert-legal-french` was found; `bge-reranker-v2-m3` (MIRACL 69.3)
remains the strongest open multilingual reranker; jina-reranker-v3 (0.6B, listwise) scores 66.5 on MIRACL and
Qwen3-Reranker-0.6B is below bge-reranker-v2-m3 on BEIR **[both from search snippets]**.

---

## 4. Techniques testable now (no LLM) and mapped to our failure modes

| failure mode | technique | evidence | expected effect on us |
|---|---|---|---|
| layman vs statute vocabulary | in-domain fine-tuning of bi-encoder / cross-encoder (§ 4.4) | BSARD MRR 26 → 47–50; LLeQA R@10 23 → 61 | large, if Belgian-statute training transfers to Fisconet+ circulaires/rulings (same jurisdiction, same French; different genres) |
| | learned-sparse doc expansion (OpenSearch multilingual, inference-free) | MIRACL fr 0.558 vs BM25 (their) 0.115; SPLADE-v3-Doc 47.0 BEIR vs BM25 ~44 | adds statute synonyms to the *index* side; zero query cost; likely +2–5 MRR pts as a third fusion leg |
| | RM3/Rocchio PRF; hand lexicon (ATN, précompte, QFIE…) | Lin 2019; reasoning-benchmark +6 R@10 with structured expansion | modest (+1–4), cheap; risk of drift on wrong first hit |
| near-duplicate editions | canonical-article grouping + collapse; region/year filter (exp 08 already) | SAC paper's DRM; trillion-token-datastore dedup uses 13-gram Jaccard ≥ 0.8 post-retrieval **[snippet]** | directly removes the "right article, wrong edition" rank losses; evaluate at group level |
| topic-less titles / wrong document | pseudo-title + metadata field with BM25F weight; prefix in dense input (already +0.10 for e5-base on A) | SAC halves DRM with doc-level context; exp 02 title-prefix | medium; no model cost |
| tables flattened | row-wise linearisation "col=val; col=val" per row chunk; keep table caption in every row chunk | no direct IR paper found; standard practice in table-QA | fixes a class of misses at parse time |
| all | late-interaction re-ranking (ColBERT MaxSim over top-100) | ColBERT-fr CPU 0.14 s/q with PLAID; LLeQA in-domain R@100 0.68 | replaces part of the 20 s cross-encoder; quality between dense and cross-encoder |
| all | tuned-weight fusion / small LambdaMART instead of RRF | "Know When to Fuse": in-domain fusion only helps with tuned weights | small but free; needed once anything is fine-tuned |

### 4.1 Query expansion without an LLM
(a) Rocchio/RM3 over `bm25s` (§ 1.4); (b) static-embedding nearest neighbours of query terms (our potion/model2vec
model or fastText-fr) as weighted expansion terms — the classic word-embedding-QE line (TREC 2018 JARIR run,
Kuzi-style) reports small, inconsistent gains **[snippets only]**; (c) a **curated layman→statute lexicon** built
from our own failure analysis and `codes-administratifs.md` (e.g. "voiture de société" → "avantage de toute nature",
"impôt sur mon salaire" → "précompte professionnel"); (d) learned expansion on the document side (§ 1.2) which is
the principled version of (c).

### 4.2 Duplicate collapsing
Build a canonical id per article = (code, article number, paragraph) parsed from headings; keep edition metadata
(region, tax year, version date); at retrieval collapse to the best-scoring member (MaxP) and expose the siblings
in the MCP result; when the query names a region/year (exp 08 city→region map) filter, otherwise prefer the newest.
Near-duplicates without a parsable id: MinHash on word 5-grams (datasketch) at index time, Jaccard ≥ 0.8. Evaluate
with the harness's "several acceptable ids" already present in `questions_c.json`.

### 4.3 Late chunking
Jina (2024-09 / v3 2025-07): late chunking gives **+1.5–1.9 nDCG@10 absolute** (≈ +3 % relative) averaged over
jina-v2-small, jina-v3 and nomic-embed on four BEIR sets and LongEmbed; gains are largest for *small* chunks and
vanish for large ones; it needs a long-context (8k) embedder run over the whole document (jina-v3 is 570M — the
same CPU cost class as bge-m3 that we already found too slow). Expect little on 512-token chunks; a metadata
prefix captures most of the "context" benefit at zero cost. Low priority.

### 4.4 Fine-tuning with few labels — what the evidence actually supports
* Sample sizes that produced the big legal gains: BSARD ≈ 886 train questions (multi-label), LLeQA ≈ 1.5k; the
  CJEU study reports that fine-tuning helped and analyses "the effect of the amount of data" (curve not re-read
  here). A patent-retrieval paper claims ≥ 30 % gains with 5–250 pairs **[ACM page blocked; unverified]**;
  philschmid's finance example uses 6.3k pairs for +7–9 % nDCG@10 (bge-base, 3 minutes on one GPU); the HF
  reranker guide uses 99k pairs. There is **no solid evidence that a few hundred pairs suffice for a bi-encoder**;
  there is good evidence that 1–2k in-domain questions do, and that BM25-mined hard negatives (plus structure-
  induced negatives, CuSINeS) matter as much as the number of positives.
* Practical route for us without an LLM: (1) **reuse BSARD + LLeQA (≈3k Belgian French questions, research
  licence)** as in-domain data, adding our 133 questions only for evaluation; (2) grow pairs cheaply from the
  corpus itself: question-like sentences already present in FAQ/PQ documents, "Question:"/"Réponse:" pairs in
  rulings, headings→body pairs (as in BGE's unsupervised stage); (3) doc2query-fr on a subset (§ 1.5) for
  synthetic questions; (4) cross-encoder fine-tuning with `BinaryCrossEntropyLoss` + `mine_hard_negatives`
  (sentence-transformers ≥ 4) is the most sample-efficient target because the model already knows relevance and
  only needs domain calibration; a 110M model trains on CPU in hours, a 568M one does not.
* Model choices: `intfloat/multilingual-e5-small/base` (what we deploy), or `maastrichtlawtech/dpr-legal-french`
  as an already-in-domain starting point; cross-encoder: `cross-encoder/mmarco-mMiniLMv2-L12-H384-v1` (2 s/query
  on our box) or `monobert-legal-french`, then compare with bge-reranker-v2-m3 zero-shot.

---

## 5. Things that must wait for the LLM (plan only)
Contextual retrieval (Anthropic, 2024-09: contextual embeddings −35 % top-20 failure, + contextual BM25 −49 %,
+ reranking −67 %, $1.02 per M document tokens with prompt caching) / Summary-Augmented Chunking (§ 3.6);
doc2query-- with DeepSeek instead of mT5; HyDE/Query2doc (+ up to 15 % nDCG@10 for BM25 on TREC-DL **[snippet]**);
RAPTOR summaries for "global" questions; HippoRAG-2-style graphs only if multi-hop questions become a measured
need. Given § 2.3, GraphRAG/LightRAG are **not** recommended even then.

---

## 6. Ranked shortlist for our corpus (max 8)

| # | try next | expected gain (doc-level MRR on C, honest guess) | cost on the 4-core box | model / library |
|---|---|---|---|---|
| 1 | **Canonical-article grouping + duplicate collapse + pseudo-title/metadata field with BM25F-style boost** (code, art. no., chapter heading, doc type, year, region) in both BM25 and the dense prefix; row-wise table linearisation at parse time | +0.03–0.08 (targets 3 of 4 failure modes; SAC/DRM evidence) | 1–2 days of parsing, no model compute | `bm25s` multi-field or `tantivy-py`; `datasketch` MinHash; harness group-level eval |
| 2 | **Fine-tune the cross-encoder in-domain**: mmarco-MiniLM-L12 (or `monobert-legal-french`) on BSARD+LLeQA pairs + BM25/hybrid-mined hard negatives; keep our questions for eval | +0.05–0.10 at 2 s/query instead of 20 s (LegalBench-RAG: generic rerankers can hurt; LLeQA/BSARD: in-domain training is the big lever) | training 110M on ~50k pairs: hours on CPU; inference already measured (2 s) | sentence-transformers `CrossEncoderTrainer`, `BinaryCrossEntropyLoss`, `mine_hard_negatives` |
| 3 | **Fine-tune the bi-encoder** (multilingual-e5-small/base, or start from `dpr-legal-french`) with MNRL + hard negatives on the same data; re-run fusion with *tuned* weights, not RRF | +0.05–0.15 on the dense leg (bBSARD: 110M fine-tuned ≥ 7B zero-shot); fusion may stop helping ("Know When to Fuse") | training: hours on CPU (e5-small), re-embedding C as in exp 09 | sentence-transformers `MultipleNegativesRankingLoss`; LightGBM/XGBoost `rank:ndcg` for the fusion weights |
| 4 | **Inference-free learned sparse leg**: encode chunks with `opensearch-neural-sparse-encoding-multilingual-v1`, queries by IDF lookup, fuse with BM25/dense | +0.02–0.05 (vocabulary gap on the index side; MIRACL fr 0.558; OpenSearch reports gains in all languages) | one BERT-base pass over C (same class as the e5-base pass); zero query cost; scipy sparse index | `transformers` code from the model card; scipy CSR dot product |
| 5 | **Late-interaction re-ranking of top-100** with `colbert-legal-french` (in-domain) and `colbert-xm` (zero-shot) via PyLate; optionally full PLAID index on corpus B | +0.02–0.05 over dense leg; mainly a **latency** win (0.14 s/q reported on CPU) letting us cut the cross-encoder to top-10 | token-vector index ≈ 6.7× text (fine for B, ~1.6 GB for C at fp32; use 64-dim Matryoshka/int8) | `pylate`, `fast-plaid`; check jina-colbert-v2 licence before use |
| 6 | **Query expansion without LLM**: Rocchio/RM3 over `bm25s` + curated layman→statute lexicon + static-embedding neighbours; ablate on the 64 corpus-C questions | +0.01–0.04; may hurt without #1 (duplicates dominate feedback) | < 1 day; milliseconds per query | `bm25s` term matrices, our potion/model2vec model |
| 7 | **Cross-reference / hierarchy graph as features**: regex-parse citations and headings, neighbour expansion of top-k (parent/sibling/cited articles), in-degree/PageRank prior, few-feature LambdaMART with leave-one-out CV | +0.01–0.03 now; enables G-DSR-style GNN later (BSARD 77 → 84 R@100) | 1–2 days; NetworkX/scipy seconds at 100k nodes | `networkx`, `lightgbm` lambdarank (`mean` pair method), DuckDB/SQLite tables (no graph DB needed) |
| 8 | **Reranker efficiency**: ONNX int8 export of bge-reranker-v2-m3, 512-token truncation, rerank top-15 only; compare with jina-reranker-v3 / Qwen3-Reranker-0.6B | ≈0 quality change, 2–4× less latency (int8 speed-up **[unverified on this box]**) | half a day | `optimum` ONNX Runtime, sentence-transformers backend="onnx" |

Explicitly *not* on the list: GraphRAG/LightRAG/HippoRAG (need an LLM; no factual-QA win in controlled studies),
Vespa/Elasticsearch (ops cost without ranking gain at our scale), bge-m3/MILCO/jina-v3-based late chunking (CPU
cost already ruled out in exp 02), Kuzu (archived).

---

## 7. Sources

Read in full or in the relevant sections (fetched page or PDF text extracted locally):

* BSARD — https://arxiv.org/abs/2108.11792 , https://arxiv.org/html/2108.11792 (ACL 2022)
* Finding the Law / G-DSR — https://arxiv.org/abs/2301.12847 (+ PDF) (EACL 2023)
* Bilingual BSARD — https://aclanthology.org/2025.regnlp-1.3.pdf (COLING 2025)
* CuSINeS — https://arxiv.org/abs/2404.00590 (+ PDF) (LREC-COLING 2024)
* QABISAR — https://arxiv.org/pdf/2412.00934
* LLeQA — https://arxiv.org/abs/2309.17050 (+ PDF) (AAAI 2024)
* Know When to Fuse — https://arxiv.org/abs/2409.01357 (+ PDF) (2024-09)
* Maastricht Law&Tech models — https://huggingface.co/maastrichtlawtech , https://huggingface.co/maastrichtlawtech/splade-legal-french , https://huggingface.co/maastrichtlawtech/colbert-legal-french
* lexfr-embed — https://github.com/ghislaindelabie/lexfr-embed
* SPLADE-v3 — https://arxiv.org/abs/2403.06789 (+ PDF) (2024-03)
* SPLADE efficiency study — https://arxiv.org/pdf/2207.03834 (SIGIR 2022)
* OpenSearch neural sparse v3 + multilingual — https://opensearch.org/blog/advancing-search-with-opensearch-v3-neural-sparse-models-and-a-multilingual-retrieval-model/ (2025-09-25), https://huggingface.co/opensearch-project/opensearch-neural-sparse-encoding-multilingual-v1
* BGE-M3 — https://arxiv.org/html/2402.03216v3
* MILCO — https://arxiv.org/html/2510.00671v2 (ICLR 2026)
* MIRACL — https://arxiv.org/pdf/2210.09984
* Jina-ColBERT-v2 — https://arxiv.org/html/2408.16672v4 (2024-09)
* ColBERT-XM — https://arxiv.org/abs/2402.15059 (+ PDF)
* pylate-rs — https://lightonai.github.io/pylate-rs/
* RAG vs GraphRAG — https://arxiv.org/html/2502.11371v3 (2026-03)
* HippoRAG 2 — https://arxiv.org/html/2502.14802v2 (2025-06)
* Unbiased GraphRAG evaluation — https://arxiv.org/pdf/2506.06331
* GraphRAG-Bench — https://arxiv.org/pdf/2506.02404
* Benchmarking KG-based RAG on legal documents — https://ceur-ws.org/Vol-4079/paper6.pdf (2025)
* Hier-SPCNet — https://arxiv.org/abs/2209.12474 (IPM 2022)
* CRAwLeR — https://arxiv.org/pdf/2606.21676 (2026-06)
* CLERC — https://arxiv.org/pdf/2406.17186
* Lexical vs semantic on formulaic legal language (CJEU) — https://arxiv.org/pdf/2506.12895
* Reasoning-focused legal retrieval benchmark — https://arxiv.org/html/2505.03970v1 (2025-03)
* LegalBench-RAG — https://arxiv.org/abs/2408.10343 (abstract page only)
* Summary-Augmented Chunking / DRM — https://arxiv.org/abs/2510.06999 (+ PDF) (NLLP 2025)
* COLIEE 2025 overview — https://ideas.repec.org/a/spr/trosos/v20y2026i1d10.1007_s12626-026-00199-9.html
* LLM-based embedders for prior case retrieval — https://arxiv.org/pdf/2507.18455
* MLEB — https://huggingface.co/blog/isaacus/introducing-mleb (2025-10)
* MTEB-French — https://arxiv.org/html/2405.20468v2
* Late chunking — https://arxiv.org/abs/2409.04701 , https://arxiv.org/html/2409.04701v3
* Contextual retrieval — https://www.anthropic.com/engineering/contextual-retrieval (2024-09)
* Doc2Query-- — https://arxiv.org/abs/2301.03266 (ECIR 2023)
* Fine-tuning embeddings (philschmid) — https://www.philschmid.de/fine-tune-embedding-model-for-rag (2024-06)
* Training rerankers (HF) — https://huggingface.co/blog/train-reranker (2025-03)
* XGBoost learning to rank — https://xgboost.readthedocs.io/en/latest/tutorials/learning_to_rank.html
* DuckDB FTS — https://duckdb.org/docs/current/core_extensions/full_text_search
* Tantivy — https://github.com/quickwit-oss/tantivy
* SQLite hybrid search — https://simonwillison.net/2024/Oct/4/hybrid-full-text-search-and-vector-search-with-sqlite/
* Kuzu archival and successors — https://gdotv.com/blog/kuzu-legacy-embedded-graph-database-landscape/ (2026-05)

Seen only through search-result snippets (claims marked [unverified] above): Lin 2019 "Neural hype"
(https://dl.acm.org/doi/pdf/10.1145/3308774.3308781); Waseda BM25PRF (https://ceur-ws.org/Vol-2409/docker10.pdf);
Elasticsearch combined_fields (https://www.elastic.co/docs/reference/query-languages/query-dsl/query-dsl-combined-fields-query);
FalkorDBLite (https://docs.falkordb.com/operations/falkordblite/); pyoxigraph (https://pyoxigraph.readthedocs.io/en/stable/store.html);
Vespa hybrid tutorial (https://docs.vespa.ai/en/learn/tutorials/hybrid-search.html); PyLate paper (https://arxiv.org/pdf/2508.03555);
LePaRD (https://aclanthology.org/2024.acl-long.532/); Microsoft GraphRAG (https://arxiv.org/pdf/2404.16130); RAPTOR
(https://arxiv.org/pdf/2401.18059); jina-reranker-v3 (https://arxiv.org/pdf/2509.25085); Qwen3 embedding/reranker
(https://arxiv.org/html/2506.05176v1); doc2query French mT5 (https://huggingface.co/doc2query/msmarco-14langs-mt5-base-v1);
reference-network statute retrieval (https://link.springer.com/article/10.1007/s10489-025-06818-2, paywalled);
patent few-shot fine-tuning (https://doi.org/10.1145/3787279.3787295, blocked); Kuzu archival news
(https://biggo.com/news/202510130126_KuzuDB-embedded-graph-database-archived).
