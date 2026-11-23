import pandas as pd
from ragas.testset import TestsetGenerator
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from dotenv import load_dotenv
from load_corpus import load_corpus

load_dotenv()

def generate_testset():

    faiss_db, bm25, documents = load_corpus()

    sample_docs = documents[:50]

    generator_llm = ChatOpenAI(model="gpt-4o")
    embedding_model = OpenAIEmbeddings()

    generator = TestsetGenerator.from_langchain(
        generator_llm,
        embedding_model
    )

    testset = generator.generate_with_langchain_docs(
        sample_docs,
        testset_size=30
    )

    df = testset.to_pandas()

    df.to_csv("data/eval_dataset.csv", index=False)

    print("Evaluation dataset saved to data/eval_dataset.csv")
    print(df.head())


if __name__ == "__main__":
    generate_testset()
