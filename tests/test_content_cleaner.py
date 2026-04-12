"""Unit tests for the pre-ingestion content cleaner."""

from __future__ import annotations

from storage.content_cleaner import clean_for_indexing


class TestStripIndexSections:
    """Index/reference section removal."""

    def test_removes_legislation_section(self):
        text = (
            "# Title\n\n"
            "Some intro.\n\n"
            "## Législation\n\n"
            "Article 65, CIR 92 (historique)\n\n"
            "## Commentaire\n\n"
            "Substantive commentary here."
        )
        result = clean_for_indexing(text)
        assert "Article 65, CIR 92 (historique)" not in result
        assert "Substantive commentary here." in result

    def test_removes_circulaires_section(self):
        text = (
            "# Title\n\n"
            "## Circulaires\n\n"
            "Circulaire n° Ci.RH.81/626.947 du 25.04.2013\n\n"
            "## Commentaire\n\n"
            "Real content."
        )
        result = clean_for_indexing(text)
        assert "Ci.RH.81/626.947" not in result
        assert "Real content." in result

    def test_removes_jurisprudence_section(self):
        text = (
            "# Title\n\n"
            "## Jurisprudence\n\n"
            "Arrêt de la Cour du 06.02.2023\n\n"
            "## Commentaire\n\n"
            "Real content."
        )
        result = clean_for_indexing(text)
        assert "Arrêt de la Cour" not in result
        assert "Real content." in result

    def test_removes_questions_parlementaires(self):
        text = (
            "# Title\n\n"
            "## Questions parlementaires\n\n"
            "Question n° 1747 de madame Pas du 08.11.2023\n\n"
            "## Commentaire\n\n"
            "Content."
        )
        result = clean_for_indexing(text)
        assert "Question n° 1747" not in result
        assert "Content." in result

    def test_removes_autres_documents(self):
        text = (
            "# Title\n\n"
            "## Autres documents\n\n"
            "Liste des institutions agréées\n"
        )
        result = clean_for_indexing(text)
        assert "institutions agréées" not in result

    def test_removes_avis_section(self):
        text = (
            "# Title\n\n"
            "## Avis\n\n"
            "03.02.2025 - Avis aux organismes\n\n"
            "## Circulaires\n\n"
            "Circulaire 2026/C/8\n"
        )
        result = clean_for_indexing(text)
        assert "Avis aux organismes" not in result
        # Circulaires section also removed
        assert "Circulaire 2026/C/8" not in result

    def test_preserves_circulaire_document_title(self):
        """A document titled '# Circulaire 2025/C/21 relative à ...' is NOT
        an index heading — it's a document title and must be preserved."""
        text = (
            "# Circulaire 2025/C/21 relative à l'attestation\n\n"
            "Cette circulaire précise ce qui doit être mentionné.\n"
        )
        result = clean_for_indexing(text)
        assert "Circulaire 2025/C/21" in result
        assert "Cette circulaire" in result

    def test_preserves_commentaire_section(self):
        text = (
            "# Title\n\n"
            "## Législation\n\n"
            "Art 65 CIR\n\n"
            "## Commentaire\n\n"
            "Important explanation of the law.\n"
        )
        result = clean_for_indexing(text)
        assert "Important explanation of the law." in result


class TestStripToc:
    """Table-of-contents removal."""

    def test_removes_toc_block(self):
        text = (
            "# Title\n\n"
            "Table des matières\n"
            "I. Introduction\n"
            "II. Commentaire\n"
            "A. Foo\n"
            "B. Bar\n\n"
            "# Introduction\n\n"
            "Real content here."
        )
        result = clean_for_indexing(text)
        assert "Table des matières" not in result
        assert "I. Introduction" not in result
        assert "Real content here." in result

    def test_removes_toc_with_spaced_heading(self):
        """Fisconet sometimes has 'T able des matières' with a space."""
        text = (
            "T able des matières\n"
            "I. First\n"
            "II. Second\n\n"
            "# First\n\n"
            "Content."
        )
        result = clean_for_indexing(text)
        assert "T able des matières" not in result
        assert "Content." in result


class TestStripBoilerplate:
    """Boilerplate metadata line removal."""

    def test_removes_source_guid_date(self):
        text = (
            "# Title\n\n"
            "**Source:** Fisconet+ document `abc123`\n"
            "**GUID:** abc123\n"
            "**Date:** 2025-01-01\n\n"
            "Real content."
        )
        result = clean_for_indexing(text)
        assert "Fisconet+" not in result
        assert "Real content." in result

    def test_removes_horizontal_rule(self):
        text = "# Title\n\n---\n\nContent."
        result = clean_for_indexing(text)
        assert "---" not in result
        assert "Content." in result

    def test_removes_spf_header(self):
        text = "SPF Finances, le 18 . 04 . 2025 Administration générale de la Fiscalité\n\nContent."
        result = clean_for_indexing(text)
        assert "SPF Finances" not in result
        assert "Content." in result

    def test_removes_numac(self):
        text = "Numac : 2025001234\n\nContent."
        result = clean_for_indexing(text)
        assert "Numac" not in result
        assert "Content." in result

    def test_removes_ref_interne(self):
        text = "Réf. interne : 742.051\n\nContent."
        result = clean_for_indexing(text)
        assert "Réf. interne" not in result

    def test_removes_signature_block(self):
        text = (
            "Article 3. Cet arrêté entre en vigueur.\n\n"
            "Donné à Bruxelles, le 15 décembre 2024.\n"
            "Par le Roi :\n"
            "Le Ministre des Finances,\n"
            "PHILIPPE\n"
        )
        result = clean_for_indexing(text)
        assert "Cet arrêté entre en vigueur" in result
        assert "PHILIPPE" not in result


class TestStripDecreePreamble:
    """Royal decree preamble removal."""

    def test_removes_vu_blocks(self):
        text = (
            "Vu le Code des impôts sur les revenus 1992;\n"
            "Vu la loi du 28.12.1992;\n\n"
            "Article 1. Le taux est fixé à 30%."
        )
        result = clean_for_indexing(text)
        assert "Vu le Code" not in result
        assert "Le taux est fixé à 30%" in result

    def test_removes_considerant(self):
        text = (
            "Considérant que :\n"
            "- la situation budgétaire exige\n"
            "- les recettes sont insuffisantes\n\n"
            "Article 1. Content."
        )
        result = clean_for_indexing(text)
        assert "Considérant que" not in result
        assert "Article 1. Content." in result

    def test_removes_sur_proposition(self):
        text = "Sur la proposition du Ministre des Finances,\n\nArticle 1."
        result = clean_for_indexing(text)
        assert "Sur la proposition" not in result
        assert "Article 1." in result


class TestStripKeywordLines:
    """Keyword/tag line removal."""

    def test_removes_semicolon_keywords(self):
        text = (
            "# Title\n\n"
            "impôt des personnes physiques ; biens immobiliers ; déduction\n\n"
            "Content."
        )
        result = clean_for_indexing(text)
        assert "biens immobiliers" not in result
        assert "Content." in result

    def test_preserves_normal_prose(self):
        text = "Le contribuable doit déclarer ses revenus dans le formulaire adéquat."
        result = clean_for_indexing(text)
        assert "Le contribuable" in result


class TestNormalization:
    """Whitespace normalization."""

    def test_collapses_blank_lines(self):
        text = "Line 1.\n\n\n\n\nLine 2."
        result = clean_for_indexing(text)
        assert "\n\n\n" not in result
        assert "Line 1.\n\nLine 2." == result


class TestCleanForIndexing:
    """Integration tests for the full pipeline."""

    def test_empty_input(self):
        assert clean_for_indexing("") == ""

    def test_preserves_substantive_content(self):
        text = (
            "# Circulaire 2020/C/60 relative à la garde d'enfants\n\n"
            "Cette circulaire traite des conditions de déduction des frais "
            "de garde d'enfants de moins de 14 ans.\n\n"
            "## 1. Conditions d'âge\n\n"
            "L'enfant doit avoir moins de 14 ans au 1er janvier de l'exercice."
        )
        result = clean_for_indexing(text)
        assert "frais de garde d'enfants" in result
        assert "Conditions d'âge" in result
        assert "moins de 14 ans" in result

    def test_commentaire_index_page_mostly_stripped(self):
        """A typical commentaire index page should lose most of its content."""
        text = (
            "# Commentaire de l'article 65, CIR 92\n\n"
            "**Source:** Fisconet+ document `abc`\n"
            "**Date:** 2025-01-01\n\n"
            "---\n\n"
            "## Législation\n\n"
            "Article 65, CIR 92 (historique)\n\n"
            "## Commentaire\n\n"
            "Commentaire de l'article 65, CIR 92\n\n"
            "## Circulaires\n\n"
            "Circulaire n° 1 du 01.01.2020\n"
            "Description de la circulaire.\n\n"
            "## Jurisprudence\n\n"
            "Arrêt du 01.01.2021\n"
            "Description.\n\n"
            "## Questions parlementaires\n\n"
            "Question n° 100 du 01.01.2022\n"
        )
        result = clean_for_indexing(text)
        # Title and Commentaire section preserved
        assert "Commentaire de l'article 65" in result
        # Index sections removed
        assert "Circulaire n° 1" not in result
        assert "Arrêt du" not in result
        assert "Question n° 100" not in result
        # Should be much shorter
        assert len(result) < len(text) * 0.5
