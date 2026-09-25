# 53 — Answer verification and citation grounding (attributed QA, NLI checkers, abstention)

**Idea**

Treat every answer as a set of claims, each tied to a quoted span of a retrieved chunk. After generation, a small open NLI/fact-check encoder scores whether each cited chunk *entails* its claim (ALCE-style citation precision/recall). Unsupported claims get a post-hoc support search over the 21k docs; if still weak, the claim is dropped or flagged and the assistant abstains. The MCP layer returns structured evidence (article id, exact quote, verifier score) so clients can render "verified citation" badges and quote highlighting.

**Why it fits this project**

- Wrong or *misgrounded* citations (real article, does not say that) are the dangerous failure for tax advice; the verifier targets exactly that.
- Chunks carry stable ids (article, circulaire §, ruling GUID), so "citation = chunk id + quote" is cheap to enforce; a quote not found in a retrieved chunk is by construction fabricated.
- MRR ≈ 0.70 means ~30 % of questions surface the wrong article first; a verifier catches the LLM confidently citing a near-miss (wrong year, wrong region — our near-duplicate problem).
- Open-weight, CPU-only, French: 0.1–0.6B encoder verifiers exist.

**Evidence**

- Stanford/RegLab study of Lexis+ AI, Westlaw AI-AR, Practical Law (arXiv 2405.20362, May 2024): RAG *reduces* but does not remove hallucination — 17 %, 33 %, 17 % hallucinated answers; "misgrounded" (real source, does not support claim) is a first-class category. It reports no verifier-recovery number.
- ALCE (arXiv 2305.14627, EMNLP 2023): NLI-based citation recall/precision; ChatGPT ASQA 73.6/72.5, ELI5 51.1/50.0; **rerank-by-citation-quality** lifts ASQA to 84.8/81.6; post-hoc citation of closed-book answers is poor (recall −47 %) because wording drifts from sources → verify against the chunks the answer *actually* used and keep claims close to quotes.
- MiniCheck (arXiv 2404.10774, EMNLP 2024): DeBERTa-L/RoBERTa-L ≈ 72.7 BAcc vs GPT-4 75.3 on LLM-AggreFact, "400× cheaper"; **English only**, untested in French.
- LettuceDetect (arXiv 2502.17125; github KRLabsOrg): token-level span detection, RAGTruth F1 79.2 (EN); French model `lettucedect-210m-eurobert-fr-v1` (EuroBERT-210M, MIT, 8k ctx) F1 65.7 (P 58.9 / R 74.3) on machine-translated RAGTruth-FR; 610M variant available.
- HHEM-2.1-Open (Vectara, Flan-T5-base 0.1B, Apache-2.0): ~1.5 s per 2k tokens on CPU; English-only.
- `MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7` (0.3B, MIT): XNLI-fr 0.823; generic NLI.
- FActScore-style claim decomposition (arXiv 2305.14251) needs an LLM (DeepSeek later).

**How we would implement it**

1. *Contract*: the `answer` tool (once DeepSeek exists) must emit `[claim, chunk_id, quote]` triples; a claim without a triple is rendered as "non sourcé".
2. *Locate*: fuzzy-match the quote in the chunk (rapidfuzz); mismatch ⇒ fabricated quote, hard reject.
3. *Entail*: score (chunk → claim) with mDeBERTa-xnli and lettucedect-fr; take the min. Thresholds tuned on ~100 hand-labelled (claim, chunk) pairs from the validation set.
4. *Recover*: unsupported claim ⇒ post-hoc search (hybrid + bge-reranker) using the claim as query; accept if top chunk entails.
5. *Abstain*: if >x % of claims unsupported or no claim covers the question's core, return "insufficient support" with the best chunks instead of an answer.
6. *Metrics*: citation precision/recall in the harness; report "answers with ≥1 misgrounded citation".
7. *Product*: verifier score + quote offsets in MCP output for badges/highlighting.

**Expected gain and cost**

Literature suggests catching a large share of misgrounded citations (ALCE reranking +11 pts citation recall; encoder checkers near GPT-4 in English), plausibly halving citation-level hallucinations; unverified for French legal text. CPU cost: 0.2–0.3B encoders, ~0.1–0.3 s per (claim, chunk) pair → 1–3 s per answer of 5 claims × 2 chunks; a recovery search adds ~1 s. One to two days to wire, plus labelling.

**Risks / open questions**

- French verifiers are trained on translated general-domain data; legal entailment (condition in another paragraph, exception in §3) may fool them both ways.
- Multi-hop claims (rate in art. X, condition in art. Y) need joint premises; encoders take one.
- Over-abstention hurts usefulness; the threshold must be measured.
- Without DeepSeek there is no claim decomposition; only quote-locate is testable now.

**Verdict**

**try-when-LLM** — quote-locate and citation metrics can be built now; the NLI gate only pays off once an answering LLM produces claims, and should ship with it from day one.

**Sources**

- https://arxiv.org/abs/2405.20362 (Hallucination-Free? legal RAG tools)
- https://arxiv.org/abs/2305.14627 (ALCE)
- https://arxiv.org/abs/2404.10774 (MiniCheck)
- https://arxiv.org/abs/2502.17125 (LettuceDetect)
- https://github.com/KRLabsOrg/LettuceDetect
- https://huggingface.co/KRLabsOrg/lettucedect-210m-eurobert-fr-v1
- https://huggingface.co/vectara/hallucination_evaluation_model (HHEM-2.1-Open)
- https://huggingface.co/MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7
- https://arxiv.org/abs/2305.14251 (FActScore; not fetched this session)
