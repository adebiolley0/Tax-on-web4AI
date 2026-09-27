"""Unit checks of the reference grammar and the miner's text helpers (no corpus)."""
from rag_eval.legal_refs import classify_tail, expand_items, iter_article_refs, region_of, title_keys
from rag_eval.mining import build_pq_query, clean_objet, faq_headings, is_policy, norm_text, qid


def _refs(text):
    return [(items, classify_tail(tail)) for _, items, tail in iter_article_refs(text)]


def test_article_references():
    assert _refs("Conformément à l'article 44 du Code de la TVA, la livraison") == [(["44"], ("family", "ctva"))]
    got = _refs("voir les articles 202 à 205 du CIR 92 et l'article 7, § 1er, 2°, c, excéder")
    assert got == [(["202", "à", "205"], ("family", "cir92")), (["7"], ("same", ""))]
    assert _refs("l'article 3 de la loi du 12.07.2013") == [(["3"], ("external", ""))]
    assert _refs("article 46bis du C. enr.") == [(["46bis"], ("family", "cenr"))]
    assert expand_items(["202", "à", "204", "7"], lambda n: {n}, lambda a, b: {a, b, "203"}) == {"202", "203", "204", "7"}


def test_title_keys_and_regions():
    keys, attrs = title_keys("Article 145/33, CIR 92 (revenus 2024)", "code_et_legislation", ["Fisconet", "Impôts sur les revenus"])
    assert keys == ["art:cir92:145/33", "art:cir92:fed:145/33"] and attrs == {"family": "cir92", "num": "145/33", "region": "fed"}
    assert title_keys("Circulaire 2019/C/40 concernant ...", "circulaires", [])[0] == ["c:2019/C/40"]
    assert title_keys("Décision anticipée n° 2018.0775 du 02.10.2018", "decisions_anticipees_l_24_12_2002", [])[0] == ["da:2018.0775"]
    assert region_of("Code des droits d'enregistrement - Région wallonne", []) == "wal" and region_of("x", []) is None


def test_text_helpers():
    assert norm_text("article 183 bis, § 1 er, art. 145 8 à 145 16").startswith("article 183bis, § 1er, art. 145/8 à 145/16")
    assert is_policy("Combien de dossiers ont été traités ?") == "stat"
    assert is_policy("Le ministre envisage-t-il une réforme ?") == "policy"
    assert is_policy("Quel est le taux applicable ?") is None
    q, why = build_pq_query("Le contexte est celui de la TVA sur les livraisons. Quel est le taux applicable aux livres ? "
                            "Combien de contrôles ont eu lieu en 2020 ?")
    assert q == "Le contexte est celui de la TVA sur les livraisons. Quel est le taux applicable aux livres ?" and why is None
    assert build_pq_query("Combien de contrôles ont eu lieu en 2020 ?") == (None, "policy")
    assert qid("MB", "pq", "questions_parlementaires/x") == "MB-PQ-cc75161e"
    assert clean_objet("1. La demande vise à obtenir la confirmation que : 1.1. la société X peut déduire") == "La société X peut déduire"
    heads = faq_headings("1. Quelle est la question ?\n2. Autre question ?\n\n1. Quelle est la question ?\nRéponse un.\n2. Autre question ?\nRéponse deux.")
    assert heads == [(3, "Quelle est la question ?", "Réponse un."), (5, "Autre question ?", "Réponse deux.")]
