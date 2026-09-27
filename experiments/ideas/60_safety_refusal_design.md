# 60 — Safety and refusal design for tax advice

**Idea**

Wrap retrieval in three cheap guards that the MCP `search`/`fetch` results carry back to the answering model: (1) a **scope gate** (Belgian tax / other Belgian law / foreign tax / personal-situation advice / off-topic), (2) a **confidence tier** computed from retrieval signals only (reranker top score, top-1 vs top-2 margin, BM25↔dense agreement, temporal validity), and (3) an **abstention + disclaimer policy** keyed on the tier, plus a structured **audit log** per call. The answering LLM (DeepSeek later) is told, in the tool result itself, whether to answer, hedge, or redirect to SPF Finances / an ITAA member.

**Why it fits this project**

- MRR ≈ 0.70: the first hit is wrong ~30 % of the time; without a confidence signal the LLM answers fluently from the wrong circulaire. Retrieval-side uncertainty is the only lever we control before the LLM exists.
- Users act on answers; a wrong code or deadline has legal cost; superseded yearly versions (ideas 25/41) make validity a safety issue.
- MCP-native: the server cannot force the client LLM's wording, but it can return `scope`, `confidence`, `caveats`, `superseded_by` fields and put disclaimers in tool descriptions and result headers (idea 48).

**Evidence**

- GOV.UK Chat (Jan 2024, n=157): ~70 % found answers useful, yet "answers did not reach the highest level of accuracy demanded"; users **under-estimated inaccuracy risk because of the GOV.UK brand**. Mitigations: LLM restricted to retrieved context, red-teaming, personal data blocked. (verified)
- Stanford RegLab, arXiv 2405.20362: Lexis+ AI and Westlaw AI-AR hallucinate **17–33 %** despite RAG — grounding needs explicit verification/refusal. (verified)
- Trust-Align, arXiv 2409.11242: training RAG models to *refuse when evidence is insufficient* + cite gains 12–36 points over baselines on ASQA/QAMPARI/ELI5 — refusal is learnable and measurable. (verified)
- ANAO (ATO) and TIGTA (IRS) chatbot audits: oversight gaps rather than error rates; pages unreachable today — **unverified**.
- EU AI Act: Annex III point 5 covers public-authority *benefit eligibility* decisions, point 8 judicial use; a citizen-facing tax **information** assistant is not listed, so likely **not high-risk** (Art. 6(3) exemption plausible — unverified reading). **Art. 50** transparency ("you are talking to an AI") applies from **2 Aug 2026**. (verified)
- ITAA: law of 17 March 2019 + code of ethics — independence, competence, secrecy, disciplinary liability; the accountant stays personally liable; no AI-specific rule found (page verified, AI point unverified).

**How we would implement it**

1. **Scope gate**: rules + small classifier (idea 49); foreign tax / non-tax law → refuse with pointer; "should *I* …" → answer the rule, add "consult an ITAA member".
2. **Confidence tiers** from existing signals: reranker top score `s1`, margin `s1−s2`, RRF leg overlap@10, validity flag. Calibrate thresholds on the validation set plus ~50 new off-topic/unanswerable negatives, targeting precision ≥ 0.9 in tier A. A: answer + citations; B: answer + "low confidence, verify"; C: abstain, return hits as "possibly related".
3. **Result schema**: add `confidence`, `scope`, `disclaimer`, `superseded_by`; tool description states this is not tax advice and only the cited text binds the administration.
4. **Audit log**: query hash, GUIDs + scores, tier, index/model version, timestamp (feeds idea 55); no PII, ≤ 12-month retention.
5. With DeepSeek: verification pass (idea 53) downgrades the tier when the answer is not entailed by the cited chunk.

**Expected gain and cost**

A *precision-at-answer* gain, not MRR. Abstaining on the lowest-confidence 15–25 % of queries could roughly halve wrong answers delivered (estimate, unmeasured). Cost: 1–2 days engineering, ~50 negative queries for calibration, zero added latency.

**Risks / open questions**

- Reranker scores are poorly calibrated across doc types; thresholds tuned on ~64 questions will overfit.
- Over-abstention frustrates accountants; keep a "show anyway" path.
- MCP cannot guarantee the client LLM shows the disclaimer.
- AI Act classification and ITAA stance on AI-assisted advice need a proper legal read.

**Verdict**

**try-now** — the signals already exist, negatives can be added in a day, and it is the only mitigation that scales with the known 30 % top-1 error before any LLM is in the loop.

**Sources**

- https://insidegovuk.blog.gov.uk/2024/01/18/the-findings-of-our-first-generative-ai-experiment-gov-uk-chat/
- https://arxiv.org/abs/2405.20362 (Hallucination-Free? legal RAG tools)
- https://arxiv.org/abs/2409.11242 (Trust-Align)
- https://artificialintelligenceact.eu/annex/3/
- https://artificialintelligenceact.eu/article/50/
- https://www.itaa.be/fr/deontologie/
- https://www.anao.gov.au/ (ATO AI governance audit — unreachable, unverified)
- https://www.tigta.gov/ (IRS chatbot reviews — unreachable, unverified)
