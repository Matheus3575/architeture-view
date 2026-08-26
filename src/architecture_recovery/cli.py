from __future__ import annotations

import argparse
import json
from pathlib import Path

from .graph import GraphAggregationConfig
from .ir.schema import json_schema
from .pipeline import analyze_repository
from .profiling import AnalysisProfile, profile_stage
from .rendering import render_graphml, render_mermaid, render_svg
from .visualization import (
    ArchitecturalProjectionBuilder,
    VisualizationReadModelBuilder,
    audit_projection,
    build_projection_audit_report,
    write_projection_audit_reports,
)
from .web import serve_visualization


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="architecture-recovery")
    subparsers = parser.add_subparsers(dest="command", required=True)

    analyze = subparsers.add_parser(
        "analyze",
        help="Analyze a local or remote repository",
    )
    analyze.add_argument("repository")
    analyze.add_argument("--ref", "--branch", dest="ref", default=None)
    analyze.add_argument("--output", default="architecture.json")
    analyze.add_argument("--graph", default=None)
    analyze.add_argument("--classification-report", default=None)
    analyze.add_argument("--include-standard-library", action="store_true")
    analyze.add_argument("--exclude-unknown", action="store_true")
    analyze.add_argument("--exclude-generated", action="store_true")
    analyze.add_argument(
        "--format",
        choices=("json", "graphml", "mermaid"),
        default="json",
    )
    analyze.add_argument("--strict", action="store_true")
    analyze.add_argument("--profile", action="store_true", help="Print macro stage timings and cardinalities")

    visualize = subparsers.add_parser(
        "visualize",
        help="Generate visualization SVG files from a repository",
    )
    _add_visualization_arguments(visualize)

    audit = subparsers.add_parser(
        "audit",
        help="Generate a persisted high-level projection audit",
    )
    audit.add_argument("repository")
    audit.add_argument(
        "--output-dir",
        default=".",
        help="Directory for architecture-audit.md/json (default: current directory)",
    )
    audit.add_argument(
        "--format",
        choices=("both", "markdown", "json", "md"),
        default="both",
        help="Report format (default: both)",
    )
    audit.add_argument("--force", action="store_true", help="Overwrite existing reports")
    audit.add_argument("--profile", action="store_true", help="Include macro profile in reports")

    serve = subparsers.add_parser(
        "serve",
        help="Analyze a repository, generate SVG files and serve them locally",
    )
    _add_visualization_arguments(serve)

    schema = subparsers.add_parser(
        "schema",
        help="Print the Architecture IR JSON Schema",
    )
    schema.add_argument("--output", default=None)
    return parser


def _add_visualization_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("repository")
    parser.add_argument(
        "--output",
        default="architecture.svg",
        help="Static SVG output path",
    )
    parser.add_argument(
        "--animated",
        action="store_true",
        help="Also generate an animated SVG",
    )
    parser.add_argument(
        "--serve",
        action="store_true",
        help="Start the local web consumer after generating SVG files",
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=8000, type=int)
    parser.add_argument("--profile", action="store_true", help="Print macro stage timings and cardinalities")


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.command == "schema":
        text = json.dumps(json_schema(), indent=2, ensure_ascii=False) + "\n"
        if args.output:
            Path(args.output).write_text(text, encoding="utf-8")
        else:
            print(text, end="")
        return 0

    if args.command == "audit":
        _run_audit(
            args.repository,
            output_dir=args.output_dir,
            output_format=args.format,
            force=args.force,
            profile=AnalysisProfile() if args.profile else None,
        )
        return 0

    if args.command in {"visualize", "serve"}:
        _run_visualization(
            args.repository,
            output=args.output,
            animated=args.animated,
            serve=args.command == "serve" or args.serve,
            host=args.host,
            port=args.port,
            profile=AnalysisProfile() if args.profile else None,
        )
        return 0

    profile = AnalysisProfile() if args.profile else None
    analysis_kwargs = {"ref": args.ref}
    if profile:
        analysis_kwargs["profile"] = profile
    if args.include_standard_library or args.exclude_unknown or args.exclude_generated:
        analysis_kwargs["aggregation_config"] = GraphAggregationConfig(
            include_standard_library=args.include_standard_library,
            include_unknown=not args.exclude_unknown,
            include_generated=not args.exclude_generated,
        )
    ir = analyze_repository(args.repository, **analysis_kwargs)
    write_outputs(
        ir,
        args.output,
        args.graph,
        args.format,
        args.classification_report,
    )
    if profile:
        print(profile.render_text())
    return 1 if args.strict and not ir.validation.valid else 0


def _run_visualization(
    repository: str,
    *,
    output: str | Path,
    animated: bool,
    serve: bool,
    host: str,
    port: int,
    profile: AnalysisProfile | None = None,
) -> None:
    ir = analyze_repository(repository, **({"profile": profile} if profile else {}))
    read_model = VisualizationReadModelBuilder().build(ir, profile=profile)

    static_path = Path(output)
    with profile_stage(profile, "svg_rendering") as timer:
        static_svg = render_svg(read_model, mode="static")
        if timer:
            timer.set_counts(bytes=len(static_svg.encode("utf-8")), mode="static")
    static_path.write_text(static_svg, encoding="utf-8")
    print(f"Static SVG: {static_path}")

    animated_path: Path | None = None
    if animated:
        animated_path = _animated_path(static_path)
        with profile_stage(profile, "svg_rendering_animated") as timer:
            animated_svg = render_svg(read_model, mode="animated")
            if timer:
                timer.set_counts(bytes=len(animated_svg.encode("utf-8")), mode="animated")
        animated_path.write_text(animated_svg, encoding="utf-8")
        print(f"Animated SVG: {animated_path}")

    if profile:
        print(profile.render_text())

    if serve:
        serve_visualization(
            static_path,
            animated_path,
            host=host,
            port=port,
        )


def _run_audit(
    repository: str,
    *,
    output_dir: str | Path,
    output_format: str,
    force: bool,
    profile: AnalysisProfile | None = None,
) -> list[Path]:
    """Analyze once, audit once, and derive all selected reports from one payload."""
    ir = analyze_repository(repository, **({"profile": profile} if profile else {}))
    with profile_stage(profile, "architectural_significance_projection") as timer:
        projection = ArchitecturalProjectionBuilder().build(ir)
        if timer:
            timer.set_counts(
                detailed_nodes=projection.detailed_node_count,
                projected_nodes=projection.high_level_node_count,
                projected_edges=len(projection.projected_edges),
            )
    with profile_stage(profile, "projection_audit") as timer:
        audit = audit_projection(ir, projection)
        if timer:
            timer.set_counts(
                projected_nodes=audit.projected_node_count,
                projected_edges=audit.projected_edge_count,
                evidence_coverage=audit.evidence_coverage,
            )
    report = build_projection_audit_report(ir, projection, audit, profile=profile)
    if profile:
        profile.record(
            "projection_audit_report",
            0.0,
            {
                "evidence_groups": report["summary"]["evidence_groups"],
                "projected_nodes": report["summary"]["projected_nodes"],
                "projected_edges": report["summary"]["projected_edges"],
                "components": report["summary"]["components"],
                "architectural_components": report["summary"]["architectural_components"],
                "component_candidates": report["summary"]["component_candidates"],
            },
        )
        report["profile"] = profile.as_dict()
    paths = write_projection_audit_reports(report, output_dir, output_format, force)
    summary = report["summary"]
    print("Projection Audit complete.")
    print(f"Repository: {summary['repository']['path']}")
    print(f"Projected nodes: {summary['projected_nodes']}")
    print(f"Projected edges: {summary['projected_edges']}")
    print(f"Context roots: {summary['context_roots']}")
    print(f"Without context: {audit.projected_without_context_count}")
    print(f"Local framework promotions: {audit.local_only_framework_promotion_count}")
    print(f"DEPENDS_ON: {audit.depends_on_total}")
    print("Reports:")
    for path in paths:
        print(f"  {path}")
    if profile:
        print(profile.render_text())
    return paths


def _animated_path(static_path: Path) -> Path:
    if static_path.suffix:
        return static_path.with_name(
            f"{static_path.stem}-animated{static_path.suffix}"
        )
    return static_path.with_name(f"{static_path.name}-animated.svg")


def write_outputs(
    ir,
    output: str,
    graph: str | None = None,
    output_format: str = "json",
    classification_report: str | None = None,
) -> None:
    """Write primary, graph, and optional classification outputs."""
    if output_format == "json":
        Path(output).write_text(
            json.dumps(ir.model_dump(mode="json"), indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
    elif output_format == "graphml":
        Path(output).write_bytes(render_graphml(ir))
    else:
        Path(output).write_text(render_mermaid(ir), encoding="utf-8")

    if graph:
        suffix = Path(graph).suffix.lower()
        if suffix == ".mmd":
            Path(graph).write_text(render_mermaid(ir), encoding="utf-8")
        else:
            Path(graph).write_bytes(render_graphml(ir))
    if classification_report:
        Path(classification_report).write_text(
            json.dumps(
                ir.classifications.model_dump(mode="json"),
                indent=2,
                ensure_ascii=False,
            )
            + "\n",
            encoding="utf-8",
        )
