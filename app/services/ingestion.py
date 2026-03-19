import uuid
import re
from pathlib import Path

import fitz  # PyMuPDF
import chromadb
from sentence_transformers import SentenceTransformer

from app.config import settings
from app.models.document import DocumentMeta


_embedding_model: SentenceTransformer | None = None


def get_embedding_model() -> SentenceTransformer:
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = SentenceTransformer("all-mpnet-base-v2")
    return _embedding_model


def _get_chroma_client() -> chromadb.PersistentClient:
    return chromadb.PersistentClient(path=str(settings.chroma_dir))


def _extract_text_pages(pdf_path: Path) -> list[tuple[int, str]]:
    """Extract (page_num, text) tuples from a PDF."""
    doc = fitz.open(str(pdf_path))
    pages = []
    for page_num, page in enumerate(doc, start=1):
        text = page.get_text("text")
        if text.strip():
            pages.append((page_num, text))
    doc.close()
    return pages


def _chunk_text(page_num: int, text: str, chunk_size: int = 1600, overlap: int = 200) -> list[dict]:
    """Split page text into chunks with overlap. Returns list of chunk dicts."""
    # Split on sentence boundaries
    sentences = re.split(r'(?<=[.!?])\s+', text)
    chunks = []
    current = ""

    for sentence in sentences:
        if len(current) + len(sentence) <= chunk_size:
            current = current + " " + sentence if current else sentence
        else:
            if len(current) >= 50 * 4:  # min 50 tokens ≈ 200 chars
                chunks.append({"page_num": page_num, "text": current.strip()})
            # Start new chunk with overlap
            # Take the tail of current as overlap seed
            overlap_text = current[-overlap:] if len(current) > overlap else current
            current = overlap_text + " " + sentence

    if current and len(current) >= 50 * 4:
        chunks.append({"page_num": page_num, "text": current.strip()})

    return chunks


def ingest_document(file_path: Path, original_filename: str) -> DocumentMeta:
    """
    Parse PDF, chunk text, embed chunks, store in ChromaDB.
    Returns DocumentMeta for the ingested document.
    """
    doc_id = str(uuid.uuid4()).replace("-", "")

    # Validate file size
    size_bytes = file_path.stat().st_size
    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    if size_bytes > max_bytes:
        raise ValueError(f"File exceeds maximum size of {settings.max_upload_size_mb}MB")

    # Extract text
    pages = _extract_text_pages(file_path)
    if not pages:
        raise ValueError("No text content could be extracted from the PDF")

    page_count = len(pages)

    # Chunk all pages
    all_chunks: list[dict] = []
    for page_num, text in pages:
        chunks = _chunk_text(page_num, text)
        for i, chunk in enumerate(chunks):
            chunk["chunk_index"] = len(all_chunks)
            chunk["doc_id"] = doc_id
            chunk["source_file"] = original_filename
            all_chunks.append(chunk)

    if not all_chunks:
        raise ValueError("No chunks could be created from the document")

    # Embed all chunks
    model = get_embedding_model()
    texts = [c["text"] for c in all_chunks]
    embeddings = model.encode(texts, show_progress_bar=False, batch_size=32).tolist()

    # Store in ChromaDB
    client = _get_chroma_client()
    collection_name = f"doc_{doc_id}"
    collection = client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"},
    )

    ids = [f"{doc_id}_chunk_{c['chunk_index']}" for c in all_chunks]
    metadatas = [
        {
            "doc_id": c["doc_id"],
            "page_num": c["page_num"],
            "chunk_index": c["chunk_index"],
            "source_file": c["source_file"],
        }
        for c in all_chunks
    ]

    collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=texts,
        metadatas=metadatas,
    )

    return DocumentMeta(
        document_id=doc_id,
        name=original_filename,
        filename=original_filename,
        file_path=str(file_path),
        page_count=page_count,
        chunk_count=len(all_chunks),
        size_bytes=size_bytes,
    )


def delete_document_collection(doc_id: str) -> None:
    """Remove ChromaDB collection for a document."""
    client = _get_chroma_client()
    collection_name = f"doc_{doc_id}"
    try:
        client.delete_collection(collection_name)
    except Exception:
        pass  # Collection may not exist
