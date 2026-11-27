"""Optional evaluation-testset generation entry point."""

from __future__ import annotations


def generate_testset() -> None:
    import pandas as pd
    from dotenv import load_dotenv
    from langchain_openai import ChatOpenAI, OpenAIEmbeddings
    from ragas.testset import TestsetGenerator

    from ..corpus.loader import load_corpus

    load_dotenv()
    _, _, documents = load_corpus()
    generator = TestsetGenerator.from_langchain(ChatOpenAI(model="gpt-4o"), OpenAIEmbeddings())
    dataframe = generator.generate_with_langchain_docs(documents[:50], testset_size=30).to_pandas()
    dataframe.to_csv("data/eval_dataset.csv", index=False)
    print("Evaluation dataset saved to data/eval_dataset.csv")


if __name__ == "__main__":
    generate_testset()
