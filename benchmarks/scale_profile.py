"""Synthetic scale benchmark for the opt-in macro pipeline profile."""

from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path
from typing import Iterable

from architecture_recovery.pipeline import analyze_repository
from architecture_recovery.visualization import VisualizationReadModelBuilder
from architecture_recovery.profiling import AnalysisProfile


DEFAULT_SCALES = (50, 200, 400)


def generate_scale_repository(root: Path, module_count: int) -> Path:
    """Create a small deterministic Python repository with linear growth."""
    package = root / "app"
    package.mkdir(parents=True, exist_ok=True)
    (package / "__init__.py").write_text("", encoding="utf-8")
    for index in range(module_count):
        previous = f"app.module_{index - 1}" if index else "math"
        (package / f"module_{index}.py").write_text(
            f"import {previous}\n\n"
            f"alias_{index} = {previous}\n\n"
            f"def function_{index}(value):\n"
            f"    return value + {index}\n\n"
            f"class Class{index}:\n"
            f"    def method(self, value):\n"
            f"        return function_{index}(value)\n",
            encoding="utf-8",
        )
    return root


def run_scale_profiles(scales: Iterable[int] = DEFAULT_SCALES) -> list[dict[str, object]]:
    results: list[dict[str, object]] = []
    for module_count in scales:
        with tempfile.TemporaryDirectory(prefix="architecture-recovery-scale-") as value:
            profile = AnalysisProfile()
            repository = generate_scale_repository(Path(value), module_count)
            ir = analyze_repository(repository, profile=profile)
            read_model = VisualizationReadModelBuilder().build(ir, profile=profile)
            results.append(
                {
                    "modules": module_count,
                    "files": profile.stages["scanner"].counts["files"],
                    "file_count": profile.stages["scanner"].counts["file_count"],
                    "symbols": profile.stages["symbol_resolution"].counts["symbols"],
                    "symbol_count": profile.stages["symbol_resolution"].counts["symbol_count"],
                    "raw_nodes": len(ir.raw_graph.nodes),
                    "raw_edges": len(ir.raw_graph.edges),
                    "evidence": len(ir.evidence),
                    "architectural_nodes": profile.stages["architecture_ir"].counts["architectural_nodes"],
                    "architectural_edges": profile.stages["architecture_ir"].counts["architectural_edges"],
                    "components": profile.stages["component_detection"].counts["components"],
                    "projected_nodes": profile.stages["visualization_read_model"].counts["projected_nodes"],
                    "projected_edges": profile.stages["visualization_read_model"].counts["projected_edges"],
                    "evidence_groups": profile.stages["visualization_read_model"].counts["evidence_groups"],
                    "total_seconds": profile.total_seconds,
                    "stages": profile.as_dict()["stages"],
                }
            )
    for previous, current in zip(results, results[1:]):
        current["growth"] = {
            "input_ratio": current["modules"] / previous["modules"],
            "runtime_ratio": current["total_seconds"] / previous["total_seconds"],
        }
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    args = parser.parse_args()
    results = run_scale_profiles()
    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print("modules files raw_nodes raw_edges evidence total_seconds")
        for result in results:
            print(
                f"{result['modules']:7} {result['files']:5} {result['raw_nodes']:9} "
                f"{result['raw_edges']:9} {result['evidence']:8} {result['total_seconds']:13.3f}"
            )
        for result in results:
            print(f"\nScale {result['modules']}")
            for name, stage in result["stages"].items():
                print(f"  {name:<28} {stage['seconds']:.3f} s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
