"""
rag_quality_report.py

Recursively scans a folder (including subfolders) for:
  - "*_rag_eval.txt"  RAGAS-style judge reports produced by rag_eval.py / batch_rag_eval.py
  - "*.json"          GRC assessment result files produced by report_builder.py / batch_assess.py
                       (any other JSON files are silently skipped)

It aggregates the current RAG quality across every file found, renders a set
of summary charts (PNG), and asks a Claude Sonnet model for a narrative
expert analysis of the aggregate findings. Everything is written to a
timestamped output directory as a single Markdown report plus the chart
images it references.

This is read-only / analysis tooling: it does not call the assessment
pipeline and does not modify any of the scanned files.

Usage:
    python rag_quality_report.py <folder> [--output-dir DIR] [--no-llm] [--model MODEL_ID]

Example:
    python rag_quality_report.py data/rag_eval_results
    python rag_quality_report.py data/rag_eval_results --no-llm
"""
from __future__ import annotations

import argparse
import asyncio
import json
import re
import statistics
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from app.config import settings  # loads .env

DIMENSIONS = [
    "Faithfulness",
    "Evidence Relevance",
    "Score Consistency",
    "Gap Completeness",
    "Recommendation Quality",
    "Evidence Groundedness",
]

# Real, currently-available model ID (the codebase's own judge model in
# rag_eval.py uses the same one). Override with --model if needed.
_DEFAULT_MODEL = "claude-sonnet-4-6"


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class EvalReport:
    path: Path
    pdf_document: str = ""
    assessment_json: str = ""
    frameworks: str = ""
    evaluation_date: str = ""
    overall_score: float | None = None
    overall_label: str = ""
    controls_evaluated: int = 0
    dimension_scores: dict[str, float] = field(default_factory=dict)
    control_dimension_scores: dict[str, list[float]] = field(default_factory=lambda: defaultdict(list))
    # control_reasons[dimension] -> list of (control_id, score, reason_text)
    control_reasons: dict[str, list[tuple[str, float, str]]] = field(default_factory=lambda: defaultdict(list))


@dataclass
class AssessmentJson:
    path: Path
    document_name: str = ""
    frameworks_assessed: list[str] = field(default_factory=list)
    overall_posture_score: float | None = None
    maturity_scores: list[float] = field(default_factory=list)
    framework_overall_scores: dict[str, float] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Parsing: *_rag_eval.txt
# ---------------------------------------------------------------------------

_HEADER_PAT = re.compile(r"^(PDF Document|Assessment JSON|Evaluator Model|Evaluation Date|Frameworks)\s*:\s*(.*)$")
_OVERALL_PAT = re.compile(r"^OVERALL RAG QUALITY SCORE:\s+([\d.]+)\s*/\s*1\.000\s+\(([^)]+)\)")
_CONTROLS_PAT = re.compile(r"^Controls evaluated:\s*(\d+)")
_DIM_ALT = "|".join(re.escape(d) for d in DIMENSIONS)
# File/framework-level summary row, e.g.:
#   Faithfulness            0.839  [#################...]  Good
_SUMMARY_ROW_PAT = re.compile(r"^\s{2}(" + _DIM_ALT + r")\s+([\d.]+)\s+\[[#. ]*\]")
# Per-control detail row (4-space indent, no bar chart), e.g.:
#     Evidence Relevance        0.250  The cited excerpts are largely tangential...
_CONTROL_DIM_PAT = re.compile(r"^\s{4}(" + _DIM_ALT + r")\s+([\d.]+)\s+(.*)$")
# Per-control header row, e.g.:
#   ID.AM-1  |  Asset Management: Physical Device Inventory  |  Maturity: 2 (Developing)  |  Quality: 0.657 (Needs Improvement)
_CONTROL_HEADER_PAT = re.compile(
    r"^\s{2}(\S.*?)\s+\|\s+.+?\s+\|\s+Maturity:\s*[\d.]+\s*\([^)]*\)\s+\|\s+Quality:\s*[\d.]+\s*\([^)]*\)\s*$"
)


def parse_eval_report(path: Path) -> EvalReport | None:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        print(f"  [WARN] could not read {path}: {e}", file=sys.stderr)
        return None

    report = EvalReport(path=path)
    seen_summary_dims: set[str] = set()
    current_control_id = "?"

    for line in text.splitlines():
        m = _HEADER_PAT.match(line)
        if m:
            key, val = m.group(1), m.group(2).strip()
            if key == "PDF Document":
                report.pdf_document = val
            elif key == "Assessment JSON":
                report.assessment_json = val
            elif key == "Evaluation Date":
                report.evaluation_date = val
            elif key == "Frameworks":
                report.frameworks = val
            continue

        m = _OVERALL_PAT.match(line)
        if m:
            report.overall_score = float(m.group(1))
            report.overall_label = m.group(2)
            continue

        m = _CONTROLS_PAT.match(line)
        if m:
            report.controls_evaluated = int(m.group(1))
            continue

        m = _CONTROL_HEADER_PAT.match(line)
        if m:
            current_control_id = m.group(1).strip()
            continue

        m = _SUMMARY_ROW_PAT.match(line)
        if m:
            dim = m.group(1)
            if dim not in seen_summary_dims:
                report.dimension_scores[dim] = float(m.group(2))
                seen_summary_dims.add(dim)
            continue

        m = _CONTROL_DIM_PAT.match(line)
        if m:
            dim, score, reason = m.group(1), float(m.group(2)), m.group(3).strip()
            report.control_dimension_scores[dim].append(score)
            report.control_reasons[dim].append((current_control_id, score, reason))
            continue

    if report.overall_score is None:
        print(f"  [WARN] {path}: no overall score found, skipping", file=sys.stderr)
        return None
    return report


# ---------------------------------------------------------------------------
# Parsing: GRC assessment JSON files
# ---------------------------------------------------------------------------

def parse_assessment_json(path: Path) -> AssessmentJson | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return None
    if not isinstance(data, dict) or "framework_results" not in data:
        return None  # not a GRC assessment file — skip silently

    aj = AssessmentJson(path=path)
    aj.document_name = data.get("document_name", "")
    aj.frameworks_assessed = data.get("frameworks_assessed", []) or []
    aj.overall_posture_score = data.get("overall_posture_score")

    for fw in data.get("framework_results", []) or []:
        fw_id = fw.get("framework_id", "?")
        if fw.get("overall_score") is not None:
            aj.framework_overall_scores[fw_id] = fw.get("overall_score")
        for cr in fw.get("control_results", []) or []:
            ms = cr.get("maturity_score")
            if isinstance(ms, (int, float)):
                aj.maturity_scores.append(float(ms))
    return aj


# ---------------------------------------------------------------------------
# Scan
# ---------------------------------------------------------------------------

def scan_folder(root: Path) -> tuple[list[EvalReport], list[AssessmentJson]]:
    eval_reports: list[EvalReport] = []
    assessment_jsons: list[AssessmentJson] = []

    for p in sorted(root.rglob("*_rag_eval.txt")):
        r = parse_eval_report(p)
        if r:
            eval_reports.append(r)

    for p in sorted(root.rglob("*.json")):
        aj = parse_assessment_json(p)
        if aj:
            assessment_jsons.append(aj)

    return eval_reports, assessment_jsons


# ---------------------------------------------------------------------------
# Aggregation
# ---------------------------------------------------------------------------

def aggregate_dimension_stats(reports: list[EvalReport]) -> dict:
    per_control: dict[str, list[float]] = defaultdict(list)
    per_file_summary: dict[str, list[float]] = defaultdict(list)
    for r in reports:
        for dim, scores in r.control_dimension_scores.items():
            per_control[dim].extend(scores)
        for dim, score in r.dimension_scores.items():
            per_file_summary[dim].append(score)

    stats = {}
    for dim in DIMENSIONS:
        vals = per_control.get(dim, [])
        if not vals:
            continue
        stats[dim] = {
            "n": len(vals),
            "mean": statistics.mean(vals),
            "median": statistics.median(vals),
            "stdev": statistics.pstdev(vals) if len(vals) > 1 else 0.0,
            "pct_below_0.5": sum(1 for v in vals if v < 0.5) / len(vals),
            "pct_below_0.7": sum(1 for v in vals if v < 0.7) / len(vals),
            "file_level_mean": (
                statistics.mean(per_file_summary[dim]) if per_file_summary.get(dim) else None
            ),
        }
    return stats


def weakest_dimension(dim_stats: dict) -> str | None:
    """Return the dimension with the lowest mean score (usually Evidence Relevance)."""
    if not dim_stats:
        return None
    return min(dim_stats, key=lambda d: dim_stats[d]["mean"])


# Number of worst-scoring example controls to show for the single weakest
# dimension vs. the other five (kept short so the report/LLM prompt stays
# readable while still giving deep context on the biggest problem area).
_WEAKEST_DIM_EXAMPLES = 12
_OTHER_DIM_EXAMPLES = 3


def worst_controls(reports: list[EvalReport], dim: str, n: int = 3):
    entries = []
    for r in reports:
        for cid, score, reason in r.control_reasons.get(dim, []):
            entries.append((score, r.path.name, cid, reason))
    entries.sort(key=lambda x: x[0])
    return entries[:n]


# ---------------------------------------------------------------------------
# Charts
# ---------------------------------------------------------------------------

def make_charts(reports: list[EvalReport], assessment_jsons: list[AssessmentJson], out_dir: Path) -> list[str]:
    out_dir.mkdir(parents=True, exist_ok=True)
    chart_files: list[str] = []
    dim_stats = aggregate_dimension_stats(reports)

    # 1. Overall RAG quality score per report file
    if reports:
        pairs = sorted(
            ((r.path.name.replace("_rag_eval.txt", ""), r.overall_score) for r in reports),
            key=lambda x: x[1],
        )
        names = [p[0] for p in pairs]
        scores = [p[1] for p in pairs]
        colors = ["#d9534f" if s < 0.7 else "#f0ad4e" if s < 0.8 else "#5cb85c" for s in scores]

        fig, ax = plt.subplots(figsize=(max(6, len(names) * 0.45), 5.5))
        ax.bar(range(len(names)), scores, color=colors)
        ax.set_xticks(range(len(names)))
        ax.set_xticklabels(names, rotation=80, ha="right", fontsize=6.5)
        ax.set_ylim(0, 1)
        ax.set_ylabel("Overall RAG quality score")
        ax.set_title(f"Overall RAG Quality Score per Report (n={len(names)})")
        ax.axhline(0.7, color="gray", linestyle="--", linewidth=0.8)
        ax.axhline(0.8, color="gray", linestyle="--", linewidth=0.8)
        fig.tight_layout()
        fname = "overall_scores.png"
        fig.savefig(out_dir / fname, dpi=150)
        plt.close(fig)
        chart_files.append(fname)

    # 2. Six-dimension averages bar chart
    if dim_stats:
        dims = [d for d in DIMENSIONS if d in dim_stats]
        means = [dim_stats[d]["mean"] for d in dims]
        colors = ["#d9534f" if m < 0.7 else "#f0ad4e" if m < 0.85 else "#5cb85c" for m in means]

        fig, ax = plt.subplots(figsize=(9, 5))
        ax.bar(dims, means, color=colors)
        ax.set_ylim(0, 1)
        ax.set_ylabel("Mean score across all judged controls")
        ax.set_title("RAG Quality — Six Dimension Averages")
        for i, m in enumerate(means):
            ax.text(i, m + 0.02, f"{m:.3f}", ha="center", fontsize=9)
        plt.setp(ax.get_xticklabels(), rotation=20, ha="right")
        fig.tight_layout()
        fname = "dimension_means.png"
        fig.savefig(out_dir / fname, dpi=150)
        plt.close(fig)
        chart_files.append(fname)

    # 3. Radar / spider chart of the six dimensions
    if dim_stats:
        import math
        dims = [d for d in DIMENSIONS if d in dim_stats]
        means = [dim_stats[d]["mean"] for d in dims]
        angles = [n / float(len(dims)) * 2 * math.pi for n in range(len(dims))]
        angles += angles[:1]
        means_closed = means + means[:1]

        fig = plt.figure(figsize=(6.5, 6.5))
        ax = fig.add_subplot(111, polar=True)
        ax.plot(angles, means_closed, linewidth=2, color="#337ab7")
        ax.fill(angles, means_closed, color="#337ab7", alpha=0.25)
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(dims, fontsize=8)
        ax.set_ylim(0, 1)
        ax.set_title("RAG Quality Profile (Radar)")
        fig.tight_layout()
        fname = "radar_profile.png"
        fig.savefig(out_dir / fname, dpi=150)
        plt.close(fig)
        chart_files.append(fname)

    # 4. Histograms of the two weakest/most-scrutinized dimensions
    er_vals = [s for r in reports for s in r.control_dimension_scores.get("Evidence Relevance", [])]
    sc_vals = [s for r in reports for s in r.control_dimension_scores.get("Score Consistency", [])]
    if er_vals or sc_vals:
        fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
        if er_vals:
            axes[0].hist(er_vals, bins=20, range=(0, 1), color="#d9534f", edgecolor="white")
            axes[0].set_title(f"Evidence Relevance distribution (n={len(er_vals)})")
            axes[0].set_xlabel("score")
            axes[0].set_ylabel("count")
        if sc_vals:
            axes[1].hist(sc_vals, bins=20, range=(0, 1), color="#f0ad4e", edgecolor="white")
            axes[1].set_title(f"Score Consistency distribution (n={len(sc_vals)})")
            axes[1].set_xlabel("score")
        fig.tight_layout()
        fname = "histograms_weak_dims.png"
        fig.savefig(out_dir / fname, dpi=150)
        plt.close(fig)
        chart_files.append(fname)

    # 5. Maturity score distribution from the GRC assessment JSONs
    maturities = [m for aj in assessment_jsons for m in aj.maturity_scores]
    if maturities:
        buckets = list(range(6))
        counts = [sum(1 for m in maturities if round(m) == b) for b in buckets]

        fig, ax = plt.subplots(figsize=(6, 4.5))
        ax.bar(buckets, counts, color="#5bc0de")
        ax.set_xticks(buckets)
        ax.set_xlabel("Maturity score (0-5)")
        ax.set_ylabel("Number of controls")
        ax.set_title(f"Maturity Score Distribution (n={len(maturities)} controls)")
        top = max(counts) if counts else 1
        for i, c in enumerate(counts):
            ax.text(i, c + top * 0.01, str(c), ha="center", fontsize=9)
        fig.tight_layout()
        fname = "maturity_distribution.png"
        fig.savefig(out_dir / fname, dpi=150)
        plt.close(fig)
        chart_files.append(fname)

    return chart_files


# ---------------------------------------------------------------------------
# LLM narrative analysis
# ---------------------------------------------------------------------------

def _build_stats_blob(
    reports: list[EvalReport],
    assessment_jsons: list[AssessmentJson],
    dim_stats: dict,
) -> str:
    lines: list[str] = []
    lines.append(f"RAGAS eval reports analyzed: {len(reports)}")
    lines.append(f"GRC assessment JSON files analyzed: {len(assessment_jsons)}")
    total_controls = sum(r.controls_evaluated for r in reports)
    lines.append(f"Total controls judged (RAGAS): {total_controls}")

    if reports:
        overall = [r.overall_score for r in reports]
        lines.append(
            f"Overall RAG quality score across reports: mean={statistics.mean(overall):.3f}, "
            f"median={statistics.median(overall):.3f}, min={min(overall):.3f}, max={max(overall):.3f}"
        )

    lines.append("")
    lines.append("Six-dimension aggregate stats (across all judged controls, 0-1 scale, higher=better):")
    for dim in DIMENSIONS:
        s = dim_stats.get(dim)
        if not s:
            continue
        lines.append(
            f"  - {dim}: mean={s['mean']:.3f} median={s['median']:.3f} stdev={s['stdev']:.3f} "
            f"pct<0.5={s['pct_below_0.5']*100:.1f}% pct<0.7={s['pct_below_0.7']*100:.1f}% (n={s['n']})"
        )

    weakest = weakest_dimension(dim_stats)
    lines.append("")
    lines.append("Worst-scoring example controls per dimension (concrete context):")
    for dim in DIMENSIONS:
        n = _WEAKEST_DIM_EXAMPLES if dim == weakest else _OTHER_DIM_EXAMPLES
        entries = worst_controls(reports, dim, n=n)
        if not entries:
            continue
        lines.append(f"  {dim}{' [WEAKEST DIMENSION]' if dim == weakest else ''}:")
        for score, fname, cid, reason in entries:
            lines.append(f"    - [{score:.2f}] {fname} / {cid}: {reason[:220]}")

    maturities = [m for aj in assessment_jsons for m in aj.maturity_scores]
    if maturities:
        lines.append("")
        dist = ", ".join(f"{i}:{sum(1 for m in maturities if round(m) == i)}" for i in range(6))
        lines.append(
            f"Maturity score distribution (0-5 scale, {len(maturities)} controls): "
            f"mean={statistics.mean(maturities):.2f}, counts=[{dist}]"
        )

    return "\n".join(lines)


async def get_llm_analysis(
    reports: list[EvalReport],
    assessment_jsons: list[AssessmentJson],
    dim_stats: dict,
    model: str,
) -> str:
    api_key = settings.anthropic_api_key
    if not api_key:
        return "_(skipped: ANTHROPIC_API_KEY is not set in .env)_"

    import anthropic
    client = anthropic.AsyncAnthropic(api_key=api_key)

    stats_blob = _build_stats_blob(reports, assessment_jsons, dim_stats)

    system = (
        "You are a senior RAG/GRC quality auditor. You are given aggregate RAGAS-style quality "
        "statistics for a retrieval-augmented-generation compliance assessment system, across "
        "many documents and frameworks. The six dimensions (0-1 scale, higher is better) are: "
        "Faithfulness, Evidence Relevance, Score Consistency, Gap Completeness, "
        "Recommendation Quality, and Evidence Groundedness. You are also given example "
        "worst-scoring controls and the maturity-score (0-5) distribution the system produced. "
        "Write a concise expert analysis (roughly 300-500 words) covering: "
        "(1) overall RAG quality verdict; "
        "(2) the strongest and weakest dimensions, and what that implies about where the "
        "system's failures concentrate (retrieval quality vs. generation/prompting vs. "
        "hallucination); "
        "(3) whether the maturity-score distribution looks well-calibrated relative to the "
        "evidence quality (watch for score inflation); "
        "(4) concrete, prioritized recommendations. "
        "Be specific and quantitative, referencing the numbers given. Respond in English."
    )

    msg = await client.messages.create(
        model=model,
        max_tokens=3000,
        system=system,
        messages=[{"role": "user", "content": stats_blob}],
    )
    # Some models return extended-thinking blocks before the actual text
    # block, so content[0] is not reliably the answer — scan for the first
    # real text block instead.
    for block in msg.content:
        if getattr(block, "type", None) == "text":
            return block.text
    return "_(no text block found in model response — check the model's output format)_"


# ---------------------------------------------------------------------------
# Markdown report
# ---------------------------------------------------------------------------

def write_markdown_report(
    out_dir: Path,
    root: Path,
    reports: list[EvalReport],
    assessment_jsons: list[AssessmentJson],
    dim_stats: dict,
    chart_files: list[str],
    llm_analysis: str | None,
) -> Path:
    lines: list[str] = []

    def ln(s: str = "") -> None:
        lines.append(s)

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    ln("# RAG Quality Report")
    ln()
    ln(f"- Generated: {now}")
    ln(f"- Source folder (scanned recursively): `{root}`")
    ln(f"- RAGAS eval reports found: **{len(reports)}**")
    ln(f"- GRC assessment JSON files found: **{len(assessment_jsons)}**")
    total_controls = sum(r.controls_evaluated for r in reports)
    ln(f"- Total controls judged (RAGAS): **{total_controls}**")
    frameworks = sorted({
        fw.strip() for r in reports if r.frameworks
        for fw in r.frameworks.split(",") if fw.strip()
    })
    if frameworks:
        ln(f"- Frameworks covered (eval reports): {', '.join(frameworks)}")
    ln()

    if reports:
        ln("## Overall RAG Quality Score per Report")
        ln()
        ln("| Report | Frameworks | Controls | Overall Score | Label |")
        ln("|---|---|---|---|---|")
        for r in sorted(reports, key=lambda x: x.overall_score):
            ln(
                f"| {r.path.name} | {r.frameworks} | {r.controls_evaluated} "
                f"| {r.overall_score:.3f} | {r.overall_label} |"
            )
        overall = [r.overall_score for r in reports]
        ln()
        ln(
            f"**Aggregate overall score**: mean={statistics.mean(overall):.3f}, "
            f"median={statistics.median(overall):.3f}, min={min(overall):.3f}, max={max(overall):.3f}"
        )
        ln()

    if dim_stats:
        ln("## Six-Dimension Aggregate Stats (per-control, across all reports)")
        ln()
        ln("| Dimension | Mean | Median | Stdev | %<0.5 | %<0.7 | N |")
        ln("|---|---|---|---|---|---|---|")
        for dim in DIMENSIONS:
            s = dim_stats.get(dim)
            if not s:
                continue
            ln(
                f"| {dim} | {s['mean']:.3f} | {s['median']:.3f} | {s['stdev']:.3f} "
                f"| {s['pct_below_0.5']*100:.1f}% | {s['pct_below_0.7']*100:.1f}% | {s['n']} |"
            )
        ln()

        ln("## Worst-Scoring Example Controls per Dimension")
        ln()
        weakest = weakest_dimension(dim_stats)
        for dim in DIMENSIONS:
            n = _WEAKEST_DIM_EXAMPLES if dim == weakest else _OTHER_DIM_EXAMPLES
            entries = worst_controls(reports, dim, n=n)
            if not entries:
                continue
            ln(f"**{dim}**{' — weakest dimension, showing more examples' if dim == weakest else ''}")
            for score, fname, cid, reason in entries:
                ln(f"- `[{score:.2f}]` {fname} / {cid}: {reason}")
            ln()

    if assessment_jsons:
        maturities = [m for aj in assessment_jsons for m in aj.maturity_scores]
        if maturities:
            ln("## Maturity Score Distribution (from GRC assessment JSONs)")
            ln()
            ln(f"Total controls: {len(maturities)}, mean maturity: {statistics.mean(maturities):.2f} / 5")
            ln()
            ln("| Maturity | Count | % |")
            ln("|---|---|---|")
            for i in range(6):
                c = sum(1 for m in maturities if round(m) == i)
                ln(f"| {i} | {c} | {c/len(maturities)*100:.1f}% |")
            ln()

    if chart_files:
        ln("## Charts")
        ln()
        for fname in chart_files:
            ln(f"![{fname}](./{fname})")
            ln()

    if llm_analysis is not None:
        ln("## LLM Expert Analysis")
        ln()
        ln(llm_analysis)
        ln()

    report_path = out_dir / "rag_quality_report.md"
    report_path.write_text("\n".join(lines), encoding="utf-8")
    return report_path


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def _run(args: argparse.Namespace) -> None:
    root = Path(args.folder).resolve()
    if not root.exists():
        sys.exit(f"Error: folder not found: {root}")

    print(f"Scanning {root} recursively for *_rag_eval.txt and *.json ...")
    reports, assessment_jsons = scan_folder(root)
    print(f"Found {len(reports)} eval reports, {len(assessment_jsons)} assessment JSON files.")

    if not reports and not assessment_jsons:
        sys.exit("No parseable *_rag_eval.txt or assessment JSON files found under this folder.")

    if args.output_dir:
        out_dir = Path(args.output_dir).resolve()
    else:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        out_dir = root / f"quality_report_{stamp}"
    out_dir.mkdir(parents=True, exist_ok=True)

    dim_stats = aggregate_dimension_stats(reports)

    print("Rendering charts ...")
    chart_files = make_charts(reports, assessment_jsons, out_dir)
    print(f"  wrote {len(chart_files)} chart(s) to {out_dir}")

    llm_analysis = None
    if not args.no_llm:
        print(f"Calling {args.model} for narrative analysis ...")
        llm_analysis = await get_llm_analysis(reports, assessment_jsons, dim_stats, args.model)

    report_path = write_markdown_report(
        out_dir, root, reports, assessment_jsons, dim_stats, chart_files, llm_analysis
    )
    print(f"\nReport written to: {report_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("folder", help="Folder to scan recursively for *_rag_eval.txt and *.json files")
    parser.add_argument("--output-dir", help="Where to write the report + charts (default: <folder>/quality_report_<timestamp>/)")
    parser.add_argument("--no-llm", action="store_true", help="Skip the Claude API call; charts + stats only")
    parser.add_argument("--model", default=_DEFAULT_MODEL, help=f"Claude model ID for the narrative analysis (default: {_DEFAULT_MODEL})")
    args = parser.parse_args()
    asyncio.run(_run(args))


if __name__ == "__main__":
    main()
