FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install crawl4ai browser system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy shared common package and MCP package
COPY tax_search /app/tax_search
COPY mcp_server /app/mcp_server

# Install both packages (tax-search is a local path dep of tax-mcp-server)
RUN pip install ./tax_search ./mcp_server

# Install Playwright browsers for crawl4ai
RUN python -m playwright install --with-deps chromium

EXPOSE 8000

ENV QDRANT_URL=http://qdrant:6333 \
    QDRANT_COLLECTION=belgian_tax_docs

CMD ["fastmcp", "run", "tax_mcp.server:mcp", "--transport", "streamable-http", "--host", "0.0.0.0", "--port", "8000"]
