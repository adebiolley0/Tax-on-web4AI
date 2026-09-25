# 48 — Tool design for the MCP retrieval server

**Idea**

Replace the current three loosely typed tools (`search` → scraped HTML, `fetch(urls)`, `semantic_search` with free-string filters, all returning raw JSON strings) by a small, namespaced, typed tool set built on "search then fetch": search returns *short, citable* hits (stable ids, snippets, facet counts, `next_cursor`); fetch returns one document by id with a `mode` enum controlling size; a few narrow lookups cover cases where ranking is the wrong primitive (article by number, graph neighbours, indexed amounts, procedures). Descriptions are prompts, filters are enums, every error says what to do instead.

**Why it fits this project**

- Hybrid retrieval (BM25 + dense + reranker) stays *inside* the server; the LLM sees one `search`, not three legs.
- Ideas 27 (facets), 31/32 (citation graph, breadcrumb), 33/39 (definitions, amounts) each need a surface; fixing it once lets experiments plug in.
- DeepSeek has weak Belgian-law priors: enum-typed filters and explicit ids reduce hallucinated filters and citations; `url` on every hit makes citations render in ChatGPT-style clients.
- 100k documents and long statutes make response budgets (25k tokens Claude Code default) real: snippets by default, full text on demand.

**Evidence**

- Few, non-overlapping tools; `response_format` enum (206 → 72 tokens); pagination + truncation with steering text; actionable errors; descriptions written "for a new hire"; evaluate with agentic loops (accuracy, calls, tokens). https://www.anthropic.com/engineering/writing-tools-for-agents
- Tool-use examples in definitions lifted accuracy 72 % → 90 %; tool search helps only past ~10 tools. https://www.anthropic.com/engineering/advanced-tool-use
- Just-in-time context: keep lightweight identifiers, load on demand; bloated tool sets are a named failure mode. https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents
- Documentation alone matches few-shot demonstrations for tool use. https://arxiv.org/abs/2308.00675
- MCP spec: `outputSchema` + `structuredContent`, `resource_link`, `readOnlyHint`, `isError` results. https://modelcontextprotocol.io/specification/2025-06-18/server/tools
- FastMCP: Pydantic returns → structured output, `Literal`/`Enum` params, `ToolError` survives masking. https://gofastmcp.com/servers/tools
- OpenAI deep-research connectors *require* `search(query) → {id,title,url}` and `fetch(id) → {id,title,text,url,metadata}`; citations only when `url` is non-empty. https://developers.openai.com/api/docs/mcp
- Fewer tools → better function-calling accuracy and 70 % lower latency on small models (DATE 2025). https://arxiv.org/abs/2411.15399
- MCP-Bench (250 tools, 20 LLMs): failures concentrate on tool discovery and multi-hop grounding. https://arxiv.org/abs/2508.20453
- CourtListener v4: `snippet`, opt-in `highlight=on`, cursor `next`. https://wiki.free.law/c/courtlistener/help/api/rest/v4/search
- MCPEval: auto-generates tasks from MCP servers, scores trajectories. https://arxiv.org/abs/2507.12806

**How we would implement it**

Namespace `beltax_*`, all `readOnlyHint=True`, Pydantic return models, French descriptions with 2–3 worked examples each.

1. `beltax_search(query, document_type?: Literal[circulaire, code, commentaire, jurisprudence, ruling, qp, ar], region?: Literal[fed, wal, bxl, vla], income_year?: int, code?: Literal[CIR92, CTVA, CDS, CIR-BXL…], limit=10, cursor?)` → `{hits:[{id, title, url, doc_type, region, year, citation (e.g. "Art. 171 CIR 92"), snippet ≤ 400 chars, score, breadcrumb}], facet_counts, next_cursor, notes}`. Soft-route when filters absent; on zero hits with filters, relax and say so in `notes`.
2. `beltax_fetch(id, mode: Literal[summary, section, full]=section, section?: str)` → `{id, title, url, text, sections:[…], metadata}`; `full` truncated at ~8k tokens with "use section=…" steering.
3. `beltax_article(code, article, version_year?)` → exact statute/commentary text; version list.
4. `beltax_related(id, relation: Literal[cites, cited_by, siblings, commentary, same_article_other_year], limit=10)`.
5. `beltax_browse(node_id?)` → children of a hierarchy node (Fisconet arborescence).
6. `beltax_amount(concept, income_year, region?)` → indexed amount + source id (idea 39).
7. `beltax_procedure(topic)` → step list with deadlines/forms and source ids.

Ids: stable, self-describing (`fisconet:GUID#art171`); URL always present. Errors: `ToolError("Code 'CIR' inconnu — valeurs: CIR92, CTVA…")`. Evaluation: 40–60 tasks (questions A/B/C + procedural) through a minimal agent loop with Claude and DeepSeek; metrics = answer correctness (LLM-judge), citation precision, tool calls/task, tokens/task, wrong-filter rate; A/B description variants; log LLM-chosen filters vs router (idea 27).

**Expected gain and cost**

Not a retrieval-metric gain: expect ≤ 3 tool calls per answer, 3–5× fewer response tokens than today's full-chunk JSON, and fewer fabricated article numbers thanks to `beltax_article`. Cost: ~3 days for tools 1–4 (5–7 depend on ideas 32/39), one day for the agent-loop harness.

**Risks / open questions**

- Seven tools is near where weak models start confusing them; `amount`/`procedure` may merge into `search` filters.
- Snippets cut legal conditions mid-sentence; use section-aligned snippets, not fixed windows.
- Facet vocabularies must be final before enums ship.
- Year semantics (income vs assessment) still unresolved — expose both or document clearly.
- LLMs rarely paginate; `limit` + steering may suffice (unverified).

**Verdict**

try-now — cheap, decouples retrieval experiments from the client, and the agent-loop harness becomes our first end-to-end evaluation.

**Sources**

URLs inline above; current server: `/home/user/Tax-on-web4AI/mcp_server/src/tax_mcp/server.py`.
