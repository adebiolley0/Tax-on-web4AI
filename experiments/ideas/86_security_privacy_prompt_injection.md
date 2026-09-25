# 86 — Security and privacy: PII handling, prompt injection, MCP hardening

**Idea**

Treat the MCP server as a *data-only* boundary with three layers: (1) **PII minimisation** — queries scrubbed before logging, nothing personal stored raw, embedding/reranking local so no taxpayer text leaves the box; (2) **untrusted-content discipline** — retrieved chunks returned as typed data (`structuredContent`) with provenance markers and an injection flag, never merged into tool descriptions; (3) **transport hardening** — bearer/JWT auth, Host/Origin validation, localhost or reverse-proxy binding, stateless HTTP, request budgets.

**Why it fits this project**

- Users type income, family situation, addresses, sometimes national numbers; GDPR Art. 5(1)(c) minimisation and Art. 25 by-design apply from the first log line (idea 55 assumes scrubbed logs).
- The corpus is crawled; `fetch(urls)` accepts *any* URL, so a poisoned page can be pulled straight into the assistant's context.
- `server.py` has no auth, binds `0.0.0.0`, returns raw JSON strings; the MCP spec says servers MUST validate `Origin`, SHOULD bind localhost and authenticate.
- Local-only inference is the cheapest privacy control; make it a documented invariant.

**Evidence** (URLs in Sources)

- OWASP LLM Top 10 2025: LLM01 Prompt Injection (direct/indirect), LLM02 Sensitive Information Disclosure, LLM05 Improper Output Handling, LLM08 Vector/Embedding Weaknesses (2023's LLM07 *Insecure Plugin Design* is today's MCP tool surface). Mitigations: segregate external content, constrain output format, least-privilege tokens, adversarial testing.
- Greshake et al. 2023: retrieved data acts as "arbitrary code execution" in LLM-integrated apps.
- Spotlighting (Hines et al. 2024): delimiting/datamarking/encoding cut attack success from >50 % to <2 % on GPT models (unverified on small local models).
- CaMeL (Debenedetti et al. 2025): separating control from data flow gives provable security on 77 % of AgentDojo tasks; a read-only retrieval server is the easy case.
- Invariant Labs: tool poisoning (instructions hidden in tool descriptions), rug pulls (description changed after approval), cross-server shadowing; mitigation: pin versions by hash.
- MCP security best practices: no token passthrough; sessions MUST NOT authenticate; session ids MUST be non-deterministic.
- FastMCP ≥3: `host_origin_protection`, `allowed_hosts/allowed_origins`, `JWTVerifier`/`RemoteAuthProvider`, `stateless_http=True`, ASGI middleware; auth "highly recommended" for remote servers.

**How we would implement it**

1. **Scrubber** (0.5 day): Presidio + regexes for Belgian NRN (`YY.MM.DD-XXX.CC`, mod-97 check), IBAN, phone, e-mail, street+number. Applied to query text *before* the log row is written; retention 90 days pseudonymised; `LOG_PII_MODE=drop|hash|none`. Short DPIA in `SECURITY.md`.
2. **Content sandboxing**: Pydantic return models (idea 48) with the body under `untrusted_document_text`, `provenance {url, sha256, crawled_at, corpus_version}`, and `injection_flag` from a regex classifier ("ignore previous", role tags, `<|` tokens, zero-width/homoglyph chars); one fixed line in the result telling the host model to treat text as data. Strip scripts, HTML comments and `display:none` blocks at ingestion. `fetch` gets a domain allowlist (`*.belgium.be`, `*.fgov.be`), no off-list redirects, size cap, private-IP block (SSRF).
3. **Tool-surface integrity**: descriptions are code constants hashed in CI; `readOnlyHint=True`; no `tools/list_changed`.
4. **Transport**: default `host="127.0.0.1"`, `0.0.0.0` only behind Caddy/Traefik with TLS; `host_origin_protection=True`; `JWTVerifier` (static secret single-tenant, OIDC later); `stateless_http=True`; per-token rate limit and response-size cap via middleware; secrets from env only.
5. **Red-team set**: ~30 poisoned documents (body, PDF annex, Dutch, homoglyphs) run through the agent-loop harness; metric = share of runs where the host model obeys the injection.

**Expected gain and cost**

No retrieval-metric gain; removes the three blockers to any deployment beyond localhost (auth, PII in logs, open `fetch`). Cost ≈ 3–4 days (scrubber 0.5, structured returns 1 shared with idea 48, transport 0.5, red-team corpus 1–2); runtime overhead negligible.

**Risks / open questions**

- Spotlighting numbers come from GPT-4-class models; small local models may ignore markers — measure first.
- The host LLM is outside our control: the server can only *label* untrusted text; CaMeL-style enforcement needs the client.
- Over-scrubbing destroys signal (amounts are query content); hash numbers rather than drop them.
- Multi-tenant accountants need per-client OAuth scopes — out of scope now.
- Is NRN scrubbing enough when address + income year remain? Needs legal review (unverified).

**Verdict**

**try-now** — transport and scrubbing are one-day fixes the spec marks MUST/SHOULD, and the red-team corpus becomes a permanent regression test before any LLM ships.

**Sources**

- https://genai.owasp.org/llm-top-10/ ; https://genai.owasp.org/llmrisk/llm01-prompt-injection/
- https://arxiv.org/abs/2302.12173 ; https://arxiv.org/abs/2403.14720 ; https://arxiv.org/abs/2503.18813 ; https://arxiv.org/abs/2406.13352 (AgentDojo, not re-fetched)
- https://invariantlabs.ai/blog/mcp-security-notification-tool-poisoning-attacks
- https://modelcontextprotocol.io/specification/2025-06-18/basic/transports ; https://modelcontextprotocol.io/specification/2025-06-18/basic/security_best_practices
- https://gofastmcp.com/deployment/http ; https://gofastmcp.com/servers/auth/authentication
- https://microsoft.github.io/presidio/ (not re-fetched); server: `/home/user/Tax-on-web4AI/mcp_server/src/tax_mcp/server.py`; ideas 48, 55, 60.
