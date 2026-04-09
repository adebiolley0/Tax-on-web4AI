"""Tests for content_extractor utilities."""

from content_extractor import detect_language, extract_fiscal_codes


class TestExtractFiscalCodes:
    def test_cir92(self):
        text = "Conformément à l'art. 7 CIR 92, les revenus immobiliers..."
        codes = extract_fiscal_codes(text)
        assert any("CIR 92" in c for c in codes)

    def test_ctva(self):
        text = "L'art. 44 CTVA prévoit des exemptions."
        codes = extract_fiscal_codes(text)
        assert any("CTVA" in c for c in codes)

    def test_multiple_codes(self):
        text = "Voir art. 7 CIR 92 et art. 44 CTVA pour les détails."
        codes = extract_fiscal_codes(text)
        assert len(codes) >= 2

    def test_no_codes(self):
        text = "Aucune référence fiscale dans ce texte."
        codes = extract_fiscal_codes(text)
        assert codes == []


class TestDetectLanguage:
    def test_french(self):
        assert detect_language("https://fin.belgium.be/fr/particuliers/declaration") == "fr"

    def test_dutch(self):
        assert detect_language("https://fin.belgium.be/nl/particulieren/aangifte") == "nl"

    def test_german(self):
        assert detect_language("https://fin.belgium.be/de/privatpersonen") == "de"

    def test_default_french(self):
        assert detect_language("https://fin.belgium.be/particuliers") == "fr"
