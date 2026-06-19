# ingest.py
import os
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
    CSVLoader,
    UnstructuredExcelLoader,
    UnstructuredPowerPointLoader,
)
from langchain_community.document_loaders import Docx2txtLoader
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
from transcriber import extract_transcript
from config import cfg


# -- Embedding Setup ----------------------------------------------------------
def get_embeddings():
    return OllamaEmbeddings(
        model    = cfg.ollama.embedding,
        base_url = cfg.ollama.base_url,
    )


# -- Load Reference Documents -------------------------------------------------
def load_reference_docs(session_name: str) -> list:
    session_docs_dir = os.path.join(cfg.data.documents_dir, session_name)
    if not os.path.exists(session_docs_dir):
        print(f"No reference docs folder found for session: {session_name}")
        return []

    docs = []
    loader_map = {
        ".pdf" : PyPDFLoader,
        ".docx": Docx2txtLoader,
        ".txt" : TextLoader,
        ".csv" : CSVLoader,
        ".xlsx": UnstructuredExcelLoader,
        ".xls" : UnstructuredExcelLoader,
        ".pptx": UnstructuredPowerPointLoader,
        ".ppt" : UnstructuredPowerPointLoader,
        ".py"  : TextLoader,
        ".sql" : TextLoader,
        ".json": TextLoader,
        ".md"  : TextLoader,
    }

    for filename in os.listdir(session_docs_dir):
        ext      = os.path.splitext(filename)[-1].lower()
        filepath = os.path.join(session_docs_dir, filename)
        loader_cls = loader_map.get(ext)

        if not loader_cls:
            print(f"Skipping unsupported file type: {filename}")
            continue

        try:
            loaded = loader_cls(filepath).load()
            for doc in loaded:
                doc.metadata["session_name"] = session_name
                doc.metadata["doc_type"]     = ext.replace(".", "")
                doc.metadata["source"]       = filename
            docs.extend(loaded)
            print(f"Loaded [{ext}]: {filename} ({len(loaded)} pages)")
        except Exception as e:
            print(f"Error loading {filename}: {e}")

    return docs


# -- Load Transcript as Document ----------------------------------------------
def load_transcript_as_doc(
    session_name : str,
    video_path   : str,
    caption_path : str = None
) -> list:
    transcript_text = extract_transcript(
        session_name = session_name,
        video_path   = video_path,
        caption_path = caption_path,
    )
    doc = Document(
        page_content = transcript_text,
        metadata     = {
            "session_name": session_name,
            "doc_type"    : "transcript",
            "source"      : f"{session_name}.txt",
            "page"        : 1,
        }
    )
    return [doc]


# -- Chunk Documents ----------------------------------------------------------
def chunk_documents(docs: list) -> list:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size    = cfg.data.chunk_size,
        chunk_overlap = cfg.data.chunk_overlap,
        separators    = ["\n\n", "\n", ".", " "]
    )
    chunks = splitter.split_documents(docs)
    print(f"Total chunks created: {len(chunks)}")
    return chunks


# -- Store in ChromaDB --------------------------------------------------------
def store_in_chromadb(chunks: list):
    print(f"Loading embedding model: {cfg.ollama.embedding} via Ollama")
    embeddings = get_embeddings()

    print(f"Storing {len(chunks)} chunks in ChromaDB")
    Chroma.from_documents(
        documents         = chunks,
        embedding         = embeddings,
        collection_name   = cfg.chroma.collection_name,
        persist_directory = cfg.chroma.db_path,
    )
    print(f"Successfully stored {len(chunks)} chunks in ChromaDB")


# -- Main Ingestion Entry Point -----------------------------------------------
def ingest_kt_session(
    session_name : str,
    video_path   : str = None,
    caption_path : str = None,
):
    print("=" * 60)
    print(f"Ingesting KT Session: {session_name}")
    print("=" * 60)

    all_docs = []

    # load transcript
    if video_path:
        print("\n[1/3] Extracting transcript from video...")
        transcript_docs = load_transcript_as_doc(
            session_name = session_name,
            video_path   = video_path,
            caption_path = caption_path,
        )
        all_docs.extend(transcript_docs)
        print(f"Transcript loaded: {len(transcript_docs)} document(s)")
    else:
        print("\n[1/3] No video file provided, skipping transcript extraction.")

    # load reference docs
    print("\n[2/3] Loading reference documents...")
    ref_docs = load_reference_docs(session_name)
    all_docs.extend(ref_docs)
    print(f"Reference docs loaded: {len(ref_docs)} document(s)")

    # chunk and store
    print("\n[3/3] Chunking and storing in ChromaDB...")
    chunks = chunk_documents(all_docs)
    store_in_chromadb(chunks)

    print(f"\nKT Session ingestion complete: {session_name}")
    print(f"Total documents : {len(all_docs)}")
    print(f"Total chunks    : {len(chunks)}")
    print("=" * 60)


if __name__ == "__main__":
    # example manual run
    ingest_kt_session(
        session_name = "kafka-pipeline-onboarding",
        video_path   = "data/videos/kafka-pipeline-onboarding.mp4",
        caption_path = "data/captions/kafka-pipeline-onboarding.vtt",
    )