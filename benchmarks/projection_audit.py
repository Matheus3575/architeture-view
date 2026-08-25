"""Compact explainability audit for the high-level projection."""

from __future__ import annotations

import argparse
import json
import tempfile
from collections.abc import Iterable
from pathlib import Path

from architecture_recovery.pipeline import analyze_repository
from architecture_recovery.visualization import ArchitecturalProjectionBuilder, audit_projection

from .refinement_investigation import DEFAULT_SCENARIOS, generate_context_fixture


def _scenario_paths(include_generated: bool = True) -> Iterable[tuple[str, Path]]:
    yield from DEFAULT_SCENARIOS
    if include_generated:
        with tempfile.TemporaryDirectory(prefix="architecture-recovery-projection-audit-") as value:
            yield "neutral_context_generated", generate_context_fixture(Path(value) / "neutral-context")


def audit_scenarios() -> list[dict]:
    results = []
    for name, repository in _scenario_paths():
        ir = analyze_repository(repository)
        projection = ArchitecturalProjectionBuilder().build(ir)
        audit = audit_projection(ir, projection)
        results.append({
            "name": name,
            "repository": str(repository),
            "projection": {
                "projected_node_count": projection.high_level_node_count,
                "projected_edge_count": len(projection.projected_edges),
                "context_root_ids": sorted(projection.context_root_ids),
            },
            "audit": audit.model_dump(mode="json"),
        })
    return results


def _print_report(results: list[dict]) -> None:
    print("Projection Explainability Audit")
    print("scenario                         nodes roots no-context edges DEPENDS_ON only/shadowed/agg same/cross")
    for result in results:
        audit = result["audit"]
        print(
            f"{result['name']:<32} "
            f"{audit['projected_node_count']:>5} "
            f"{audit['context_root_count']:>5} "
            f"{audit['projected_without_context_count']:>10} "
            f"{audit['projected_edge_count']:>5} "
            f"{audit['depends_on_only_relation_count']:>4}/"
            f"{audit['depends_on_shadowed_count']:<8}/"
            f"{audit['depends_on_aggregated_structural_count']:<3} "
            f"{audit['depends_on_same_context_count']:>4}/"
            f"{audit['depends_on_cross_context_count']:<5}"
        )
    for result in results:
        audit = result["audit"]
        print(f"\n[{result['name']}] projected nodes")
        for item in audit["node_explanations"]:
            if not item["projection_eligible"]:
                continue
            roots = ",".join(item["context_root_ids"]) or "none"
            flags = []
            if item["locally_significant"]:
                flags.append("local-only")
            if item["globally_contextualized"]:
                flags.append("contextualized")
            print(
                f"  {item['subject_id']} {item['significance'].upper()} "
                f"score={item['score']:.3f} roots={roots} "
                f"framework_facts={item['local_framework_fact_count']} "
                f"flags={','.join(flags) or 'none'}"
            )
            for reason in item["strong_reasons"][:3]:
                print(f"    reason: {reason}")
        print(f"  traceability={audit['traceability']} evidence_coverage={audit['evidence_coverage']}")
        print("  projected relations")
        for item in audit["relation_explanations"]:
            category = f" category={item['depends_on_category']}" if item["depends_on_category"] else ""
            stronger = f" stronger={','.join(item['stronger_relation_kinds'])}" if item["stronger_relation_kinds"] else ""
            print(
                f"    {item['source']} --{item['kind']}--> {item['target']} "
                f"scope={item['context_scope']} evidence={item['evidence_count']} "
                f"support={item['support_count']}{category}{stronger}"
            )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Emit complete structured audit JSON")
    args = parser.parse_args()
    results = audit_scenarios()
    if args.json:
        print(json.dumps({"schema_version": "0.1", "scenarios": results}, indent=2, sort_keys=True))
    else:
        _print_report(results)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
