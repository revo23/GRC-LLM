from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class DocumentMeta:
    document_id: str
    name: str
    filename: str
    file_path: str
    page_count: int
    chunk_count: int
    upload_time: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    size_bytes: int = 0
