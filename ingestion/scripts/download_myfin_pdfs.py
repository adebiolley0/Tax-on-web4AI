"""Download every PDF publication of the Fisconet+ (MyMinfin) public library.

The public library (``GET /library/documents``) lists the coordinated codes
published as PDF: CIR 92 and AR/CIR 92 (federal + regional editions), Code TVA,
registration / inheritance duty codes, Flemish Codex, Brussels procedure code...

The real PDF bytes are embedded base64 in ``GET /document/{guid}``
(``data.content.type == "PDF"``). The ``/pdf?id=`` endpoint must NOT be used for
these: it returns a generic placeholder (the Fisconet+ user guide).

Output: ``myfin_pdfs/<slug>.pdf`` at the repository root plus
``myfin_pdfs/manifest.json`` with the document metadata, for later RAG
ingestion.

Usage:
    uv run --package tax-ingestion python ingestion/scripts/download_myfin_pdfs.py
"""

from __future__ import annotations

import asyncio
import base64
import hashlib
import json
import re
import sys
import unicodedata
from pathlib import Path

import httpx
import pymupdf

BASE_URL = "https://www.minfin.fgov.be/myminfin-rest/fisconetPlus/public"
REPO_ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = REPO_ROOT / "myfin_pdfs"
LANGUAGE = "fr"
CONCURRENCY = 4
RETRIES = 4

# Library items without legal value (see MYFIN_ARBORESCENCE.md § Classification).
# They are still downloaded but flagged ``ingest: false`` in the manifest.
NON_LEGAL_TITLES = ("memento fiscal",)


def slugify(text: str, max_len: int = 110) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    text = re.sub(r"[^a-zA-Z0-9]+", "_", text).strip("_").lower()
    return text[:max_len].rstrip("_")


async def get_json(client: httpx.AsyncClient, url: str, **params) -> dict:
    for attempt in range(RETRIES):
        try:
            resp = await client.get(url, params=params or None)
            resp.raise_for_status()
            return resp.json()
        except (httpx.HTTPError, ValueError):
            if attempt == RETRIES - 1:
                raise
            await asyncio.sleep(2 ** (attempt + 1))
    raise AssertionError("unreachable")


async def download_one(client: httpx.AsyncClient, item: dict, sem: asyncio.Semaphore) -> dict:
    guid = item["id"]
    async with sem:
        payload = await get_json(client, f"{BASE_URL}/document/{guid}")
    data = payload["data"]
    meta = data["metadata"]
    content = data["content"]
    pdf_guid = guid
    if content.get("type") == "HTML" and content.get("content"):
        # Some library entries are an HTML table of contents whose "[PDF]" link
        # points to another Fisconet document holding the coordinated PDF.
        html = base64.b64decode(content["content"]).decode("utf-8", "replace")
        for linked in dict.fromkeys(re.findall(r"fisconet\.direct/([0-9a-f-]{36})", html)):
            async with sem:
                linked_data = (await get_json(client, f"{BASE_URL}/document/{linked}"))["data"]
            if linked_data["content"].get("type") == "PDF":
                pdf_guid, content = linked, linked_data["content"]
                break
    if content.get("type") != "PDF" or not content.get("content"):
        raise ValueError(f"{guid}: content type is {content.get('type')!r}, not an embedded PDF")

    pdf_bytes = base64.b64decode(content["content"])
    if not pdf_bytes.startswith(b"%PDF"):
        raise ValueError(f"{guid}: decoded content is not a PDF")
    with pymupdf.open(stream=pdf_bytes, filetype="pdf") as doc:
        pages = doc.page_count

    filename = f"{slugify(item['title'])}.pdf"
    (OUT_DIR / filename).write_bytes(pdf_bytes)

    return {
        "guid": guid,
        "pdf_guid": pdf_guid,
        "file": filename,
        "library_title": item["title"].strip(),
        "title": meta.get("title"),
        "summary": meta.get("summary"),
        "language": meta.get("language"),
        "document_type": (meta.get("documentType") or {}).get("label", {}).get("fr"),
        "taxonomies": [t.get("label", {}).get("fr") for t in meta.get("taxonomies") or []],
        "path": [p.get("label", {}).get("fr") for p in meta.get("pathItems") or []],
        "document_date": meta.get("documentDate"),
        "last_modified": meta.get("lastModified"),
        "linked_document_nl": (meta.get("linkedDocument") or {}).get("nl"),
        "pages": pages,
        "size_bytes": len(pdf_bytes),
        "sha256": hashlib.sha256(pdf_bytes).hexdigest(),
        "source_url": f"{BASE_URL}/document/{pdf_guid}",
        "ingest": not any(t in item["title"].lower() for t in NON_LEGAL_TITLES),
    }


async def main() -> int:
    OUT_DIR.mkdir(exist_ok=True)
    async with httpx.AsyncClient(timeout=180.0) as client:
        library = (await get_json(client, f"{BASE_URL}/library/documents", language=LANGUAGE))["data"]
        # One item (the external user guide) has a SharePoint URL instead of a GUID: skip it.
        items = [i for i in library if re.fullmatch(r"[0-9a-f-]{36}", i["id"])]
        skipped = [i["title"] for i in library if i not in items]
        print(f"{len(library)} library items, {len(items)} with a Fisconet GUID, skipped: {skipped}")

        sem = asyncio.Semaphore(CONCURRENCY)
        results = await asyncio.gather(
            *(download_one(client, i, sem) for i in items), return_exceptions=True
        )

    entries, errors = [], []
    for item, res in zip(items, results):
        if isinstance(res, Exception):
            errors.append(f"{item['id']} {item['title']}: {res}")
        else:
            entries.append(res)
            print(f"  ok  {res['pages']:>5} p  {res['size_bytes'] / 1e6:6.1f} MB  {res['file']}")

    manifest = {
        "source": f"{BASE_URL}/library/documents?language={LANGUAGE}",
        "count": len(entries),
        "documents": sorted(entries, key=lambda e: e["file"]),
    }
    (OUT_DIR / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")

    for err in errors:
        print(f"  ERR {err}", file=sys.stderr)
    print(f"{len(entries)} PDFs saved to {OUT_DIR}, {len(errors)} errors")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
