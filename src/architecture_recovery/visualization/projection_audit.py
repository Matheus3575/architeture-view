"""Read-only explainability and relation audit for high-level projection."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from architecture_recovery.ir import (
    ArchitectureIR,
    EdgeType,
    NodeType,
    canonical_relation_type,
    relation_strength,
)
from .projection import HighLevelArchitectureProjection, SignificanceLevel


class ProjectionContextLink(BaseModel):
    model_config = ConfigDict(extra="forbid")

    root_id: str
    subject_id: str
    relation_kind: str
    relation_id: str | None = None
    evidence_refs: list[str] = Field(default_factory=list)
    chain: list[str] = Field(default_factory=list)


class ProjectionExplanation(BaseModel):
    """Deterministic explanation for one detailed or projected node."""

    model_config = ConfigDict(extra="forbid")

    subject_id: str
    significance: SignificanceLevel
    score: float = Field(ge=0.0, le=1.0)
    role: str | None = None
    projection_eligible: bool = False
    boundary_justification: list[str] = Field(default_factory=list)
    context_root_ids: list[str] = Field(default_factory=list)
    context_chain: list[ProjectionContextLink] = Field(default_factory=list)
    locally_significant: bool = False
    globally_contextualized: bool = False
    local_framework_fact_count: int = Field(default=0, ge=0)
    strong_reasons: list[str] = Field(default_factory=list)
    supporting_reasons: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    semantic_relation_refs: list[str] = Field(default_factory=list)


class ProjectedRelationExplanation(BaseModel):
    """Deterministic explanation for one projected high-level edge."""

    model_config = ConfigDict(extra="forbid")

    edge_id: str
    source: str
    target: str
    kind: str
    relation_strength: str
    source_significance: SignificanceLevel | None = None
    target_significance: SignificanceLevel | None = None
    source_context_root_ids: list[str] = Field(default_factory=list)
    target_context_root_ids: list[str] = Field(default_factory=list)
    context_scope: str
    evidence_count: int = Field(default=0, ge=0)
    evidence_refs: list[str] = Field(default_factory=list)
    support_count: int = Field(default=1, ge=1)
    raw_edge_ids: list[str] = Field(default_factory=list)
    stronger_relation_kinds: list[str] = Field(default_factory=list)
    depends_on_category: str | None = None
    projection_reason: str


class HypothesisContextExplanation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    pattern: str
    supporting_evidence_total: int = Field(default=0, ge=0)
    contradicting_evidence_total: int = Field(default=0, ge=0)
    context_root_evidence_count: int = Field(default=0, ge=0)
    local_only_evidence_count: int = Field(default=0, ge=0)
    cross_context_evidence_count: int = Field(default=0, ge=0)
    unclassified_evidence_count: int = Field(default=0, ge=0)


class ProjectionAudit(BaseModel):
    """Compact audit report; full evidence refs remain available in records."""

    model_config = ConfigDict(extra="forbid")

    projected_node_count: int = Field(default=0, ge=0)
    context_root_count: int = Field(default=0, ge=0)
    contextualized_projected_count: int = Field(default=0, ge=0)
    independent_boundary_count: int = Field(default=0, ge=0)
    projected_without_context_count: int = Field(default=0, ge=0)
    local_only_framework_promotion_count: int = Field(default=0, ge=0)
    projected_edge_count: int = Field(default=0, ge=0)
    relation_kind_counts: dict[str, int] = Field(default_factory=dict)
    relation_strength_counts: dict[str, int] = Field(default_factory=dict)
    depends_on_total: int = Field(default=0, ge=0)
    depends_on_only_relation_count: int = Field(default=0, ge=0)
    depends_on_shadowed_count: int = Field(default=0, ge=0)
    depends_on_aggregated_structural_count: int = Field(default=0, ge=0)
    depends_on_same_context_count: int = Field(default=0, ge=0)
    depends_on_cross_context_count: int = Field(default=0, ge=0)
    hypothesis_contextual_support_count: int = Field(default=0, ge=0)
    hypothesis_local_only_support_count: int = Field(default=0, ge=0)
    hypothesis_cross_context_support_count: int = Field(default=0, ge=0)
    traceability: bool = True
    evidence_coverage: float = Field(default=1.0, ge=0.0, le=1.0)
    deterministic: bool = True
    node_explanations: list[ProjectionExplanation] = Field(default_factory=list)
    relation_explanations: list[ProjectedRelationExplanation] = Field(default_factory=list)
    hypothesis_explanations: list[HypothesisContextExplanation] = Field(default_factory=list)


_CONTEXT_RELATIONS = {
    EdgeType.ROUTES_TO.value,
    EdgeType.DEPLOYS.value,
    EdgeType.CALLS.value,
    EdgeType.INSTANTIATES.value,
    EdgeType.CONNECTS_TO.value,
}
_STRONG_FLOW_RELATIONS = {
    EdgeType.ROUTES_TO.value,
    EdgeType.QUERIES.value,
    EdgeType.PUBLISHES.value,
    EdgeType.CONSUMES.value,
    EdgeType.CONNECTS_TO.value,
}
_RELATION_RANK = {"weak": 1, "medium": 2, "strong": 3}


def _raw_to_arch(ir: ArchitectureIR) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for node in ir.architectural_graph.nodes:
        for raw_id in node.metadata.get("raw_node_ids", []):
            mapping[raw_id] = node.id
    return mapping


def _resolve(value: str | None, arch_nodes: dict[str, Any], raw_to_arch: dict[str, str]) -> str | None:
    if not value:
        return None
    if value in arch_nodes:
        return value
    if value in raw_to_arch:
        return raw_to_arch[value]
    module_name = value.split(":", 1)[-1].split(".", 1)[0]
    for raw_id, arch_id in raw_to_arch.items():
        if raw_id.endswith(f":{module_name}"):
            return arch_id
    return None


def _selected_owner(
    value: str,
    selected: set[str],
    arch_nodes: dict[str, Any],
    raw_to_arch: dict[str, str],
) -> str | None:
    resolved = _resolve(value, arch_nodes, raw_to_arch) or value
    if resolved in selected:
        return resolved
    node = arch_nodes.get(resolved)
    if not node:
        return None
    raw_ids = set(node.metadata.get("raw_node_ids", []))
    for candidate in sorted(selected):
        parent = arch_nodes.get(candidate)
        if parent and raw_ids & set(parent.metadata.get("raw_node_ids", [])):
            return candidate
    return None


def _relation_id(edge: Any) -> str | None:
    return edge.id if getattr(edge, "id", None) else None


def _edge_endpoints(
    ir: ArchitectureIR,
    selected: set[str],
    arch_nodes: dict[str, Any],
    raw_to_arch: dict[str, str],
) -> dict[tuple[str, str], list[tuple[str, str, list[str], str | None]]]:
    pairs: dict[tuple[str, str], list[tuple[str, str, list[str], str | None]]] = defaultdict(list)
    for edge in ir.architectural_graph.edges:
        source = _selected_owner(edge.source, selected, arch_nodes, raw_to_arch)
        target = _selected_owner(edge.target, selected, arch_nodes, raw_to_arch)
        if not source or not target or source == target:
            continue
        pairs[(source, target)].append((
            canonical_relation_type(edge.type),
            edge.id or "",
            list(edge.evidence_refs),
            edge.id,
        ))
    resource_ids = {resource.id for resource in ir.infrastructure_resources}
    for relation in ir.infrastructure_relations:
        source_value = relation.source if relation.source in resource_ids else _resolve(relation.source, arch_nodes, raw_to_arch)
        target_value = relation.target if relation.target in resource_ids else _resolve(relation.target, arch_nodes, raw_to_arch)
        source = _selected_owner(source_value or relation.source, selected, arch_nodes, raw_to_arch)
        target = _selected_owner(target_value or relation.target, selected, arch_nodes, raw_to_arch)
        if not source or not target or source == target:
            continue
        pairs[(source, target)].append((
            canonical_relation_type(relation.type),
            relation.id,
            list(relation.evidence_refs),
            relation.id,
        ))
    return pairs


def _context_links(
    ir: ArchitectureIR,
    roots: set[str],
    arch_nodes: dict[str, Any],
    raw_to_arch: dict[str, str],
    raw_edges: dict[str, Any],
):
    links: dict[str, list[ProjectionContextLink]] = defaultdict(list)
    for root in sorted(roots):
        links[root].append(ProjectionContextLink(
            root_id=root,
            subject_id=root,
            relation_kind="CONTEXT_ROOT",
            chain=[root],
        ))
    direct_subjects: dict[str, set[str]] = defaultdict(set)
    for fact in ir.framework_facts:
        values = [
            _resolve(value, arch_nodes, raw_to_arch)
            for value in (fact.subject, fact.target, fact.attributes.get("endpoint"), fact.attributes.get("module"))
        ]
        fact_roots = sorted({value for value in values if value in roots})
        if not fact_roots:
            continue
        for root in fact_roots:
            for subject in sorted({value for value in values if value and value != root and value in arch_nodes}):
                link = ProjectionContextLink(
                    root_id=root,
                    subject_id=subject,
                    relation_kind="FRAMEWORK_CONTEXT",
                    relation_id=f"framework:{fact.kind}:{root}:{subject}",
                    evidence_refs=sorted(set(fact.evidence_refs)),
                    chain=[root, subject],
                )
                links[subject].append(link)
                direct_subjects[root].add(subject)
    # Mirror the existing unambiguous single-application fallback used by
    # projection. It is not a global-primary-root assumption: it applies only
    # when one observed root and one framework application component exist.
    if len(roots) == 1:
        root = next(iter(roots))
        application_components: list[tuple[str, Any]] = []
        for fact in ir.framework_facts:
            if fact.kind != "APPLICATION":
                continue
            for value in (fact.subject, fact.target, fact.attributes.get("module")):
                subject = _resolve(value, arch_nodes, raw_to_arch)
                if subject and arch_nodes.get(subject) and arch_nodes[subject].type == NodeType.COMPONENT:
                    application_components.append((subject, fact))
        unique_components = {subject for subject, _ in application_components}
        if len(unique_components) == 1:
            subject = sorted(unique_components)[0]
            fact = sorted(application_components, key=lambda item: (item[0], item[1].kind, item[1].evidence_refs))[0][1]
            links[subject].append(ProjectionContextLink(
                root_id=root,
                subject_id=subject,
                relation_kind="FRAMEWORK_CONTEXT_SINGLE_APPLICATION",
                relation_id=f"framework:{fact.kind}:{root}:{subject}",
                evidence_refs=sorted(set(fact.evidence_refs)),
                chain=[root, subject],
            ))
            direct_subjects[root].add(subject)
    application_components = set()
    for fact in ir.framework_facts:
        if fact.kind != "APPLICATION":
            continue
        for value in (fact.subject, fact.target, fact.attributes.get("module")):
            subject = _resolve(value, arch_nodes, raw_to_arch)
            if subject and arch_nodes.get(subject) and arch_nodes[subject].type == NodeType.COMPONENT:
                application_components.add(subject)
    semantic_flow_subjects = set()
    for edge in ir.architectural_graph.edges:
        kind = canonical_relation_type(edge.type)
        raw_flow = any(
            raw_edges.get(raw_id) and raw_edges[raw_id].type in {
                EdgeType.CALLS, EdgeType.INSTANTIATES, EdgeType.EXTENDS,
            }
            for raw_id in edge.raw_edge_ids
        )
        source_node = arch_nodes.get(edge.source)
        target_node = arch_nodes.get(edge.target)
        if (
            source_node and target_node
            and source_node.type == NodeType.COMPONENT
            and target_node.type == NodeType.COMPONENT
            and (kind in _STRONG_FLOW_RELATIONS or raw_flow)
        ):
            semantic_flow_subjects.update((edge.source, edge.target))
    for edge in ir.architectural_graph.edges:
        if edge.type != EdgeType.CONTAINS or edge.source not in roots:
            continue
        subject = _resolve(edge.target, arch_nodes, raw_to_arch) or edge.target
        if subject not in application_components or subject not in semantic_flow_subjects:
            continue
        links[subject].append(ProjectionContextLink(
            root_id=edge.source,
            subject_id=subject,
            relation_kind="APPLICATION_CONTEXT_OWNERSHIP",
            relation_id=_relation_id(edge),
            evidence_refs=sorted(set(edge.evidence_refs)),
            chain=[edge.source, subject],
        ))
        direct_subjects[edge.source].add(subject)
    for edge in ir.architectural_graph.edges:
        kind = canonical_relation_type(edge.type)
        if kind not in _CONTEXT_RELATIONS:
            continue
        for root, subject in ((edge.source, edge.target), (edge.target, edge.source)):
            if root not in roots:
                continue
            resolved = _resolve(subject, arch_nodes, raw_to_arch) or subject
            if resolved == root or resolved not in arch_nodes:
                continue
            link = ProjectionContextLink(
                root_id=root,
                subject_id=resolved,
                relation_kind=kind,
                relation_id=_relation_id(edge),
                evidence_refs=sorted(set(edge.evidence_refs)),
                chain=[root, resolved],
            )
            links[resolved].append(link)
            direct_subjects[root].add(resolved)
    # One bounded semantic-flow hop. This is explanatory only and mirrors the
    # bounded context used by projection; it does not create significance.
    for edge in ir.architectural_graph.edges:
        kind = canonical_relation_type(edge.type)
        raw_flow = any(
            raw_edges.get(raw_id) and raw_edges[raw_id].type in {
                EdgeType.CALLS, EdgeType.INSTANTIATES, EdgeType.EXTENDS,
            }
            for raw_id in edge.raw_edge_ids
        )
        if kind not in _STRONG_FLOW_RELATIONS and kind != EdgeType.CALLS.value and not raw_flow:
            continue
        source = _resolve(edge.source, arch_nodes, raw_to_arch) or edge.source
        target = _resolve(edge.target, arch_nodes, raw_to_arch) or edge.target
        for root, subject, via in (
            (root, target, source) for root, subjects in direct_subjects.items() if source in subjects
        ):
            if subject == root:
                continue
            links[subject].append(ProjectionContextLink(
                root_id=root,
                subject_id=subject,
                relation_kind=kind,
                relation_id=_relation_id(edge),
                evidence_refs=sorted(set(edge.evidence_refs)),
                chain=[root, via, subject],
            ))
        for root, subject, via in (
            (root, source, target) for root, subjects in direct_subjects.items() if target in subjects
        ):
            if subject == root:
                continue
            links[subject].append(ProjectionContextLink(
                root_id=root,
                subject_id=subject,
                relation_kind=kind,
                relation_id=_relation_id(edge),
                evidence_refs=sorted(set(edge.evidence_refs)),
                chain=[root, via, subject],
            ))
    return {
        subject: sorted(
            values,
            key=lambda item: (item.root_id, item.subject_id, item.relation_kind, item.relation_id or "", item.chain),
        )
        for subject, values in links.items()
    }


def audit_projection(ir: ArchitectureIR, projection: HighLevelArchitectureProjection) -> ProjectionAudit:
    """Build a deterministic audit without modifying IR, projection or ReadModel."""

    arch_nodes = {node.id: node for node in ir.architectural_graph.nodes}
    raw_to_arch = _raw_to_arch(ir)
    selected = set(projection.projected_node_ids)
    significance = {item.subject: item for item in projection.significances}
    roots = set(projection.context_root_ids)
    raw_edges = {edge.id: edge for edge in ir.raw_graph.edges if edge.id}
    links = _context_links(ir, roots, arch_nodes, raw_to_arch, raw_edges)
    framework_counts: dict[str, int] = defaultdict(int)
    for fact in ir.framework_facts:
        for value in (fact.subject, fact.target, fact.attributes.get("endpoint"), fact.attributes.get("module")):
            subject = _resolve(value, arch_nodes, raw_to_arch)
            if subject:
                framework_counts[subject] += 1
    semantic_refs: dict[str, set[str]] = defaultdict(set)
    for edge in ir.architectural_graph.edges:
        kind = canonical_relation_type(edge.type)
        if relation_strength(kind) != "weak":
            for subject in (edge.source, edge.target):
                resolved = _resolve(subject, arch_nodes, raw_to_arch) or subject
                semantic_refs[resolved].add(edge.id or "")
    for relation in ir.infrastructure_relations:
        if relation_strength(relation.type) != "weak":
            for subject in (relation.source, relation.target):
                resolved = _resolve(subject, arch_nodes, raw_to_arch) or subject
                semantic_refs[resolved].add(relation.id)
    explanations: list[ProjectionExplanation] = []
    for subject in sorted(significance):
        item = significance[subject]
        subject_links = links.get(subject, [])
        root_ids = sorted({link.root_id for link in subject_links})
        boundary = [
            reason for reason in item.reasons
            if "architectural context root" in reason
            or "explicit architectural boundary" in reason
            or "explicit infrastructure boundary relation" in reason
        ]
        strong_reasons = [
            reason for reason in item.reasons
            if any(token in reason for token in ("strong", "explicit", "principal", "observed application"))
        ]
        supporting_reasons = sorted(set(item.reasons) - set(strong_reasons))
        global_context = bool(root_ids or boundary)
        local = item.significance in {SignificanceLevel.HIGH, SignificanceLevel.MEDIUM} and not global_context
        explanations.append(ProjectionExplanation(
            subject_id=subject,
            significance=item.significance,
            score=item.score,
            role=item.role or (arch_nodes[subject].type.value if subject in arch_nodes else None),
            projection_eligible=subject in selected,
            boundary_justification=sorted(set(boundary)),
            context_root_ids=root_ids,
            context_chain=subject_links,
            locally_significant=local,
            globally_contextualized=global_context,
            local_framework_fact_count=framework_counts.get(subject, 0),
            strong_reasons=sorted(set(strong_reasons)),
            supporting_reasons=supporting_reasons,
            evidence_refs=sorted(set(item.evidence_refs)),
            semantic_relation_refs=sorted(ref for ref in semantic_refs.get(subject, set()) if ref),
        ))
    explanation_by_subject = {item.subject_id: item for item in explanations}
    pairs = _edge_endpoints(ir, selected, arch_nodes, raw_to_arch)
    relation_explanations: list[ProjectedRelationExplanation] = []
    relation_kind_counts: dict[str, int] = defaultdict(int)
    strength_counts: dict[str, int] = defaultdict(int)
    depends_counts = defaultdict(int)
    context_evidence: set[str] = set()
    local_evidence: set[str] = set()
    cross_evidence: set[str] = set()
    for explanation in explanations:
        if explanation.globally_contextualized:
            context_evidence.update(explanation.evidence_refs)
        if explanation.locally_significant:
            local_evidence.update(explanation.evidence_refs)
    for edge in sorted(projection.projected_edges, key=lambda item: item.id):
        source_explanation = explanation_by_subject.get(edge.source)
        target_explanation = explanation_by_subject.get(edge.target)
        source_roots = source_explanation.context_root_ids if source_explanation else []
        target_roots = target_explanation.context_root_ids if target_explanation else []
        if set(source_roots) & set(target_roots):
            context_scope = "SAME_CONTEXT"
        elif source_roots and target_roots:
            context_scope = "CROSS_CONTEXT"
        else:
            context_scope = "UNCONTEXTUALIZED"
        pair_kinds = {kind for kind, _, _, _ in pairs.get((edge.source, edge.target), [])}
        current_strength = relation_strength(edge.kind)
        stronger = sorted(
            kind for kind in pair_kinds
            if kind != canonical_relation_type(edge.kind)
            and _RELATION_RANK[relation_strength(kind)] > _RELATION_RANK[current_strength]
        )
        category = None
        if canonical_relation_type(edge.kind) == EdgeType.DEPENDS_ON.value:
            if stronger:
                category = "SHADOWED_BY_STRONGER_RELATION"
                depends_counts["shadowed"] += 1
            elif edge.support_count > 1 or len(edge.raw_edge_ids) > 1:
                category = "AGGREGATED_STRUCTURAL_SUPPORT"
                depends_counts["aggregated"] += 1
            else:
                category = "ONLY_RELATION"
                depends_counts["only"] += 1
            depends_counts["total"] += 1
            depends_counts["same" if context_scope == "SAME_CONTEXT" else "cross" if context_scope == "CROSS_CONTEXT" else "uncontextualized"] += 1
        relation_kind_counts[canonical_relation_type(edge.kind)] += 1
        strength_counts[current_strength] += 1
        if context_scope == "CROSS_CONTEXT":
            cross_evidence.update(edge.evidence_refs)
        reason = "both endpoints are projection-eligible and the canonical relation has evidence"
        if stronger:
            reason += "; stronger relation exists for the same directed pair"
        if context_scope == "CROSS_CONTEXT":
            reason += "; relation crosses independent context roots"
        relation_explanations.append(ProjectedRelationExplanation(
            edge_id=edge.id,
            source=edge.source,
            target=edge.target,
            kind=canonical_relation_type(edge.kind),
            relation_strength=current_strength,
            source_significance=source_explanation.significance if source_explanation else None,
            target_significance=target_explanation.significance if target_explanation else None,
            source_context_root_ids=sorted(source_roots),
            target_context_root_ids=sorted(target_roots),
            context_scope=context_scope,
            evidence_count=len(edge.evidence_refs),
            evidence_refs=sorted(set(edge.evidence_refs)),
            support_count=edge.support_count,
            raw_edge_ids=sorted(set(edge.raw_edge_ids)),
            stronger_relation_kinds=stronger,
            depends_on_category=category,
            projection_reason=reason,
        ))
    hypothesis_explanations: list[HypothesisContextExplanation] = []
    for hypothesis in sorted(ir.architecture.hypotheses, key=lambda item: item.pattern):
        supporting = set(hypothesis.supporting_evidence) | set(hypothesis.evidence_refs)
        contradicting = set(hypothesis.contradicting_evidence)
        local = supporting & local_evidence
        contextual = supporting & context_evidence
        cross = supporting & cross_evidence
        classified = contextual | local | cross
        hypothesis_explanations.append(HypothesisContextExplanation(
            pattern=hypothesis.pattern,
            supporting_evidence_total=len(supporting),
            contradicting_evidence_total=len(contradicting),
            context_root_evidence_count=len(contextual),
            local_only_evidence_count=len(local - contextual),
            cross_context_evidence_count=len(cross),
            unclassified_evidence_count=len(supporting - classified),
        ))
    evidence_ids = {item.id for item in ir.evidence}
    audited_refs = [
        ref for item in explanations for ref in item.evidence_refs
    ] + [
        ref for item in relation_explanations for ref in item.evidence_refs
    ]
    evidence_coverage = (
        sum(ref in evidence_ids for ref in audited_refs) / len(audited_refs)
        if audited_refs else 1.0
    )
    traceability = all(ref in evidence_ids for ref in audited_refs)
    projected_explanations = [item for item in explanations if item.projection_eligible]
    contextualized = sum(bool(item.context_root_ids or item.boundary_justification) for item in projected_explanations)
    independent_boundaries = sum(bool(item.boundary_justification) for item in projected_explanations)
    without_context = sum(
        not item.context_root_ids and not item.boundary_justification
        for item in projected_explanations
    )
    local_framework = sum(
        item.local_framework_fact_count > 0 and item.locally_significant
        for item in projected_explanations
    )
    return ProjectionAudit(
        projected_node_count=len(selected),
        context_root_count=len(roots),
        contextualized_projected_count=contextualized,
        independent_boundary_count=independent_boundaries,
        projected_without_context_count=without_context,
        local_only_framework_promotion_count=local_framework,
        projected_edge_count=len(relation_explanations),
        relation_kind_counts=dict(sorted(relation_kind_counts.items())),
        relation_strength_counts=dict(sorted(strength_counts.items())),
        depends_on_total=depends_counts["total"],
        depends_on_only_relation_count=depends_counts["only"],
        depends_on_shadowed_count=depends_counts["shadowed"],
        depends_on_aggregated_structural_count=depends_counts["aggregated"],
        depends_on_same_context_count=depends_counts["same"],
        depends_on_cross_context_count=depends_counts["cross"],
        hypothesis_contextual_support_count=sum(item.context_root_evidence_count for item in hypothesis_explanations),
        hypothesis_local_only_support_count=sum(item.local_only_evidence_count for item in hypothesis_explanations),
        hypothesis_cross_context_support_count=sum(item.cross_context_evidence_count for item in hypothesis_explanations),
        traceability=traceability,
        evidence_coverage=round(evidence_coverage, 6),
        node_explanations=explanations,
        relation_explanations=relation_explanations,
        hypothesis_explanations=hypothesis_explanations,
    )


__all__ = [
    "HypothesisContextExplanation",
    "ProjectedRelationExplanation",
    "ProjectionAudit",
    "ProjectionContextLink",
    "ProjectionExplanation",
    "audit_projection",
]
