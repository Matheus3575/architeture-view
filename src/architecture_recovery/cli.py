from __future__ import annotations

import argparse
import json
from pathlib import Path

from .ir.schema import json_schema
from .pipeline import analyze_repository
from .rendering import render_graphml, render_mermaid


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="architecture-recovery")
    subparsers = parser.add_subparsers(dest="command", required=True)
    analyze = subparsers.add_parser("analyze", help="Analyze a local or remote repository")
    analyze.add_argument("repository")
    analyze.add_argument("--ref", "--branch", dest="ref", default=None)
    analyze.add_argument("--output", default="architecture.json")
    analyze.add_argument("--graph", default=None)
    analyze.add_argument("--format", choices=("json", "graphml", "mermaid"), default="json")
    analyze.add_argument("--strict", action="store_true")
    schema = subparsers.add_parser("schema", help="Print the Architecture IR JSON Schema")
    schema.add_argument("--output", default=None)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "schema":
        text = json.dumps(json_schema(), indent=2, ensure_ascii=False) + "\n"
        if args.output:
            Path(args.output).write_text(text, encoding="utf-8")
        else:
            print(text, end="")
        return 0

    ir = analyze_repository(args.repository, ref=args.ref)
    write_outputs(ir, args.output, args.graph, args.format)
    return 1 if args.strict and not ir.validation.valid else 0


def write_outputs(ir, output: str, graph: str | None = None, output_format: str = "json") -> None:
    """Write the requested primary output and optional graph output."""
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
