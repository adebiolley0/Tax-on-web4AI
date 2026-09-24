"""Download every public MyMinfin (Fisconet+) PDF into ``myfin_pdfs/`` at the repo root.

The PDFs are kept as raw source material for the RAG pipeline. Two sources are
combined (see MYFIN_ARBORESCENCE.md and WEBSITE_FINDINGS.md § Fisconet+):

1. **Bibliothèque publique** — ``GET /library/documents?language={lang}``:
   curated publications (CIR 92, AR/CIR 92, Code TVA, regional codes, …).
2. **Navigation tree** — ``GET /navigation/tree``: every leaf node carries a
   ``documentId`` per language (the 420 leaves listed in MYFIN_ARBORESCENCE.md).

Each document is fetched through ``GET /pdf?id={guid}&language={lang}``.

Filtering follows the AGENTS.md document policy: training material, portal
help pages, newsletters, the Mémento fiscal, aperçu documentaire index pages
and tables of contents are skipped. The Fisconet+ PDF endpoint returns a
generic placeholder for many documents; identical files served for several
distinct GUIDs are detected by hash, removed, and flagged in the manifest.

Downloads are resumable: files already on disk (valid ``%PDF`` header) are
not fetched again.

Usage::

    uv run python ingestion/scripts/download_myfin_pdfs.py
    uv run python ingestion/scripts/download_myfin_pdfs.py --languages fr nl
    uv run python ingestion/scripts/download_myfin_pdfs.py --dry-run
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import logging
import re
import sys
import unicodedata
from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import httpx

logger = logging.getLogger("download_myfin_pdfs")

BASE_URL = "https://www.minfin.fgov.be/myminfin-rest/fisconetPlus/public"
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUT_DIR = REPO_ROOT / "myfin_pdfs"
TIMEOUT = httpx.Timeout(120.0, connect=30.0)
MAX_RETRIES = 4
# WEBSITE_FINDINGS.md recommends 1-2 req/s for bulk operations.
REQUEST_DELAY_S = 0.6
# GitHub rejects files > 100 MB; flag anything close to it.
GITHUB_FILE_LIMIT = 95 * 1024 * 1024
# The same bytes served for this many distinct GUIDs = generic placeholder.
PLACEHOLDER_MIN_DUPLICATES = 3

UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.I)

# Titles / breadcrumb segments excluded by the AGENTS.md filtering policy.
EXCLUDE_PATTERNS = [
    r"cours professionnels?",
    r"beroepsopleiding",
    r"guide utilisateur",
    r"gebruikershandleiding",
    r"m[ée]mento fiscal",
    r"fiscaal memento",
    r"aper[çc]u documentaire",
    r"documentair overzicht",
    r"lettres? d.information",
    r"nieuwsbrie",
    r"veille documentaire",
    r"comp[ée]tences et formulaires",
    r"bevoegdheden en formulieren",
    r"tables? des mati[èe]res",
    r"inhoudstafel",
    r"working papers?",
    r"briefing notes?",
    r"subventions? fossiles?",
    r"fossiele subsidies",
]
EXCLUDE_RE = re.compile("|".join(EXCLUDE_PATTERNS), re.I)


@dataclass
class PdfTarget:
    guid: str
    language: str
    title: str
    source: str  # "library" | "tree"
    path: list[str] = field(default_factory=list)
    file: str | None = None
    status: str = "pending"  # downloaded | cached | skipped | placeholder | failed
    size: int | None = None
    sha256: str | None = None
    error: str | None = None


# ---------------------------------------------------------------------------
# Discovery
# ---------------------------------------------------------------------------

def _label(value, language: str) -> str:
    if isinstance(value, dict):
        return value.get(language) or value.get("fr") or next(iter(value.values()), "") or ""
    return value or ""


def _unwrap(payload):
    if isinstance(payload, dict) and "data" in payload and len(payload) <= 3:
        return payload["data"]
    return payload


def iter_tree_leaves(node, language: str, path: list[str] | None = None):
    """Yield ``(guid, title, breadcrumb)`` for every tree node with a document in *language*."""
    path = path or []
    if isinstance(node, list):
        for child in node:
            yield from iter_tree_leaves(child, language, path)
        return
    if not isinstance(node, dict):
        return

    title = _label(node.get("label") or node.get("title"), language)
    children = node.get("children") or []
    doc_id = node.get("documentId")
    if isinstance(doc_id, dict):
        doc_id = doc_id.get(language)
    if doc_id and isinstance(doc_id, str) and UUID_RE.match(doc_id):
        yield doc_id, title, path
    for child in children:
        yield from iter_tree_leaves(child, language, path + [title] if title else path)


def is_excluded(title: str, path: list[str]) -> bool:
    return any(EXCLUDE_RE.search(part or "") for part in [title, *path])


async def _get_json(client: httpx.AsyncClient, url: str, **params):
    for attempt in range(MAX_RETRIES + 1):
        try:
            resp = await client.get(url, params=params or None)
            resp.raise_for_status()
            return _unwrap(resp.json())
        except (httpx.HTTPError, ValueError) as exc:
            if attempt == MAX_RETRIES:
                raise
            wait = 2 ** (attempt + 1)
            logger.warning("GET %s failed (%s), retrying in %ss", url, exc, wait)
            await asyncio.sleep(wait)


async def discover_targets(client: httpx.AsyncClient, languages: list[str]) -> list[PdfTarget]:
    targets: dict[tuple[str, str], PdfTarget] = {}

    def add(t: PdfTarget) -> None:
        key = (t.guid.lower(), t.language)
        if key in targets:
            return
        if is_excluded(t.title, t.path):
            t.status, t.error = "skipped", "excluded by document policy"
        targets[key] = t

    for lang in languages:
        library = await _get_json(client, f"{BASE_URL}/library/documents", language=lang)
        items = library if isinstance(library, list) else (library or {}).get("documents", [])
        for item in items:
            guid = str(item.get("id") or "")
            title = _label(item.get("title"), lang)
            if not UUID_RE.match(guid):
                # e.g. "Guide utilisateur externe" whose id is a SharePoint URL.
                logger.info("Library item without UUID id skipped: %s", title)
                continue
            add(PdfTarget(guid=guid, language=lang, title=title, source="library",
                          path=["Bibliothèque publique"]))
        logger.info("[%s] library: %d items", lang, len(items))

    tree = await _get_json(client, f"{BASE_URL}/navigation/tree")
    for lang in languages:
        n = 0
        for guid, title, path in iter_tree_leaves(tree, lang):
            add(PdfTarget(guid=guid, language=lang, title=title, source="tree", path=path))
            n += 1
        logger.info("[%s] navigation tree: %d leaf documents", lang, n)

    return list(targets.values())


# ---------------------------------------------------------------------------
# Download
# ---------------------------------------------------------------------------

def slugify(text: str, max_len: int = 90) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    text = re.sub(r"[^A-Za-z0-9]+", "-", text).strip("-").lower()
    return text[:max_len].rstrip("-") or "document"


def target_path(out_dir: Path, t: PdfTarget) -> Path:
    return out_dir / t.language / t.source / f"{slugify(t.title)}__{t.guid[:8]}.pdf"


async def download_one(client: httpx.AsyncClient, t: PdfTarget, out_dir: Path) -> None:
    dest = target_path(out_dir, t)
    if dest.exists() and dest.read_bytes()[:4] == b"%PDF":
        data = dest.read_bytes()
        t.file = str(dest.relative_to(out_dir))
        t.status, t.size, t.sha256 = "cached", len(data), hashlib.sha256(data).hexdigest()
        return

    for attempt in range(MAX_RETRIES + 1):
        try:
            resp = await client.get(f"{BASE_URL}/pdf", params={"id": t.guid, "language": t.language})
            if resp.status_code == 404:
                t.status, t.error = "failed", "HTTP 404"
                return
            resp.raise_for_status()
            data = resp.content
            if not data.startswith(b"%PDF"):
                t.status = "failed"
                t.error = f"not a PDF (content-type={resp.headers.get('content-type')}, {len(data)} bytes)"
                return
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(data)
            t.file = str(dest.relative_to(out_dir))
            t.status, t.size, t.sha256 = "downloaded", len(data), hashlib.sha256(data).hexdigest()
            t.error = None
            return
        except httpx.HTTPError as exc:
            t.error = str(exc) or type(exc).__name__
            if attempt == MAX_RETRIES:
                t.status = "failed"
                return
            await asyncio.sleep(2 ** (attempt + 1))


def flag_placeholders(targets: list[PdfTarget], out_dir: Path) -> None:
    """Remove files whose exact bytes are served for many distinct GUIDs."""
    have = [t for t in targets if t.status in ("downloaded", "cached")]
    counts = Counter(t.sha256 for t in have)
    for t in have:
        if counts[t.sha256] >= PLACEHOLDER_MIN_DUPLICATES:
            (out_dir / t.file).unlink(missing_ok=True)
            t.status, t.error = "placeholder", f"identical bytes served for {counts[t.sha256]} GUIDs"
            t.file = None


def write_manifest(targets: list[PdfTarget], out_dir: Path, languages: list[str]) -> dict:
    stats = Counter(t.status for t in targets)
    kept = [t for t in targets if t.status in ("downloaded", "cached")]
    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": BASE_URL,
        "languages": languages,
        "stats": dict(stats),
        "total_bytes": sum(t.size or 0 for t in kept),
        "oversized_for_github": [t.file for t in kept if (t.size or 0) > GITHUB_FILE_LIMIT],
        "documents": [asdict(t) for t in sorted(targets, key=lambda t: (t.language, t.source, t.file or t.title))],
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    return manifest


async def run(out_dir: Path, languages: list[str], dry_run: bool, concurrency: int) -> dict:
    headers = {"Accept": "application/json, application/pdf", "User-Agent": "tax-on-web4ai/0.1 (+RAG research)"}
    async with httpx.AsyncClient(timeout=TIMEOUT, headers=headers, follow_redirects=True) as client:
        targets = await discover_targets(client, languages)
        todo = [t for t in targets if t.status == "pending"]
        logger.info("%d targets (%d to fetch, %d excluded)", len(targets), len(todo),
                    len(targets) - len(todo))
        if dry_run:
            for t in todo:
                logger.info("  %s/%s  %s  %s", t.language, t.source, t.guid, t.title)
            return write_manifest(targets, out_dir, languages)

        sem = asyncio.Semaphore(concurrency)
        done = 0

        async def worker(t: PdfTarget) -> None:
            nonlocal done
            async with sem:
                await download_one(client, t, out_dir)
                await asyncio.sleep(REQUEST_DELAY_S)
            done += 1
            logger.info("[%d/%d] %-10s %s", done, len(todo), t.status, t.file or t.title)

        await asyncio.gather(*(worker(t) for t in todo))

    flag_placeholders(targets, out_dir)
    return write_manifest(targets, out_dir, languages)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--languages", nargs="+", default=["fr"])
    parser.add_argument("--concurrency", type=int, default=2)
    parser.add_argument("--dry-run", action="store_true", help="List targets without downloading PDFs")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    manifest = asyncio.run(run(args.out_dir, args.languages, args.dry_run, args.concurrency))
    logger.info("Stats: %s — %.1f MB kept", manifest["stats"], manifest["total_bytes"] / 1e6)
    if manifest["oversized_for_github"]:
        logger.warning("Files over GitHub's 100 MB limit: %s", manifest["oversized_for_github"])
    return 0 if manifest["stats"].get("failed", 0) == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
