"""Download the legal documents of the Fisconet+ (MyMinfin) navigation tree as Markdown.

Walks ``GET /navigation/tree`` (see MYFIN_ARBORESCENCE.md), fetches every leaf
document and follows the links of the "Table des matières" pages
(``fisconet.direct/{guid}`` and ``fisconet.compare/{guid}``) to reach the actual
articles, circulars, decrees... Only documents with legal value are kept, per
the policy in AGENTS.md / MYFIN_ARBORESCENCE.md § Classification:

- skipped sections: Veille documentaire, Working Papers, Lettres d'information,
  fossil-fuel subsidy inventory, external studies, "Compétences et formulaires";
- skipped types: Cours professionnels, Brochures et publications, Mémento fiscal,
  "aperçu documentaire" commentaries (ComIR 92), historical / "ancien" code versions;
- year-specific CIR 92 / AR-CIR 92 editions: only income years in ``KEEP_INCOME_YEARS``;
- tables of contents themselves are not saved (they only list links).

Embedded PDFs are skipped: the big coordinated PDFs are in ``myfin_pdfs/``
(``download_myfin_pdfs.py``).

Output: ``myfin_docs/<document-type>/<title>_<guid8>.md`` (YAML front matter +
Markdown body) and ``myfin_docs/manifest.json``.

Usage:
    uv run --package tax-ingestion python ingestion/scripts/download_myfin_docs.py
"""

from __future__ import annotations

import asyncio
import base64
import json
import re
import sys
import unicodedata
from pathlib import Path

import httpx
from bs4 import BeautifulSoup, NavigableString, Tag

BASE_URL = "https://www.minfin.fgov.be/myminfin-rest/fisconetPlus/public"
REPO_ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = REPO_ROOT / "myfin_docs"
CONCURRENCY = 8
RETRIES = 4
MAX_TOC_DEPTH = 2
MIN_BODY_CHARS = 200
KEEP_INCOME_YEARS = {2025, 2026, 2027}

TOC_TYPE = "Table des matières"
SKIP_TYPES = {"Cours professionnels", "Brochures et publications"}
SKIP_PATH_PARTS = (
    "Veille documentaire",
    "Working Papers",
    "Lettres d'information",
    "Inventaire des subventions",
    "Etudes et analyses externes",
    "Guide utilisateur",
)
SKIP_TITLE_RE = re.compile(
    r"Mémento|Memento|Compétences et formulaires|ComIR|aperçu documentaire|Historique|\(ancien\)"
    r"|\bancien\b|Cours de base|PDF",
    re.I,
)
INCOME_YEAR_RE = re.compile(r"[Rr]evenus(?: de)? (\d{4})")
LINK_RE = re.compile(r"fisconet\.(?:direct|compare)/([0-9a-f-]{36})")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def slugify(text: str, max_len: int = 80) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    text = re.sub(r"[^a-zA-Z0-9]+", "_", text).strip("_").lower()
    return text[:max_len].rstrip("_") or "document"


def fr(obj: dict | None) -> str:
    label = (obj or {}).get("label") or {}
    return label.get("fr") or label.get("nl") or (obj or {}).get("name") or ""


def year_allowed(title: str) -> bool:
    years = [int(y) for y in INCOME_YEAR_RE.findall(title)]
    return not years or any(y in KEEP_INCOME_YEARS for y in years)


def skip_reason(title: str, doc_type: str, path: str, taxonomies: list[str]) -> str | None:
    if any(part in path for part in SKIP_PATH_PARTS):
        return "excluded section"
    if doc_type in SKIP_TYPES:
        return f"excluded type ({doc_type})"
    if SKIP_TITLE_RE.search(title) or any("aperçu documentaire" in t for t in taxonomies):
        return "excluded title (index, history, training or PDF listing)"
    if not year_allowed(title):
        return "income year out of scope"
    return None


BLOCKS = {"p", "li", "tr", "h1", "h2", "h3", "h4", "h5", "h6", "pre", "blockquote"}
INLINE = {"span", "a", "b", "strong", "i", "em", "u", "font", "sup", "sub", "small", "abbr", "code"}


def is_layout_table(table: Tag, cells: list[list[Tag]]) -> bool:
    """True for tables used for page layout rather than tabular data."""
    if not cells or max(len(r) for r in cells) <= 1:
        return True
    if table.find(["table", "h1", "h2", "h3", "h4", "h5", "h6"]):
        return True
    return any(len(c.get_text(" ", strip=True)) > 1500 for row in cells for c in row)


def html_to_markdown(html: str) -> str:
    """Convert Fisconet HTML to Markdown, emitting each block once."""
    html = html.replace("﻿", "").replace("​", "")
    soup = BeautifulSoup(html, "html.parser")
    for el in soup(["script", "style"]):
        el.decompose()
    lines: list[str] = []

    def text_of(el: Tag) -> str:
        return re.sub(r"\s+", " ", el.get_text(" ", strip=True)).strip()

    def walk(node: Tag) -> None:
        # Consecutive inline content (text, spans, links...) forms one paragraph.
        inline: list[str] = []

        def flush() -> None:
            text = re.sub(r"\s+", " ", " ".join(inline)).strip()
            inline.clear()
            if text:
                lines.extend(["", text, ""])

        for child in node.children:
            if isinstance(child, NavigableString):
                if type(child) is NavigableString:  # skip comments, CDATA...
                    inline.append(str(child))
                continue
            if not isinstance(child, Tag):
                continue
            name = child.name
            if name in INLINE and not child.find(BLOCKS | {"table", "div"}):
                inline.append(child.get_text(" "))
                continue
            flush()
            if name in ("h1", "h2", "h3", "h4", "h5", "h6"):
                text = text_of(child)
                if text:
                    lines.extend(["", f"{'#' * (int(name[1]) + 1)} {text}", ""])
            elif name == "table":
                trs = [tr for tr in child.find_all("tr") if tr.find_parent("table") is child]
                cells = [[c for c in tr.find_all(["td", "th"], recursive=False)] for tr in trs]
                if is_layout_table(child, cells):
                    # Fisconet wraps whole documents in layout tables: walk the cells.
                    for row in cells:
                        for cell in row:
                            walk(cell)
                    continue
                rows = [[text_of(c) for c in row] for row in cells]
                rows = [r for r in rows if any(r)]
                if rows:
                    width = max(len(r) for r in rows)
                    lines.append("")
                    for i, r in enumerate(rows):
                        r = [c.replace("|", "\\|") for c in r] + [""] * (width - len(r))
                        lines.append("| " + " | ".join(r) + " |")
                        if i == 0:
                            lines.append("|" + " --- |" * width)
                    lines.append("")
            elif name == "li":
                text = text_of(child)
                if text:
                    lines.append(f"- {text}")
            elif name in ("p", "pre", "blockquote"):
                text = text_of(child)
                if text:
                    lines.extend(["", text, ""])
            elif name == "br":
                lines.append("")
            elif child.find(BLOCKS):
                walk(child)
            else:
                text = text_of(child)
                if text:
                    lines.extend(["", text, ""])
        flush()

    walk(soup)
    md = "\n".join(lines)
    md = re.sub(r"[ \t]+\n", "\n", md)
    return re.sub(r"\n{3,}", "\n\n", md).strip()


def yaml_value(value) -> str:
    return json.dumps(value, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Crawl
# ---------------------------------------------------------------------------

class Crawler:
    def __init__(self, client: httpx.AsyncClient) -> None:
        self.client = client
        self.sem = asyncio.Semaphore(CONCURRENCY)
        self.seen: set[str] = set()
        self.saved: dict[str, dict] = {}
        self.skipped: dict[str, dict] = {}
        self.errors: dict[str, str] = {}
        self.used_names: set[str] = set()

    async def fetch(self, guid: str) -> dict | None:
        for attempt in range(RETRIES):
            try:
                async with self.sem:
                    resp = await self.client.get(f"{BASE_URL}/document/{guid}")
                resp.raise_for_status()
                data = resp.json().get("data")
                if not data or not data.get("metadata"):
                    self.errors[guid] = "empty response"
                    return None
                return data
            except (httpx.HTTPError, ValueError) as exc:
                if attempt == RETRIES - 1:
                    self.errors[guid] = str(exc) or type(exc).__name__
                    return None
                await asyncio.sleep(2 ** (attempt + 1))
        return None

    async def visit(self, guid: str, tree_path: str, depth: int, via: str | None) -> None:
        if guid in self.seen:
            return
        self.seen.add(guid)
        data = await self.fetch(guid)
        if data is None:
            return

        meta, content = data["metadata"], data.get("content") or {}
        title = (meta.get("title") or "").strip()
        doc_type = fr(meta.get("documentType")) or "(sans type)"
        taxonomies = [fr(t) for t in meta.get("taxonomies") or []]
        path = tree_path or " > ".join(fr(p) for p in meta.get("pathItems") or [])
        html = ""
        if content.get("type") == "HTML" and content.get("content"):
            html = base64.b64decode(content["content"]).decode("utf-8", "replace")

        reason = skip_reason(title, doc_type, path, taxonomies)
        is_toc = doc_type == TOC_TYPE or title.lower().startswith("table des mati")
        # Follow links from tree documents and tables of contents only: ordinary
        # documents link to older versions and related texts, which would explode the crawl.
        if reason is None and html and depth < MAX_TOC_DEPTH and (depth == 0 or is_toc):
            links = list(dict.fromkeys(LINK_RE.findall(html)))
            await asyncio.gather(*(self.visit(g, "", depth + 1, guid) for g in links))

        if reason is None and is_toc:
            reason = "table of contents (links followed)"
        if reason is None and content.get("type") != "HTML":
            reason = f"content type {content.get('type')} (PDFs are in myfin_pdfs/)"
        body = html_to_markdown(html) if reason is None else ""
        if reason is None and len(body) < MIN_BODY_CHARS:
            reason = f"body too short ({len(body)} chars)"
        if reason:
            self.skipped[guid] = {"title": title, "document_type": doc_type, "reason": reason}
            return

        folder = slugify(doc_type, 60)
        name = f"{slugify(title)}_{guid[:8]}.md"
        rel = f"{folder}/{name}"
        (OUT_DIR / folder).mkdir(parents=True, exist_ok=True)
        front = {
            "guid": guid,
            "title": title,
            "document_type": doc_type,
            "language": meta.get("language"),
            "document_date": meta.get("documentDate"),
            "publication_date": meta.get("publicationDate"),
            "effective_date": meta.get("effectiveDate"),
            "last_modified": meta.get("lastModified"),
            "taxonomies": taxonomies,
            "path": [fr(p) for p in meta.get("pathItems") or []],
            "linked_document_nl": (meta.get("linkedDocument") or {}).get("nl"),
            "found_via": via,
            "source_url": f"{BASE_URL}/document/{guid}",
        }
        header = "---\n" + "".join(f"{k}: {yaml_value(v)}\n" for k, v in front.items()) + "---\n\n"
        (OUT_DIR / rel).write_text(f"{header}# {title}\n\n{body}\n", encoding="utf-8")
        self.saved[guid] = {**{k: front[k] for k in ("guid", "title", "document_type", "document_date",
                                                      "last_modified", "found_via")},
                            "file": rel, "chars": len(body)}
        if len(self.saved) % 250 == 0:
            print(f"  … {len(self.saved)} saved, {len(self.skipped)} skipped", flush=True)


def tree_leaves(tree: dict) -> list[tuple[str, str]]:
    leaves: list[tuple[str, str]] = []

    def walk(node: dict, path: list[str]) -> None:
        path = path + [fr(node)]
        guid = (node.get("documentId") or {}).get("fr")
        if guid and guid != "#":
            leaves.append((guid, " > ".join(path)))
        for child in node.get("children") or []:
            walk(child, path)

    for key, node in tree.items():
        if key != "FINANCE - Copy":
            walk(node, [])
    return leaves


async def main() -> int:
    OUT_DIR.mkdir(exist_ok=True)
    async with httpx.AsyncClient(timeout=180.0) as client:
        resp = await client.get(f"{BASE_URL}/navigation/tree")
        resp.raise_for_status()
        leaves = tree_leaves(resp.json()["data"])
        print(f"{len(leaves)} tree documents")
        crawler = Crawler(client)
        await asyncio.gather(*(crawler.visit(g, p, 0, None) for g, p in leaves))

    by_type: dict[str, int] = {}
    for doc in crawler.saved.values():
        by_type[doc["document_type"]] = by_type.get(doc["document_type"], 0) + 1
    skip_reasons: dict[str, int] = {}
    for doc in crawler.skipped.values():
        key = doc["reason"].split(" (")[0]
        skip_reasons[key] = skip_reasons.get(key, 0) + 1

    manifest = {
        "source": f"{BASE_URL}/navigation/tree",
        "income_years": sorted(KEEP_INCOME_YEARS),
        "count": len(crawler.saved),
        "by_document_type": dict(sorted(by_type.items(), key=lambda kv: -kv[1])),
        "skipped_by_reason": dict(sorted(skip_reasons.items(), key=lambda kv: -kv[1])),
        "errors": crawler.errors,
        "documents": sorted(crawler.saved.values(), key=lambda d: d["file"]),
        "skipped": dict(sorted(crawler.skipped.items())),
    }
    (OUT_DIR / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1) + "\n")
    print(f"{len(crawler.saved)} documents saved to {OUT_DIR}, {len(crawler.skipped)} skipped, "
          f"{len(crawler.errors)} errors")
    print(json.dumps(manifest["by_document_type"], ensure_ascii=False, indent=1))
    print(json.dumps(manifest["skipped_by_reason"], ensure_ascii=False, indent=1))
    return 1 if crawler.errors else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
