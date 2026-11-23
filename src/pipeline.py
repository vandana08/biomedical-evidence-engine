import time

import streamlit as st 
from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnableLambda, RunnableParallel, RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from prompt.baseline_prompt import *
from src.hybrid_retriever import HybridRetriever



# Define format_docs
def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)


def run_rag(
    query: str,
    faiss_db,
    bm25_index,
    documents,
    top_k: int = 20,
    return_latency: bool = False,
):
    """Run retrieval and generation, optionally returning latency measurements.

    Latencies are measured with ``perf_counter`` and reported in milliseconds.
    The default return shape remains ``(answer, documents)`` for compatibility
    with existing callers.
    """
    request_start = time.perf_counter()

    hybrid_retriever = HybridRetriever(faiss_db=faiss_db, 
                                bm25_index=bm25_index, 
                                documents= documents)

    retrieval_start = time.perf_counter()
    retrieved_docs = hybrid_retriever.retrieve_docs(query)
    retrieval_latency_ms = (time.perf_counter() - retrieval_start) * 1000

    # retriever_runnable = RunnableLambda(lambda question: format_docs(PubMedRetriever(vector_store_db, question, top_k).retrieve_docs()) )
    
    chain = RunnableParallel({
        'retrieved_docs':  lambda _: format_docs(retrieved_docs),
        'user_question': RunnablePassthrough()
    }) | prompt | ChatOpenAI(model="gpt-4o-mini") | StrOutputParser()
    generation_start = time.perf_counter()
    answer = chain.invoke(query)
    generation_latency_ms = (time.perf_counter() - generation_start) * 1000

    latency = {
        "retrieval_ms": retrieval_latency_ms,
        "generation_ms": generation_latency_ms,
        "total_ms": (time.perf_counter() - request_start) * 1000,
    }

    if return_latency:
        return answer, retrieved_docs, latency

    return answer, retrieved_docs

