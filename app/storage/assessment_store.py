import json
from dataclasses import asdict
from pathlib import Path
from datetime import datetime

from app.config import settings
from app.models.assessment import AssessmentResult


def _assessments_dir() -> Path:
    d = settings.data_dir / "assessments"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _assessment_path(assessment_id: str) -> Path:
    return _assessments_dir() / f"{assessment_id}.json"


def save_assessment(result: AssessmentResult) -> None:
    path = _assessment_path(result.assessment_id)
    with open(path, "w") as f:
        json.dump(asdict(result), f, indent=2)


def get_assessment(assessment_id: str) -> dict | None:
    path = _assessment_path(assessment_id)
    if not path.exists():
        return None
    with open(path) as f:
        return json.load(f)


def list_assessments() -> list[dict]:
    d = _assessments_dir()
    results = []
    for path in sorted(d.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        try:
            with open(path) as f:
                results.append(json.load(f))
        except Exception:
            pass
    return results


def update_assessment_status(assessment_id: str, status: str) -> None:
    data = get_assessment(assessment_id)
    if data:
        data["status"] = status
        path = _assessment_path(assessment_id)
        with open(path, "w") as f:
            json.dump(data, f, indent=2)


def save_pending_assessment(assessment_id: str, document_id: str, document_name: str, framework_ids: list[str]) -> None:
    """Save a placeholder record for an in-progress assessment."""
    placeholder = {
        "assessment_id": assessment_id,
        "document_id": document_id,
        "document_name": document_name,
        "frameworks_assessed": framework_ids,
        "overall_posture_score": 0.0,
        "framework_results": [],
        "created_at": datetime.utcnow().isoformat(),
        "status": "pending",
    }
    path = _assessment_path(assessment_id)
    with open(path, "w") as f:
        json.dump(placeholder, f, indent=2)
