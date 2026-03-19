from pydantic import BaseModel


class ReportDownloadResponse(BaseModel):
    assessment_id: str
    filename: str
    content_type: str = "application/json"
