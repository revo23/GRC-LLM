import asyncio
import uuid
import logging

from fastapi import APIRouter, HTTPException, BackgroundTasks

from app.frameworks import FRAMEWORK_REGISTRY
from app.schemas.assessment import (
    AssessmentRunRequest,
    AssessmentRunResponse,
    AssessmentDetailResponse,
    AssessmentListItem,
)
from app.storage.assessment_store import (
    get_assessment,
    list_assessments,
    save_pending_assessment,
    update_assessment_status,
)
from app.storage.document_store import get_document
from app.services.report_builder import run_assessment

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/assessments", tags=["assessments"])


async def _run_assessment_task(
    assessment_id: str,
    document_id: str,
    document_name: str,
    framework_ids: list[str],
):
    try:
        update_assessment_status(assessment_id, "running")
        await run_assessment(assessment_id, document_id, document_name, framework_ids)
    except Exception as e:
        logger.error(f"Assessment {assessment_id} failed: {e}")
        update_assessment_status(assessment_id, "failed")


@router.post("/run", response_model=AssessmentRunResponse)
async def run_assessment_endpoint(
    request: AssessmentRunRequest,
    background_tasks: BackgroundTasks,
):
    # Validate document exists
    doc = get_document(request.document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # Validate framework IDs
    invalid_ids = [fid for fid in request.framework_ids if fid not in FRAMEWORK_REGISTRY]
    if invalid_ids:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown framework IDs: {invalid_ids}. Valid IDs: {list(FRAMEWORK_REGISTRY.keys())}",
        )

    if not request.framework_ids:
        raise HTTPException(status_code=400, detail="At least one framework must be selected")

    assessment_id = str(uuid.uuid4())
    save_pending_assessment(assessment_id, request.document_id, doc.name, request.framework_ids)

    background_tasks.add_task(
        _run_assessment_task,
        assessment_id,
        request.document_id,
        doc.name,
        request.framework_ids,
    )

    return AssessmentRunResponse(
        assessment_id=assessment_id,
        status="pending",
        document_id=request.document_id,
        framework_ids=request.framework_ids,
    )


@router.get("", response_model=list[AssessmentListItem])
async def list_all_assessments():
    assessments = list_assessments()
    return [
        AssessmentListItem(
            assessment_id=a["assessment_id"],
            document_id=a["document_id"],
            document_name=a.get("document_name", ""),
            frameworks_assessed=a.get("frameworks_assessed", []),
            overall_posture_score=a.get("overall_posture_score", 0.0),
            created_at=a.get("created_at", ""),
            status=a.get("status", "unknown"),
        )
        for a in assessments
    ]


@router.get("/{assessment_id}", response_model=AssessmentDetailResponse)
async def get_assessment_detail(assessment_id: str):
    data = get_assessment(assessment_id)
    if not data:
        raise HTTPException(status_code=404, detail="Assessment not found")
    return AssessmentDetailResponse(**data)
