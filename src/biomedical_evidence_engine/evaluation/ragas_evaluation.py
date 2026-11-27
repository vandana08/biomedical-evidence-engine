"""Optional RAGAS evaluation entry point."""

from __future__ import annotations


def run_evaluation() -> None:
    import pandas as pd
    from datasets import Dataset
    from dotenv import load_dotenv
    from langchain_openai import ChatOpenAI
    from ragas import evaluate
    from ragas.llms import LangchainLLMWrapper
    from ragas.metrics import answer_relevancy, context_precision, context_recall, faithfulness

    from ..app.pipeline import format_docs
    from ..corpus.loader import load_corpus
    from ..retrieval.hybrid_reranked import HybridRetriever

    load_dotenv()
    eval_df = pd.read_csv("data/eval_dataset.csv")
    faiss_db, bm25, documents = load_corpus()
    retriever = HybridRetriever(faiss_db=faiss_db, bm25_index=bm25, documents=documents, top_k=25)
    llm = ChatOpenAI(model="gpt-4o")
    answers, contexts = [], []
    for question in eval_df["user_input"].tolist():
        docs = retriever.retrieve_docs(question)
        contexts.append([doc.page_content for doc in docs])
        response = llm.invoke(
            f"Use only the provided context to answer the question:\n\nContext:\n{format_docs(docs)}\n\nQuestion:\n{question}"
        )
        answers.append(response.content)
    dataset = Dataset.from_pandas(pd.DataFrame({
        "question": eval_df["user_input"].tolist(),
        "answer": answers,
        "contexts": contexts,
        "ground_truth": eval_df["reference"].tolist(),
    }))
    result = evaluate(
        dataset,
        metrics=[faithfulness, answer_relevancy, context_precision, context_recall],
        llm=LangchainLLMWrapper(ChatOpenAI(model="gpt-4o")),
    )
    print("\n===== RAGAS Evaluation Results =====")
    print(result)


if __name__ == "__main__":
    run_evaluation()
