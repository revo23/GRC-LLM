import json
import logging
from typing import Any

import anthropic

from app.config import settings
from app.models.control import Control
from app.models.assessment import ControlAssessmentResult
from app.services.retrieval import retrieve_chunks

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a cybersecurity compliance expert performing a maturity assessment.
You will receive a security control requirement and excerpts from an organization's
policy document. Assess how well the policy satisfies the control.

Respond ONLY with valid JSON matching this exact schema:
{
  "control_id": string,
  "maturity_score": integer (0-5),
  "score_rationale": string (1-2 sentences explaining the score),
  "evidence": [string] (direct quotes from the policy that support the assessment),
  "gaps": [string] (specific requirements not addressed by the policy),
  "recommendations": [string] (concrete improvement actions)
}

Maturity scale:
0 - Not Implemented: No evidence of the control in the policy
1 - Initial: Ad hoc mention, no formal process defined
2 - Developing: Some elements present but incomplete or inconsistent
3 - Defined: Formal, documented process covering most requirements
4 - Managed: Measured, monitored with defined metrics and accountability
5 - Optimized: Continuously improved, integrated with risk management"""


def _build_user_prompt(control: Control, chunks: list[dict]) -> str:
    excerpts = ""
    for i, chunk in enumerate(chunks, start=1):
        excerpts += f"\n---\nExcerpt {i} [Page {chunk['page_num']}]:\n{chunk['text']}\n"

    if not excerpts:
        excerpts = "\n---\nNo relevant policy excerpts found for this control.\n"

    return f"""CONTROL: {control.id} — {control.name}
REQUIREMENT: {control.description}

POLICY EXCERPTS (from uploaded document):
{excerpts}
Assess this control."""


def _parse_assessment_response(response_text: str, control: Control, framework_id: str) -> ControlAssessmentResult:
    """Parse Claude's JSON response into a ControlAssessmentResult."""
    # Strip markdown code fences if present
    text = response_text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:-1]) if lines[-1].strip() == "```" else "\n".join(lines[1:])

    data = json.loads(text)

    score = int(data.get("maturity_score", 0))
    score = max(0, min(5, score))  # Clamp to 0-5

    return ControlAssessmentResult(
        control_id=control.id,
        control_name=control.name,
        family=control.family,
        framework_id=framework_id,
        maturity_score=score,
        score_rationale=data.get("score_rationale", ""),
        evidence=data.get("evidence", []),
        gaps=data.get("gaps", []),
        recommendations=data.get("recommendations", []),
    )


def _fallback_result(control: Control, framework_id: str, error: str) -> ControlAssessmentResult:
    return ControlAssessmentResult(
        control_id=control.id,
        control_name=control.name,
        family=control.family,
        framework_id=framework_id,
        maturity_score=0,
        score_rationale=f"Assessment failed: {error}",
        evidence=[],
        gaps=["Assessment could not be completed due to an error"],
        recommendations=["Retry the assessment"],
    )


async def assess_control(
    client: anthropic.AsyncAnthropic,
    doc_id: str,
    control: Control,
    framework_id: str,
) -> ControlAssessmentResult:
    """
    Retrieve relevant chunks for the control, then call Claude to assess it.
    Retries once on JSON parse failure.
    """
    query = f"{control.name}: {control.description}"
    chunks = retrieve_chunks(doc_id, query, n_results=5)

    user_prompt = _build_user_prompt(control, chunks)

    for attempt in range(2):
        try:
            message = await client.messages.create(
                model=settings.claude_model,
                max_tokens=1024,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_prompt}],
            )

            response_text = message.content[0].text
            return _parse_assessment_response(response_text, control, framework_id)

        except json.JSONDecodeError as e:
            if attempt == 0:
                logger.warning(f"JSON parse error for {control.id}, retrying: {e}")
                # Add correction instruction for retry
                user_prompt += "\n\nIMPORTANT: Respond ONLY with valid JSON, no other text."
                continue
            logger.error(f"JSON parse failed twice for {control.id}: {e}")
            return _fallback_result(control, framework_id, str(e))

        except Exception as e:
            logger.error(f"Error assessing control {control.id}: {e}")
            return _fallback_result(control, framework_id, str(e))

    return _fallback_result(control, framework_id, "Max retries exceeded")
