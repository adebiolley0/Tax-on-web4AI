"""Regenerate MYFIN_ARBORESCENCE.md from the live Fisconet+ (MyMinfin) public API.

Every section derived from the API is rebuilt: global statistics, document-type
counts, public-library publications, change-feed years and the full navigation
tree. The hand-written "Classification" section (ingestion policy) is kept
verbatim from the existing file.

Usage:
    uv run --package tax-ingestion python ingestion/scripts/build_myfin_arborescence.py
"""

from __future__ import annotations

import asyncio
import datetime as dt
import re
from pathlib import Path

import httpx

BASE_URL = "https://www.minfin.fgov.be/myminfin-rest/fisconetPlus/public"
PORTAL_URL = "https://www.minfin.fgov.be/myminfin-web/pages/public/fisconet"
OUT_FILE = Path(__file__).resolve().parents[2] / "MYFIN_ARBORESCENCE.md"
LANGUAGES = ("fr", "nl", "de", "en")
# Empty duplicate branch exposed by the API.
IGNORED_BRANCHES = {"FINANCE - Copy"}

# Grouping of the public-library publications, first matching rule wins.
LIBRARY_GROUPS = [
    ("AR/CIR 92", lambda t: t.startswith("AR/CIR")),
    ("Impôts sur les revenus (CIR 92)", lambda t: t.startswith("CIR 92")),
    ("TVA / Douanes", lambda t: "TVA" in t or "douane" in t.lower()),
    ("Fiscalité régionale", lambda t: "flamand" in t.lower() or "bruxellois" in t.lower()
     or t.startswith("Arrêté du gouvernement de la région")),
    ("Droits et taxes", lambda t: t.startswith(("Code des", "Code du", "Arrêté royal"))),
    ("Autres", lambda t: True),
]


async def get(client: httpx.AsyncClient, path: str, **params):
    resp = await client.get(f"{BASE_URL}{path}", params=params or None)
    resp.raise_for_status()
    return resp.json()["data"]


async def search_facets(client: httpx.AsyncClient, language: str) -> dict:
    body = {
        "searchCriteria": {"language": language, "searchTerms": "", "orderBy": "RELEVANCE",
                           "taxonomies": [], "documentTypes": [], "keywords": []},
        "paginationParameters": {"currentPageNumber": 0, "pageSize": 1},
    }
    resp = await client.post(f"{BASE_URL}/search", json=body)
    resp.raise_for_status()
    return resp.json()["data"]["pageFilters"]


def doc_id(node: dict, lang: str) -> str | None:
    val = (node.get("documentId") or {}).get(lang)
    return val if val and val != "#" else None


def is_leaf_doc(node: dict) -> bool:
    return bool(doc_id(node, "fr") or doc_id(node, "nl"))


def count_docs(node: dict) -> int:
    return int(is_leaf_doc(node)) + sum(count_docs(c) for c in node.get("children") or [])


def short(guid: str | None) -> str:
    return f"`{guid[:8]}…`" if guid else "—"


def labels(node: dict) -> tuple[str, str | None]:
    label = node.get("label") or {}
    fr = label.get("fr") or node.get("name") or "?"
    nl = label.get("nl")
    return fr, (nl if nl and nl != fr else None)


def render_node(node: dict, depth: int, lines: list[str]) -> None:
    fr, nl = labels(node)
    nl_part = f" *(NL: {nl})*" if nl else ""
    ids = f" (fr: {short(doc_id(node, 'fr'))} / nl: {short(doc_id(node, 'nl'))})" if is_leaf_doc(node) else ""
    children = node.get("children") or []
    if depth == 0:
        lines += ["", f"## {fr}", f"*NL: {nl}*" if nl else "", "",
                  f"**Documents indexés:** {count_docs(node)}", ""]
    elif depth == 1:
        lines += ["", f"### {fr}", f"*NL: {nl}*" if nl else "", ""]
        if ids:
            lines.append(f"Document{ids}")
            lines.append("")
    elif depth == 2:
        lines += [f"#### {fr}{nl_part}", f"*{count_docs(node)} document(s)*{ids}", ""]
    else:
        indent = "  " * (depth - 3)
        lines.append(f"{indent}- **{fr}**{nl_part}{ids}")
    for child in children:
        render_node(child, depth + 1, lines)
    if depth == 2 and children:
        lines.append("")


def library_section(library: list[dict]) -> list[str]:
    groups: dict[str, list[str]] = {name: [] for name, _ in LIBRARY_GROUPS}
    for item in library:
        title = item["title"].strip()
        if not re.fullmatch(r"[0-9a-f-]{36}", item["id"]):
            title += " *(⚠ son `id` est une URL SharePoint PDF, pas un GUID Fisconet)*"
        name = next(n for n, rule in LIBRARY_GROUPS if rule(item["title"].strip()))
        groups[name].append(title)
    lines = ["## Bibliothèque publique — Publications clés", "",
             f"Publications curatées accessibles via `GET /library/documents?language=fr` ({len(library)} items) :", ""]
    for name, titles in groups.items():
        if titles:
            lines += [f"**{name}**", "", *[f"- {t}" for t in titles], ""]
    lines += [
        "> **Note API:** le PDF réel est encodé en base64 dans `GET /document/{guid}` "
        "(`data.content.type == \"PDF\"`). L'endpoint `GET /pdf?id=` renvoie un PDF générique "
        "(le guide utilisateur Fisconet+) et ne doit pas être utilisé. Une entrée (*Code des droits "
        "d'enregistrement - Région de Bruxelles-Capitale*) est une table des matières HTML dont le lien "
        "`fisconet.direct/{guid}` pointe vers le PDF. Téléchargement : `ingestion/scripts/download_myfin_pdfs.py` "
        "→ `myfin_pdfs/`.",
        "",
    ]
    return lines


def classification_section(existing: str) -> str:
    match = re.search(r"^## Classification.*?(?=^## Bibliothèque publique — Publications clés)",
                      existing, flags=re.S | re.M)
    if not match:
        raise SystemExit("Could not find the Classification section to preserve")
    return match.group(0).rstrip() + "\n"


async def main() -> None:
    existing = OUT_FILE.read_text()
    async with httpx.AsyncClient(timeout=120.0) as client:
        tree = await get(client, "/navigation/tree")
        library = await get(client, "/library/documents", language="fr")
        years = sorted(await get(client, "/changes/limit-year"))
        facets = {lang: await search_facets(client, lang) for lang in LANGUAGES}

    branches = [n for k, n in tree.items() if k not in IGNORED_BRANCHES]
    totals = {lang: sum(t["count"] for t in facets[lang]["documentTypes"]) for lang in LANGUAGES}
    doc_types = sorted(facets["fr"]["documentTypes"], key=lambda t: -t["count"])

    out = [
        "# Fisconet+ (MyMinfin) — Arborescence complète",
        "",
        f"> **Source:** API publique Fisconet+ — `GET {BASE_URL}/navigation/tree`",
        f"> **Date d'extraction:** {dt.date.today().isoformat()}",
        f"> **Portal:** {PORTAL_URL}",
        "> **Régénération:** `uv run --package tax-ingestion python ingestion/scripts/build_myfin_arborescence.py`",
        "",
        "L'arborescence ci-dessous reflète exactement la hiérarchie exposée par l'API de navigation Fisconet+.",
        "Chaque nœud portant un GUID (fr/nl) est un document indexé dans la base, accessible via `GET /document/{guid}`.",
        "Les GUIDs sont tronqués aux 8 premiers caractères (UUID complet disponible dans l'API).",
        "",
        "## Statistiques globales",
        "",
        "| Branche | Documents (nœuds avec GUID) |",
        "|---------|---------------------|",
        *[f"| {labels(b)[0]} | {count_docs(b)} |" for b in branches],
        f"| **TOTAL** | **{sum(count_docs(b) for b in branches)}** |",
        "",
        f"## Types de documents ({len(doc_types)} catégories)",
        "",
        "| Type | Label FR | Nb docs (FR) |",
        "|------|----------|-------------|",
        *[f"| `{t['guid'][:8]}…` | {t['label']['fr']} | {t['count']:,} |".replace(",", " ") for t in doc_types],
        "",
        f"> Total FR : ~{totals['fr']:,} documents (NL : ~{totals['nl']:,} | DE : ~{totals['de']:,} "
        f"| EN : ~{totals['en']:,})".replace(",", " "),
        "",
        "---",
        "",
        classification_section(existing),
        *library_section(library),
        "## Historique des modifications",
        "",
        "Endpoint `GET /changes/searches?language=fr&month=M&year=Y` disponible pour les années :",
        "",
        "> " + " · ".join(years),
        "",
        "Chaque entrée contient : `guid`, `title`, `date`, `taxonomyTerm`, `documentType`, `status` (New/Modified).",
        "",
        "---",
        "",
        "# Arborescence de navigation",
        "",
        f"La hiérarchie suit {len(branches)} grandes branches (la branche `FINANCE - Copy` est un doublon vide ignoré).",
    ]
    for branch in branches:
        render_node(branch, 0, out)

    text = re.sub(r"\n{3,}", "\n\n", "\n".join(out)).rstrip() + "\n"
    OUT_FILE.write_text(text)
    print(f"Wrote {OUT_FILE} ({sum(count_docs(b) for b in branches)} documents, {len(library)} library items)")


if __name__ == "__main__":
    asyncio.run(main())
