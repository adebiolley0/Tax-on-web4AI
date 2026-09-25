# 73 — Mining a larger Belgian tax QA test set from existing question/answer sources (no LLM)

**Idea**

Grow the 133 hand-written questions to 500+ by harvesting *questions that someone already asked* and whose answer already names the governing text: (1) the 1,362 Fisconet+ parliamentary questions (PQs) — the QUESTION block is the query, the article citations in the REPONSE block map to `code_et_legislation/` ids; (2) the 16 "FAQ" circulaires (2019/C/40, 2019/C/134 …) and the 7 `faq/` documents, whose numbered headings are natural questions and whose answer paragraphs are the passage-level ground truth; (3) the 581 SDA rulings with an "Objet de la demande" section, which state a fact pattern plus the articles whose application is requested; (4) SPF Finances web FAQs (finances.belgium.be) as an extra layman-phrased source. Ground truth is derived by regex from citations, then filtered, and the whole set is split by topic so that no topic straddles train/val/test.

**Why it fits this project**

- Measurement is the bottleneck (idea 58): n≈130 gives SE(MRR)≈0.05, so most +0.02…+0.05 ideas are invisible. Sources 1–3 are already local, French, and citable, so no LLM and no crawling is needed to reach n≈600.
- PQ and FAQ questions are *not* written from the target document's title (unlike our corpus C set, EXPERIMENTS.md §5), so they correct the lexical bias that currently favours BM25.
- Ruling "objets" give exactly the accountant-style multi-article questions (idea 45) that the hand-written set lacks.

**Evidence (local counts, `myfin_docs/`)**

- PQs: 1,362 files, 1,359 in French; 1,089 have a bare `QUESTION` line, 583 a `REPONSE`/`Réponse` heading; 538 answers cite `art. N … CIR/WIB/Code`, 297 cite "article N … Code des droits de succession/d'enregistrement"; only 19 cite a circulaire. 767 are dated ≥ 2015.
- Topic skew: 532 registration duties, 327 succession, 256 assimilated taxes (vehicle taxes), 145 misc. taxes, **only 59 IPP, 1 ISoc, 12 VAT** — the opposite of what taxpayers ask.
- `code_et_legislation/` ids are article-granular and region/year-suffixed (`article_100_du_code_des_droits_d_enregistrement_region_wallonne_…`, `article_171_cir_92_revenus_2026_…`; 1,278 registration and 793 succession article files), so a citation "article 100 C.enr." maps to 3 regional files → list all as acceptable ids, as corpus C already does.
- FAQ circulars: 16 titled FAQ, 462 numbered question headings; `faq/`: 7 documents, 318 `?` headings (e.g. "2. Quel montant puis-je verser ?" in FAQ épargne-pension).
- Rulings: 581 with "Objet de la demande", 535 of which cite an article inside that section (e.g. 2018.0775: art. 211 §1 CIR 92 + art. 115/120 C.enr.).
- finances.belgium.be answered a CAPTCHA to WebFetch here; `WEBSITE_FINDINGS.md` records the Akamai interstitial as bypassable with the crawl4ai session (FAQ extraction 96–97 %). La Chambre publishes QRVA bulletins as PDF per legislature with full-text search (fetched, no bulk API).
- Forum/expert Q&A (e.g. accountant forums, Fisconetplus commentary blogs): licence unverified; assume not redistributable — skip.

**How we would implement it**

1. `scripts/mine_questions.py` (regex only): PQ → split on `QUESTION`/`REPONSE`; keep sub-questions ≤ 400 chars that end with `?`; parse citations (`art(icle)?\.? N(bis|ter)? … (CIR 92|C\.? ?enr\.|Code des droits de succession|Code TVA)`), resolve to `code_et_legislation/` ids by article number + code, expanding regions/years to `expected` + `secondary`. Secondary positive: the PQ file itself.
2. FAQ circulars/`faq/`: heading = question, answer chunk = passage ground truth; document-level positive = the FAQ file; also attach any article cited in the answer.
3. Rulings: "Objet de la demande" paragraph → question after stripping "La demande vise à obtenir la confirmation que"; positives = the ruling id + cited articles.
4. Quality filters: drop questions asking for statistics/budget ("combien de fois", "quel est le coût"), policy opinions ("le ministre envisage-t-il"), or answers that cite nothing; require the cited article file to exist and contain the article number; de-duplicate near-identical questions (MinHash on tokens); cap each code at 25 % of the set to flatten the registration/succession skew; downweight pre-2005 PQs (regionalised law since 2002).
5. Split by `topic` = (code, article range) clusters, not by source: all questions on art. 171 CIR go to one fold; keep the 133 human questions as held-out test; PQ/ruling-mined sets serve as train/val for ideas 12, 14, 74.
6. Label 10 % by hand (≈60 questions, ~3 h) to estimate citation-mapping precision before trusting the numbers.

**Expected gain and cost**

No retrieval gain; ~600–900 extra questions with document-level ground truth for ≈1 day of scripting plus 3 h checking; SE(MRR) halves. Expected precision of derived labels 80–90 % (unverified) — usable for relative comparisons and for fine-tuning data.

**Risks / open questions**

- PQ bias: policy-oriented, minister-addressed, old, and dominated by regional duties; a set built from them rewards succession/registration retrieval, not IPP.
- Answers cite the *provision*, not the *best* document; a commentaire or circulaire may be the better hit and will count as a miss.
- Regional/yearly article variants inflate "acceptable ids" and mask temporal errors (idea 25).
- Circular FAQ questions are near-verbatim in the target document → easy for BM25 (same bias as corpus C); keep them as a separate "easy" slice.
- Rulings anonymise facts ("société X"), so questions are abstract.

**Verdict**

**try-now** — the PQ, FAQ-circular and ruling sources are already local and citation-parseable; a one-day regex pipeline yields 600+ labelled questions, provided the set is stratified and reported per source slice.

**Sources**

- `myfin_docs/questions_parlementaires/`, `myfin_docs/circulaires/circulaire_2019_c_134_faq_…`, `myfin_docs/faq/faq_epargne_pension_02bee55b.md`, `myfin_docs/decisions_anticipees_l_24_12_2002/` (local)
- https://www.lachambre.be/kvvcr/showpage.cfm?section=qrva&language=fr&cfm=qrvaList.cfm (fetched)
- https://finances.belgium.be/fr/particuliers/avantages_fiscaux/epargne_pension (CAPTCHA on fetch; see `WEBSITE_FINDINGS.md`)
- `experiments/ideas/58_label_free_evaluation.md`, `experiments/EXPERIMENTS.md` §5
