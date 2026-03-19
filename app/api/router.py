from fastapi import APIRouter

from app.api.documents import router as documents_router
from app.api.assessments import router as assessments_router
from app.api.frameworks import router as frameworks_router
from app.api.reports import router as reports_router

router = APIRouter()
router.include_router(documents_router)
router.include_router(assessments_router)
router.include_router(frameworks_router)
router.include_router(reports_router)
