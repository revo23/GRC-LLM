from pydantic import BaseModel


class AssessmentRunRequest(BaseModel):
    document_id: str
    framework_ids: list[str]


class AssessmentRunResponse(BaseModel):
    assessment_id: str
    status: str
    document_id: str
    framework_ids: list[str]


class ControlResultSchema(BaseModel):
    control_id: str
    control_name: str
    family: str
    framework_id: str
    maturity_score: int
    score_rationale: str
    evidence: list[str]
    gaps: list[str]
    recommendations: list[str]


class FamilyScoreSchema(BaseModel):
    family: str
    framework_id: str
    average_score: float
    control_count: int
    weight: float


class FrameworkResultSchema(BaseModel):
    framework_id: str
    framework_name: str
    overall_score: float
    family_scores: list[FamilyScoreSchema]
    control_results: list[ControlResultSchema]


class AssessmentDetailResponse(BaseModel):
    assessment_id: str
    document_id: str
    document_name: str
    frameworks_assessed: list[str]
    overall_posture_score: float
    framework_results: list[FrameworkResultSchema]
    created_at: str
    status: str


class AssessmentListItem(BaseModel):
    assessment_id: str
    document_id: str
    document_name: str
    frameworks_assessed: list[str]
    overall_posture_score: float
    created_at: str
    status: str
