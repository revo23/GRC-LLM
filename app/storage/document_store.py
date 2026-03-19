import json
from dataclasses import asdict
from pathlib import Path

from app.config import settings
from app.models.document import DocumentMeta


def _docs_path() -> Path:
    return settings.data_dir / "documents.json"


def _load_all() -> dict[str, dict]:
    path = _docs_path()
    if not path.exists():
        return {}
    with open(path) as f:
        return json.load(f)


def _save_all(docs: dict[str, dict]) -> None:
    path = _docs_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(docs, f, indent=2)


def save_document(meta: DocumentMeta) -> None:
    docs = _load_all()
    docs[meta.document_id] = asdict(meta)
    _save_all(docs)


def get_document(doc_id: str) -> DocumentMeta | None:
    docs = _load_all()
    data = docs.get(doc_id)
    if not data:
        return None
    return DocumentMeta(**data)


def list_documents() -> list[DocumentMeta]:
    docs = _load_all()
    return [DocumentMeta(**d) for d in docs.values()]


def delete_document(doc_id: str) -> bool:
    docs = _load_all()
    if doc_id not in docs:
        return False
    del docs[doc_id]
    _save_all(docs)
    return True
