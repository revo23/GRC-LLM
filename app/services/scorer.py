from app.models.assessment import (
    ControlAssessmentResult,
    ControlFamilyScore,
    FrameworkAssessmentResult,
    AssessmentResult,
)
from app.models.control import FrameworkDefinition


def compute_family_scores(
    controls: list[ControlAssessmentResult],
    framework: FrameworkDefinition,
) -> list[ControlFamilyScore]:
    """Aggregate control scores into per-family scores."""
    family_map: dict[str, list[ControlAssessmentResult]] = {}
    for result in controls:
        family_map.setdefault(result.family, []).append(result)

    family_scores = []
    for family, results in family_map.items():
        # Weighted average within family based on control weights
        control_weights = {c.id: c.weight for c in framework.controls}
        total_weight = sum(control_weights.get(r.control_id, 1.0) for r in results)
        weighted_sum = sum(
            r.maturity_score * control_weights.get(r.control_id, 1.0)
            for r in results
        )
        avg = weighted_sum / total_weight if total_weight > 0 else 0.0

        family_scores.append(ControlFamilyScore(
            family=family,
            framework_id=results[0].framework_id,
            average_score=round(avg, 2),
            control_count=len(results),
            weight=framework.family_weights.get(family, 1.0),
        ))

    return family_scores


def compute_framework_score(
    control_results: list[ControlAssessmentResult],
    framework: FrameworkDefinition,
) -> FrameworkAssessmentResult:
    """Compute a single framework's overall score from its control results."""
    family_scores = compute_family_scores(control_results, framework)

    # Weighted average of family scores
    total_weight = sum(fs.weight for fs in family_scores)
    weighted_sum = sum(fs.average_score * fs.weight for fs in family_scores)
    overall = weighted_sum / total_weight if total_weight > 0 else 0.0

    return FrameworkAssessmentResult(
        framework_id=framework.id,
        framework_name=framework.name,
        overall_score=round(overall, 2),
        family_scores=family_scores,
        control_results=control_results,
    )


def compute_overall_posture(framework_results: list[FrameworkAssessmentResult]) -> float:
    """Compute the overall posture score as the mean of all framework scores."""
    if not framework_results:
        return 0.0
    return round(sum(fr.overall_score for fr in framework_results) / len(framework_results), 2)


def build_assessment_result(
    assessment_id: str,
    document_id: str,
    document_name: str,
    framework_results: list[FrameworkAssessmentResult],
) -> AssessmentResult:
    overall = compute_overall_posture(framework_results)
    framework_ids = [fr.framework_id for fr in framework_results]

    return AssessmentResult(
        assessment_id=assessment_id,
        document_id=document_id,
        document_name=document_name,
        frameworks_assessed=framework_ids,
        overall_posture_score=overall,
        framework_results=framework_results,
    )
