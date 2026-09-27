# 37 — Administrative commentary as the bridge between statute and practice

**Idea**

Treat administrative commentary (Commentaire TVA chapters, Rép. RJ entries, later ComIR 92) as the *answer* layer and statute as the *citation* layer: split commentaries into numbered paragraphs, attach to each its article(s), edition date and region, keep one live edition per chapter (older ones only via a date filter), and let MCP `search` return the paragraph plus its statute anchor as a typed pair.

**Why it fits this project**

- Commentary is explanatory French ("frais de réception", "beaux-petits-enfants"); statute is terse. It is the natural landing place for layman questions, the dominant failure mode on corpus B.
- The structure is already in the files, unused. Commentaire TVA (95 files, up to 564 kB) carries `Mise à jour 01.09.2025 – Versions précédentes : [01.07.2018] … [01.12.2024]` and a Livre/Chapitre/Section/1./A./a. outline; ~20 chapters exist in two dated versions. Rép. RJ (4.4k files, median 1.9 kB) encodes the article in the title (`Numéro E 129/07-01` = art. 129 C. enr., topic 07, entry 01; `S 50-VL/01-01` = art. 50 C. succ., Flanders), then a topic heading (`01. – Héritiers ou légataires.`), a source line (`Circulaire du 24.12.1958, n° 36`) and a publication date.
- Measured pain: on corpus C the 8 commentary questions score MRR 0.61 under the best stack vs 0.72 for the rest; whole-document BM25 alone gets 0.72 on them (C42: rank 4 whole-doc, 42 chunked) — chunking the monster chapters loses section context. Rép. RJ succession questions (C47, C48) sit at rank 4–7 behind opaque titles.
- ComIR 92 (`49/01…49/21` numbering, binding on officials; Fisconetplus shows original + updates + article on one page since 2020) is not yet in the corpus (only its `aperçu documentaire` index pages, excluded); the same scheme applies once ingested.

**Evidence**

- BOFiP is the reference design: hierarchical ids with a date suffix (`BOI-IS-BASE-10-10-10-10-20230621`), paragraphs numbered in tens, a "Versions sur la période" list, CGI articles linked to Legifrance, opposable under art. L.80 A LPF; open data (`bofip-vigueur` = current editions only).
- LaborBench (arXiv 2603.03300, Feb 2026): a statute-only RAG systematically missed provisions set by regulation or administrative interpretation — the only quantified evidence that commentary-type sources change answers.
- Legal RAG Bench (Isaacus, Feb 2026): whole corpus is a practitioner guidance book (Victoria Criminal Charge Book, 4,876 passages ≤ 512 tokens); retrieval "sets the ceiling" on correctness.
- LLeQA (AAAI 2024): layman questions answered from statute only; zero-shot R@10 ≈ 0.37 (idea 01). No paper directly compares statute vs commentary vs case on layman questions (gap, unverified).
- Summary-Augmented Chunking (arXiv 2510.06999, Oct 2025): a ~150-char summary prepended to each chunk halves document-level mismatch on LegalBench-RAG.
- eulex-rag (GitHub, 2025): article-boundary chunks, citation-graph expansion, fail-closed citations. arXiv 2606.09724 (Jun 2026): bitemporal validity against "diachronic blindness".

**How we would implement it**

1. Parser: Commentaire TVA → paragraph units keyed `tva:<chapter>:<section>.<point>.<letter>`, prefix `title › Section › point` (≤ 1,200 chars); Rép. RJ → regex on title for `code`, `article`, `region`, `01. –` heading as topic; extract `article 45, § 2, du Code` references into `cites[]`.
2. Metadata: `edition_date`, `is_current` (latest date per chapter; older editions hidden unless `as_of`), `source_kind = commentary`.
3. Retrieval: paragraph index aggregated per document (max) plus a whole-document BM25 leg; reranker unchanged.
4. MCP: `search` returns `{paragraph, article_ref, edition_date}`; `fetch(article)` joins the CIR 92 / C. TVA article text from corpus B as citation.
5. With DeepSeek: one-line chapter summaries (SAC) and a ComIR `code→article` alias table.

**Expected gain and cost**

Commentary questions from 0.61 to ≈ 0.70–0.75 (whole-doc already gives 0.72; article/region filters fix C47/C48), i.e. +0.01–0.02 overall on corpus C, plus a citation-ready answer object. Cost: 2–3 days of parsing and metadata, no training, no query-time cost; removes ~20 duplicated TVA editions.

**Risks / open questions**

- Only 8 validation questions target commentary; write 20 more first.
- Rép. RJ entries date from 1958–2011, partly pre-regionalisation; `is_current` needs a legal rule, not a date.
- ComIR 92 must first be fetched; whether post-2020 updates keep `nr/xx` numbering is unverified.
- Whole-document scoring of 564 kB chapters is BM25-only.

**Verdict**

**try-now** — the structure is already in the files, parsing is cheap, and it targets a measured 0.11 MRR deficit on commentary questions while giving the MCP server a citation-ready answer object.

**Sources**

- https://bofip.impots.gouv.fr/bofip/1924-PGP.html/identifiant=BOI-IS-BASE-10-10-10-10-20230621
- https://www.data.gouv.fr/datasets/bofip-impots-publications-en-vigueur
- https://www.fiscaloo.fr/bofip/
- https://arxiv.org/html/2603.03300 (LaborBench)
- https://huggingface.co/blog/isaacus/legal-rag-bench
- https://huggingface.co/datasets/maastrichtlawtech/lleqa
- https://arxiv.org/html/2510.06999v1 (SAC)
- https://github.com/tomashermansen-lang/eulex-rag
- https://arxiv.org/abs/2606.09724
- https://arxiv.org/abs/2605.24534 (commentaries from case databases)
- https://blog.forumforthefuture.be/fr/article/le-comir-92-fait-peau-neuve-.../9915
- https://questionfiscale.be/lexique/commentaire-code-impots-revenus-1992/
- Local: `myfin_docs/commentaires_dont_rep_rj/`, `experiments/results/09_corpus_c/*.json`, `experiments/data/corpus_c/questions_c.json`
