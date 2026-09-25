# 04 — Long-context embedders and late chunking

**Idea**

Encode a whole document (up to 8,192 tokens) with a long-context embedder, then mean-pool the *token* vectors per chunk ("late chunking", Günther et al. 2024). Every chunk vector then carries context from the rest of the document (title, defined terms, the article a paragraph belongs to), instead of being embedded in isolation. Candidate open models: bge-m3 (568M, 8k, MIT), jina-embeddings-v3 (570M, 8k, CC-BY-NC), nomic-embed v1.5 (8k, English only; v2-moe is 512 tokens and unusable here).

**Why it fits this project**

Two known failure modes are context loss: 100–500 kB circulars and *Commentaire* chapters chunked at 1,200 chars lose their topic, and topic-less paragraphs ("le contribuable visé à l'alinéa précédent…") cannot be matched to layman questions. Late chunking is the zero-LLM way to inject document context; our title/heading prefix (+0.02–0.04 MRR) is a crude version of it.

**Evidence**

* Original paper (arXiv 2409.04701, v3 Jul 2025), nDCG@10, 256-token chunks, jina-v3: SciFact 71.8→73.2, NFCorpus 35.6→36.7, FiQA 46.3→47.6, TRECCOVID 73.0→77.2; nomic-v1 is flat on two of four sets. Average gain ≈ +1.9 abs (+3.6 % rel); gains grow with document length and shrink with chunk size ≥ 512 tokens.
* Reconstructing Context (arXiv 2504.19754, Apr 2025), NFCorpus, jina-v3: naive 0.291, late 0.294, LLM contextual retrieval 0.308 nDCG@10; late chunking *underperformed* naive with bge-m3.
* Beyond Chunk-Then-Embed (arXiv 2602.16974, Feb 2026): for *in-document* retrieval (GutenQA) late chunking degrades all models: nomic −53 %, jina-v3 −30 %, e5-large −4 % — "encodes broader document themes rather than chunk-specific details".
* When Is Complex Chunking Worth It (arXiv 2608.16586, CIKM'26, Aug 2026): at 1M documents, Recall@100 token chunking 56.7–57.3 vs late chunking 48.0–50.5; "rarely achieves significant wins", high indexing memory.
* voyage-context-3 (Jul 2025, proprietary): beats jina-v3 late chunking by 23.7 % chunk-level — learned contextualisation ≫ post-hoc pooling, but closed.
* Storage cost is identical to naive chunking (Weaviate, Sep 2024).
* Our own data: 560M models cost ~1 h / 1,000 512-token chunks on the 4-core box; corpus C p99 length is 118k chars, i.e. far beyond 8k tokens.

**How we would implement it**

`chonkie` LateChunker (sentence-transformers backend) or 30 lines with `AutoModel` + span mean-pooling (jina-ai/late-chunking repo); bge-m3 via FlagEmbedding/ONNX exposes token vectors. Documents > 8k tokens need "long late chunking": overlapping 8k macro-windows, so a 125k-token circular still gets only window-local context. No LLM needed. CPU feasibility for 201k chunks (≈ 65M tokens): bge-m3 at 512 tokens already needs ≈ 200 CPU-hours; at 8k windows attention adds ~1.5–2× (unverified estimate) → 300–400 h, and eager attention on 8,192² matrices needs several GB per layer (must use SDPA). e5-small/e5-base cannot do it (512-token limit). Only a GPU makes this a routine index rebuild.

**Expected gain and cost**

Literature: +1–2 nDCG points on document-level retrieval, possibly negative on chunk-level precision and at scale. On our metric (document-level MRR after bge-reranker) the reranker already sees the title-prefixed chunk, so the likely delta is within noise (±0.01). Cost: weeks of CPU or a GPU, a switch from e5 to bge-m3 (itself measured as too slow on C), and a non-commercial licence if jina-v3.

**Risks / open questions**

* Two 2026 large-scale studies report late chunking below plain chunking; the wins are from the method's authors on short BEIR documents.
* Our long documents exceed 8k tokens 20–60×, so "global context" is a window, not the document.
* Chunk-level precision matters for citing an article: contextual bleed may pull in neighbouring articles (yearly/regional near-duplicates get *more* similar, not less).
* Untested: whether a French legal corpus behaves like BEIR; a corpus A pilot (91 docs, ~300k tokens, ~40 windows, ≈ 2 h CPU with bge-m3) would settle it cheaply.

**Verdict**

**skip** — evidence for late chunking is small and contradicted at scale, our documents are too long for its 8k window, and it costs 300+ CPU-hours; the cheaper context injection (heading prefix now, LLM contextual retrieval later, topic 06) covers the same failure mode.

**Sources**

* https://arxiv.org/abs/2409.04701 (v3, Jul 2025)
* https://jina.ai/news/late-chunking-in-long-context-embedding-models/ (Aug 2024)
* https://github.com/jina-ai/late-chunking
* https://arxiv.org/abs/2504.19754 (Apr 2025)
* https://arxiv.org/abs/2602.16974 (Feb 2026)
* https://arxiv.org/abs/2608.16586 (Aug 2026)
* https://blog.voyageai.com/2025/07/23/voyage-context-3/
* https://weaviate.io/blog/late-chunking (Sep 2024)
* https://jina.ai/models/jina-embeddings-v3/ (CC-BY-NC-4.0, deprecated)
* https://huggingface.co/BAAI/bge-m3 ; https://github.com/allen2c/bge-m3-lite
* https://huggingface.co/nomic-ai/nomic-embed-text-v2-moe
* https://docs.chonkie.ai/oss/chunkers/late-chunker
