"""Shared helpers for retrieval implementations."""

from __future__ import annotations

from typing import Any, Iterable


def validate_query(query: str) -> str:
    if not isinstance(query, str):
        raise TypeError("query must be a string")
    return query


def normalize_top_k(top_k: int) -> int:
    if not isinstance(top_k, int) or isinstance(top_k, bool):
        raise TypeError("top_k must be an integer")
    if top_k < 0:
        raise ValueError("top_k must be non-negative")
    return top_k


def document_key(document: Any, fallback: str | None = None) -> str:
    metadata = getattr(document, "metadata", None) or {}
    chunk_id = metadata.get("chunk_id")
    if chunk_id is not None:
        return str(chunk_id)
    if fallback is not None:
        return fallback
    page_content = getattr(document, "page_content", None)
    return str(page_content) if page_content is not None else repr(document)


def reciprocal_rank_fusion(ranked_lists: Iterable[Iterable[Any]], rrf_k: int = 60) -> list[Any]:
    if not isinstance(rrf_k, int) or isinstance(rrf_k, bool) or rrf_k < 0:
        raise ValueError("rrf_k must be a non-negative integer")
    scores: dict[str, float] = {}
    documents: dict[str, Any] = {}
    first_seen: dict[str, int] = {}
    sequence = 0
    for ranked_documents in ranked_lists:
        for rank, document in enumerate(ranked_documents):
            key = document_key(document)
            if key not in documents:
                documents[key] = document
                first_seen[key] = sequence
                sequence += 1
            scores[key] = scores.get(key, 0.0) + 1 / (rrf_k + rank + 1)
    ranked_keys = sorted(scores, key=lambda key: (-scores[key], first_seen[key]))
    return [documents[key] for key in ranked_keys]
