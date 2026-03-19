from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ControlAssessmentResult:
    control_id: str
    control_name: str
    family: str
    framework_id: str
    maturity_score: int  # 0–5
    score_rationale: str
    evidence: list[str]
    gaps: list[str]
    recommendations: list[str]


@dataclass
class ControlFamilyScore:
    family: str
    framework_id: str
    average_score: float
    control_count: int
    weight: float


@dataclass
class FrameworkAssessmentResult:
    framework_id: str
    framework_name: str
    overall_score: float
    family_scores: list[ControlFamilyScore]
    control_results: list[ControlAssessmentResult]


@dataclass
class AssessmentResult:
    assessment_id: str
    document_id: str
    document_name: str
    frameworks_assessed: list[str]
    overall_posture_score: float
    framework_results: list[FrameworkAssessmentResult]
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    status: str = "completed"
