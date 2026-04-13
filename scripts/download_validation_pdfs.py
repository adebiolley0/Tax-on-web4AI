"""Download documents about personal income tax (IPP) from Fisconet+.

The Fisconet+ PDF endpoint returns a generic placeholder for most documents,
so we use the document API (base64-encoded HTML content) and convert to markdown
via html2text.  The raw HTML is also saved for reference.

Only documents with **legal or substantive informational value** are included
(circulaires, FAQs, legislation). Aperçu documentaire index pages, training
materials, and portal navigation pages are excluded per MYFIN_ARBORESCENCE.md.

Topics covered (diverse personal tax situations):
- Vehicle / automobile expenses (frais de voiture)
- Pension savings (épargne-pension)
- Real estate income (revenus immobiliers)
- Dependents (personnes à charge)
- Disability-related FAQ
- Investment income (revenus mobiliers / précompte mobilier)
- Charitable donations (libéralités)
- Childcare expenses (garde d'enfants)
- Mortgage / housing deductions (emprunts hypothécaires)
- Alimony (rentes alimentaires)
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
# ALL entries are substantive circulaires or FAQs — no aperçu documentaire.
CANDIDATES = [
    # --- Vehicle / automobile expenses (Q1) ---
    ("7cfec008-5ef5-4e2d-9367-213a0c66c627", "circ_2022_C10_frais_voiture",
     "Circulaire 2022/C/10 limitation de la déduction des frais de voiture"),
    ("5432d72d-0c78-4a2c-a86b-a85e2310ce51", "circ_2023_C99_fiscalite_automobile",
     "Circulaire 2023/C/99 FAQ verdissement fiscal mobilité – fiscalité automobile"),
    # --- Pension savings (Q2) ---
    ("cdb7d27b-5aae-45f5-be33-adc82670cf80", "circ_2025_C21_epargne_pension",
     "Circulaire 2025/C/21 attestation 281.60 épargne-pension"),
    ("1e2e3504-3565-43f9-8596-9a16e6d4151f", "circ_2018_C72_epargne_pension_duale",
     "Circulaire 2018/C/72 relative à l'épargne-pension duale"),
    # --- Real estate income (Q3) ---
    ("b079577f-8eb9-427c-803f-f96c51adaea3", "faq_revenus_immobiliers",
     "FAQ – Revenus immobiliers – Nouvelle version"),
    ("6a71f275-3f37-4cfd-95f0-9a5458fd2669", "circ_2026_C2_fiscalite_immobiliere",
     "Circulaire 2026/C/2 fiscalité immobilière fédérale"),
    # --- Dependents / family (Q4, Q8, Q9) ---
    ("2a1dc887-7fde-4f76-9df9-220e7c3f9662", "circ_2026_C25_personnes_charge",
     "Circulaire 2026/C/25 personnes à charge"),
    ("e7136d0a-fea8-457d-a0e2-2fe0c6e457f6", "circ_2023_C69_coparentalite",
     "Circulaire 2023/C/69 crédit d'impôt coparentalité"),
    ("ae52f547-9a8f-42af-9a18-197bd40d3eef", "circ_2019_C108_handicapes",
     "Circulaire 2019/C/108 handicapés FAQ"),
    # --- Donations (Q5) ---
    ("ad51d7c8-7925-4c14-8a4b-26f6d57e5e62", "circ_2020_C111_liberalites",
     "Circulaire 2020/C/111 réduction d'impôt libéralités"),
    # --- Childcare (Q6) ---
    ("410b634a-4fd7-4398-b745-10bd50ac87fd", "circ_2020_C60_garde_enfant",
     "Circulaire 2020/C/60 réduction garde d'enfant"),
    # --- Mortgage / housing (Q7) ---
    ("01809183-a23f-40ce-a297-08c33e3d7f21", "circ_2025_C35_emprunts_hypo_flandre",
     "Circulaire 2025/C/35 avantages fiscaux emprunts hypothécaires Flandre"),
    ("fe3be86f-429a-446a-8300-fd5f78a39330", "circ_2025_C33_emprunts_hypo_bruxelles",
     "Circulaire 2025/C/33 avantages fiscaux emprunts hypothécaires Bruxelles-Capitale"),
    # --- Alimony / rentes alimentaires (Q10) ---
    ("6613677d-6353-42f4-a793-e68511f341da", "circ_2026_C12_rentes_alimentaires",
     "Circulaire 2026/C/12 traitement fiscal des rentes alimentaires"),
    ("67eef234-8d87-4bd8-abea-d35a3207a85c", "circ_2023_C43_rentes_alimentaires",
     "Circulaire 2023/C/43 rentes alimentaires déductibilité et imposition"),
    # --- Investment income / précompte mobilier ---
    ("b95b791f-1ed2-48e2-b843-8c8ab34c46a5", "circ_2020_C21_precompte_mobilier",
     "Circulaire 2020/C/21 détermination du revenu mobilier imposable – précompte mobilier"),
    # --- Additional documents for semantic search (10 new) ---
    # Professional expenses / frais professionnels
    ("565c632d-7b74-46ce-8a98-04a369de40a2", "circ_2026_C46_frais_majores",
     "Circulaire 2026/C/46 déduction de frais majorée pour les dépenses professionnelles"),
    ("3aca75c0-c88b-4fad-ab7b-4153988e3a7f", "circ_2022_C86_frais_professionnels",
     "Circulaire 2022/C/86 déductibilité de certains frais professionnels"),
    # Self-employment / travail indépendant
    ("490475d3-0bf0-4467-a168-1e2d2956ee1b", "circ_2020_C101_complement_entreprise",
     "Circulaire 2020/C/101 exonération fiscale du complément d'entreprise"),
    # Capital gains / gains en capital
    ("e84a0d56-c9e7-451f-9fe7-a18505c06de0", "circ_2004_gains_capital",
     "Circulaire n° AREC 6/2004 gains en capital immobilier"),
    ("5601f462-648c-488a-91d8-88c6e5fcb708", "circ_2017_C22_gains_capital_reduction",
     "Circulaire 2017/C/22 modifications réductions d'impôt pour gains en capital"),
    # Non-salary benefits / avantages extralégaux
    ("ca40e32f-4c06-47c8-8450-a89558321199", "circ_1984_avantages_extralegalux",
     "Circulaire n° 1 du 30.01.1984 avantages extralégaux rémunération"),
    # Training and continuing education / frais de formation
    ("d19d1de9-a3e8-4748-a5c4-0118e457c75d", "circ_2000_frais_formation",
     "Circulaire n° Ci.RH.241/494.326 frais de formation continue professionnelle"),
    # Various income / revenus divers
    ("31233ff2-390b-4dec-9739-664ca59f2ab4", "circ_1997_revenus_divers",
     "Circulaire n° Ci.RH.241/467.430 du 08.08.1997 revenus divers prestations"),
    # Student work / travail étudiant
    ("7ee79498-2067-403d-96bb-22cc925c4a02", "circ_2025_C55_travail_etudiant",
     "Circulaire 2025/C/55 modifications concernant le travail étudiant"),
    # Rental income / revenu locatif
    ("961b3b18-a132-47f0-a715-52416e5cc331", "circ_1997_revenu_locatif",
     "Circulaire n° Ci.RH.241-460.408 du 26.11.1997 revenu locatif"),
    # --- 5 additional documents for expanded semantic search evaluation ---
    # Home renovation and thermal improvements
    ("c828e396-9590-449b-aa2a-99c7f67360f9", "circ_2011_travaux_renovation",
     "Circulaire réductions impôt pour travaux de rénovation isolation thermique"),
    # Medical and healthcare expenses
    ("8256e11a-af82-4e3a-900e-628ea8525bbc", "circ_2008_frais_medicaux",
     "Circulaire réduction impôt dépenses frais médicaux dentistes"),
    # Social contributions / employer charges
    ("cfc036a7-b646-4f1f-887a-b0074826d6c2", "circ_1989_cotisations_sociales",
     "Circulaire cotisations sociales patronales charges employeur"),
    # Recent general tax reduction
    ("912bb212-2371-4ef1-a9ae-e7f402e6867b", "circ_2024_C20_impot_recent",
     "Circulaire 2024/C/20 commentant loi portant dispositions fiscales"),
    # Tax credit for business income increase
    ("53cc4f44-548c-49c4-9fda-142c9b0d4ef8", "circ_2026_C5_credit_croissance",
     "Circulaire 2026/C/5 crédit d'impôt pour l'accroissement des revenus"),
]

TARGET = 31


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
