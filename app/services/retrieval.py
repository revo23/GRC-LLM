import chromadb
from sentence_transformers import SentenceTransformer

from app.config import settings
from app.services.ingestion import get_embedding_model


def _get_chroma_client() -> chromadb.PersistentClient:
    return chromadb.PersistentClient(path=str(settings.chroma_dir))


def retrieve_chunks(doc_id: str, query: str, n_results: int = 5) -> list[dict]:
    """
    Query ChromaDB for the top-k most relevant chunks for a given query.
    Returns list of dicts with 'text', 'page_num', 'chunk_index'.
    """
    model: SentenceTransformer = get_embedding_model()
    query_embedding = model.encode([query], show_progress_bar=False)[0].tolist()

    client = _get_chroma_client()
    collection_name = f"doc_{doc_id}"

    try:
        collection = client.get_collection(collection_name)
    except Exception:
        return []

    # Get actual count to avoid requesting more than available
    actual_count = collection.count()
    n_results = min(n_results, actual_count)
    if n_results == 0:
        return []

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
        include=["documents", "metadatas", "distances"],
    )

    chunks = []
    if results["documents"] and results["documents"][0]:
        for text, meta, distance in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        ):
            chunks.append({
                "text": text,
                "page_num": meta.get("page_num", 0),
                "chunk_index": meta.get("chunk_index", 0),
                "relevance_score": 1 - distance,  # cosine similarity
            })

    return chunks
