from biomedical_evidence_engine.corpus.ingestor import PubMedIngestor


def test_abstract_extraction_preserves_sections():
    text, sections = PubMedIngestor._extract_abstract({
        "Abstract": {
            "AbstractText": ["Background text", "Results text"],
        }
    })
    assert text == "Background text\nResults text"
    assert [section["text"] for section in sections] == ["Background text", "Results text"]
