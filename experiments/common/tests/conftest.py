"""Shared toy fixtures: no models, no corpora — everything runs in well under a second."""
from __future__ import annotations

import pytest

from rag_eval.corpora import Doc, Question


@pytest.fixture
def toy_questions() -> list[Question]:
    return [
        Question("q1", "first", ["d1"], ["d2"]),                       # secondary d2
        Question("q2", "second", ["d1", "d4"]),                         # two expected docs
        Question("q3", "third", ["d5"]),                                # miss
        Question("MB-PQ-deadbeef", "mined", ["d1"], [], {"exclude": ["d3"], "source": "pq", "label_basis": "explicit"}),
    ]


@pytest.fixture
def toy_rankings() -> dict[str, list[str]]:
    return {
        "q1": ["d3", "d1", "d2", "d1"],       # duplicate d1 must not count twice
        "q2": ["d1", "d9", "d8", "d7", "d6", "d4"],
        "q3": ["d1", "d2"],
        "MB-PQ-deadbeef": ["d3", "d1"],       # d3 excluded → d1 is rank 1
    }


@pytest.fixture
def toy_docs() -> list[Doc]:
    para = "Ceci est une phrase de test. " * 12          # ≈ 350 chars
    text = ("# Titre\n\n" + para + "\n\n## Section 1\n\n" + para + "\n\n" + para
            + "\n\n## Section 2\n\n" + para + "\n\nDernier paragraphe court.")
    return [Doc("docA", "Document A", text, {"heading_path": ["Livre I", "Chapitre 2"]}),
            Doc("docB", "Document B", "Un tout petit document.", {})]
