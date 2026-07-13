"""
Handles turning raw resume/JD uploads into:
  1. A per-session Chroma vector store (for grounded retrieval during questioning)
  2. LLM-generated structured summaries (used to steer question generation)

Embeddings use Google's hosted embedding API (reusing the same GOOGLE_API_KEY
already configured for Gemini backup) rather than a local sentence-transformers
model. The local model previously loaded `torch` + model weights into process
memory, which reliably OOM-killed the process on Render's 512MB free/Starter
instances the moment a session started - this API-based approach has no local
model to load, so it works fine within 512MB of RAM.
"""
import io
from typing import Optional
from pypdf import PdfReader
from langchain_community.vectorstores import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from app.config import GOOGLE_API_KEYS

_embeddings: Optional[GoogleGenerativeAIEmbeddings] = None


def get_embeddings() -> GoogleGenerativeAIEmbeddings:
    global _embeddings
    if _embeddings is None:
        if not GOOGLE_API_KEYS:
            raise RuntimeError(
                "RAG embeddings need GOOGLE_API_KEYS set (reuses your Gemini backup key) - "
                "add at least one Google API key to your environment."
            )
        _embeddings = GoogleGenerativeAIEmbeddings(
            model="models/gemini-embedding-001", google_api_key=GOOGLE_API_KEYS[0]
        )
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