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
from .context import ContextPropagation, context_propagation_kind, context_strength
from .projection import HighLevelArchitectureProjection, SignificanceLevel


class ProjectionContextLink(BaseModel):
    model_config = ConfigDict(extra="forbid")

    root_id: str
    subject_id: str
    relation_kind: str
    relation_id: str | None = None
    evidence_refs: list[str] = Field(default_factory=list)
    chain: list[str] = Field(default_factory=list)
    relation_strength: str = "strong"
    propagation_class: str = "can_propagate_context"


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
    context_root_strength: str | None = None
    context_root_kind: str | None = None
    context_membership_source: str = "none"
    context_membership_strength: str = "weak"
    locally_significant: bool = False
    globally_contextualized: bool = False
    local_framework_fact_count: int = Field(default=0, ge=0)
    strong_reasons: list[str] = Field(default_factory=list)
    supporting_reasons: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    semantic_relation_refs: list[str] = Field(default_factory=list)
    application_provenance: str | None = None
    boundary_evidence_kind: str | None = None
    observed_inferred_status: str | None = None
    executable_entrypoint_evidence: bool = False
    framework_application_evidence: bool = False
    deployment_evidence: bool = False
    ownership_source_relation: str | None = None
    ownership_evidence_refs: list[str] = Field(default_factory=list)
    ownership_kind: str = "none"


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
    context_propagation: str = "does_not_propagate_context"


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
    context_root_strength_counts: dict[str, int] = Field(default_factory=dict)
    strong_context_root_count: int = Field(default=0, ge=0)
    weak_navigation_root_count: int = Field(default=0, ge=0)
    propagation_relation_kind_counts: dict[str, int] = Field(default_factory=dict)
    context_chain_strength_counts: dict[str, int] = Field(default_factory=dict)
    nodes_contextualized_by_strong_relation: int = Field(default=0, ge=0)
    nodes_reachable_only_by_weak_relation: int = Field(default=0, ge=0)
    projected_without_strong_context_count: int = Field(default=0, ge=0)
    locally_significant_only_count: int = Field(default=0, ge=0)
    independent_local_boundary_count: int = Field(default=0, ge=0)
    independent_global_boundary_count: int = Field(default=0, ge=0)
    weak_evidence_saturation_count: int = Field(default=0, ge=0)
    application_node_count: int = Field(default=0, ge=0)
    strong_application_boundary_count: int = Field(default=0, ge=0)
    observed_application_boundary_count: int = Field(default=0, ge=0)
    inferred_application_boundary_count: int = Field(default=0, ge=0)
    architectural_ownership_count: int = Field(default=0, ge=0)
    structural_ownership_rejected_count: int = Field(default=0, ge=0)
    globally_contextualized_by_ownership_count: int = Field(default=0, ge=0)


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
    root_strengths: dict[str, str],
    arch_nodes: dict[str, Any],
    raw_to_arch: dict[str, str],
    raw_edges: dict[str, Any],
):
    links: dict[str, list[ProjectionContextLink]] = defaultdict(list)
    direct_subjects: dict[str, set[str]] = defaultdict(set)
    resource_ids = {resource.id for resource in ir.infrastructure_resources}
    subject_ids = set(arch_nodes) | resource_ids

    def add_link(
        root: str,
        subject: str,
        relation_kind: str,
        relation_id: str | None,
        evidence_refs: list[str],
        chain: list[str],
        propagation: ContextPropagation,
    ) -> None:
        if subject == root or subject not in subject_ids:
            return
        strength = context_strength(propagation).value
        links[subject].append(ProjectionContextLink(
            root_id=root,
            subject_id=subject,
            relation_kind=relation_kind,
            relation_id=relation_id,
            evidence_refs=sorted(set(evidence_refs)),
            chain=chain,
            relation_strength=strength,
            propagation_class=propagation.value,
        ))
        direct_subjects[root].add(subject)

    for root in sorted(roots):
        links[root].append(ProjectionContextLink(
            root_id=root,
            subject_id=root,
            relation_kind="CONTEXT_ROOT",
            chain=[root],
            relation_strength=root_strengths.get(root, "strong"),
            propagation_class="context_root",
        ))

    framework_application_components: set[str] = set()
    deployment_boundary_components = {
        edge.target
        for edge in ir.architectural_graph.edges
        if edge.type == EdgeType.DEPLOYS
        and edge.target in arch_nodes
        and arch_nodes[edge.target].type in {NodeType.COMPONENT, NodeType.CONTAINER}
    }
    for fact in ir.framework_facts:
        if fact.kind != "APPLICATION":
            continue
        for value in (fact.subject, fact.target, fact.attributes.get("module")):
            subject = _resolve(value, arch_nodes, raw_to_arch)
            if subject and arch_nodes.get(subject) and arch_nodes[subject].type == NodeType.COMPONENT:
                framework_application_components.add(subject)

    fact_subjects: dict[str, set[str]] = defaultdict(set)
    for fact in ir.framework_facts:
        values = [
            _resolve(value, arch_nodes, raw_to_arch)
            for value in (fact.subject, fact.target, fact.attributes.get("endpoint"), fact.attributes.get("module"))
        ]
        fact_roots = sorted({value for value in values if value in roots})
        for root in fact_roots:
            for subject in sorted({value for value in values if value and value != root and value in arch_nodes}):
                add_link(
                    root,
                    subject,
                    "FRAMEWORK_CONTEXT",
                    f"framework:{fact.kind}:{root}:{subject}",
                    list(fact.evidence_refs),
                    [root, subject],
                    ContextPropagation.CAN_PROPAGATE_CONTEXT,
                )
                fact_subjects[root].add(subject)

    # Preserve the existing bounded ownership rule for a framework application
    # component contained by an observed application root and participating in
    # semantic component flow. Generic repository CONTAINS is not enough.
    semantic_flow_subjects: set[str] = set()
    for edge in ir.architectural_graph.edges:
        source = arch_nodes.get(edge.source)
        target = arch_nodes.get(edge.target)
        raw_types = [
            raw_edges[raw_id].type
            for raw_id in edge.raw_edge_ids
            if raw_id in raw_edges
        ]
        propagation = context_propagation_kind(edge.type, raw_relation_types=raw_types)
        if (
            source and target
            and source.type == NodeType.COMPONENT
            and target.type == NodeType.COMPONENT
            and propagation != ContextPropagation.DOES_NOT_PROPAGATE_CONTEXT
        ):
            semantic_flow_subjects.update((source.id, target.id))

    for edge in ir.architectural_graph.edges:
        if edge.type != EdgeType.CONTAINS or edge.source not in roots:
            continue
        subject = _resolve(edge.target, arch_nodes, raw_to_arch) or edge.target
        if edge.metadata.get("architectural_ownership") or edge.metadata.get("ownership_kind") == "architectural":
            add_link(
                edge.source,
                subject,
                "APPLICATION_CONTEXT_OWNERSHIP",
                _relation_id(edge),
                list(edge.evidence_refs),
                [edge.source, subject],
                ContextPropagation.CAN_PROPAGATE_CONTEXT,
            )

    candidates: list[tuple[str, str, str, str | None, list[str], ContextPropagation]] = []
    for edge in ir.architectural_graph.edges:
        source = _resolve(edge.source, arch_nodes, raw_to_arch) or edge.source
        target = _resolve(edge.target, arch_nodes, raw_to_arch) or edge.target
        raw_types = [
            raw_edges[raw_id].type
            for raw_id in edge.raw_edge_ids
            if raw_id in raw_edges
        ]
        ownership = (
            edge.type == EdgeType.CONTAINS
            and edge.metadata.get("architectural_ownership")
        )
        propagation = context_propagation_kind(
            edge.type,
            raw_relation_types=raw_types,
            semantic_ownership=bool(ownership),
        )
        if propagation == ContextPropagation.DOES_NOT_PROPAGATE_CONTEXT:
            continue
        candidates.append((
            source,
            target,
            canonical_relation_type(edge.type),
            edge.id,
            list(edge.evidence_refs),
            propagation,
        ))

    for relation in ir.infrastructure_relations:
        source = (
            relation.source
            if relation.source in subject_ids
            else _resolve(relation.source, arch_nodes, raw_to_arch)
        )
        target = (
            relation.target
            if relation.target in subject_ids
            else _resolve(relation.target, arch_nodes, raw_to_arch)
        )
        if not source or not target:
            continue
        propagation = context_propagation_kind(relation.type)
        if propagation == ContextPropagation.DOES_NOT_PROPAGATE_CONTEXT:
            continue
        candidates.append((source, target, canonical_relation_type(relation.type), relation.id, list(relation.evidence_refs), propagation))

    for source, target, kind, relation_id, refs, propagation in candidates:
        for root, subject in ((source, target), (target, source)):
            if root in roots:
                add_link(root, subject, kind, relation_id, refs, [root, subject], propagation)

    # One additional semantic hop is intentionally bounded. Weak-only paths
    # are not added to direct_subjects and therefore cannot become membership.
    for source, target, kind, relation_id, refs, propagation in candidates:
        for root, via, subject in (
            (root, source, target)
            for root, subjects in direct_subjects.items()
            if source in subjects
        ):
            if subject != root:
                add_link(root, subject, kind, relation_id, refs, [root, via, subject], propagation)
        for root, via, subject in (
            (root, target, source)
            for root, subjects in direct_subjects.items()
            if target in subjects
        ):
            if subject != root:
                add_link(root, subject, kind, relation_id, refs, [root, via, subject], propagation)

    return {
        subject: sorted(
            values,
            key=lambda item: (
                item.root_id,
                item.subject_id,
                item.relation_kind,
                item.relation_id or "",
                item.chain,
            ),
        )
        for subject, values in links.items()
    }

def _weak_only_reachable(
    ir: ArchitectureIR,
    roots: set[str],
    arch_nodes: dict[str, Any],
    raw_to_arch: dict[str, str],
    raw_edges: dict[str, Any],
    max_hops: int = 2,
) -> set[str]:
    adjacency: dict[str, set[str]] = defaultdict(set)
    resource_ids = {resource.id for resource in ir.infrastructure_resources}
    subject_ids = set(arch_nodes) | resource_ids
    for edge in ir.architectural_graph.edges:
        source = _resolve(edge.source, arch_nodes, raw_to_arch) or edge.source
        target = _resolve(edge.target, arch_nodes, raw_to_arch) or edge.target
        raw_types = [
            raw_edges[raw_id].type
            for raw_id in edge.raw_edge_ids
            if raw_id in raw_edges
        ]
        if context_propagation_kind(edge.type, raw_relation_types=raw_types) == ContextPropagation.DOES_NOT_PROPAGATE_CONTEXT:
            adjacency[source].add(target)
            adjacency[target].add(source)
    for relation in ir.infrastructure_relations:
        source = (
            relation.source
            if relation.source in subject_ids
            else _resolve(relation.source, arch_nodes, raw_to_arch)
        )
        target = (
            relation.target
            if relation.target in subject_ids
            else _resolve(relation.target, arch_nodes, raw_to_arch)
        )
        if not source or not target:
            continue
        if context_propagation_kind(relation.type) == ContextPropagation.DOES_NOT_PROPAGATE_CONTEXT:
            adjacency[source].add(target)
            adjacency[target].add(source)
    frontier = set(roots)
    reached: set[str] = set()
    for _ in range(max_hops):
        next_frontier = {
            target
            for source in frontier
            for target in adjacency.get(source, set())
            if target not in roots and target not in reached
        }
        reached.update(next_frontier)
        frontier = next_frontier
        if not frontier:
            break
    return reached

def audit_projection(ir: ArchitectureIR, projection: HighLevelArchitectureProjection) -> ProjectionAudit:
    """Build a deterministic audit without modifying IR, projection or ReadModel."""

    arch_nodes = {node.id: node for node in ir.architectural_graph.nodes}
    raw_to_arch = _raw_to_arch(ir)
    selected = set(projection.projected_node_ids)
    significance = {item.subject: item for item in projection.significances}
    roots = set(projection.context_root_ids)
    raw_edges = {edge.id: edge for edge in ir.raw_graph.edges if edge.id}
    links = _context_links(ir, roots, projection.context_root_strengths, arch_nodes, raw_to_arch, raw_edges)
    framework_counts: dict[str, int] = defaultdict(int)
    for fact in ir.framework_facts:
        for value in (fact.subject, fact.target, fact.attributes.get("endpoint"), fact.attributes.get("module")):
            subject = _resolve(value, arch_nodes, raw_to_arch)
            if subject:
                framework_counts[subject] += 1
    application_fact_subjects: dict[str, list[Any]] = defaultdict(list)
    for fact in ir.framework_facts:
        if fact.kind != "APPLICATION":
            continue
        for value in (fact.subject, fact.target, fact.attributes.get("module")):
            subject = _resolve(value, arch_nodes, raw_to_arch)
            if subject:
                application_fact_subjects[subject].append(fact)
    deployment_subjects = {
        endpoint
        for edge in ir.architectural_graph.edges
        if edge.type == EdgeType.DEPLOYS
        for endpoint in (edge.source, edge.target)
    }
    structural_ownership_rejected = 0
    structural_ownership_subjects: set[str] = set()
    for edge in ir.architectural_graph.edges:
        source = _resolve(edge.source, arch_nodes, raw_to_arch) or edge.source
        target = _resolve(edge.target, arch_nodes, raw_to_arch) or edge.target
        if (
            edge.type == EdgeType.CONTAINS
            and arch_nodes.get(source)
            and arch_nodes[source].type == NodeType.APPLICATION
            and target in arch_nodes
            and not (edge.metadata.get("architectural_ownership") or edge.metadata.get("ownership_kind") == "architectural")
        ):
            structural_ownership_rejected += 1
            structural_ownership_subjects.add(target)
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
    globally_linked_boundaries: set[str] = set()
    resource_ids = {resource.id for resource in ir.infrastructure_resources}
    # Keep this diagnostic aligned with projection eligibility: an explicit
    # infrastructure relation to a projected significant subject, or an
    # application-owned deployment boundary, is a global boundary signal.
    for relation in ir.infrastructure_relations:
        source = relation.source if relation.source in selected or relation.source in resource_ids else _resolve(relation.source, arch_nodes, raw_to_arch)
        target = relation.target if relation.target in selected or relation.target in resource_ids else _resolve(relation.target, arch_nodes, raw_to_arch)
        if not source or not target:
            continue
        resource_endpoint = source in resource_ids or target in resource_ids
        if not resource_endpoint:
            continue
        for boundary, other in ((source, target), (target, source)):
            if boundary not in resource_ids:
                continue
            if (
                other in roots
                or links.get(other)
                or (
                    other in selected
                    and significance.get(other)
                    and significance[other].significance in {SignificanceLevel.HIGH, SignificanceLevel.MEDIUM}
                )
            ):
                globally_linked_boundaries.add(boundary)
    deployment_targets = {
        edge.target
        for edge in ir.architectural_graph.edges
        if edge.type == EdgeType.DEPLOYS and edge.target in selected
    }
    for edge in ir.architectural_graph.edges:
        if edge.type == EdgeType.CONTAINS and edge.source in roots and edge.target in deployment_targets:
            globally_linked_boundaries.add(edge.target)

    explanations: list[ProjectionExplanation] = []
    for subject in sorted(significance):
        item = significance[subject]
        subject_links = links.get(subject, [])
        node = arch_nodes.get(subject)
        application_provenance = None
        boundary_evidence_kind = None
        observed_inferred_status = node.status.value if node else None
        executable_entrypoint_evidence = False
        framework_application_evidence = bool(application_fact_subjects.get(subject))
        deployment_evidence = subject in deployment_subjects
        if node and node.type == NodeType.APPLICATION:
            application_provenance = str(node.metadata.get("application_provenance", "")) or (
                "standalone_application" if not node.metadata.get("raw_node_ids") else "detected_application"
            )
            boundary_evidence_kind = str(node.metadata.get("boundary_evidence_kind", "")) or "unspecified"
            executable_entrypoint_evidence = bool(
                node.metadata.get("entrypoint")
                or node.metadata.get("executable")
                or any(
                    fact.attributes.get("entrypoint") or fact.metadata.get("entrypoint")
                    for fact in application_fact_subjects.get(subject, [])
                )
            )
        ownership_links = [
            link for link in subject_links
            if link.relation_kind == "APPLICATION_CONTEXT_OWNERSHIP"
        ]
        ownership_source_relation = ownership_links[0].relation_kind if ownership_links else None
        ownership_evidence_refs = sorted({ref for link in ownership_links for ref in link.evidence_refs})
        ownership_kind = "architectural" if ownership_links else (
            "structural_rejected" if subject in structural_ownership_subjects else "none"
        )
        root_ids = sorted({link.root_id for link in subject_links})
        root_strength = (
            projection.context_root_strengths.get(root_ids[0])
            if root_ids
            else None
        )
        root_kind = (
            projection.context_root_kinds.get(root_ids[0])
            if root_ids
            else None
        )
        if root_ids:
            membership_source = "context_root" if subject in roots else (
                "propagated:" + ",".join(sorted({link.relation_kind for link in subject_links}))
            )
            membership_strength = max(
                (link.relation_strength for link in subject_links),
                key=lambda value: {"weak": 0, "supporting": 1, "strong": 2}.get(value, 0),
                default="weak",
            )
        else:
            membership_source = "none"
            membership_strength = "weak"
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
        global_boundary_reasons = [
            reason for reason in boundary
            if "architectural context root" in reason
            or "explicit architectural boundary" in reason
            or "observed application boundary" in reason
        ]
        global_context = bool(root_ids or global_boundary_reasons or subject in globally_linked_boundaries)
        if boundary and not root_ids:
            membership_source = "independent_boundary"
            membership_strength = "strong" if global_context else "weak"
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
            context_root_strength=root_strength,
            context_root_kind=root_kind,
            context_membership_source=membership_source,
            context_membership_strength=membership_strength,
            locally_significant=local,
            globally_contextualized=global_context,
            local_framework_fact_count=framework_counts.get(subject, 0),
            strong_reasons=sorted(set(strong_reasons)),
            supporting_reasons=supporting_reasons,
            evidence_refs=sorted(set(item.evidence_refs)),
            semantic_relation_refs=sorted(ref for ref in semantic_refs.get(subject, set()) if ref),
            application_provenance=application_provenance,
            boundary_evidence_kind=boundary_evidence_kind,
            observed_inferred_status=observed_inferred_status,
            executable_entrypoint_evidence=executable_entrypoint_evidence,
            framework_application_evidence=framework_application_evidence,
            deployment_evidence=deployment_evidence,
            ownership_source_relation=ownership_source_relation,
            ownership_evidence_refs=ownership_evidence_refs,
            ownership_kind=ownership_kind,
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
        raw_types = [
            raw_edges[raw_id].type
            for raw_id in edge.raw_edge_ids
            if raw_id in raw_edges
        ]
        propagation = context_propagation_kind(
            edge.kind,
            raw_relation_types=raw_types,
        )
        reason = "both endpoints are projection-eligible and the canonical relation has evidence"
        if propagation == ContextPropagation.DOES_NOT_PROPAGATE_CONTEXT:
            reason += "; relation is valid but does not propagate context"
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
            context_propagation=propagation.value,
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
        ref for item in explanations for link in item.context_chain for ref in link.evidence_refs
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
    root_strength_counts = defaultdict(int)
    for root in roots:
        root_strength_counts[projection.context_root_strengths.get(root, "strong")] += 1
    propagation_counts = defaultdict(int)
    chain_strength_counts = defaultdict(int)
    for item in projected_explanations:
        for link in item.context_chain:
            chain_strength_counts[link.relation_strength] += 1
    for item in relation_explanations:
        propagation_counts[item.kind + ":" + item.context_propagation] += 1
    weak_reachable = _weak_only_reachable(ir, roots, arch_nodes, raw_to_arch, raw_edges)
    contextualized_by_strong = sum(
        any(link.relation_strength == "strong" for link in item.context_chain)
        and item.subject_id not in roots
        for item in projected_explanations
    )
    projected_without_strong = sum(
        not item.globally_contextualized
        for item in projected_explanations
    )
    local_only = sum(item.locally_significant for item in projected_explanations)
    independent_local = sum(
        bool(item.boundary_justification)
        and not item.globally_contextualized
        and not item.context_root_ids
        for item in projected_explanations
    )
    independent_global = sum(
        bool(item.boundary_justification)
        and item.globally_contextualized
        and not item.context_root_ids
        for item in projected_explanations
    )
    application_explanations = [
        item for item in projected_explanations
        if item.application_provenance is not None
    ]
    strong_application_boundaries = sum(
        item.subject_id in roots
        and item.subject_id in arch_nodes
        and arch_nodes[item.subject_id].type == NodeType.APPLICATION
        for item in application_explanations
    )
    observed_application_boundaries = sum(
        item.subject_id in roots and item.observed_inferred_status == "observed"
        for item in application_explanations
    )
    inferred_application_boundaries = sum(
        item.subject_id in roots and item.observed_inferred_status == "inferred"
        for item in application_explanations
    )
    architectural_ownership_count = sum(
        item.ownership_kind == "architectural"
        for item in projected_explanations
    )
    contextualized_by_ownership = sum(
        item.ownership_kind == "architectural" and item.globally_contextualized
        for item in projected_explanations
    )
    weak_only_projected = sum(
        item.subject_id in weak_reachable
        and not item.context_root_ids
        and not item.boundary_justification
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
        context_root_strength_counts=dict(sorted(root_strength_counts.items())),
        strong_context_root_count=sum(value for key, value in root_strength_counts.items() if key == "strong"),
        weak_navigation_root_count=len(projection.navigation_root_ids),
        propagation_relation_kind_counts=dict(sorted(propagation_counts.items())),
        context_chain_strength_counts=dict(sorted(chain_strength_counts.items())),
        nodes_contextualized_by_strong_relation=contextualized_by_strong,
        nodes_reachable_only_by_weak_relation=weak_only_projected,
        projected_without_strong_context_count=projected_without_strong,
        locally_significant_only_count=local_only,
        independent_local_boundary_count=independent_local,
        independent_global_boundary_count=independent_global,
        weak_evidence_saturation_count=projection.weak_evidence_saturation_count,
        application_node_count=sum(1 for node in arch_nodes.values() if node.type == NodeType.APPLICATION),
        strong_application_boundary_count=strong_application_boundaries,
        observed_application_boundary_count=observed_application_boundaries,
        inferred_application_boundary_count=inferred_application_boundaries,
        architectural_ownership_count=architectural_ownership_count,
        structural_ownership_rejected_count=structural_ownership_rejected,
        globally_contextualized_by_ownership_count=contextualized_by_ownership,
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
