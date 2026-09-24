# How legal AI agents (Harvey & co.) work — technical research

Research date: 2026-09-24.

**Legend:**
- **[C]**: a cited source confirms the claim.
- **[I]**: our own inference or synthesis.

Most vendor claims come from the vendors' own blogs and press releases and are not independently audited. A few pages (openai.com/index/harvey, openai.com/index/blue-j, TR Labs Medium) blocked our fetcher, so we relied on search snippets and secondary summaries for those.

---

## 1. Harvey (harvey.ai)

### 1.1 Model strategy: from a custom OpenAI model to multiple models
- **2023–2024, custom case-law model with OpenAI [C].** Harvey found fine-tuning through the public APIs and plain RAG too limited. It worked with OpenAI to custom-train a model on US case law, adding roughly 10B tokens of legal data. Lawyers preferred its output to GPT-4's 97% of the time. Sources: [OpenAI customer story](https://openai.com/index/harvey/), [Microsoft/Azure story](https://www.microsoft.com/en/customers/story/19750-harvey-azure-open-ai-service).
- **May 2025, multi-model [C].** Harvey added Anthropic models (through Bedrock) and Google models (through Vertex). An "auto" router picks a model per task, and users can override it. Model strengths differ by task. Harvey now focuses its optimization on task execution, firm knowledge and collaboration rather than on the base model ([Expanding Harvey's Model Offerings](https://www.harvey.ai/blog/expanding-harveys-model-offerings)).
- **March 2026, "multi-model by design" [C].** Harvey routes across Claude, GPT and Gemini by task, availability and region, with failover when a provider has an outage ([blog](https://www.harvey.ai/blog/why-harvey-is-multi-model-by-design)).
- **February 2026, MCP connector [C].** Claude users can invoke Harvey workflows from inside Claude: Claude orchestrates and Harvey supplies the legal domain layer ([Legal IT Insider](https://legaltechnology.com/from-market-meltdown-to-strategic-realignment-harvey-and-lexisnexis-chart-diverging-paths-with-anthropic/)).
  - This is the same pattern this repo follows: an MCP server exposing a domain corpus to a general-purpose assistant.
- **Fine-tuning vs prompting [I].** The trend is away from a custom model and toward frontier models plus orchestration, retrieval and evals. Fine-tuning on firm data is problematic because much of it is client data ([interview](https://www.notion.com/blog/first-block-with-gabe-pereyra)). Bespoke customer-exclusive models remain available on an opt-in basis [C].

### 1.2 Product architecture
- **Assistant became a pure agent (mid-2025) [C].**
  - Built on the OpenAI Agents SDK. Retrieval, integrations and editing are all **tool calls** under one shared system prompt.
  - Feature teams ship **"Tool Bundles"**: groups of tools with their own prompt fragment. One example is a file-system bundle with grep-like search, open-file and semantic search.
  - Each bundle must pass **eval gates** (a dataset, evaluators and thresholds), plus **leave-one-out** checks that catch prompt/tool conflicts and context degradation.
  - Sources: [3 Principles… Agent Development](https://www.harvey.ai/blog/principles-that-helped-us-scale-agent-development), [ZenML summary](https://www.zenml.io/llmops-database/scaling-agent-based-architecture-for-legal-ai-assistant).
- **Vault [C].** Long-lived projects of roughly 1k–10k documents. Harvey distinguishes three corpus types:
  - ephemeral uploads (1–50 documents)
  - Vault projects
  - third-party legal and regulatory sources covering 45+ countries

  Source: [Enterprise-Grade RAG](https://www.harvey.ai/blog/enterprise-grade-rag-systems).
- **Agents [C].** Harvey's agents **plan** (split a task into steps), **adapt** (change the plan based on results) and **interact** with humans or other agents, with visible "thinking states" ([Introducing Agents](https://www.harvey.ai/blog/introducing-harvey-agents)).
- **Workflow Builder, renamed Agent Builder [C].** A no-code, block-based builder. Each step can use a different model, and agents are tested, permissioned and versioned before publishing ([blog](https://www.harvey.ai/blog/introducing-workflow-builder)). In May 2026 Harvey released 500 pre-built agents ([Law.com](https://www.law.com/legaltechnews/2026/05/05/harvey-launches-pre-built-ai-agents-self-service-customization-tool/)).

### 1.3 Retrieval
- **Vector infrastructure [C].** LanceDB Enterprise in production, and pgvector for small public-data projects. Harvey's stated design priorities:
  - **sparse + dense** representations, to handle rare terms and case identifiers
  - metadata filtering
  - ingestion throughput
  - hosting in the customer's own storage

  With PwC, Harvey built a tax system that was preferred over ChatGPT 91% of the time ([Enterprise-Grade RAG](https://www.harvey.ai/blog/enterprise-grade-rag-systems)).
- **Agentic Search (Dec 2025) [C].**
  - A ReAct-style loop: plan, then pick a source and query it, then reason, then check completeness, then retrieve again if needed, then answer with citations. It spans 150+ sources.
  - Complex queries went from 1 retrieval call to 3–10. Tool-selection precision reached 0.8–0.9.
  - Harvey tracks hallucination, tool recall, retrieval recall and answer quality.
  - Source: [Agentic Search](https://www.harvey.ai/blog/how-agentic-search-unlocks-legal-research-intelligence).
- **"Data Factory" (Feb 2026) [C].** Coverage went from 6 to 60+ jurisdictions and from 20 to 400+ sources. The pipeline:
  - A **Sourcing Agent** finds authoritative government portals.
  - A **Legal Review Agent** checks terms of use, with an attorney signing off.
  - Each source is evaluated at about 150k tokens: scenario generation, production simulation, and **trace validation, where any hallucinated citation rejects the source**.
  - Each jurisdiction is a **declarative config** (domains, filter hierarchies, permissions, agent instructions), so one agent can reason across all of them.
  - Source: [Using Agents to Scale Harvey's Knowledge Sources](https://www.harvey.ai/blog/using-agents-to-scale-harveys-knowledge-sources).
- **LexisNexis alliance (June 2025) [C].** Gives Harvey US case law, statutes and **Shepard's Citations** (good-law status) ([press release](https://www.globenewswire.com/news-release/2025/06/18/3101418/0/en/LexisNexis-and-Harvey-Announce-Strategic-Alliance-to-Integrate-Trusted-High-Quality-AI-Technology-and-Legal-Content-and-Develop-Advanced-Workflows.html)).

### 1.4 Citation grounding and hallucination control
- **Knowledge Source Identification [C].** An auto-evaluator that checks citations in three steps: metadata extraction, embedding retrieval, then LLM document matching. Reported at over 95% accuracy against attorney-validated sets ([Scaling AI Evaluation](https://www.harvey.ai/blog/scaling-ai-evaluation-through-expertise)).
- **Other controls [C].** Shepard's for validity; vetted, authoritative sources only; rejection of any source whose evaluation traces contain a hallucinated citation.
- **No independent audit [I].** We found no independent audit of Harvey equivalent to the Stanford study (section 3).

### 1.5 Evaluation
- **BigLaw Bench [C].**
  - Tasks are modeled on billable work, and each has a bespoke rubric.
  - Rubrics award **negative points for hallucination**.
  - Scoring is split: an **Answer Score**, and a **Source Score** (the share of correct claims that are correctly sourced).
  - Source: [Introducing BigLaw Bench](https://www.harvey.ai/blog/introducing-biglaw-bench).
- **Legal Agent Benchmark (May 2026) [C].** 1,200+ tasks and 75k+ expert rubric criteria. Grading is **all-pass**: a task fails if any single criterion fails ([LAB](https://www.harvey.ai/blog/introducing-harveys-legal-agent-benchmark)).
- **Process [C].**
  - Expert A/B tests with Likert ratings.
  - Nightly canary evals.
  - Vetting of each new model before adoption.
  - Eval data written by former lawyers, so no customer data is used.

### 1.6 Security [C]
- Zero data retention with model providers, and no training on customer data.
- Hosting options in the EU and Switzerland.
- Logically separated workspaces, with firms' ethical walls synced into access control.
- Retention set by the customer.
- Certifications: SOC 2 Type II, ISO 27001, 27701 and 42001.
- Sources: [Harvey Security](https://www.harvey.ai/security), [How Harvey manages customer data](https://www.harvey.ai/blog/how-harvey-manages-customer-data).

---

## 2. Comparable systems

- **Thomson Reuters CoCounsel / Westlaw Deep Research [C].**
  - Multi-agent: separate components for case law, statutes and secondary sources.
  - Multi-step planning, searches run **in parallel**, and explicit **stopping criteria** decide when research is done.
  - Westlaw features rebuilt as agent tools: search, citation-following and KeyCite.
  - Outputs carry inline citations, KeyCite flags and highlighted excerpts.
  - Evaluation uses calibrated LLM judges plus editorial review.
  - Sources: [TR press release](https://www.thomsonreuters.com/en/press-releases/2025/august/thomson-reuters-launches-cocounsel-legal-transforming-legal-work-with-agentic-ai-and-deep-research), [ZenML summary](https://www.zenml.io/llmops-database/agentic-ai-for-legal-research-building-deep-research-in-westlaw-and-cocounsel).
- **CoCounsel Tax / Checkpoint Edge [C].** Answers grounded in editorial content, the IRS code and firm documents, with agentic "Ready to Advise / Review" apps ([Checkpoint Edge](https://tax.thomsonreuters.com/en/products/checkpoint-edge)).
- **Lexis+ AI / Protégé [C].**
  - An **Orchestrator Agent** hands tasks to sub-agents.
  - **Shepard's Verify** flags citations that don't exist or aren't good law, in AI and human drafts alike.
  - A "Best Fit" router chooses between GPT and Claude models ([LawSites](https://www.lawnext.com/2025/08/lexisnexis-launches-protege-general-ai-expanding-the-agentic-capabilities-of-its-ai-assistant-to-general-ai-models-such-as-gpt-5.html)).
  - In August 2026 a dynamic "Legal Intelligence Engine" replaced the fixed workflows ([LawSites](https://www.lawnext.com/2026/08/lexisnexis-unveils-legal-intelligence-engine-rebuilding-protege-around-dynamic-agentic-orchestration.html)).
- **Legora [C].** Built on Claude. Its **Tabular Review** has one row per document and one column per question, and every cell links to its source ([Anthropic case study](https://claude.com/customers/legora)).
- **Luminance [C].** A proprietary legal LLM combined with a "Panel of Judges" mixture of experts that reaches consensus across models ([Luminance](https://www.luminance.com/ai-technology/)).
- **Blue J (tax) [C].** RAG over curated primary sources plus Tax Notes and IBFD commentary, producing fully cited answers. The IBFD partnership added cross-border coverage ([how it works](https://www.bluej.com/how-it-works), [IBFD](https://www.ibfd.org/news/blue-j-and-ibfd-unveil-ai-platform-instant-cross-border-tax-research)).
- **Big Four [C].**
  - **PwC Belgium** launched a Belgian tax model on Harvey (Sept 2025), trained on Belgian legislation, case law and regulatory sources, with source citations ([PwC BE](https://press.pwc.be/pwc-belgium-rolls-out-belgian-version-of-the-pwc-tax-ai-assistant-the-tax-profession-is-evolving-at-full-speed)).
  - **EY** runs 150+ tax agents on its EY.ai platform.
  - **Deloitte** has Zora AI.
- **Belgium [C].**
  - Wolters Kluwer **Libra**, added to InView Legal and monKEY in 2026 ([WK](https://www.wolterskluwer.com/en/news/wolters-kluwer-brings-libra-ai-workflows-into-inview-legal)).
  - **Accountable**, an AI tax assistant for Belgian self-employed people ([Accountable](https://www.accountable.eu/en-be/blog/first-ai-tax-advisor-in-belgium/)).
  - Neither publishes technical details.

---

## 3. The Stanford RegLab/HAI hallucination study (Magesh et al., 2024; JELS 2025)

**Setup [C].** 202 preregistered queries. A response counts as a hallucination if it is **incorrect** *or* **misgrounded**, meaning the cited source does not support the claim.

| Tool | Accurate | Hallucinated | Incomplete |
|---|---|---|---|
| Lexis+ AI | 65% | 17% | 18% |
| Westlaw AI-AR | 41% | 33% | 25% |
| Ask Practical Law AI | 19% | 17% | 62% |
| GPT-4 (baseline) | – | ~43% | – |

**Causes of error [C]:**
- **Naive retrieval**: the most relevant sources were not found.
- **Inapplicable authority**: wrong jurisdiction, or overruled or superseded law.
- **Reasoning errors**: misread holdings or ignored the court hierarchy.
- **Sycophancy**: accepting a false premise.

Sources: [arXiv 2405.20362](https://arxiv.org/abs/2405.20362), [JELS](https://onlinelibrary.wiley.com/doi/full/10.1111/jels.12413).

**Implications [I]:**
- RAG reduces hallucinations but does not eliminate them.
- Misgrounding is the subtle failure: a real source cited for a claim it doesn't support.
- Check each claim against the passage it cites, not just whether the citation exists.
- Filter authorities by validity date and jurisdiction.
- Allow "I don't know": an incomplete answer is safer than a confident error.

---

## 4. Common technical patterns

1. **Hybrid retrieval (BM25 + dense), plus a legal reranker.**
   - On **BSARD**, a set of 1,100 French-language Belgian legal questions over 22.6k statute articles, BM25 is competitive with zero-shot dense models, and fine-tuned dense retrieval does best ([BSARD](https://arxiv.org/abs/2108.11792)) [C].
   - LegalBench-RAG found a generic reranker underperformed on legal text ([arXiv 2408.10343](https://arxiv.org/abs/2408.10343)) [C].
2. **Structure-aware chunking.** One chunk per article or section, with metadata for its place in the code hierarchy. LegalBench-RAG found structure-respecting splits beat fixed-size chunks [C].
3. **Temporal validity.**
   - Commercial tools use citators (Shepard's, KeyCite) for good-law status [C].
   - For statutes, a 2026 benchmark on **French tax codes** found static RAG almost never retrieved the article version in force on the question's date. **Date-conditioned retrieval** over article versions with validity start and end dates reached about 98%. The authors recommend deterministic scoring over an LLM judge ([arXiv 2608.09393](https://arxiv.org/html/2608.09393v1)) [C].
4. **Query decomposition and iterative agentic search.** Plan, retrieve in parallel over several rounds, check completeness, and stop on explicit criteria (Harvey, TR, Lexis) [C].
5. **Orchestration.** Either one agent with modular tool bundles and declarative per-source configs (Harvey), or an orchestrator with specialist sub-agents (TR, Lexis). Models are routed per step, with failover [C].
6. **Citation verification.** Citator checks, matching each claim to its source passage, rejecting hallucinated traces during source onboarding, and linking every answer or cell to its passage [C].
7. **Human in the loop.** Visible reasoning steps, steps that ask for user input, and expert sign-off on new sources [C].
8. **Evals with expert rubrics.**
   - Atomic rubric criteria with hallucination penalties, and separate answer and source scores [C].
   - All-pass grading for agent work [C].
   - LLM judges calibrated against human grading [C].
   - Nightly regression runs [C].
   - Deterministic checks for amounts, rates and dates [C].
9. **Security.** Zero data retention with model providers, regional hosting and per-tenant isolation [C].
10. **Model strategy.** Frontier models plus retrieval, tools and evals have replaced custom LLMs. The moat is the **curated, versioned, citable content graph** and the **eval sets** [I].

---

## 5. What this means for Tax-on-web4AI [I]

| Harvey / industry pattern | Application here |
|---|---|
| MCP connector: the domain layer is exposed to a general assistant | Already our architecture (`mcp_server/`). Keep tools narrow and composable: `search`, `fetch`, and later `get_article(code, article, as_of)`, `list_versions`, `compute_*`. |
| Hybrid sparse + dense retrieval | Qdrant supports sparse vectors (BM25/SPLADE) alongside dense ones, so use hybrid queries with fusion. BSARD shows BM25 is strong on Belgian statutes. |
| Article-level chunking with hierarchy metadata | Chunk the CIR 92, TVA code and similar texts per article. Store the code, book, title, article number and paragraph. |
| Temporal validity ("as of" date) | Store `valid_from`/`valid_to` and the tax year (exercice d'imposition / revenus) on each chunk, and filter on them. This is critical for filing, which always concerns a past income year. |
| Citator / good-law status | Track when circulaires are replaced or withdrawn, and when rulings are overturned, using Fisconet+ change feeds. |
| Claim-level citation verification | Return passages with their Fisconet+ GUID and URL. Optionally add a `verify_citation(claim, source_id)` tool. |
| Eval sets with separate answer and source scores | Extend `validation_dataset` / `TESTING.md` with rubric-graded Q&A and deterministic checks for rates and amounts. |
| Agentic filing workflow | Break filing into steps: gather the facts, then classify income, then map it to form codes (`codes-administratifs.md`), then compute, then have a human review. |
| Multi-jurisdiction via declarative configs | One config per country (BE/FR/LU/NL) holding its sources, ID scheme, language and hierarchy. See `research/fr_lu_nl_tax_sources.md`. |
