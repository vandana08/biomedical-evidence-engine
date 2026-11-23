from langchain_core.prompts import PromptTemplate

prompt = PromptTemplate(template=''' You are a biomedical expert assistant.
                        Use the information from the PubMed abstracts below to answer the user's question accurately and concisely. Do not use any information that is not present in the provided documents. If the answer cannot be determined from the documents, say “The answer is not available in the provided context.”
                        ### User Question:
                        {user_question}
                        ### Context from PubMed:
                        {retrieved_docs}
                        ### Answer:
                         ''',
                        input_variables=['user_question', 'retrieved_docs']
)