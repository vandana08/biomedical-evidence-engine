"""Question answering pipeline."""

import time

from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableParallel, RunnablePassthrough
from langchain_openai import ChatOpenAI

from ..prompts.baseline import prompt
from ..retrieval.hybrid_reranked import HybridRetriever


def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)


def run_rag(query: str, faiss_db, bm25_index, documents, top_k: int = 20, return_latency: bool = False):
    request_start = time.perf_counter()
    retriever = HybridRetriever(
        faiss_db=faiss_db,
        bm25_index=bm25_index,
        documents=documents,
        top_k=top_k,
    )
    retrieval_start = time.perf_counter()
    retrieved_docs = retriever.retrieve_docs(query)
    retrieval_latency_ms = (time.perf_counter() - retrieval_start) * 1000
    chain = RunnableParallel({
        "retrieved_docs": lambda _: format_docs(retrieved_docs),
        "user_question": RunnablePassthrough(),
    }) | prompt | ChatOpenAI(model="gpt-4o-mini") | StrOutputParser()
    generation_start = time.perf_counter()
    answer = chain.invoke(query)
    generation_latency_ms = (time.perf_counter() - generation_start) * 1000
    latency = {
        "retrieval_ms": retrieval_latency_ms,
        "generation_ms": generation_latency_ms,
        "total_ms": (time.perf_counter() - request_start) * 1000,
    }
    return (answer, retrieved_docs, latency) if return_latency else (answer, retrieved_docs)
