from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

def create_vector_store(chunks):
    """
    Creates a FAISS vector store from text chunks using OpenAI embeddings.
    """
    embeddings = OpenAIEmbeddings()
    vector_store = FAISS.from_documents(chunks, embeddings)
    print("Vector store created.")
    return vector_store

def get_retriever(vector_store, k=3):
    """
    Returns a retriever from the vector store.
    """
    retriever = vector_store.as_retriever(search_kwargs={"k": k})
    return retriever
