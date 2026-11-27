from types import SimpleNamespace

from scripts.benchmarks.run_retrieval_stability_benchmark import jaccard, pmid_ranking, rbo_at_k


def doc(pmid):
    return SimpleNamespace(metadata={"pmid": pmid})


def test_pmid_ranking_deduplicates_chunks():
    assert pmid_ranking([doc("p1"), doc("p1"), doc("p2")], top_k=2) == ["p1", "p2"]


def test_jaccard_and_rbo_distinguish_sets_and_order():
    first = ["p1", "p2", "p3"]
    same_set_reordered = ["p3", "p2", "p1"]
    disjoint = ["p4", "p5", "p6"]
    assert jaccard(first, same_set_reordered) == 1.0
    assert jaccard(first, disjoint) == 0.0
    assert rbo_at_k(first, first) == 1.0
    assert rbo_at_k(first, same_set_reordered) < 1.0


def test_rbo_empty_lists_are_stable():
    assert rbo_at_k([], []) == 1.0
