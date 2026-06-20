"""
rag_eval.py — RAGAS-inspired quality evaluator for GRC-LLM RAG assessment outputs.

Evaluates a completed assessment JSON on 6 quality dimensions using Claude
claude-sonnet-4-6 as the LLM judge, plus a computed evidence-grounding check.

Usage:
    python rag_eval.py <pdf_path> <json_path> [options]

Options:
    --frameworks fw1,fw2,...   Comma-separated framework IDs to evaluate
                               (default: all frameworks present in the JSON)
    --output path/to/out.txt   Output file path
                               (default: <json_stem>_rag_eval.txt next to the JSON)
    --concurrency N            Max parallel LLM calls (default: 5)
    --list-frameworks          Print available framework IDs and exit

Evaluation dimensions (each scored 0.0 – 1.0):
  1. Faithfulness          — rationale/gaps claims are grounded in evidence quotes
  2. Evidence Relevance    — evidence quotes match the specific control requirement
  3. Score Consistency     — maturity score is justified by evidence + rationale
  4. Gap Completeness      — gaps accurately capture what's missing from the policy
  5. Recommendation Quality— recommendations are specific and actionable
  6. Evidence Groundedness — evidence quotes can be located in the original PDF
                             (computed, no LLM call; detects hallucinated citations)

Score interpretation:
  0.90 – 1.00  Excellent
  0.80 – 0.89  Good
  0.70 – 0.79  Acceptable
  0.60 – 0.69  Needs Improvement
  0.00 – 0.59  Poor
"""

from __future__ import annotations

import argparse
import asyncio
import difflib
import json
import logging
import re
import sys
import unicodedata
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Bootstrap: ensure project root on sys.path
# ---------------------------------------------------------------------------
_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from app.config import settings  # loads .env

# ---------------------------------------------------------------------------
# Evaluation model — hardcoded per spec
# ---------------------------------------------------------------------------
_EVAL_MODEL = "claude-sonnet-4-6"

# ---------------------------------------------------------------------------
# Maturity label helper
# ---------------------------------------------------------------------------
_MATURITY = {
    0: "Not Implemented",
    1: "Initial",
    2: "Developing",
    3: "Defined",
    4: "Managed",
    5: "Optimized",
}

_SCORE_LABEL = [
    (0.90, "Excellent"),
    (0.80, "Good"),
    (0.70, "Acceptable"),
    (0.60, "Needs Improvement"),
    (0.00, "Poor"),
]


def _quality_label(score: float) -> str:
    for threshold, label in _SCORE_LABEL:
        if score >= threshold:
            return label
    return "Poor"


# ---------------------------------------------------------------------------
# LLM judge client (claude-sonnet-4-6 only)
# ---------------------------------------------------------------------------

class _EvalClient:
    """Minimal async wrapper around Anthropic SDK for the evaluation model."""

    def __init__(self) -> None:
        api_key = settings.anthropic_api_key
        if not api_key:
            sys.exit("Error: ANTHROPIC_API_KEY is not set in .env")
        import anthropic
        self._client = anthropic.AsyncAnthropic(api_key=api_key)

    async def judge(self, system: str, user: str) -> str:
        msg = await self._client.messages.create(
            model=_EVAL_MODEL,
            max_tokens=1024,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return msg.content[0].text


# ---------------------------------------------------------------------------
# Prompt templates
# ---------------------------------------------------------------------------

_JUDGE_SYSTEM = """You are an expert quality auditor for a RAG-based GRC compliance assessment system.
The system retrieves policy excerpts from a document and uses an LLM to assess how well
the policy satisfies each security control, producing: a maturity score (0–5), a rationale,
evidence quotes, gaps, and recommendations.

Evaluate the assessment on FIVE dimensions. Each score is 0.00 to 1.00.

DIMENSION DEFINITIONS:
1. faithfulness (0–1):
   Do the claims in score_rationale and gaps derive ONLY from what the evidence quotes
   actually state? Penalise if the rationale asserts facts with no evidence basis, or if
   gaps claim things are absent while evidence quotes contradict that.

2. evidence_relevance (0–1):
   Are the evidence quotes genuinely relevant to THIS control's specific requirement?
   Penalise generic policy boilerplate that does not address the control, or off-topic excerpts.

3. score_consistency (0–1):
   Is the maturity_score logically consistent with the evidence strength, rationale, and gaps?
   Strong evidence + minor gaps → expect score ≥ 3; no evidence → expect score 0–1.
   Penalise inflated or deflated scores.

4. gap_completeness (0–1):
   Do the gaps accurately and comprehensively capture what the control requires but the
   evidence does NOT show? Penalise: (a) gaps contradicted by evidence, (b) gaps that
   miss obvious requirements of the control, (c) vague or redundant gaps.

5. recommendation_quality (0–1):
   Are recommendations specific, actionable, and directly addressing the identified gaps?
   Penalise generic or boilerplate suggestions not tied to the gaps.

Respond ONLY with valid JSON — no markdown, no prose outside the JSON:
{
  "faithfulness": <float>,
  "faithfulness_reason": "<1-sentence justification>",
  "evidence_relevance": <float>,
  "evidence_relevance_reason": "<1-sentence justification>",
  "score_consistency": <float>,
  "score_consistency_reason": "<1-sentence justification>",
  "gap_completeness": <float>,
  "gap_completeness_reason": "<1-sentence justification>",
  "recommendation_quality": <float>,
  "recommendation_quality_reason": "<1-sentence justification>"
}"""


def _build_judge_prompt(control_id: str, control_name: str, control_desc: str,
                        cr: dict) -> str:
    evidence_lines = "\n".join(
        f"  [{i+1}] {q}" for i, q in enumerate(cr.get("evidence", []))
    ) or "  (none)"
    gaps_lines = "\n".join(
        f"  - {g}" for g in cr.get("gaps", [])
    ) or "  (none)"
    recs_lines = "\n".join(
        f"  - {r}" for r in cr.get("recommendations", [])
    ) or "  (none)"

    return f"""CONTROL ID: {control_id}
CONTROL NAME: {control_name}
CONTROL REQUIREMENT: {control_desc}

ASSESSMENT OUTPUT:
  Maturity Score: {cr.get('maturity_score', 'N/A')} / 5
  Score Rationale: {cr.get('score_rationale', '')}

  Evidence (policy quotes cited):
{evidence_lines}

  Gaps:
{gaps_lines}

  Recommendations:
{recs_lines}

Evaluate this assessment on the five dimensions."""


# ---------------------------------------------------------------------------
# Evidence Groundedness (computed — no LLM)
# ---------------------------------------------------------------------------

def _normalize(text: str) -> str:
    """Collapse whitespace and normalise unicode for fuzzy matching."""
    text = unicodedata.normalize("NFKC", text)
    return re.sub(r"\s+", " ", text).strip().lower()


def _groundedness_score(evidence_quotes: list[str], pdf_text: str) -> tuple[float, list[bool]]:
    """
    For each evidence quote, check whether it (or a close paraphrase) can be
    found in the PDF full text via sliding-window SequenceMatcher.

    Returns (mean_score, per_quote_found_list).
    A quote is 'found' when the best window similarity >= 0.72.
    """
    if not evidence_quotes:
        return 1.0, []  # no evidence to verify — not penalised here

    norm_pdf = _normalize(pdf_text)
    results: list[bool] = []

    for quote in evidence_quotes:
        norm_q = _normalize(quote)
        q_len = len(norm_q)
        if q_len < 15:
            results.append(True)  # too short to verify meaningfully
            continue

        # Slide a window of quote-length (+50% slack) over the PDF text
        window = int(q_len * 1.4)
        best = 0.0
        step = max(1, q_len // 4)
        for start in range(0, max(1, len(norm_pdf) - window + 1), step):
            chunk = norm_pdf[start : start + window]
            ratio = difflib.SequenceMatcher(None, norm_q, chunk, autojunk=False).ratio()
            if ratio > best:
                best = ratio
            if best >= 0.72:
                break

        results.append(best >= 0.72)

    found_count = sum(results)
    score = found_count / len(results) if results else 1.0
    return round(score, 3), results


# ---------------------------------------------------------------------------
# Per-control evaluation dataclass
# ---------------------------------------------------------------------------

class ControlEval:
    __slots__ = (
        "control_id", "control_name", "family", "maturity_score",
        "faithfulness", "faithfulness_reason",
        "evidence_relevance", "evidence_relevance_reason",
        "score_consistency", "score_consistency_reason",
        "gap_completeness", "gap_completeness_reason",
        "recommendation_quality", "recommendation_quality_reason",
        "evidence_groundedness", "groundedness_detail",
        "composite", "error",
    )

    def __init__(self, control_id: str, control_name: str, family: str,
                 maturity_score: int) -> None:
        self.control_id = control_id
        self.control_name = control_name
        self.family = family
        self.maturity_score = maturity_score
        self.faithfulness = 0.0
        self.faithfulness_reason = ""
        self.evidence_relevance = 0.0
        self.evidence_relevance_reason = ""
        self.score_consistency = 0.0
        self.score_consistency_reason = ""
        self.gap_completeness = 0.0
        self.gap_completeness_reason = ""
        self.recommendation_quality = 0.0
        self.recommendation_quality_reason = ""
        self.evidence_groundedness = 1.0
        self.groundedness_detail: list[bool] = []
        self.composite = 0.0
        self.error: str | None = None

    def compute_composite(self) -> None:
        # Equal weights for the 5 LLM dimensions; groundedness as a 6th equal dimension
        dims = [
            self.faithfulness,
            self.evidence_relevance,
            self.score_consistency,
            self.gap_completeness,
            self.recommendation_quality,
            self.evidence_groundedness,
        ]
        self.composite = round(sum(dims) / len(dims), 4)


# ---------------------------------------------------------------------------
# Evaluate a single control
# ---------------------------------------------------------------------------

async def _eval_control(
    client: _EvalClient,
    semaphore: asyncio.Semaphore,
    control_id: str,
    control_name: str,
    control_desc: str,
    cr: dict,
    pdf_text: str,
) -> ControlEval:
    ev = ControlEval(
        control_id=control_id,
        control_name=control_name,
        family=cr.get("family", ""),
        maturity_score=cr.get("maturity_score", 0),
    )

    # 1. Computed: Evidence Groundedness (no LLM needed)
    ev.evidence_groundedness, ev.groundedness_detail = _groundedness_score(
        cr.get("evidence", []), pdf_text
    )

    # 2. LLM judge: 5 dimensions
    prompt = _build_judge_prompt(control_id, control_name, control_desc, cr)

    for attempt in range(2):
        try:
            async with semaphore:
                raw = await client.judge(_JUDGE_SYSTEM, prompt)
            # Strip markdown fences if any
            text = raw.strip()
            if text.startswith("```"):
                lines = text.splitlines()
                text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
            data = json.loads(text)

            ev.faithfulness          = float(data.get("faithfulness", 0))
            ev.faithfulness_reason   = data.get("faithfulness_reason", "")
            ev.evidence_relevance    = float(data.get("evidence_relevance", 0))
            ev.evidence_relevance_reason = data.get("evidence_relevance_reason", "")
            ev.score_consistency     = float(data.get("score_consistency", 0))
            ev.score_consistency_reason  = data.get("score_consistency_reason", "")
            ev.gap_completeness      = float(data.get("gap_completeness", 0))
            ev.gap_completeness_reason   = data.get("gap_completeness_reason", "")
            ev.recommendation_quality      = float(data.get("recommendation_quality", 0))
            ev.recommendation_quality_reason = data.get("recommendation_quality_reason", "")
            break

        except json.JSONDecodeError as e:
            if attempt == 0:
                prompt += "\n\nIMPORTANT: Output strictly valid JSON only. No markdown."
                continue
            ev.error = f"JSON parse failed: {e}"
        except Exception as e:
            ev.error = f"LLM call failed: {e}"
            break

    ev.compute_composite()
    return ev


# ---------------------------------------------------------------------------
# Text report formatter
# ---------------------------------------------------------------------------

_SEP  = "=" * 80
_DASH = "-" * 80
_DIM_NAMES = [
    ("faithfulness",       "Faithfulness          "),
    ("evidence_relevance", "Evidence Relevance    "),
    ("score_consistency",  "Score Consistency     "),
    ("gap_completeness",   "Gap Completeness      "),
    ("recommendation_quality", "Recommendation Quality"),
    ("evidence_groundedness",  "Evidence Groundedness "),
]


def _bar(score: float, width: int = 20) -> str:
    filled = int(round(score * width))
    return "[" + "#" * filled + "." * (width - filled) + "]"


def _fmt_score(score: float) -> str:
    return f"{score:.3f}  {_bar(score)}  {_quality_label(score)}"


def _dim_avg(evals: list[ControlEval], attr: str) -> float:
    vals = [getattr(e, attr) for e in evals if e.error is None]
    return round(sum(vals) / len(vals), 4) if vals else 0.0


def _format_report(
    pdf_path: Path,
    json_path: Path,
    assessment: dict,
    fw_evals: dict[str, list[ControlEval]],
    requested_frameworks: list[str],
) -> str:
    lines: list[str] = []

    def ln(s: str = "") -> None:
        lines.append(s)

    # ── Header ────────────────────────────────────────────────────────────────
    ln(_SEP)
    ln("GRC-LLM RAG Evaluation Report")
    ln(_SEP)
    ln(f"PDF Document   : {pdf_path.name}")
    ln(f"Assessment JSON: {json_path.name}")
    ln(f"Evaluator Model: {_EVAL_MODEL}")
    ln(f"Evaluation Date: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
    ln(f"Frameworks     : {', '.join(requested_frameworks)}")
    ln()

    # ── Dimension legend ──────────────────────────────────────────────────────
    ln("EVALUATION DIMENSIONS")
    ln(_DASH)
    legend = [
        ("Faithfulness",           "Claims in rationale/gaps are grounded in evidence quotes"),
        ("Evidence Relevance",     "Evidence quotes are relevant to the specific control requirement"),
        ("Score Consistency",      "Maturity score (0-5) is justified by evidence and rationale"),
        ("Gap Completeness",       "Gaps accurately capture what is missing from the policy"),
        ("Recommendation Quality", "Recommendations are specific, actionable, and gap-targeted"),
        ("Evidence Groundedness",  "Evidence quotes can be located in the original PDF (hallucination check)"),
    ]
    for name, desc in legend:
        ln(f"  {name:<24}  {desc}")
    ln()

    # ── Overall summary across all evaluated frameworks ────────────────────────
    all_evals: list[ControlEval] = [e for evals in fw_evals.values() for e in evals]
    valid_evals = [e for e in all_evals if e.error is None]
    total_controls = len(all_evals)
    failed_evals   = len([e for e in all_evals if e.error])

    overall_composite = round(
        sum(e.composite for e in valid_evals) / len(valid_evals), 4
    ) if valid_evals else 0.0

    ln(_SEP)
    ln(f"OVERALL RAG QUALITY SCORE:  {overall_composite:.3f} / 1.000  "
       f"({_quality_label(overall_composite)})")
    ln(_SEP)
    ln(f"Controls evaluated: {total_controls}"
       + (f"  |  Evaluation errors: {failed_evals}" if failed_evals else ""))
    ln()

    ln(f"{'Dimension':<28}  {'Score':>6}  {'Bar (0→1)':<24}  {'Label'}")
    ln(_DASH)
    for attr, label in _DIM_NAMES:
        avg = _dim_avg(all_evals, attr)
        ln(f"  {label}  {avg:.3f}  {_bar(avg)}  {_quality_label(avg)}")
    ln()

    # ── Per-framework breakdown ────────────────────────────────────────────────
    for fw_id, evals in fw_evals.items():
        valid = [e for e in evals if e.error is None]
        fw_composite = round(
            sum(e.composite for e in valid) / len(valid), 4
        ) if valid else 0.0

        # Framework header
        fw_name = next(
            (fr["framework_name"] for fr in assessment.get("framework_results", [])
             if fr["framework_id"] == fw_id),
            fw_id,
        )
        ln(_SEP)
        ln(f"FRAMEWORK: {fw_name}")
        ln(f"Quality Score: {fw_composite:.3f}  {_bar(fw_composite)}  "
           f"{_quality_label(fw_composite)}")
        ln(_SEP)
        ln()

        # Framework-level dimension summary
        ln(f"  {'Dimension':<28}  {'Score':>6}  {'Bar':<24}")
        ln(f"  {_DASH[:62]}")
        for attr, label in _DIM_NAMES:
            avg = _dim_avg(evals, attr)
            ln(f"  {label}  {avg:.3f}  {_bar(avg)}")
        ln()

        # Per-family grouping
        families: dict[str, list[ControlEval]] = {}
        for ev in evals:
            families.setdefault(ev.family, []).append(ev)

        for family, fam_evals in families.items():
            fam_valid = [e for e in fam_evals if e.error is None]
            fam_composite = round(
                sum(e.composite for e in fam_valid) / len(fam_valid), 4
            ) if fam_valid else 0.0

            ln(f"  Family: {family}  "
               f"({len(fam_evals)} controls)  "
               f"Quality: {fam_composite:.3f}  {_quality_label(fam_composite)}")
            ln(f"  {_DASH}")

            for ev in fam_evals:
                maturity_lbl = _MATURITY.get(ev.maturity_score, str(ev.maturity_score))
                ln(f"  {ev.control_id}  |  {ev.control_name}  "
                   f"|  Maturity: {ev.maturity_score} ({maturity_lbl})"
                   f"  |  Quality: {ev.composite:.3f} ({_quality_label(ev.composite)})")

                if ev.error:
                    ln(f"    [ERROR] {ev.error}")
                    ln()
                    continue

                # Dimension scores in a compact table
                dims_data = [
                    ("Faithfulness",           ev.faithfulness,          ev.faithfulness_reason),
                    ("Evidence Relevance",     ev.evidence_relevance,    ev.evidence_relevance_reason),
                    ("Score Consistency",      ev.score_consistency,     ev.score_consistency_reason),
                    ("Gap Completeness",       ev.gap_completeness,      ev.gap_completeness_reason),
                    ("Recommendation Quality", ev.recommendation_quality, ev.recommendation_quality_reason),
                ]
                for dim_name, dim_score, dim_reason in dims_data:
                    ln(f"    {dim_name:<24}  {dim_score:.3f}  {dim_reason}")

                # Evidence Groundedness — computed
                found = ev.groundedness_detail
                n_quotes = len(found)
                n_found  = sum(found)
                if n_quotes == 0:
                    grnd_detail = "no evidence quotes to verify"
                else:
                    grnd_detail = f"{n_found}/{n_quotes} quotes located in PDF"
                    if n_found < n_quotes:
                        grnd_detail += "  [WARNING: possible hallucinated citations]"
                ln(f"    {'Evidence Groundedness':<24}  "
                   f"{ev.evidence_groundedness:.3f}  {grnd_detail}")
                ln()

            ln()

    # ── Anomaly summary ────────────────────────────────────────────────────────
    low_threshold = 0.60
    anomalies = [
        e for e in valid_evals if e.composite < low_threshold
    ]
    if anomalies:
        ln(_SEP)
        ln(f"CONTROLS FLAGGED FOR REVIEW  (composite quality < {low_threshold:.2f})")
        ln(_SEP)
        for e in sorted(anomalies, key=lambda x: x.composite):
            ln(f"  {e.control_id:<12}  {e.control_name:<50}  "
               f"Quality: {e.composite:.3f}")
        ln()

    hallucinations = [
        e for e in valid_evals
        if e.evidence_groundedness < 0.50 and e.groundedness_detail
    ]
    if hallucinations:
        ln(_SEP)
        ln("CONTROLS WITH POTENTIAL HALLUCINATED EVIDENCE  (groundedness < 0.50)")
        ln(_SEP)
        for e in sorted(hallucinations, key=lambda x: x.evidence_groundedness):
            ln(f"  {e.control_id:<12}  Groundedness: {e.evidence_groundedness:.3f}  "
               f"{e.control_name}")
        ln()

    ln(_SEP)
    ln("END OF REPORT")
    ln(_SEP)
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

async def _run_eval(
    pdf_path: Path,
    json_path: Path,
    requested_fw_ids: list[str],
    output_path: Path,
    concurrency: int,
) -> None:
    # Load assessment JSON
    with open(json_path, encoding="utf-8") as f:
        assessment: dict = json.load(f)

    # Index framework results by fw_id
    fw_results_by_id: dict[str, dict] = {
        fr["framework_id"]: fr
        for fr in assessment.get("framework_results", [])
    }

    # Filter to requested frameworks
    missing = [fid for fid in requested_fw_ids if fid not in fw_results_by_id]
    if missing:
        print(f"Warning: framework(s) not found in JSON: {missing}")
        print(f"  JSON contains: {list(fw_results_by_id.keys())}")
    eval_fw_ids = [fid for fid in requested_fw_ids if fid in fw_results_by_id]
    if not eval_fw_ids:
        sys.exit("Error: none of the requested frameworks are present in the JSON.")

    # Load control descriptions from framework registry
    from app.frameworks import FRAMEWORK_REGISTRY
    ctrl_desc: dict[str, str] = {}
    for fw_id in eval_fw_ids:
        fw_def = FRAMEWORK_REGISTRY.get(fw_id)
        if fw_def:
            for c in fw_def.controls:
                ctrl_desc[c.id] = c.description

    # Extract PDF full text for groundedness check
    print("[1/3] Extracting PDF text for groundedness check ...")
    import fitz
    pdf_doc = fitz.open(str(pdf_path))
    pdf_text = "\n".join(
        page.get_text("text") for page in pdf_doc
        if page.get_text("text").strip()
    )
    pdf_doc.close()
    print(f"      Extracted {len(pdf_text):,} characters from {pdf_path.name}")

    # Set up LLM client and semaphore
    client = _EvalClient()
    semaphore = asyncio.Semaphore(concurrency)

    total_controls = sum(
        len(fw_results_by_id[fid]["control_results"]) for fid in eval_fw_ids
    )
    print(f"[2/3] Evaluating {total_controls} controls across "
          f"{len(eval_fw_ids)} framework(s) ...")

    # Build and run all evaluation tasks
    fw_evals: dict[str, list[ControlEval]] = {}
    done_count = 0

    for fw_id in eval_fw_ids:
        fr = fw_results_by_id[fw_id]
        control_results: list[dict] = fr.get("control_results", [])

        tasks = []
        for cr in control_results:
            cid   = cr["control_id"]
            cname = cr["control_name"]
            cdesc = ctrl_desc.get(cid, cname)  # fall back to name if desc missing
            tasks.append(_eval_control(
                client, semaphore, cid, cname, cdesc, cr, pdf_text
            ))

        results = await asyncio.gather(*tasks, return_exceptions=True)
        evals: list[ControlEval] = []
        for cr, res in zip(control_results, results):
            if isinstance(res, Exception):
                ev = ControlEval(
                    cr["control_id"], cr["control_name"],
                    cr.get("family", ""), cr.get("maturity_score", 0),
                )
                ev.error = str(res)
                ev.compute_composite()
                evals.append(ev)
            else:
                evals.append(res)
            done_count += 1
            print(f"      [{done_count}/{total_controls}] {cr['control_id']}", end="\r")

        fw_evals[fw_id] = evals
        print()

    # Write report
    print(f"[3/3] Writing report -> {output_path}")
    report = _format_report(pdf_path, json_path, assessment, fw_evals, eval_fw_ids)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report, encoding="utf-8")

    # Summary
    all_valid = [e for evs in fw_evals.values() for e in evs if e.error is None]
    overall = round(sum(e.composite for e in all_valid) / len(all_valid), 3) if all_valid else 0.0
    print(f"\nDone. Overall RAG quality: {overall:.3f} ({_quality_label(overall)})")
    print(f"Report: {output_path}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="RAGAS-inspired RAG quality evaluator for GRC-LLM assessment outputs.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("pdf",  nargs="?", help="Path to the original PDF policy document")
    parser.add_argument("json", nargs="?", help="Path to the assessment JSON file")
    parser.add_argument(
        "--frameworks", default="",
        help="Comma-separated framework IDs to evaluate (default: all in JSON)",
    )
    parser.add_argument(
        "--output", default="",
        help="Output .txt path (default: <json_stem>_rag_eval.txt next to JSON)",
    )
    parser.add_argument(
        "--concurrency", type=int, default=5,
        help="Max parallel LLM calls (default: 5)",
    )
    parser.add_argument(
        "--list-frameworks", action="store_true",
        help="Print available framework IDs and exit",
    )
    args = parser.parse_args()

    if args.list_frameworks:
        from app.frameworks import FRAMEWORK_REGISTRY
        print("Available framework IDs:")
        for fid, fw in FRAMEWORK_REGISTRY.items():
            print(f"  {fid:<25}  {fw.name}")
        return

    if not args.pdf or not args.json:
        parser.error("Both pdf and json arguments are required.")

    pdf_path  = Path(args.pdf)
    json_path = Path(getattr(args, "json"))

    if not pdf_path.exists():
        sys.exit(f"Error: PDF not found: {pdf_path}")
    if not json_path.exists():
        sys.exit(f"Error: JSON not found: {json_path}")

    # Determine frameworks to evaluate
    if args.frameworks.strip():
        fw_ids = [f.strip() for f in args.frameworks.split(",") if f.strip()]
    else:
        # Default: all frameworks in the JSON
        with open(json_path, encoding="utf-8") as f:
            tmp = json.load(f)
        fw_ids = [fr["framework_id"] for fr in tmp.get("framework_results", [])]
        if not fw_ids:
            sys.exit("Error: JSON contains no framework_results.")
        print(f"No --frameworks specified; evaluating all {len(fw_ids)} in JSON: "
              f"{fw_ids}")

    # Output path
    if args.output.strip():
        output_path = Path(args.output)
    else:
        output_path = json_path.parent / f"{json_path.stem}_rag_eval.txt"

    logging.basicConfig(
        level=logging.WARNING,
        format="%(levelname)s  %(name)s  %(message)s",
    )

    asyncio.run(_run_eval(pdf_path, json_path, fw_ids, output_path, args.concurrency))


if __name__ == "__main__":
    main()
