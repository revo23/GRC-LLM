import json
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse, Response

from app.storage.assessment_store import get_assessment

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/{assessment_id}/download")
async def download_report(assessment_id: str):
    data = get_assessment(assessment_id)
    if not data:
        raise HTTPException(status_code=404, detail="Assessment not found")

    if data.get("status") not in ("completed",):
        raise HTTPException(
            status_code=409,
            detail=f"Assessment is not yet complete (status: {data.get('status')})",
        )

    filename = f"grc_report_{assessment_id[:8]}.json"
    content = json.dumps(data, indent=2)

    return Response(
        content=content,
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
