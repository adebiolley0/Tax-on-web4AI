# 26 — Near-duplicate detection and canonicalisation

**Idea**

Index *canonical documents*, not editions. At ingestion, cluster near-identical texts (yearly editions, regional twins, re-issued circulars, indexation notices, FR/NL pairs) with exact hashing + MinHash/LSH, elect one canonical per cluster, attach the others as *variants* with metadata (income year, region, language, what changed). Retrieval scores canonicals only; `search` returns the canonical hit plus its variant list, and a `year`/`region`/`lang` filter or `fetch` picks the exact edition. Query-time collapse (Elastic `collapse`, Vespa `grouping`/`diversity`) is the fallback if all editions stay indexed.

**Why it fits this project**

Corpus C shows yearly triplication of CIR 92 articles, regional quadruplication of codes, ×8 circulars (exp 09). Duplicates split the reranker's top-5 between identical texts, waste hit@1 and context tokens, and confuse users who see three "art. 145/1" entries. The validation set already accepts "several ids where yearly editions coexist" — a canonical id makes evaluation honest. At 100k documents the problem grows; collapsing at ingestion also cuts the embedding bill (3.3 h for 201k chunks) by the duplication factor.

**Evidence**

- Bernstein & Zobel (CIKM 2005): 23.4 % of GOV2 documents content-equivalent to another; 16.6 % of relevant documents in TREC 2004 Terabyte runs redundant; user study confirmed fingerprinting matches user judgement. https://people.eng.unimelb.edu.au/jzobel/fulltext/cikm05bz.pdf
- Fröbe et al. (SIGIR 2020): near-duplicates bias LTR rankings; effectiveness under the novelty principle drops up to 39 %; deduplicate before training and evaluation. https://dl.acm.org/doi/abs/10.1145/3397271.3401212 (abstract only)
- Manku, Jain, Das Sarma (WWW 2007): 64-bit SimHash, Hamming ≤ 3 on 8 B fingerprints. https://research.google.com/pubs/archive/33026.pdf
- datasketch MinHashLSH: `threshold`, `num_perm`, FP/FN weights; ~0.03 ms/query on a near-duplicate corpus; Redis/Cassandra backends. https://ekzhu.com/datasketch/lsh.html — Milvus 3.x ships a native MINHASH_LSH index with Jaccard refinement. https://milvus.io/docs/minhash-lsh.md
- SemDeDup (2023): k-means then intra-cluster cosine > 1−ε; keeps the member nearest the centroid. https://arxiv.org/abs/2303.09540
- RAG-side: byte-exact chunk dedup, 0.16 % reduction on BEIR vs 24 % on enterprise data, no quality regression (May 2026, unverified). https://arxiv.org/abs/2605.09611 — duplicate/paraphrased context does not improve answers; diverse sources +17–47 % (Aug 2026). https://arxiv.org/abs/2608.13956
- Engines: Elastic `collapse` (one top hit per key, `inner_hits` for variants, extra query per group) https://www.elastic.co/docs/reference/elasticsearch/rest-apis/collapse-search-results ; Vespa `diversity` (first-phase), `grouping max(1)` (after second phase), `collapsefield` https://docs.vespa.ai/en/querying/result-diversity.html ; Google canonical + `hreflang` for language/regional variants. https://developers.google.com/search/docs/crawling-indexing/canonicalization

**How we would implement it**

1. *Normalise*: strip amendment preambles, dates, "exercice d'imposition 20xx", region names, SharePoint residue; lowercase; NFKC.
2. *Exact tier*: SHA-256 of normalised body → byte-identical editions (most CIR 92 triplicates) collapse for free.
3. *Near tier*: datasketch MinHash, 5-word shingles, `num_perm=128`, LSH `threshold=0.85` (weights FN-heavy 0.4/0.6), then exact Jaccard on candidates, union-find into clusters. Cost: 21k docs in minutes; 1 M chunks ≈ 1 M×128×4 B = 0.5 GB signatures, ~1 h on 4 cores. SimHash (64-bit, Hamming ≤ 3) is the cheaper alternative for chunks.
4. *Structural tier*: the article parser already yields `code` + `article` + `region` + `income_year`; group on that key first and let MinHash confirm.
5. *Canonical election*: latest valid edition (or "federal" for regional twins only when text is identical); variants keep `year`, `region`, `lang`, `guid`, `jaccard`, and a `difflib` unified diff of what changed (numbers, thresholds, dates) — the diff becomes a short "changes vs canonical" note.
6. *Query time*: index canonicals only; return `{canonical, variants[...]}`; filters on `year`/`region` select the variant when it differs. FR/NL pairs: separate language field, link as variants, never collapse text.
7. No LLM needed; a DeepSeek pass could later summarise diffs.

**Expected gain and cost**

Ingestion-time collapse of an estimated 30–50 % of documents; hit@1 +0.03–0.08 and MRR +0.02–0.05 on C (the "wrong-year twin" cases), fewer wasted reranker slots, ~40 % smaller embedding jobs. Cost: 2–3 days (pipeline + tests), no runtime cost, no new models.

**Risks / open questions**

- Editions differing in one figure (indexed amounts) are 0.98 Jaccard yet legally distinct: collapse only with a diff note and year filter, never silently.
- Regional twins with identical text but different applicability — the canonical must not hide the region.
- Threshold tuning needs ~200 labelled pairs; MinHash on stripped text may merge template-heavy short documents.
- The evaluation set must be re-mapped to canonical ids; part of any hit@1 gain reflects stricter labels.

**Verdict**

try-now — the corpus is provably duplicate-heavy, the tooling is mature and CPU-cheap, and canonical + variants fixes both metrics and user confusion at ingestion rather than by query-time tricks.

**Sources**

URLs inline above, plus https://github.com/webis-de/sigir20-sampling-bias-due-to-near-duplicates-in-learning-to-rank · https://docs.vespa.ai/en/querying/grouping.html · experiments/09_corpus_c/README.md.
