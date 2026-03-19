import shutil
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, HTTPException

from app.config import settings
from app.schemas.document import DocumentUploadResponse, DocumentListItem, DeleteResponse
from app.services.ingestion import ingest_document, delete_document_collection
from app.storage.document_store import save_document, get_document, list_documents, delete_document

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    settings.ensure_dirs()

    # Save file to disk
    dest_path = settings.upload_dir / file.filename
    # Handle duplicate filenames
    if dest_path.exists():
        stem = dest_path.stem
        suffix = dest_path.suffix
        import time
        dest_path = settings.upload_dir / f"{stem}_{int(time.time())}{suffix}"

    with open(dest_path, "wb") as f:
        content = await file.read()
        f.write(content)

    try:
        meta = ingest_document(dest_path, file.filename)
    except ValueError as e:
        dest_path.unlink(missing_ok=True)
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        dest_path.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")

    # Update the stored file path
    meta.file_path = str(dest_path)
    save_document(meta)

    return DocumentUploadResponse(
        document_id=meta.document_id,
        name=meta.name,
        page_count=meta.page_count,
        chunk_count=meta.chunk_count,
        size_bytes=meta.size_bytes,
        upload_time=meta.upload_time,
    )


@router.get("", response_model=list[DocumentListItem])
async def list_all_documents():
    docs = list_documents()
    return [
        DocumentListItem(
            document_id=d.document_id,
            name=d.name,
            page_count=d.page_count,
            chunk_count=d.chunk_count,
            size_bytes=d.size_bytes,
            upload_time=d.upload_time,
        )
        for d in docs
    ]


@router.delete("/{doc_id}", response_model=DeleteResponse)
async def delete_doc(doc_id: str):
    meta = get_document(doc_id)
    if not meta:
        raise HTTPException(status_code=404, detail="Document not found")

    # Remove ChromaDB collection
    delete_document_collection(doc_id)

    # Remove PDF file
    file_path = Path(meta.file_path)
    file_path.unlink(missing_ok=True)

    # Remove from store
    delete_document(doc_id)

    return DeleteResponse(deleted=True, document_id=doc_id)
