# 35 — Case-law retrieval: what COLIEE / CLERC / LePaRD / ECtHR-PCR teach for our 1.9k court decisions

**Idea**

Treat court decisions as *structured* documents. Parse each Fisconet decision into header line
(matter keywords), *Résumé* (headnote), *Texte intégral*; build one always-French "headnote chunk" =
title + court + date + matter + keywords + résumé; extract cited articles ("art. 113 C. succ.") into a
`cited_articles` field; keep BM25 first stage with field boosts and MaxP; filter on court / date /
matter. Later (DeepSeek) generate résumés + concept keywords where missing.

**Why it fits this project**

- Local profile (2026-09-25): `jurisprudence_belge` 1,730 docs, median 15.5k chars; **1,499 have a
  `Résumé`** (median 1.1k chars, p90 2.4k), 1,395 a `Texte intégral`, of which ≈705 are Dutch — the
  résumé is then the *only* French text. Matters: succession 720, enregistrement 711, taxes assimilées
  201. 871 docs cite `C. succ.` / `C. enreg.` articles. `jurisprudence_europeenne`: 126/155 have a résumé.
- Titles are "Arrêt de … du dd.mm.yyyy"; the topic lives in the header line ("Recouvrement –
  Prescription – …") and the résumé — the headnote/regeste that Swiss and Cour de cassation
  (*sommaire/titrage*) systems key on.
- Our queries are citizen questions, not full case documents; only the structural lessons of "prior
  case retrieval" transfer — and they are cheap.

**Evidence**

- BM25 is a strong case-law baseline: ECtHR-PCR (LREC-COLING 2024, arXiv 2404.00596) BM25 R@50 22.1 /
  R@100 27.8 / MAP 9.65 vs dense bi-encoder 20.4 / 29.3 / 6.72; dense degrades more over time. CLERC
  (NAACL 2025, arXiv 2406.17186): zero-shot BM25 R@1000 48.3 vs best bi-encoders 42.4, ColBERTv2 17.6;
  fine-tuned LegalBERT-DPR 68.5. CJEU passages (ICAIL 2025, arXiv 2506.12895): BM25 beats zero-shot dense
  on 4/7 metrics (R@5 63.6 vs 61.3 Ada-v2); fine-tuned 33M SBERT beats BM25.
- Section choice matters: ECtHR-PCR, indexing the *law/reasoning* section alone (R@100 28.7, MAP 10.3)
  beats *facts* alone (24.8 / 8.2) — the reasoning/headnote carries the retrievable signal.
- Segments + statute field: COLIEE 2022 (arXiv 2304.08188) passage-level > document-level (dev F1
  0.118 → 0.140), plus an extracted statute-section field → 0.145. COLIEE 2021 runner-up (arXiv
  2105.05686): plain BM25 on 10-sentence windows, max over windows.
- Summaries: COLIEE 2025 NOWJ (arXiv 2509.08025) Qwen-2.5-14B summaries + bge-m3 pre-ranking R@200
  0.778, R@500 0.895 (recall up, R@1 slightly down); winners use BM25 first stage (76–85 % recall at
  top 100–200) then reranking. LeCoPCR (arXiv 2501.14114) concept-augmented queries: BM25 MAP 9.54 →
  9.78, Longformer 11.59 → 13.68; oracle concepts R@50 32.9 vs 22.
- Counter-example: LePaRD (ACL 2024) argument-context → passage, low lexical overlap: BM25 rc@10 26.8
  vs fine-tuned SBERT 62.1 (10k passages). Not our query type. Citation-graph tricks (CaseLink,
  fenced citation context) need dense inter-case citations; our slice has few. Skip.

**How we would implement it**

1. Parser (`ingestion`): split decisions into `keywords` / `resume` / `full_text`; language-detect the
   full text; regex `cited_articles` (`art\. ?\d+\w*(?: ?§ ?\d+)?` + `C\. succ\.|C\. enreg\.|CIR 92|C\. TVA`);
   emit metadata `court`, `decision_date`, `matter` (path[1]), `has_resume`, `body_lang`.
2. Chunk 0 = headnote chunk (title + court + date + matter + keywords + résumé), always French; body
   chunks tagged `section=full_text`.
3. BM25 (bm25s / LanceDB FTS): headnote boost ×2, `cited_articles` field; doc score = max over chunks.
4. Filters: court / date range / matter as SQL metadata (same mechanism as region filters, exp 08).
5. Eval: ~13 case-law questions in `questions_c.json` + 20 new ones written from résumés of
   Dutch-body decisions; log to leaderboard.
6. Later (DeepSeek): résumé + 5 concept keywords for the 231 Belgian / 29 EU docs without one;
   optional query-side concept expansion (LeCoPCR).

**Expected gain and cost**

Case-law slice ≈ 9 % of corpus C; on its questions +0.05–0.15 MRR, ≤ +0.02 overall. Cost: 1–2 days
parser + re-index, no new models, no GPU.

**Risks / open questions**

- Header line is inconsistent (sometimes repeats the title, once an HTML span).
- Résumés may omit the fact a user asks about; over-boosting could hide motivation-level details.
- Dutch bodies stay unsearchable in French beyond the résumé (idea 10).
- Only ~13 existing questions target decisions — small, noisy evaluation.
- Benchmarks are English/EU, case-as-query; transfer unverified.

**Verdict**

**try-now** — a cheap structural change (headnote chunk, cited-article field, court/date filters)
every case-law benchmark supports; the LLM summary/keyword extension waits for DeepSeek.

**Sources**

https://arxiv.org/abs/2404.00596 · https://arxiv.org/abs/2501.14114 · https://arxiv.org/abs/2406.17186 ·
https://arxiv.org/abs/2311.09356 · https://arxiv.org/abs/2506.12895 · https://arxiv.org/abs/2105.05686 ·
https://arxiv.org/abs/2304.08188 · https://coliee.org/documents/waivers/overview_COLIEE2024.pdf ·
https://arxiv.org/abs/2509.08025 · https://dl.acm.org/doi/10.1145/3769126.3785016 (paywalled; abstract only) ·
https://arxiv.org/abs/2607.17142 · https://aclanthology.org/2022.lrec-1.509.pdf
