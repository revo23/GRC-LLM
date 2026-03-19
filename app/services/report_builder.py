import asyncio
import logging
import uuid
from dataclasses import asdict

import anthropic

from app.config import settings
from app.frameworks import FRAMEWORK_REGISTRY
from app.models.assessment import AssessmentResult, FrameworkAssessmentResult
from app.services.assessor import assess_control
from app.services.scorer import compute_framework_score, build_assessment_result
from app.storage.assessment_store import save_assessment, update_assessment_status

logger = logging.getLogger(__name__)


async def run_assessment(
    assessment_id: str,
    document_id: str,
    document_name: str,
    framework_ids: list[str],
) -> AssessmentResult:
    """
    Orchestrate full assessment: for each framework, assess all controls in parallel.
    Saves intermediate status updates and final result to storage.
    """
    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    framework_results: list[FrameworkAssessmentResult] = []

    for fw_id in framework_ids:
        framework = FRAMEWORK_REGISTRY.get(fw_id)
        if not framework:
            logger.warning(f"Unknown framework: {fw_id}")
            continue

        logger.info(f"Assessing framework: {framework.name} ({len(framework.controls)} controls)")

        # Assess all controls in a framework concurrently (with rate limiting)
        semaphore = asyncio.Semaphore(5)  # Max 5 concurrent API calls

        async def assess_with_semaphore(control):
            async with semaphore:
                return await assess_control(client, document_id, control, fw_id)

        tasks = [assess_with_semaphore(control) for control in framework.controls]
        control_results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions
        valid_results = []
        for i, result in enumerate(control_results):
            if isinstance(result, Exception):
                logger.error(f"Control assessment failed: {result}")
                # Create fallback result
                from app.services.assessor import _fallback_result
                valid_results.append(_fallback_result(
                    framework.controls[i], fw_id, str(result)
                ))
            else:
                valid_results.append(result)

        fw_result = compute_framework_score(valid_results, framework)
        framework_results.append(fw_result)
        logger.info(f"Framework {fw_id} score: {fw_result.overall_score}")

    result = build_assessment_result(
        assessment_id=assessment_id,
        document_id=document_id,
        document_name=document_name,
        framework_results=framework_results,
    )

    save_assessment(result)
    return result
