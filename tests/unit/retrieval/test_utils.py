from dataclasses import dataclass

import pytest

from biomedical_evidence_engine.retrieval.utils import (
    document_key,
    reciprocal_rank_fusion,
    validate_query,
)


@dataclass
class Document:
    metadata: dict
    page_content: str = ""


@pytest.mark.parametrize("query", ["", "   ", "\t\n"])
def test_validate_query_rejects_empty_input(query):
    with pytest.raises(ValueError, match="query must not be empty"):
        validate_query(query)


def test_validate_query_strips_surrounding_whitespace():
    assert validate_query("  EGFR T790M\n") == "EGFR T790M"


def test_validate_query_rejects_non_string_input():
    with pytest.raises(TypeError, match="query must be a string"):
        validate_query(None)


def test_document_key_requires_chunk_id():
    with pytest.raises(ValueError, match="missing required chunk_id"):
        document_key(Document(metadata={}, page_content="same text"))

    with pytest.raises(ValueError, match="missing required chunk_id"):
        document_key(Document(metadata={"chunk_id": ""}, page_content="same text"))


def test_rrf_keeps_same_content_with_different_chunk_ids_distinct():
    first = Document(metadata={"chunk_id": "chunk-1"}, page_content="same text")
    second = Document(metadata={"chunk_id": "chunk-2"}, page_content="same text")

    result = reciprocal_rank_fusion([[first], [second]])

    assert result == [first, second]


def test_rrf_rejects_documents_without_chunk_id():
    document = Document(metadata={}, page_content="same text")

    with pytest.raises(ValueError, match="missing required chunk_id"):
        reciprocal_rank_fusion([[document]])
