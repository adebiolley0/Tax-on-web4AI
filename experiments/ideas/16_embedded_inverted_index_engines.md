# 16 — Embedded inverted-index engine for the lexical leg

**Idea**

Replace the in-memory `bm25s` leg with a persistent embedded inverted index (Tantivy via `tantivy-py`): French analyzer (lowercase → ASCII-fold → stopwords → Snowball stem), field boosts, phrase/proximity (`"revenu cadastral"~2`), metadata filters and incremental add/delete/commit — no server, no Docker.

**Why it fits this project**

- `bm25s` has no fields, phrases, filters or incremental updates; at ~1M chunks the index must live off-heap and survive restarts.
- Legal text needs exact article phrases (`"article 90, 1°"`), title/heading weighting and filters on doc type, year, language, source — all native to Tantivy.
- CPU-only, no infra: Tantivy ships MIT manylinux wheels (Python ≥3.10) and runs in-process in the FastMCP server.

**Evidence** (checked 2026-09-25; *unverified* where marked)

| Engine | Version / licence / install | French analysis | Boosts / phrase / proximity | Filters / incremental | Scale notes |
|---|---|---|---|---|---|
| **tantivy-py** [1][2] | 0.26.2 (2026-09-17), MIT, wheels | `Filter.stemmer("french")`, `Filter.stopword("french")`, `Filter.ascii_fold()`, `lowercase`, `remove_long`; custom `TextAnalyzerBuilder` | `parse_query(field_boosts=…)`, `boost_query`; `"a b"~N` slop; `phrase_query(slop=)`; fuzzy | `term_set_query`, `range_query` in `boolean_query`; `delete_documents_by_term/by_query`, `commit`, `reload` | Wikipedia (EN) TOP-100 medians: ~1.1 ms AND, 2.7 ms OR, 0.5 ms phrase, on par with Lucene [3] |
| **LanceDB native FTS** [4][5] | 0.39.0, Apache-2.0, abi3 wheels | `language="French"` stem, `ascii_folding` (default on), stopwords | `MultiMatchQuery(columns, boosts)`, `BoostQuery`, `PhraseQuery(slop)` (needs `with_position=True`); no AND/OR in query string | SQL `where` pre/post-filter; `optimize()` folds new rows | 41M-doc Wikipedia demo, numbers not published [6] |
| **Xapian** [7][8][9] | 2.1.0 / 1.4.32 (2026-08-13), GPL-2+, distro packages only (PyPI `xapian-bindings` 0.1.0, 2020, builds from source) | Snowball French; no built-in accent folding (*unverified*) | `OP_SCALE_WEIGHT` per prefix, BM25/BM25+; `NEAR/n`, `ADJ/n`, phrase | `OP_FILTER`, value ranges; `replace_document` | Mature; GPL is a distribution constraint |
| **PyLucene** [10][11] | 10.0.0 (2024-10-20), Apache-2.0, JCC + JDK 21 source build, no wheels; Lucene core is at 10.5.1 | `FrenchAnalyzer` (elision, light stem), ASCII folding | full Lucene query language | full | best features, worst ops cost |
| **whoosh3** [12][13] | 3.54.0 (2026-09-21), BSD; original and `Whoosh-Reloaded` inactive; fork maintained by an "AI agent", 0 stars | Snowball | BM25F, phrase, proximity | yes | pure Python, self-described ceiling "low millions" |
| **Bleve / Sonic** [14][15] | Go library, no Python bindings / standalone Rust server with clients | — / no ranking, IDs only | — | — | not embeddable |

**How we would implement it**

1. `experiments/17_tantivy/` (uv project): a `TantivyLexicalIndex` adapter behind the `rag_eval` retriever interface.
2. Schema: `chunk_id` (stored), `title` / `headings` / `body` with analyzer `fr_stem`; `body_exact` (lowercase + fold, no stem) for phrase/proximity; string fields `doc_type`, `source`, `lang`, `article_ref`; `year` as fast u64.
3. Queries: `parse_query(q, ["title","headings","body"], field_boosts={"title":3,"headings":2,"body":1})` OR'd with a `phrase_query(slop=2)` on `body_exact`; filters as `Occur.Must` `term_set_query`/`range_query` in a `boolean_query`.
4. Ingestion: delete-by-term on `chunk_id`, add, commit per batch; `Index.is_compatible()` on startup.
5. Evaluate against the bm25s baseline on the existing question sets; log to `leaderboard.jsonl`; then RRF with embeddings.

**Expected gain and cost**

- Quality: parity to small gain (+0–3 nDCG points from boosts and phrase rescue on article citations, *unverified*). The real win is operational: persistent index, sub-5 ms queries at 1M chunks, filters, live updates, memory off the Python heap.
- Cost: ~2–3 dev days; one compiled wheel; index rebuild on Tantivy format bumps.

**Risks / open questions**

- Tantivy sums per-field BM25 (not true BM25F); title boosts can over-reward short fields — tune on the leaderboard.
- No elision filter (`l'`, `d'`, `qu'`): needs a regex tokenizer or pre-clean; verify stem parity with `bm25s`.
- `tantivy-py` lags Tantivy core by months; volunteer-driven releases.
- LanceDB is the fallback if we later want vectors + FTS in one store, at the price of no boolean query string.

**Verdict**

**try-now** — Tantivy gives everything bm25s lacks (fields, phrases, filters, persistence, incremental updates) as one MIT wheel, so the experiment is cheap and the ops upside is certain even at ranking parity.

**Sources**

1. https://pypi.org/project/tantivy/ (0.26.2, MIT, history)
2. https://raw.githubusercontent.com/quickwit-oss/tantivy-py/master/tantivy/tantivy.pyi (API)
3. https://serenedb.com/blog/search-benchmark-game-overview (2026-03-18) and https://github.com/quickwit-oss/search-benchmark-game
4. https://docs.lancedb.com/search/full-text-search
5. https://github.com/lancedb/lancedb/blob/main/docs/src/fts.md
6. https://www.lancedb.com/blog/feature-full-text-search
7. https://xapian.org/ (versions, GPL)
8. https://xapian.org/docs/queryparser.html ; https://xapian.org/docs/stemming.html
9. https://xapian.org/docs/apidoc/html/classXapian_1_1Query.html (OP_SCALE_WEIGHT, OP_NEAR) ; https://pypi.org/project/xapian-bindings/
10. https://lucene.apache.org/pylucene/news.html
11. https://lucene.apache.org/pylucene/install.html
12. https://pypi.org/project/whoosh3/ ; https://github.com/SantiagoDaleffe/whoosh
13. https://snyk.io/advisor/python/whoosh-reloaded
14. https://github.com/blevesearch/bleve
15. https://github.com/xmonader/python-sonic-client
