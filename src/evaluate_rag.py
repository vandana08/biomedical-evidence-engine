import pandas as pd
import os
import sys
sys.path.append(os.getcwd())
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_recall,
    context_precision,
)
from ragas.llms import LangchainLLMWrapper

from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from hybrid_retriever import HybridRetriever
from load_corpus import load_corpus
from pipeline import format_docs

load_dotenv()


def run_evaluation():

    eval_df = pd.read_csv("data/eval_dataset.csv")
    questions = eval_df["user_input"].tolist()
    ground_truths = eval_df["reference"].tolist()

    # Load corpus
    faiss_db, bm25, documents = load_corpus()

    retriever = HybridRetriever(
        faiss_db=faiss_db,
        bm25_index=bm25,
        documents=documents,
        top_k=25
    )

    llm = ChatOpenAI(model="gpt-4o")

    answers = []
    contexts = []

    for q in questions:
        docs = retriever.retrieve_docs(q)
        context_text = [doc.page_content for doc in docs]

        response = llm.invoke(
            f"Use only the provided context to answer the question:\n\nContext:\n{format_docs(docs)}\n\nQuestion:\n{q}"
        )

        answers.append(response.content)
        contexts.append(context_text)

    df = pd.DataFrame({
        "question": questions,
        "answer": answers,
        "contexts": contexts,
        "ground_truth": ground_truths
    })
    

    dataset = Dataset.from_pandas(df)
    evaluator_llm = LangchainLLMWrapper(ChatOpenAI(model="gpt-4o"))

    result = evaluate(
        dataset,
        metrics=[
            faithfulness,
            answer_relevancy,
            context_precision,
            context_recall,
        ],
        llm=evaluator_llm,
    )

    print("\n===== RAGAS Evaluation Results =====")
    print(result)


if __name__ == "__main__":
    run_evaluation()
