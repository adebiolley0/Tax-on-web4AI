# 73 — Mining a larger Belgian tax QA test set from existing Q&A sources (no LLM)

**Idea**

Grow the 133 hand-written questions to 500+ by harvesting questions someone already asked whose answer names the governing text: (1) the 1,362 Fisconet+ parliamentary questions (PQs): QUESTION block = query, article citations in the REPONSE block → `code_et_legislation/` ids; (2) the 16 "FAQ" circulaires and 7 `faq/` documents: numbered headings = questions, answer paragraphs = passage ground truth; (3) the 581 SDA rulings with an "Objet de la demande": fact pattern + the articles whose application is requested; (4) SPF Finances web FAQs as a layman-phrased extra. Ground truth is derived by regex from citations, filtered, and split by topic.

**Why it fits this project**

- Measurement is the bottleneck (idea 58): at n≈130, SE(MRR)≈0.05, so +0.02…+0.05 ideas are invisible. Sources 1–3 are local, French, citable: no LLM, no crawling.
- PQ and FAQ questions are not written from the target's title (unlike corpus C, EXPERIMENTS.md §5), so they correct the BM25-favouring bias.
- Ruling "objets" are accountant-style multi-article questions (idea 45) we lack.

**Evidence (local counts, `myfin_docs/`)**

- PQs: 1,362 files, 1,359 French; 1,089 have a bare `QUESTION` line, 583 a `REPONSE` heading; 538 answers cite `art. N … CIR/Code`, 297 cite an article of the succession/registration codes, only 19 a circulaire; 767 dated ≥ 2015.
- Topic skew: 532 registration duties, 327 succession, 256 vehicle taxes, 145 misc.; **only 59 IPP, 1 ISoc, 12 VAT**: the inverse of taxpayer demand.
- `code_et_legislation/` ids are article-granular and region/year-suffixed (`article_100_du_code_des_droits_d_enregistrement_region_wallonne_…`, `article_171_cir_92_revenus_2026_…`; 1,278 registration and 793 succession article files), so "article 100 C.enr." maps to 3 regional files → list all as acceptable ids, as corpus C does.
- FAQ circulars: 16 files, 462 numbered question headings; `faq/`: 7 files, 318 `?` headings ("2. Quel montant puis-je verser ?").
- Rulings: 581 with "Objet de la demande", 535 citing an article there (e.g. 2018.0775: art. 211 CIR 92, art. 115/120 C.enr.).
- finances.belgium.be returned a CAPTCHA to WebFetch; `WEBSITE_FINDINGS.md` records the Akamai interstitial as bypassable via crawl4ai (FAQ extraction 96–97 %). La Chambre serves QRVA bulletins as per-legislature PDFs, no bulk API (fetched).
- Forum/expert Q&A: licence unverified; skip.

**How we would implement it**

1. `scripts/mine_questions.py` (regex only). PQ: split on `QUESTION`/`REPONSE`; keep sub-questions ≤ 400 chars ending in `?`; parse `art(icle)?\.? N(bis|ter)? … (CIR 92|C\.? ?enr\.|Code des droits de succession|Code TVA)`; resolve to `code_et_legislation/` ids by article + code, expanding regions/years into `expected` + `secondary`; the PQ file itself is a secondary positive.
2. FAQ circulars/`faq/`: heading → question, answer chunk → passage label, FAQ file → document label, plus any article cited in the answer.
3. Rulings: "Objet de la demande" paragraph → question (strip "La demande vise à obtenir la confirmation que"); positives = ruling id + cited articles.
4. Filters: drop statistics questions ("combien de fois"), policy questions ("le ministre envisage-t-il") and answers citing nothing; require the cited article file to exist; MinHash de-duplication; cap each code at 25 % of the set; downweight pre-2005 PQs (regionalised law).
5. Split by topic = (code, article-range) cluster, not by source: all art. 171 CIR questions in one fold; the 133 human questions stay the held-out test; mined sets serve as train/val for ideas 12, 14, 74.
6. Hand-check 10 % (≈60 questions, ~3 h) for citation-mapping precision.

**Expected gain and cost**

No retrieval gain; 600–900 extra document-labelled questions for ≈1 day of scripting plus 3 h checking; SE(MRR) halves. Label precision 80–90 % expected (unverified): fine for relative comparisons and fine-tuning.

**Risks / open questions**

- PQ bias: policy-oriented, minister-addressed, old, dominated by regional duties; the set rewards succession/registration retrieval, not IPP.
- Answers cite the provision, not the best document; a commentaire or circulaire may be the better hit and count as a miss.
- Regional/yearly variants inflate acceptable ids and mask temporal errors (idea 25).
- FAQ-circular questions are near-verbatim in the target → BM25-easy; report as a separate slice.
- Rulings anonymise facts ("société X"), so questions are abstract.

**Verdict**

**try-now** — the sources are local and citation-parseable; a one-day regex pipeline yields 600+ labelled questions, provided results are reported per source slice.

**Sources**

- Local: `myfin_docs/{questions_parlementaires,faq,decisions_anticipees_l_24_12_2002}/`, `circulaires/circulaire_2019_c_134_faq_…`
- https://www.lachambre.be/kvvcr/showpage.cfm?section=qrva&language=fr&cfm=qrvaList.cfm (fetched)
- https://finances.belgium.be/fr/particuliers/avantages_fiscaux/epargne_pension (CAPTCHA on fetch; see `WEBSITE_FINDINGS.md`)
- `experiments/ideas/58_label_free_evaluation.md`, `experiments/EXPERIMENTS.md` §5
