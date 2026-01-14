from langchain_core.tools import create_retriever_tool
from langchain_core.prompts import PromptTemplate

def create_retrieval_tool(retriever):
    """
    Creates a retrieval tool from the retriever with citation support.
    """
    # Define a prompt that includes the source and page number
    document_prompt = PromptTemplate.from_template(
        "Content: {page_content}\nSource: {source}\nPage: {page_label}"
    )
    
    tool = create_retriever_tool(
        retriever,
        "pdf_search",
        "Search for information in the provided PDF documents. Use this tool related to queries about business conduct, human rights policy, personal data protection, and VDI setup.",
        document_prompt=document_prompt
    )
    return tool
