"""
Handles turning raw resume/JD uploads into:
  1. A per-session Chroma vector store (for grounded retrieval during questioning)
  2. LLM-generated structured summaries (used to steer question generation)

Embeddings use a local sentence-transformers model so no extra API key
is needed just to run RAG.
"""
import io
from typing import Optional
from pypdf import PdfReader
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

_embeddings: Optional[HuggingFaceEmbeddings] = None


def get_embeddings() -> HuggingFaceEmbeddings:
    global _embeddings
    if _embeddings is None:
        _embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    return _embeddings


def extract_text_from_upload(filename: str, raw_bytes: bytes) -> str:
    """Supports .pdf and plain text uploads."""
    if filename.lower().endswith(".pdf"):
        reader = PdfReader(io.BytesIO(raw_bytes))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    return raw_bytes.decode("utf-8", errors="ignore")


def build_session_vectorstore(session_id: str, resume_text: str, jd_text: str) -> Chroma:
    """
    Chunks resume + JD text and embeds them into an in-memory Chroma
    collection scoped to this session (collection name = session_id).
    """
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=80)

    docs = []
    for chunk in splitter.split_text(resume_text):
        docs.append(Document(page_content=chunk, metadata={"source": "resume"}))
    for chunk in splitter.split_text(jd_text):
        docs.append(Document(page_content=chunk, metadata={"source": "jd"}))

    vectorstore = Chroma.from_documents(
        documents=docs,
        embedding=get_embeddings(),
        collection_name=f"session_{session_id}",
    )
    return vectorstore


def retrieve_context(vectorstore: Chroma, query: str, k: int = 3, source_filter: Optional[str] = None) -> str:
    """Retrieve the top-k most relevant chunks for a query, optionally filtered by source."""
    filter_dict = {"source": source_filter} if source_filter else None
    results = vectorstore.similarity_search(query, k=k, filter=filter_dict)
    return "\n---\n".join(r.page_content for r in results)
