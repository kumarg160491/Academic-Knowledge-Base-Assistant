import logging
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings, OllamaLLM
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from config import cfg
from guardrails import check_input_safety, check_output_faithfulness

logger = logging.getLogger(__name__)

PROMPT_TEMPLATE = (
    "You are an Academic Knowledge Base Assistant.\n"
    "You have access to transcripts from lecture/academic sessions and related reference documents.\n\n"
    "Use ONLY the context below to answer the question. If the answer is not available "
    "in the context, say explicitly: 'I don't have enough information in the academic knowledge base to answer this.'\n\n"
    "Always mention which lecture/academic session or document your answer is based on.\n\n"
    "Context:\n{context}\n\n"
    "Question: {question}\n\n"
    "Provide a clear and structured answer:\n"
    "- Answer:\n"
    "- Source Session:\n"
    "- Source Document:\n"
    "- Relevant Timestamp (if from transcript):\n"
)


def get_embeddings() -> OllamaEmbeddings:
    return OllamaEmbeddings(
        model=cfg.ollama.embedding,
        base_url=cfg.ollama.base_url,
    )


def _format_docs(docs):
    """Join retrieved document contents into a single context string."""
    return "\n\n".join(doc.page_content for doc in docs)


def build_rag_chain(session_filter: str = None):
    embeddings = get_embeddings()
    vectorstore = Chroma(
        collection_name=cfg.chroma.collection_name,
        embedding_function=embeddings,
        persist_directory=cfg.chroma.db_path,
    )

    search_kwargs = {"k": cfg.retriever.top_k}
    if session_filter and session_filter != "All Sessions" and session_filter != "No Active Sessions Found":
        search_kwargs["filter"] = {"session_name": session_filter}

    retriever = vectorstore.as_retriever(
        search_type=cfg.retriever.search_type,
        search_kwargs=search_kwargs,
    )

    llm = OllamaLLM(
        model=cfg.ollama.model,
        base_url=cfg.ollama.base_url,
        temperature=cfg.ollama.temperature,
    )

    prompt = PromptTemplate(
        template=PROMPT_TEMPLATE,
        input_variables=["context", "question"],
    )

    # LCEL chain: retrieve docs → format → prompt → LLM → parse
    chain = (
        {"context": retriever | _format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )

    return chain, retriever


def query_rag(chain, retriever, question: str, enable_guardrails: bool = False) -> dict:
    """
    Executes a query over the LCEL chain and retrieves source documents.
    Supports input and output guardrails if enable_guardrails is True.
    """
    if enable_guardrails:
        input_passed, input_reason = check_input_safety(question)
        if not input_passed:
            return {
                "answer": f"**Query Rejected by Input Guardrail**\n\n{input_reason}",
                "sources": [],
                "input_guardrail": {"passed": False, "reason": input_reason},
                "output_guardrail": {"passed": None, "reason": "Not checked (input rejected)"}
            }
    else:
        input_passed, input_reason = True, "Guardrails disabled"

    # Run the retrieval and generation
    source_docs = retriever.invoke(question)
    answer = chain.invoke(question)
    context = _format_docs(source_docs)

    if enable_guardrails:
        output_passed, output_reason = check_output_faithfulness(context, answer)
    else:
        output_passed, output_reason = True, "Guardrails disabled"

    return {
        "answer": answer,
        "sources": [
            {
                "session": doc.metadata.get("session_name", "Unknown"),
                "source": doc.metadata.get("source", "Unknown"),
                "doc_type": doc.metadata.get("doc_type", "Unknown"),
                "page": doc.metadata.get("page", "N/A"),
            }
            for doc in source_docs
        ],
        "input_guardrail": {"passed": input_passed, "reason": input_reason},
        "output_guardrail": {"passed": output_passed, "reason": output_reason}
    }


def get_all_sessions() -> list:
    embeddings = get_embeddings()
    vectorstore = Chroma(
        collection_name=cfg.chroma.collection_name,
        embedding_function=embeddings,
        persist_directory=cfg.chroma.db_path,
    )
    
    collection_data = vectorstore.get()
    if not collection_data or not collection_data.get("metadatas"):
        return []
        
    all_metadata = collection_data["metadatas"]
    sessions = sorted(list(set(
        m["session_name"]
        for m in all_metadata
        if m and "session_name" in m
    )))
    return sessions