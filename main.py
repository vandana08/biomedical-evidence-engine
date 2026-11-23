from dotenv import load_dotenv
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from src.pipeline import *
from src.load_corpus import load_corpus
import streamlit as st
import traceback
import pickle


load_dotenv()

@st.cache_resource
def cached_corpus():
    return load_corpus()


response = None
# Streamlit UI
st.set_page_config(page_title="PubMed RAG Chatbot", layout="wide")
st.title("🧬 PubMed RAG Biomedical Assistant")

# Get user input
query = st.text_input("Enter your biomedical question:", "")

if query and len(query.strip()) < 3:
    st.warning("Please enter a more specific query.")
elif query:
    with st.spinner("Fetching relevant PubMed abstracts..."):
        try:
            faiss_db, bm25, documents = cached_corpus()

            response, docs, latency = run_rag(
                query,
                faiss_db=faiss_db,
                bm25_index=bm25,
                documents=documents,
                top_k=3,
                return_latency=True,
            )
        except RuntimeError as re:
            # Specific handling for common runtime errors
            if "Supplied id parameter is empty" in str(re):
                st.error("❗ No relevant PubMed abstracts found. Try asking a more detailed biomedical question.")
            else:
                st.error(f"Runtime error: {re}")

        except ValueError as ve:
            st.error(f"Input error: {ve}")

        except Exception as e:
            st.error("An unexpected error occurred. Please try again later.")
            with st.expander("Show details (for debugging)"):
                st.code(traceback.format_exc())

    if response is not None:
        # Output
        st.subheader("🔎 Retrieved Answer")
        st.markdown(response)

        st.caption(
            "Latency: "
            f"{latency['total_ms']:.0f} ms total "
            f"({latency['retrieval_ms']:.0f} ms retrieval, "
            f"{latency['generation_ms']:.0f} ms generation)"
        )

        with st.expander("📚 Retrieved PubMed Abstracts"):
            for i, doc in enumerate(docs):
                st.markdown(f"**{i+1}. {doc.metadata['title']}**")
                st.markdown(f"- PMID: {doc.metadata['pmid']}")
                st.markdown(f"- Journal: {doc.metadata['journal']} ({doc.metadata['year']})")
                st.markdown(doc.page_content)
                st.markdown("---")
