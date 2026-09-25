# 42 — Typed cross-document links and answer bundles

**Idea**

A typed edge table beside the index (`interprets`, `applies`, `answers_on`, `faq_of`, `cites`, `amends/abrogates`, `version_of`, `regional_twin`, `translates`, `seq`) built from Fisconet+ metadata and exp 11's citation grammars, no LLM. At query time the flat ranking stays; a *bundle* is assembled around the top hit, one slot per role (statute · interpretation · practice · FAQ), filled from the top-k, else from typed neighbours. Exposed as a `bundle` field of `search` and a `bundle(id)` tool.

**Why it fits this project**

Users need article + circulaire + ruling/case together; MRR rewards one document and exp 11 showed score propagation cannot serve both (val −0.05…+0.02). Fisconet+ ships the relations: an API probe (25 Sep 2026) of 71 random documents found 48 with curated `relatedDocuments` (169 edges, 137 to articles): rulings 8/8, commentaries 8/8, cases 7/8, QPs 7/8, FAQs 5/7, articles 7/8, circulaires 3/8, treaties 0/8. E.g. Circ. 2025/C/9 → "Suisse - Texte coordonné", "Article 34, CIR 92 (historique)". Also `linkedDocument.{nl,previous,next}`, `historyLink`, `regionalisation{federal,flanders,wallonia}`, shared keyword GUIDs. None is in `myfin_docs/` front matter.

**Evidence**

- Local: exp 11 text citations — `cite_art` 270k, `cite_jur` 2,156, `cite_circ` 1,482, `cite_da` 99, `cite_qp` 23; 57–62 % of article mentions resolved; expansion lifts recall@10 (0.775 → 0.825/0.850) but lowers MRR; CIR 92 art. 2 has 1,092 citers. Corpus C: 24/64 questions list `secondary` documents, but only 3 pairs cross types, so today's set cannot measure bundles.
- Legal products model these edges editorially: KeyCite groups citing references by document type with depth of treatment (examined/discussed/cited/mentioned) and negative-treatment flags; Shepard's uses seven signals plus phrases (followed, distinguished, questioned, overruled); Légifrance article pages show "Créé par / Abrogé par / Textes liés / Voir les versions" and LEGI status codes M/Ab/T/D/A/S. A machine citator (followed/contradicted/abandoned/cited) is claimed by legifrance.dev (unverified).
- SearchFireSafety (arXiv 2604.06173, ACL 2026): citation graph from hyperlinks + regex, no LLM; structure-aware reranking over BGE-M3 R@10 53.77 → 54.70, nDCG@10 37.67 → 38.05 (Korean statutes). "The Missing Link" (arXiv 2506.22165, Jun 2025): joint case+norm heterogeneous graph +3.1 AP on citation prediction.
- Diversification and users: Maxwell, Azzopardi, Moshfeghi (IRJ 2019, 51 participants, BM25 vs BM25+xQuAD): on aspectual tasks users marked more relevant documents and found more novel aspects. Fang et al. (2011): xQuAD beats MMR, which admits non-relevant items when the base ranking is weak. Zhou et al. (SIGIR 2012, 56 topics): aggregated-page metrics track user preference better than diversity metrics. arXiv 2502.09017 (Apr 2025): MMR raises pre-LLM chunk recall 2–9 points, downstream only 1–3.

**How we would implement it**

1. Metadata re-crawl of 21k GUIDs (~3–6 h at 1–2 req/s) → SQLite `edge(type, src, dst, confidence, date)`; type from source×target document types (`applies` for DA/jur→article, `interprets` for circ/comm→article, `faq_of`, `answers_on`); confidence 1.0 curated, 0.9 exact-number regex (`refparse.py`), 0.5 bare "article N". Grammar for "modifié/abrogé/remplacé par" gives `amends/abrogates`.
2. Bundle assembly (dict lookups): anchor = rank-1 after reranking; slots [statute, interpretation, practice, FAQ] filled from top-20 by type, else from anchor neighbours (curated > regex, keyword overlap with query, recency; cap 3 per slot). Flat ranking untouched.
3. Label 30 corpus-C questions with a triple (article, circulaire/commentary, practice), `relatedDocuments` as candidate list; add *slot hit-rate* to `rag_eval`; xQuAD with types as sub-queries as follow-up.

**Expected gain and cost**

MRR unchanged by design. Statute slot fillable for ~70 % of practice/commentary anchors from curated edges alone; interpretation slot weaker (circulaire coverage 3/8 curated, plus 1,482 regex edges). The real payoff is perceived completeness and fewer agent tool calls, as exp 11 recommended. Cost: one crawl, 2–3 days code, 1 day labelling; query-time overhead negligible.

**Risks / open questions**

Hub articles make reverse edges noisy (within-slot ranking is the hard part); `relatedDocuments` often point to *historique* versions, so `version_of` must map to the current edition; ~30 % of documents have no curated edge; treatment polarity (distinguished vs followed) is editorial in KeyCite/Shepard's and needs an LLM here; user evidence comes from news/web collections; the bundle metric does not exist yet.

**Verdict**

try-now — the curated `relatedDocuments` edges are free, precise and untapped; build the edge table and a slot-filled bundle without touching the ranking.

**Sources**

- `experiments/11_graph_retrieval/README.md`; `experiments/data/corpus_c/questions_c.json`; `WEBSITE_FINDINGS.md` (API field table); API probe 25 Sep 2026
- https://arxiv.org/abs/2604.06173 · https://arxiv.org/abs/2506.22165 · https://arxiv.org/abs/2502.09017
- https://strathprints.strath.ac.uk/67026/ (Maxwell et al. 2019) · https://www.eecis.udel.edu/~hfang/pubs/ddr11.pdf · https://dl.acm.org/doi/10.1145/2348283.2348302
- https://library.purdueglobal.edu/westlaw_guide/keycite · https://supportcenter.lexisnexis.com/app/answers/answer_view/a_id/1088155 · https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000006392117/2025-03-20 · https://www.legifrance.dev/docs (unverified)
