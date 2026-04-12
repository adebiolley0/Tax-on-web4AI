"""Download 20 documents about personal income tax (IPP) from Fisconet+.

The Fisconet+ PDF endpoint returns a generic placeholder for most documents,
so we use the document API (base64-encoded HTML content) and convert to markdown
via html2text.  The raw HTML is also saved for reference.

Topics covered (diverse personal tax situations):
- Professional expenses / flat-rate deductions
- Pension savings (épargne-pension)
- Real estate income (revenus immobiliers)
- Dependents (personnes à charge)
- Disability-related FAQ
- Investment income (revenus mobiliers)
- Charitable donations (libéralités)
- Childcare expenses (garde d'enfants)
- Mortgage / housing deductions (bonus logement)
- Tax rates and brackets (barèmes)
- Alimony (pension alimentaire)
- Co-parenting tax credits
"""

from __future__ import annotations

import asyncio
import base64
import json
import logging
import re
import sys
from pathlib import Path

import httpx
from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

BASE_URL = "https://www.minfin.fgov.be/myminfin-rest/fisconetPlus/public"
OUT_DIR = Path(__file__).resolve().parent.parent / "validation_dataset"
MD_DIR = OUT_DIR / "md"
TIMEOUT = 60.0

# Curated GUIDs: (guid, short_name, description)
CANDIDATES = [
    # Professional expenses
    ("6a88364f-fade-4427-82b0-ac3766cea13b", "commentaire_art66_cir92",
     "Commentaire de l'article 66, CIR 92 - frais professionnels forfaitaires"),
    ("59da0db2-12c7-471d-8fca-c4a48d2f615b", "commentaire_art65_cir92",
     "Commentaire de l'article 65, CIR 92 - frais professionnels réels"),
    # Pension savings
    ("608947c4-c518-451e-9d76-0652fda0f9e2", "circ_epargne_pension_2006",
     "Circulaire épargne-pension AFER 8/2006"),
    ("cdb7d27b-5aae-45f5-be33-adc82670cf80", "circ_2025_C21_epargne_pension",
     "Circulaire 2025/C/21 attestation 281.60 épargne-pension"),
    ("8645a998-fbe6-4714-8042-9e67e1f44e25", "commentaire_art145_8_cir92",
     "Commentaire de l'article 145/8, CIR 92 - épargne-pension"),
    # Real estate income
    ("b079577f-8eb9-427c-803f-f96c51adaea3", "faq_revenus_immobiliers",
     "FAQ – Revenus immobiliers – Nouvelle version"),
    ("6a71f275-3f37-4cfd-95f0-9a5458fd2669", "circ_2026_C2_fiscalite_immobiliere",
     "Circulaire 2026/C/2 fiscalité immobilière fédérale"),
    # Dependents / family
    ("2a1dc887-7fde-4f76-9df9-220e7c3f9662", "circ_2026_C25_personnes_charge",
     "Circulaire 2026/C/25 personnes à charge"),
    ("e7136d0a-fea8-457d-a0e2-2fe0c6e457f6", "circ_2023_C69_coparentalite",
     "Circulaire 2023/C/69 crédit d'impôt coparentalité"),
    ("ae52f547-9a8f-42af-9a18-197bd40d3eef", "circ_2019_C108_handicapes",
     "Circulaire 2019/C/108 handicapés FAQ"),
    # Investment income
    ("4cda982a-90c1-4876-9fa9-5130cd3bc8af", "commentaire_art268_cir92",
     "Commentaire article 268 CIR 92 - précompte mobilier et revenus mobiliers"),
    # Donations
    ("ad51d7c8-7925-4c14-8a4b-26f6d57e5e62", "circ_2020_C111_liberalites",
     "Circulaire 2020/C/111 réduction d'impôt libéralités"),
    ("22a8c15c-5579-4500-a967-32c2e0b17392", "commentaire_art145_33_cir92",
     "Commentaire article 145/33 CIR 92 - libéralités déductibles"),
    # Childcare
    ("410b634a-4fd7-4398-b745-10bd50ac87fd", "circ_2020_C60_garde_enfant",
     "Circulaire 2020/C/60 réduction garde d'enfant"),
    # Housing / mortgage
    ("01809183-a23f-40ce-a297-08c33e3d7f21", "circ_2025_C35_emprunts_hypo_flandre",
     "Circulaire 2025/C/35 avantages fiscaux emprunts hypothécaires Flandre"),
    ("604ba298-4adf-40c8-a7db-8cfb7af69e85", "commentaire_art145_42_cir92",
     "Commentaire article 145/42 CIR 92 - bonus logement"),
    # Tax rates / quotité exemptée
    ("b5104ef7-1203-4008-9ccb-7adca0b697b4", "commentaire_art141_cir92",
     "Commentaire article 141 CIR 92 - barème IPP"),
    ("395efe92-99dd-4f26-8aa3-4c3fbaffaf90", "commentaire_art132bis_cir92",
     "Commentaire article 132bis CIR 92 - suppléments personnes à charge"),
    # Alimony
    ("575b9c27-123b-4d63-874e-f611ac7ffb89", "commentaire_art118_cir92",
     "Commentaire article 118 CIR 92 - rentes alimentaires"),
    ("aaf65b79-1c5c-472c-a3c5-6155e3246ca1", "commentaire_art143_cir92",
     "Commentaire article 143 CIR 92 - déduction rentes alimentaires"),
    # Fallbacks
    ("b5540635-1ff7-4bb2-b452-4eacebdd5f7e", "commentaire_art120_cir92",
     "Commentaire article 120 CIR 92 - capitaux rentes alimentaires"),
    ("dcf3262e-31a4-43f0-bdb6-fb99e9c53e77", "commentaire_art323_2_cir92",
     "Commentaire article 323/2 CIR 92 - garde d'enfant attestation"),
    ("3d952c26-db29-46be-a72c-a2e3b1cd99c9", "circ_2022_C15_garde_enfant_annexe",
     "Circulaire 2022/C/15 réduction garde d'enfant annexe 2"),
    ("f4124cfe-1f22-4bfe-90f1-ed7de9446f51", "commentaire_art313_cir92",
     "Commentaire article 313 CIR 92 - précompte mobilier imputation"),
    ("50f962e7-5b56-453b-9e99-df18d6b38a0e", "commentaire_art255_cir92",
     "Commentaire article 255 CIR 92 - précompte immobilier"),
]

TARGET = 20


def _html_to_markdown(html: str) -> str:
    """Convert Fisconet HTML to clean Markdown."""
    soup = BeautifulSoup(html, "html.parser")

    lines: list[str] = []

    for el in soup.descendants:
        if el.name and el.name in ("h1", "h2", "h3", "h4", "h5", "h6"):
            level = int(el.name[1])
            text = el.get_text(strip=True)
            if text:
                lines.append(f"\n{'#' * level} {text}\n")
        elif el.name == "p":
            text = el.get_text(separator=" ", strip=True)
            if text:
                lines.append(f"\n{text}\n")
        elif el.name == "li":
            text = el.get_text(separator=" ", strip=True)
            if text:
                lines.append(f"- {text}")
        elif el.name == "tr":
            cells = [td.get_text(strip=True) for td in el.find_all(["td", "th"])]
            if any(cells):
                lines.append("| " + " | ".join(cells) + " |")
        elif el.name == "table":
            lines.append("")  # spacing before table

    md = "\n".join(lines)
    # Collapse excessive blank lines
    md = re.sub(r"\n{3,}", "\n\n", md)
    return md.strip()


async def fetch_document_content(
    client: httpx.AsyncClient,
    guid: str,
) -> tuple[str, str, dict] | None:
    """Fetch a Fisconet document. Returns (html, title, metadata) or None."""
    try:
        resp = await client.get(f"{BASE_URL}/document/{guid}")
        resp.raise_for_status()
        raw = resp.json()
        envelope = raw.get("data", raw) if isinstance(raw, dict) else raw
        meta = envelope.get("metadata") or envelope

        content_block = envelope.get("content") or {}
        raw_content = content_block.get("content", "")
        if not raw_content:
            logger.warning("No content for %s", guid)
            return None

        html = base64.b64decode(raw_content).decode("utf-8")
        title = meta.get("title", "")
        return html, title, meta
    except Exception as e:
        logger.warning("Error fetching %s: %s", guid, e)
        return None


async def main() -> None:
    MD_DIR.mkdir(parents=True, exist_ok=True)

    downloaded: list[dict] = []

    async with httpx.AsyncClient(timeout=TIMEOUT, follow_redirects=True) as client:
        for guid, short_name, description in CANDIDATES:
            if len(downloaded) >= TARGET:
                break

            result = await fetch_document_content(client, guid)
            if result is None:
                continue

            html, title, meta = result
            if not html.strip():
                logger.warning("Empty HTML for %s", short_name)
                continue

            # Convert to markdown
            md_text = _html_to_markdown(html)
            if len(md_text) < 200:
                logger.warning("Markdown too short for %s (%d chars) — skipping", short_name, len(md_text))
                continue

            # Save markdown
            md_path = MD_DIR / f"{short_name}.md"
            header = f"# {title or description}\n\n"
            header += f"**Source:** Fisconet+ document `{guid}`\n"
            header += f"**Date:** {meta.get('documentDate', 'N/A')}\n\n---\n\n"
            full_md = header + md_text
            md_path.write_text(full_md, encoding="utf-8")

            # Extract metadata
            doc_type_obj = meta.get("documentType") or {}
            doc_type_labels = doc_type_obj.get("label") or {}
            doc_type = doc_type_labels.get("fr", "")

            taxonomies = []
            for tax in meta.get("taxonomies") or []:
                label = tax.get("label") or {}
                name = label.get("fr") or label.get("nl") or ""
                if name:
                    taxonomies.append(name)

            keywords = []
            for kw in meta.get("keywords") or []:
                label = kw.get("label") or {}
                name = label.get("fr") or label.get("nl") or ""
                if name:
                    keywords.append(name)

            downloaded.append({
                "guid": guid,
                "short_name": short_name,
                "description": description,
                "title": title,
                "md_path": str(md_path),
                "md_chars": len(full_md),
                "document_type": doc_type,
                "document_date": meta.get("documentDate"),
                "taxonomies": taxonomies,
                "keywords": keywords,
            })
            logger.info(
                "  → %d/%d: %s (%d chars) — %s",
                len(downloaded), TARGET, short_name, len(full_md), title[:80],
            )

    # Write manifest
    manifest_path = OUT_DIR / "manifest.json"
    manifest_path.write_text(json.dumps(downloaded, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info("Wrote manifest to %s with %d documents", manifest_path, len(downloaded))

    if len(downloaded) < TARGET:
        logger.warning("Only downloaded %d/%d documents", len(downloaded), TARGET)
    else:
        logger.info("Successfully downloaded all %d documents", len(downloaded))


if __name__ == "__main__":
    asyncio.run(main())
