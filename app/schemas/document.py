from pydantic import BaseModel


class DocumentUploadResponse(BaseModel):
    document_id: str
    name: str
    page_count: int
    chunk_count: int
    size_bytes: int
    upload_time: str


class DocumentListItem(BaseModel):
    document_id: str
    name: str
    page_count: int
    chunk_count: int
    size_bytes: int
    upload_time: str


class DeleteResponse(BaseModel):
    deleted: bool
    document_id: str
