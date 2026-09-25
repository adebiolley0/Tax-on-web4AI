# 37 — Administrative commentary as the bridge between statute and practice

**Idea**

Treat administrative commentary (Commentaire TVA chapters, Rép. RJ entries, later ComIR 92) as the *answer* layer and statute as the *citation* layer: split commentaries into numbered paragraphs, attach to each paragraph the article(s) it comments, the edition date and the region, keep one live edition per chapter (older editions searchable only by date filter), and let the MCP `search` return the paragraph plus its statute anchor as a typed pair.

**Why it fits this project**

- Commentary is written in explanatory French ("frais de réception", "beaux-petits-enfants") while statute is terse; it is the natural landing place for layman questions, which is the dominant failure mode of corpus B (EXPERIMENTS.md §3.2).
- Local structure is already there but unused. Commentaire TVA (95 files, up to 564 kB) carries `Mise à jour 01.09.2025 – Versions précédentes : [01.07.2018] … [01.12.2024]` and a Livre/Chapitre/Section/1./A./a. outline; ~20 chapters exist in two dated versions. Rép. RJ (4.4k files, median 1.9 kB) encodes the article in the title (`Numéro E 129/07-01` = art. 129 C. enr., topic 07, entry 01; `S 50-VL/01-01` = art. 50 C. succ., Flanders), has a topic heading (`01. – Héritiers ou légataires.`), a source line (`Circulaire du 24.12.1958, n° 36`) and a `Date de publication`.
- Measured pain: on corpus C the 8 commentary questions score MRR 0.61 under the best stack vs 0.72 for the rest; whole-document BM25 gets 0.72 on them (C42 rank 4 vs 42 when chunked at 1,200 chars). Chunking the monster chapters loses the chapter/section context; Rép. RJ succession questions (C47, C48) sit at rank 4–7 because titles are opaque.
- ComIR 92 (`49/01…49/21` numbering, binding on officials, Fisconetplus shows original + updates + article on one page since 2020) is absent from the corpus (only `aperçu documentaire` index pages, correctly excluded); the same scheme applies when it is ingested.

**Evidence**

- BOFiP is the reference design: hierarchical ids with a date suffix (`BOI-IS-BASE-10-10-10-10-20230621`), paragraphs numbered in tens for insertion, a "Versions sur la période" list, CGI articles hyperlinked to Legifrance, opposable under art. L.80 A LPF; full corpus in open data (CSV/JSON, Licence Ouverte 2.0, `bofip-vigueur` = current editions only; updated 17 Sep 2026).
- LaborBench (arXiv 2603.03300, Feb 2026): a statute-only RAG (STARA) systematically missed provisions set by regulation or administrative interpretation; the authors ask benchmarks to state whether ground truth includes non-statutory sources — the only quantified evidence that commentary-type sources change answers.
- Legal RAG Bench (Isaacus, Feb 2026) uses a practitioner guidance book (Victoria Criminal Charge Book, 4,876 passages ≤ 512 tokens) as the whole corpus; retrieval quality "sets the ceiling" on answer correctness.
- LLeQA (AAAI 2024): layman questions (Droits Quotidiens) answered from statute only; zero-shot retrievers stay at R@10 ≈ 0.37 (idea 01) — the gap commentary is meant to close. No paper directly compares statute vs commentary vs case on layman questions (unverified gap).
- Summary-Augmented Chunking (arXiv 2510.06999, Oct 2025): a ~150-char document summary prepended to 500-char chunks halves document-level mismatch on LegalBench-RAG — the cheap fix for our chapter-context loss.
- eulex-rag (GitHub, 2025): article-boundary chunks, citation-graph expansion, fail-closed citation validation. arXiv 2606.09724 (Jun 2026) names "diachronic blindness" and asks for bitemporal validity in legal RAG.

**How we would implement it**

1. Parser (`ingestion/`): Commentaire TVA → paragraph units keyed `tva:<chapter>:<section>.<point>.<letter>`, prefix `title › Section › point` (≤ 1,200 chars, exp 02 rule); Rép. RJ → regex on title for `code`, `article`, `region`, plus the `01. –` heading as topic; extract `article 45, § 2, du Code` references into `cites[]`.
2. Metadata: `edition_date`, `is_current` (latest date per chapter; older editions excluded from default search, available via `as_of`), `source_kind = commentary`.
3. Retrieval: index paragraphs, aggregate to document with max-of-paragraphs plus a whole-document BM25 leg (the 0.72 signal); reranker unchanged.
4. MCP contract: `search` returns `{paragraph, article_ref, edition_date}`; `fetch(article)` joins CIR 92 / C. TVA article text from corpus B for the citation.
5. When DeepSeek is available: one-line summaries per chapter (SAC), and a `code→article` alias table for ComIR once ingested.

**Expected gain and cost**

Commentary questions from 0.61 to ≈ 0.70–0.75 (whole-doc level already gives 0.72; region/article filters fix C47/C48), i.e. +0.01–0.02 on overall corpus C MRR, and a much better *answer* object for the LLM. Cost: 2–3 days of parsing and metadata, no model training, no query-time cost; halves the 20 duplicated TVA editions.

**Risks / open questions**

- Only 8 validation questions target commentary; write 20 more before measuring.
- Rép. RJ entries are old (1958–2011 decisions) and pre-regionalisation; `is_current` needs a legal, not a date, rule.
- ComIR 92 must first be fetched (only index pages are ingested); its update paragraphs may not follow `nr/xx` numbering after the 2020 redesign (unverified).
- Whole-document scoring for 564 kB chapters is BM25-only; dense models never see the full chapter.

**Verdict**

**try-now** — the structure is already in the files, the parsing is cheap, and it fixes a measured 0.11 MRR deficit on commentary questions while giving the MCP server a citation-ready answer object.

**Sources**

- https://bofip.impots.gouv.fr/bofip/1924-PGP.html/identifiant=BOI-IS-BASE-10-10-10-10-20230621
- https://www.data.gouv.fr/datasets/bofip-impots-publications-en-vigueur
- https://data.economie.gouv.fr/explore/dataset/bofip-impots/api/
- https://www.fiscaloo.fr/bofip/
- https://arxiv.org/html/2603.03300 (LaborBench)
- https://huggingface.co/blog/isaacus/legal-rag-bench
- https://huggingface.co/datasets/maastrichtlawtech/lleqa
- https://arxiv.org/html/2510.06999v1 (SAC)
- https://github.com/tomashermansen-lang/eulex-rag
- https://arxiv.org/abs/2606.09724
- https://arxiv.org/abs/2605.24534 (commentaries from case databases)
- https://arxiv.org/html/2605.21071v2 (ClaimRAG-Law)
- https://blog.forumforthefuture.be/fr/article/le-comir-92-fait-peau-neuve-.../9915
- https://questionfiscale.be/lexique/commentaire-code-impots-revenus-1992/
- Local: `myfin_docs/commentaires_dont_rep_rj/`, `experiments/results/09_corpus_c/*.json`, `experiments/data/corpus_c/questions_c.json`
