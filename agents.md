# Agents Guide

## SDKs and documentation

When working with SDKs or libraries, always consult the **latest official documentation** for the version in use (for example [FastMCP](https://gofastmcp.com/) and the [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)) rather than relying only on older examples or memory.

## Dependency Management

Dependencies are managed by **UV** (`uv`). Do NOT use `pip install` directly.

## Playwright (crawl4ai)

Crawl4ai uses Playwright’s Chromium. After `uv sync`, install browser binaries once:

```bash
uv run playwright install chromium
```

Use `uv run playwright install` if you need all bundled browsers. Without this step, crawls fail with “Executable doesn’t exist” under `~/.cache/ms-playwright/`.
