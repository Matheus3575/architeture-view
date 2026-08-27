"""Stable, compact serialization for projection audits.

This module is deliberately a reporting layer.  It consumes an existing
``ProjectionAudit`` and never recalculates significance, projection, or
relations.  Large evidence associations are represented by deterministic
EvidenceGroup references and summaries.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from architecture_recovery.ir import ArchitectureIR
from architecture_recovery.profiling import AnalysisProfile

from .evidence import EvidencePayloadIndex
from .projection import HighLevelArchitectureProjection
from .projection_audit import ProjectionAudit, ProjectionExplanation, ProjectedRelationExplanation


AUDIT_REPORT_SCHEMA_VERSION = "1"


def _profile_count(profile: AnalysisProfile | None, aliases: tuple[str, ...]) -> int | float | str | None:
    if profile is None:
        return None
    numeric: list[int | float] = []
    textual: list[str] = []
    for stage in profile.stages.values():
        for key in aliases:
            value = stage.counts.get(key)
            if isinstance(value, (int, float)):
                numeric.append(value)
            elif isinstance(value, str):
                textual.append(value)
    if numeric:
        return max(numeric)
    return textual[0] if textual else None


def _cardinalities(
    ir: ArchitectureIR,
    projection: HighLevelArchitectureProjection,
    audit: ProjectionAudit,
    profile: AnalysisProfile | None,
    evidence_group_count: int,
) -> dict[str, int | float | str]:
    values: dict[str, int | float | str] = {
        "files": _profile_count(profile, ("files", "file_count")) or 0,
        "symbols": _profile_count(profile, ("symbols", "symbol_count")) or 0,
        "raw_nodes": len(ir.raw_graph.nodes),
        "raw_edges": len(ir.raw_graph.edges),
        "evidence": len(ir.evidence),
        "architectural_nodes": len(ir.architectural_graph.nodes),
        "architectural_edges": len(ir.architectural_graph.edges),
        "components": len(ir.components) + len(ir.component_candidates),
        "architectural_components": len(ir.components),
        "component_candidates": len(ir.component_candidates),
        "projected_nodes": projection.high_level_node_count,
        "projected_edges": len(projection.projected_edges),
        "evidence_groups": evidence_group_count,
    }
    if not values["files"]:
        values["files"] = _profile_count(profile, ("source_files",)) or 0
    if not values["symbols"]:
        values["symbols"] = _profile_count(profile, ("definitions", "symbols")) or 0
    return values


def _compact_refs(refs: list[str], index: EvidencePayloadIndex) -> dict[str, Any]:
    binding = index.bind(refs)
    result: dict[str, Any] = {
        "evidence_count": binding.evidence_count,
        "evidence_group_ref": binding.group_ref,
    }
    if binding.inline_refs:
        result["evidence_refs"] = binding.inline_refs
    return result


def _compact_context_link(link: Any, index: EvidencePayloadIndex) -> dict[str, Any]:
    record = link.model_dump(mode="json", exclude={"evidence_refs"})
    record.update(_compact_refs(link.evidence_refs, index))
    return record


def _node_record(item: ProjectionExplanation, index: EvidencePayloadIndex) -> dict[str, Any]:
    record = item.model_dump(mode="json", exclude={"evidence_refs", "context_chain"})
    record.update(_compact_refs(item.evidence_refs, index))
    ownership_refs = record.pop("ownership_evidence_refs", [])
    record["ownership_evidence"] = _compact_refs(ownership_refs, index)
    record["context_chain"] = [
        _compact_context_link(link, index)
        for link in item.context_chain
    ]
    return record


def _compact_ids(values: list[str], field: str, limit: int = 20) -> dict[str, Any]:
    ordered = sorted(set(values))
    if len(ordered) <= limit:
        return {field: ordered}
    return {
        f"{field}_count": len(ordered),
        f"{field}_sample": ordered[:limit],
        f"{field}_truncated": True,
    }


def _relation_record(item: ProjectedRelationExplanation, index: EvidencePayloadIndex) -> dict[str, Any]:
    record = item.model_dump(mode="json", exclude={"evidence_refs", "raw_edge_ids"})
    record.update(_compact_refs(item.evidence_refs, index))
    record.update(_compact_ids(item.raw_edge_ids, "raw_edge_ids"))
    return record


def _hypothesis_record(item: Any, index: EvidencePayloadIndex) -> dict[str, Any]:
    supporting = getattr(item, "supporting_evidence", [])
    contradicting = getattr(item, "contradicting_evidence", [])
    record = item.model_dump(mode="json")
    record.pop("supporting_evidence", None)
    record.pop("contradicting_evidence", None)
    record.update({"supporting": _compact_refs(sorted(set(supporting)), index)})
    record.update({"contradicting": _compact_refs(sorted(set(contradicting)), index)})
    return record


def _evidence_group_records(index: EvidencePayloadIndex) -> list[dict[str, Any]]:
    return [
        {
            "id": group.id,
            "evidence_count": group.evidence_count,
            "summary": dict(group.summary),
            "source_ref_count": len(group.source_refs),
            "source_refs": list(group.source_refs[:20]),
            "source_refs_truncated": len(group.source_refs) > 20,
            "recoverability": "full evidence remains in the source ArchitectureIR/EvidenceGroup",
        }
        for group in sorted(index.groups.values(), key=lambda item: item.id)
    ]


def _diagnostics(audit: ProjectionAudit) -> list[dict[str, str]]:
    diagnostics: list[dict[str, str]] = []
    if audit.projected_without_context_count:
        diagnostics.append({
            "kind": "projected_without_context",
            "severity": "candidate_issue",
            "message": "Projected nodes without a context root or explicit boundary require review.",
        })
    if audit.projected_without_global_justification_count:
        diagnostics.append({
            "kind": "projected_without_global_justification",
            "severity": "candidate_issue",
            "message": "A projected node lacks global context or an independent global justification.",
        })
    if audit.local_only_projected_count:
        diagnostics.append({
            "kind": "local_only_projected",
            "severity": "candidate_issue",
            "message": "A locally significant node passed the final high-level projection gate.",
        })
    if audit.navigation_only_projected_count:
        diagnostics.append({
            "kind": "navigation_only_projected",
            "severity": "candidate_issue",
            "message": "A navigation-only node passed the final high-level projection gate.",
        })
    if audit.structural_ownership_rejected_count:
        diagnostics.append({
            "kind": "structural_ownership_rejected",
            "severity": "diagnostic_signal",
            "message": "Structural application containment was not used as architectural ownership.",
        })
    if audit.local_only_framework_promotion_count:
        diagnostics.append({
            "kind": "local_only_framework_promotion",
            "severity": "candidate_issue",
            "message": "Framework evidence is locally significant but lacks global context.",
        })
    if audit.rejected_framework_boundary_count:
        diagnostics.append({
            "kind": "rejected_framework_boundary",
            "severity": "diagnostic_signal",
            "message": "Framework boundary candidates lack coherent application ownership or boundary evidence.",
        })
    if audit.supporting_only_global_membership_count:
        diagnostics.append({
            "kind": "supporting_only_global_membership",
            "severity": "candidate_issue",
            "message": "A global membership appears to rely only on supporting relations.",
        })
    if audit.depends_on_shadowed_count:
        diagnostics.append({
            "kind": "shadowed_generic_dependency",
            "severity": "diagnostic_signal",
            "message": "A generic DEPENDS_ON is accompanied by a stronger relation for the same pair.",
        })
    if audit.nodes_reachable_only_by_weak_relation:
        diagnostics.append({
            "kind": "weak_only_context_reachability",
            "severity": "diagnostic_signal",
            "message": "Projected nodes are reachable from roots through weak-only relations but are not context members.",
        })
    if audit.weak_evidence_saturation_count:
        diagnostics.append({
            "kind": "weak_evidence_saturation",
            "severity": "diagnostic_signal",
            "message": "Repeated weak evidence was capped by semantic reason class.",
        })
    if audit.independent_local_boundary_count:
        diagnostics.append({
            "kind": "independent_local_boundary",
            "severity": "candidate_issue",
            "message": "An infrastructure boundary is locally supported without a global context root.",
        })
    if not audit.traceability:
        diagnostics.append({
            "kind": "traceability_failure",
            "severity": "candidate_issue",
            "message": "At least one audited evidence reference is not present in ArchitectureIR.",
        })
    return diagnostics


def build_projection_audit_report(
    ir: ArchitectureIR,
    projection: HighLevelArchitectureProjection,
    audit: ProjectionAudit,
    profile: AnalysisProfile | None = None,
) -> dict[str, Any]:
    """Build one deterministic report payload for both JSON and Markdown.

    The complete audit remains available to the caller.  The persisted payload
    intentionally omits large inline reference lists and exposes stable group
    IDs/counts instead.
    """

    index = EvidencePayloadIndex(ir.evidence)
    nodes = [_node_record(item, index) for item in audit.node_explanations if item.projection_eligible]
    application_nodes = [_node_record(item, index) for item in audit.node_explanations if item.application_provenance is not None]
    framework_nodes = [_node_record(item, index) for item in audit.node_explanations if item.framework_boundary_qualification is not None]
    relations = [_relation_record(item, index) for item in audit.relation_explanations]
    hypotheses = [_hypothesis_record(item, index) for item in audit.hypothesis_explanations]
    cardinalities = _cardinalities(ir, projection, audit, profile, len(index.groups))
    summary = {
        "repository": ir.repository.model_dump(mode="json"),
        **cardinalities,
        "context_roots": audit.context_root_count,
        "strong_context_roots": audit.strong_context_root_count,
        "weak_navigation_roots": audit.weak_navigation_root_count,
        "context_root_strength_counts": audit.context_root_strength_counts,
        "semantic_details": max(0, projection.detailed_node_count - projection.high_level_node_count),
        "external_dependencies": sum(
            1 for node in ir.architectural_graph.nodes
            if node.type.value == "external_dependency"
        ),
        "evidence_groups": len(index.groups),
        "traceability": audit.traceability,
        "evidence_coverage": audit.evidence_coverage,
        "deterministic": audit.deterministic,
        "framework_context_roots": audit.framework_context_root_count,
        "framework_boundary_candidates": audit.framework_boundary_candidate_count,
        "qualified_framework_boundaries": audit.qualified_framework_boundary_count,
        "rejected_framework_boundaries": audit.rejected_framework_boundary_count,
        "owned_framework_applications": audit.owned_framework_application_count,
        "local_framework_usage": audit.local_framework_usage_count,
        "supporting_only_global_memberships": audit.supporting_only_global_membership_count,
        "globally_eligible_projected_count": audit.globally_eligible_projected_count,
        "local_only_significant_count": audit.local_only_significant_count,
        "local_only_projected_count": audit.local_only_projected_count,
        "projected_without_global_justification_count": audit.projected_without_global_justification_count,
        "navigation_only_projected_count": audit.navigation_only_projected_count,
        "independent_global_boundary_projected_count": audit.independent_global_boundary_projected_count,
    }
    profile_payload = profile.as_dict() if profile is not None else None
    return {
        "schema_version": AUDIT_REPORT_SCHEMA_VERSION,
        "repository": ir.repository.model_dump(mode="json"),
        "summary": summary,
        "projection": {
            "detailed_node_count": projection.detailed_node_count,
            "projected_node_count": projection.high_level_node_count,
            "projected_node_ids": sorted(projection.projected_node_ids),
            "projected_edge_count": len(projection.projected_edges),
            "context_root_ids": sorted(projection.context_root_ids),
            "context_root_strengths": dict(sorted(projection.context_root_strengths.items())),
            "context_root_kinds": dict(sorted(projection.context_root_kinds.items())),
            "navigation_root_ids": sorted(projection.navigation_root_ids),
            "reduction_ratio": projection.reduction_ratio,
        },
        "nodes": sorted(nodes, key=lambda item: item["subject_id"]),
        "application_nodes": sorted(application_nodes, key=lambda item: item["subject_id"]),
        "framework_boundary_nodes": sorted(framework_nodes, key=lambda item: item["subject_id"]),
        "relations": sorted(relations, key=lambda item: item["edge_id"]),
        "hypotheses": sorted(hypotheses, key=lambda item: item["pattern"]),
        "metrics": audit.model_dump(
            mode="json",
            exclude={"node_explanations", "relation_explanations", "hypothesis_explanations"},
        ) | {"cardinalities": cardinalities},
        "diagnostics": _diagnostics(audit),
        "evidence_groups": _evidence_group_records(index),
        "profile": profile_payload,
    }


def render_projection_audit_json(report: dict[str, Any]) -> str:
    return json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True) + "\n"


def _yes_no(value: bool) -> str:
    return "yes" if value else "no"


def _compact_chain(node: dict[str, Any]) -> str:
    chains = node.get("context_chain", [])
    if not chains:
        return "missing"
    return "; ".join(" → ".join(item.get("chain", [])) for item in chains[:3])


def render_projection_audit_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "# Architecture Projection Audit",
        "",
        "## Summary",
        "",
        f"- repository: `{report['repository']['path']}`",
        f"- files: {summary['files']}",
        f"- symbols: {summary['symbols']}",
        f"- raw nodes / edges: {summary['raw_nodes']} / {summary['raw_edges']}",
        f"- architectural nodes / edges: {summary['architectural_nodes']} / {summary['architectural_edges']}",
        f"- projected nodes / edges: {summary['projected_nodes']} / {summary['projected_edges']}",
        f"- context roots: {summary['context_roots']} (strong: {summary['strong_context_roots']})",
        f"- navigation roots: {summary['weak_navigation_roots']}",
        f"- context root strengths: {summary['context_root_strength_counts']}",
        f"- framework context roots: {summary['framework_context_roots']}",
        f"- framework boundary candidates / qualified / rejected: {summary['framework_boundary_candidates']} / {summary['qualified_framework_boundaries']} / {summary['rejected_framework_boundaries']}",
        f"- owned framework applications / local usage: {summary['owned_framework_applications']} / {summary['local_framework_usage']}",
        f"- supporting-only global memberships: {summary['supporting_only_global_memberships']}",
        f"- globally eligible projected: {summary['globally_eligible_projected_count']}",
        f"- local-only significant / projected: {summary['local_only_significant_count']} / {summary['local_only_projected_count']}",
        f"- projected without global justification: {summary['projected_without_global_justification_count']}",
        f"- navigation-only projected: {summary['navigation_only_projected_count']}",
        f"- independent global boundaries projected: {summary['independent_global_boundary_projected_count']}",
        f"- semantic details: {summary['semantic_details']}",
        f"- external dependencies: {summary['external_dependencies']}",
        f"- evidence groups: {summary['evidence_groups']}",
        f"- traceability: {_yes_no(summary['traceability'])}",
        f"- determinism: {_yes_no(summary['deterministic'])}",
        "",
    ]
    if report.get("application_nodes"):
        lines.extend(["## Application Boundary Audit", ""])
        for node in report["application_nodes"]:
            lines.extend([
                f"### {node['subject_id']}",
                "",
                f"- application provenance: {node.get('application_provenance') or 'none'}",
                f"- boundary evidence kind: {node.get('boundary_evidence_kind') or 'none'}",
                f"- projected: {_yes_no(node.get('projection_eligible', False))}",
                f"- significance: {node.get('significance')}",
                f"- observed/inferred: {node.get('observed_inferred_status') or 'none'}",
                f"- executable/entrypoint evidence: {_yes_no(node.get('executable_entrypoint_evidence', False))}",
                f"- evidence count/group: {node.get('evidence_count', 0)} / {node.get('evidence_group_ref') or 'none'}",
                "",
            ])
    else:
        lines.extend(["## Application Boundary Audit", "", "- none", ""])

    if report.get("framework_boundary_nodes"):
        lines.extend(["## Framework Boundary Audit", ""])
        for node in report["framework_boundary_nodes"]:
            lines.extend([
                f"### {node['subject_id']}",
                "",
                f"- qualification: {node.get('framework_boundary_qualification') or 'none'}",
                f"- scope: {node.get('framework_boundary_scope') or 'none'}",
                f"- fact ownership: {node.get('framework_fact_ownership') or 'none'}",
                f"- boundary evidence: {', '.join(node.get('framework_boundary_evidence', [])) or 'none'}",
                f"- context root: {_yes_no(bool(node.get('context_root_ids')))}",
                f"- evidence count/group: {node.get('evidence_count', 0)} / {node.get('evidence_group_ref') or 'none'}",
                "",
            ])

    lines.extend(["## Projected Nodes", ""])
    for node in report["nodes"]:
        lines.extend([
            f"### {node['subject_id']}",
            "",
            f"- role: {node.get('role') or 'unknown'}",
            f"- significance: {node['significance']}",
            f"- score: {node['score']}",
            f"- projection eligible: {_yes_no(node['projection_eligible'])}",
            f"- context root: {_yes_no(bool(node['context_root_ids']))}",
            f"- root strength/kind: {node.get('context_root_strength') or 'none'} / {node.get('context_root_kind') or 'none'}",
            f"- membership source: {node.get('context_membership_source') or 'none'}",
            f"- membership strength: {node.get('context_membership_strength') or 'weak'}",
            f"- globally contextualized: {_yes_no(node['globally_contextualized'])}",
            f"- locally significant: {_yes_no(node['locally_significant'])}",
            f"- boundary justification: {', '.join(node['boundary_justification']) or 'none'}",
            f"- context root IDs: {', '.join(node['context_root_ids']) or 'none'}",
            f"- context chain: {_compact_chain(node)}",
            f"- strong reasons: {', '.join(node['strong_reasons']) or 'none'}",
            f"- supporting reasons: {', '.join(node['supporting_reasons']) or 'none'}",
            f"- evidence count: {node['evidence_count']}",
            f"- evidence group: {node.get('evidence_group_ref') or 'none'}",
            f"- application provenance: {node.get('application_provenance') or 'none'}",
            f"- boundary evidence kind: {node.get('boundary_evidence_kind') or 'none'}",
            f"- observed/inferred: {node.get('observed_inferred_status') or 'none'}",
            f"- executable/entrypoint evidence: {_yes_no(node.get('executable_entrypoint_evidence', False))}",
            f"- ownership: {node.get('ownership_kind') or 'none'} via {node.get('ownership_source_relation') or 'none'}",
            f"- framework qualification: {node.get('framework_boundary_qualification') or 'none'}",
            f"- framework scope: {node.get('framework_boundary_scope') or 'none'}",
            f"- framework fact ownership: {node.get('framework_fact_ownership') or 'none'}",
            f"- framework boundary evidence: {', '.join(node.get('framework_boundary_evidence', [])) or 'none'}",
            "",
        ])
    lines.extend(["## Projected Relations", ""])
    for relation in report["relations"]:
        lines.extend([
            f"### {relation['edge_id']}",
            "",
            f"- {relation['source']} → {relation['target']}",
            f"- canonical kind: {relation['kind']}",
            f"- relation strength: {relation['relation_strength']}",
            f"- context scope: {relation['context_scope']}",
            f"- DEPENDS_ON category: {relation.get('depends_on_category') or 'n/a'}",
            f"- projection reason: {relation['projection_reason']}",
            f"- support count: {relation['support_count']}",
            f"- evidence count / group: {relation['evidence_count']} / {relation.get('evidence_group_ref') or 'none'}",
            f"- stronger relation kinds: {', '.join(relation['stronger_relation_kinds']) or 'none'}",
            f"- context propagation: {relation.get('context_propagation') or 'does_not_propagate_context'}",
            "",
        ])
    metrics = report["metrics"]
    lines.extend([
        "## DEPENDS_ON Audit",
        "",
        f"- total: {metrics['depends_on_total']}",
        f"- ONLY_RELATION: {metrics['depends_on_only_relation_count']}",
        f"- AGGREGATED_STRUCTURAL_SUPPORT: {metrics['depends_on_aggregated_structural_count']}",
        f"- SHADOWED_BY_STRONGER_RELATION: {metrics['depends_on_shadowed_count']}",
        f"- SAME_CONTEXT: {metrics['depends_on_same_context_count']}",
        f"- CROSS_CONTEXT: {metrics['depends_on_cross_context_count']}",
        f"- weak-only reachable projected nodes: {metrics.get('nodes_reachable_only_by_weak_relation', 0)}",
        f"- projected without strong context: {metrics.get('projected_without_strong_context_count', 0)}",
        f"- local-only significance: {metrics.get('locally_significant_only_count', 0)}",
        f"- weak evidence saturation: {metrics.get('weak_evidence_saturation_count', 0)}",
        f"- structural ownership rejected: {metrics.get('structural_ownership_rejected_count', 0)}",
        f"- globally contextualized by ownership: {metrics.get('globally_contextualized_by_ownership_count', 0)}",
        f"- framework context roots: {metrics.get('framework_context_root_count', 0)}",
        f"- framework candidates / qualified / rejected: {metrics.get('framework_boundary_candidate_count', 0)} / {metrics.get('qualified_framework_boundary_count', 0)} / {metrics.get('rejected_framework_boundary_count', 0)}",
        f"- owned framework applications / local usage: {metrics.get('owned_framework_application_count', 0)} / {metrics.get('local_framework_usage_count', 0)}",
        f"- supporting-only global memberships: {metrics.get('supporting_only_global_membership_count', 0)}",
        f"- globally eligible projected: {metrics.get('globally_eligible_projected_count', 0)}",
        f"- local-only significant / projected: {metrics.get('local_only_significant_count', 0)} / {metrics.get('local_only_projected_count', 0)}",
        f"- projected without global justification: {metrics.get('projected_without_global_justification_count', 0)}",
        f"- navigation-only projected: {metrics.get('navigation_only_projected_count', 0)}",
        f"- independent global boundaries projected: {metrics.get('independent_global_boundary_projected_count', 0)}",
        "",
        "## Hypothesis Context Audit",
        "",
    ])
    for hypothesis in report["hypotheses"]:
        lines.extend([
            f"### {hypothesis['pattern']}",
            "",
            f"- supporting evidence: {hypothesis['supporting_evidence_total']}",
            f"- contradicting evidence: {hypothesis['contradicting_evidence_total']}",
            f"- context-root support: {hypothesis['context_root_evidence_count']}",
            f"- local-only support: {hypothesis['local_only_evidence_count']}",
            f"- cross-context support: {hypothesis['cross_context_evidence_count']}",
            f"- unclassified support: {hypothesis['unclassified_evidence_count']}",
            "",
        ])
    lines.extend(["## Diagnostics", ""])
    if report["diagnostics"]:
        for item in report["diagnostics"]:
            lines.append(f"- **{item['severity']}** `{item['kind']}`: {item['message']}")
    else:
        lines.append("- none")
    lines.extend(["", "## Evidence Groups", ""])
    if report["evidence_groups"]:
        for group in report["evidence_groups"]:
            lines.append(
                f"- `{group['id']}`: {group['evidence_count']} refs; "
                f"summary={group['summary']}; sources={', '.join(group['source_refs']) or 'unknown'}"
                + ("; source refs truncated" if group.get("source_refs_truncated") else "")
            )
    else:
        lines.append("- none")
    if report.get("profile") is not None:
        lines.extend(["", "## Profile", "", f"- total seconds: {report['profile']['total_seconds']}", ""])
        for name, stage in report["profile"]["stages"].items():
            lines.append(f"- {name}: {stage['seconds']:.6f} s; counts={stage['counts']}")
    return "\n".join(lines).rstrip() + "\n"


def write_projection_audit_reports(
    report: dict[str, Any],
    output_dir: str | Path,
    output_format: str = "both",
    force: bool = False,
) -> list[Path]:
    """Write the selected report files with a safe, all-or-nothing preflight."""

    normalized = {"md": "markdown", "json": "json"}.get(output_format, output_format)
    if normalized not in {"both", "markdown", "json"}:
        raise ValueError(f"Unsupported audit report format: {output_format}")
    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    targets: list[tuple[Path, str]] = []
    if normalized in {"both", "markdown"}:
        targets.append((directory / "architecture-audit.md", render_projection_audit_markdown(report)))
    if normalized in {"both", "json"}:
        targets.append((directory / "architecture-audit.json", render_projection_audit_json(report)))
    existing = [path for path, _ in targets if path.exists()]
    if existing and not force:
        names = ", ".join(str(path) for path in existing)
        raise FileExistsError(f"Audit report already exists: {names}. Use --force to overwrite.")
    for path, _ in targets:
        path.write_text(dict(targets)[path], encoding="utf-8")
    return [path for path, _ in targets]


__all__ = [
    "AUDIT_REPORT_SCHEMA_VERSION",
    "build_projection_audit_report",
    "render_projection_audit_json",
    "render_projection_audit_markdown",
    "write_projection_audit_reports",
]
