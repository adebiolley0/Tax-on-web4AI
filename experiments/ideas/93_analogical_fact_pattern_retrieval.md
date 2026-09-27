# 93 — Analogical retrieval by structured fact patterns (fact frames for rulings and court decisions)

**Idea**

Represent each of the 1.2k SDA rulings and 1.7k court decisions as a **fact frame**: `{tax_type, parties (person / SA-BV / holding / ASBL), transaction (scission partielle, apport, donation, vente d'actions…), assets, region (VCF / Wallonie / Bruxelles / fédéral), amount band, intent (motifs économiques valables, abus fiscal), cited articles, outcome}`. The user's plain-words situation is mapped to the same frame (lexicon slot-filling now, LLM later); precedents are ranked by **frame similarity** — weighted slot overlap + dense similarity of a *verbalised* frame ("Personne physique apporte des actions d'une SA à une holding; plus-value interne; art. 90, 9° CIR 92") — fused with résumé BM25. Factor-based case-based reasoning (TAXMAN, HYPO/CATO) rebuilt on embeddings.

**Why it fits this project**

- Both corpora carry half a frame for free (ideas 35/36): rulings have a controlled keyword header (`Motifs économiques valables` 471×, `Scission partielle` 271×), a French résumé in 1,145/1,216, `Objet / Décision` sections; decisions have a matter line, résumé in 1,499/1,730, cited `C. succ.`/`C. enreg.` articles in 871. Regional tax (succession 720, enregistrement 711) makes `region` a decisive slot that text similarity blurs.
- "Is there a ruling where the SDA accepted X in my situation?" is answered badly by a 3k-token bilingual document embedding; a frame answers it and explains the match slot-by-slot, which accountants need.
- Half the bodies are Dutch; frames are language-neutral.

**Evidence**

- Facts-only encoders beat text baselines case-to-case: SAILER (SIGIR 2023) encodes the *facts* section and reconstructs reasoning/decision; zero-shot LeCaRD NDCG@10 0.798 vs BM25 0.712; COLIEE 2020 fine-tuned MRR@10 0.882 vs 0.788 (Chinese/English criminal cases). DELTA (AAAI 2025) pulls [CLS] toward *key facts*, further gains (unverified).
- Structured reformulation beats raw text: PromptCase replaces the full case by LLM-extracted "legal facts + legal issues" and reports superior zero-shot COLIEE results; CaseGNN builds graphs from those facts/issues; CBR-RAG (ICCBR 2024) scores intra/inter-component similarity over case parts and reports significantly better legal QA answers than plain RAG. Deltas unverified (abstracts only).
- Counter-evidence: ECtHR-PCR (LREC-COLING 2024) — indexing *facts* alone (R@100 24.8, MAP 8.2) is **worse** than the law/reasoning section (28.7 / 10.3); a frame must keep articles/outcome, not just facts.
- Tax CBR history: TAXMAN (McCarty 1977) hand-coded corporate reorganisation cases; HYPO/CATO factor systems never scaled past a few hundred cases [memory]. "Pearl"/"PRESTA": not located.
- Every benchmark above is case→case; none tests layman-situation→case.

**How we would implement it**

1. Frame schema (YAML, ~12 slots, closed vocabularies per tax type) on the idea-36 parser. Rules: tax type/keywords from headers; transaction/assets via a FR/NL lexicon (~200 terms); parties via `SA|SPRL|BV|NV|ASBL|M\.|Mme`; region via court seat and `VCF` vs `C. succ.`; amounts via the idea-14 regex, binned. 2–3 days.
2. Verbalise each frame as one French sentence; embed with e5-small (2.9k sentences, minutes on CPU); slots in SQLite (idea 17) for filters.
3. Score `0.4·weighted slot-Jaccard + 0.3·dense(frame) + 0.3·BM25(résumé)`; hard filter on tax type/region when given.
4. Query side: idea-50 slot filling with the same lexicon, clarification for missing decisive slots, fallback to résumé retrieval when < 2 slots fill.
5. Eval: 25 "my situation" questions, one target each; baseline = idea-36 résumé BM25+dense.
6. LLM phase: DeepSeek fills all slots + outcome for 2.9k docs (~$3) and extracts the user frame at query time.

**Expected gain and cost**

Fact-pattern queries on the rulings/decisions subset: +0.05–0.15 MRR over résumé-only retrieval [estimate], mostly from region/tax-type/transaction filters removing near-duplicate confusions; corpus-wide ≈ +0.01. Product gain (explainable match, "your case differs on holding duration") exceeds the metric gain. Cost: 2–3 days, negligible CPU, ~$3 LLM later.

**Risks / open questions**

- Rule extraction on Dutch bodies and courts' free prose will be noisy; ruling header keywords are the only reliable "intent" source.
- Frames flatten what rulings turn on (timing, holding period, reinvestment); text must stay in the fusion.
- Users rarely state amounts/region, so matching degrades to text retrieval.
- Tiny eval set; no evidence for layman→case queries; SAILER/DELTA need GPU pre-training, not reusable here.

**Verdict**

**try-when-LLM** — ship the cheap slot-filter subset now inside idea 36; real analogical matching needs LLM-quality frames on both document and query sides.

**Sources**

- https://arxiv.org/abs/2304.11370 (SAILER; html tables read)
- https://arxiv.org/abs/2403.18435 (DELTA)
- https://arxiv.org/abs/2309.02962 (PromptCase)
- https://arxiv.org/abs/2312.11229 (CaseGNN)
- https://arxiv.org/abs/2404.04302 (CBR-RAG)
- https://arxiv.org/abs/2404.00596 (ECtHR-PCR; section numbers via idea 35)
- https://arxiv.org/abs/2305.05393 (CaseEncoder)
- https://aclanthology.org/2024.acl-long.350.pdf (legal case retrieval survey)
- Local: `experiments/ideas/35_case_law_retrieval.md`, `36_rulings_structured_extraction.md`, `50_clarification_slot_filling.md`
