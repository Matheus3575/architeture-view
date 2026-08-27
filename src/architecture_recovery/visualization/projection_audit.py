"""Read-only explainability and relation audit for high-level projection."""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from architecture_recovery.ir import (
    ArchitectureIR,
    EdgeType,
    NodeType,
    canonical_relation_type,
    relation_strength,
)
from .context import ContextPropagation, DeploymentProvenance, context_direction_pairs, context_propagation_kind, context_strength, deployment_provenance
from .projection import ArchitecturalProjectionBuilder, HighLevelArchitectureProjection, SignificanceLevel


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
    establishes_membership: bool = True
    deployment_provenance: str | None = None


class PositiveEvidenceLedgerEntry(BaseModel):
    """Read-only ledger entry for positive architectural evidence."""

    model_config = ConfigDict(extra="forbid")

    subject_id: str
    evidence_kind: str
    producer: str
    source_relation: str | None = None
    owner_id: str | None = None
    direction: str | None = None
    provenance: str = "unknown"
    accepted: bool = False
    rejection_reason: str | None = None
    architectural_role: str | None = None
    evidence_refs: list[str] = Field(default_factory=list)

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
    framework_boundary_qualification: str | None = None
    framework_boundary_scope: str | None = None
    framework_fact_ownership: str | None = None
    framework_boundary_evidence: list[str] = Field(default_factory=list)
    framework_ownership_relations: list[str] = Field(default_factory=list)
    framework_ownership_evidence_refs: list[str] = Field(default_factory=list)


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
    deployment_provenance: str | None = None


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
    positive_evidence_ledger: list[PositiveEvidenceLedgerEntry] = Field(default_factory=list)
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
    framework_context_root_count: int = Field(default=0, ge=0)
    framework_boundary_candidate_count: int = Field(default=0, ge=0)
    qualified_framework_boundary_count: int = Field(default=0, ge=0)
    rejected_framework_boundary_count: int = Field(default=0, ge=0)
    owned_framework_application_count: int = Field(default=0, ge=0)
    local_framework_usage_count: int = Field(default=0, ge=0)
    supporting_only_global_membership_count: int = Field(default=0, ge=0)
    membership_established_by_relation_kind: dict[str, int] = Field(default_factory=dict)
    membership_supported_by_relation_kind: dict[str, int] = Field(default_factory=dict)
    globally_eligible_projected_count: int = Field(default=0, ge=0)
    local_only_significant_count: int = Field(default=0, ge=0)
    local_only_projected_count: int = Field(default=0, ge=0)
    projected_without_global_justification_count: int = Field(default=0, ge=0)
    navigation_only_projected_count: int = Field(default=0, ge=0)
    independent_global_boundary_projected_count: int = Field(default=0, ge=0)
    deploys_total: int = Field(default=0, ge=0)
    deploys_by_provenance: dict[str, int] = Field(default_factory=dict)
    deploys_can_propagate_count: int = Field(default=0, ge=0)
    deploys_supporting_count: int = Field(default=0, ge=0)
    deploys_non_propagating_count: int = Field(default=0, ge=0)
    membership_established_by_deploys: int = Field(default=0, ge=0)
    deployment_boundary_candidate_count: int = Field(default=0, ge=0)
    qualified_global_deployment_boundary_count: int = Field(default=0, ge=0)
    rejected_local_deployment_boundary_count: int = Field(default=0, ge=0)
    navigation_transit_membership_count: int = Field(default=0, ge=0)
    positive_evidence_produced_count: int = Field(default=0, ge=0)
    positive_evidence_accepted_count: int = Field(default=0, ge=0)
    positive_evidence_rejected_count: int = Field(default=0, ge=0)
    positive_evidence_absent_count: int = Field(default=0, ge=0)
    rejection_reason_counts: dict[str, int] = Field(default_factory=dict)
    executable_root_count: int = Field(default=0, ge=0)
    owned_framework_boundary_count: int = Field(default=0, ge=0)
    related_framework_boundary_count: int = Field(default=0, ge=0)
    unresolved_framework_boundary_count: int = Field(default=0, ge=0)
    qualified_local_framework_boundary_count: int = Field(default=0, ge=0)
    framework_ownership_evidence_count: int = Field(default=0, ge=0)
    framework_ownership_lost_count: int = Field(default=0, ge=0)
    framework_local_false_promotion_count: int = Field(default=0, ge=0)
    semantic_membership_count: int = Field(default=0, ge=0)
    explicit_deployment_ownership_count: int = Field(default=0, ge=0)
    directional_propagation_count: int = Field(default=0, ge=0)
    executable_entrypoint_count: int = Field(default=0, ge=0)
    resolved_entrypoint_count: int = Field(default=0, ge=0)
    unresolved_entrypoint_count: int = Field(default=0, ge=0)
    first_party_entrypoint_count: int = Field(default=0, ge=0)
    accepted_entrypoint_evidence_count: int = Field(default=0, ge=0)
    rejected_entrypoint_evidence_count: int = Field(default=0, ge=0)
    entrypoint_root_count: int = Field(default=0, ge=0)

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


def _deployment_provenance_for_subjects(
    ir: ArchitectureIR,
    source: str,
    target: str,
    metadata: dict[str, Any] | None = None,
    evidence_refs: list[str] | None = None,
) -> DeploymentProvenance:
    arch_nodes = {node.id: node for node in ir.architectural_graph.nodes}
    resources = {resource.id: resource for resource in ir.infrastructure_resources}
    source_node = arch_nodes.get(source)
    target_node = arch_nodes.get(target)
    source_resource = resources.get(source)
    target_resource = resources.get(target)
    source_type = source_node.type if source_node else source_resource.kind if source_resource else None
    target_type = target_node.type if target_node else target_resource.kind if target_resource else None
    evidence_by_id = {item.id: item for item in ir.evidence}
    refs = evidence_refs or []
    return deployment_provenance(
        EdgeType.DEPLOYS,
        source_id=source,
        target_id=target,
        source_type=source_type,
        target_type=target_type,
        metadata=metadata,
        evidence_sources=(
            evidence_by_id[ref].source_type.value
            for ref in refs
            if ref in evidence_by_id
        ),
    )

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
        establishes_membership: bool = True,
        deployment_kind: DeploymentProvenance | None = None,
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
            establishes_membership=establishes_membership,
            deployment_provenance=deployment_kind.value if deployment_kind else None,
        ))
        if establishes_membership:
            direct_subjects[root].add(subject)

    for root in sorted(roots):
        links[root].append(ProjectionContextLink(
            root_id=root,
            subject_id=root,
            relation_kind="CONTEXT_ROOT",
            chain=[root],
            relation_strength=root_strengths.get(root, "strong"),
            propagation_class="context_root",
            establishes_membership=True,
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

    candidates: list[tuple[str, str, str, str | None, list[str], ContextPropagation, DeploymentProvenance | None]] = []
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
        deployment_kind = _deployment_provenance_for_subjects(ir, source, target, edge.metadata, list(edge.evidence_refs)) if edge.type == EdgeType.DEPLOYS else None
        propagation = context_propagation_kind(
            edge.type,
            raw_relation_types=raw_types,
            semantic_ownership=bool(ownership),
            deployment_provenance=deployment_kind,
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
            deployment_kind,
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
        deployment_kind = _deployment_provenance_for_subjects(ir, source, target, relation.metadata, list(relation.evidence_refs)) if canonical_relation_type(relation.type) == EdgeType.DEPLOYS.value else None
        propagation = context_propagation_kind(relation.type, deployment_provenance=deployment_kind)
        if propagation == ContextPropagation.DOES_NOT_PROPAGATE_CONTEXT:
            continue
        candidates.append((source, target, canonical_relation_type(relation.type), relation.id, list(relation.evidence_refs), propagation, deployment_kind))

    # Establish membership only from semantic relations. SUPPORTS_CONTEXT may
    # annotate an already established member, but cannot create membership.
    for expected in (ContextPropagation.CAN_PROPAGATE_CONTEXT, ContextPropagation.SUPPORTS_CONTEXT):
        for source, target, kind, relation_id, refs, propagation, deployment_kind in candidates:
            if propagation != expected:
                continue
            for root, subject in context_direction_pairs(source, target, kind):
                if root in roots:
                    already_member = subject in direct_subjects[root]
                    if expected == ContextPropagation.CAN_PROPAGATE_CONTEXT or already_member:
                        add_link(
                            root, subject, kind, relation_id, refs, [root, subject], propagation,
                            establishes_membership=expected == ContextPropagation.CAN_PROPAGATE_CONTEXT,
                            deployment_kind=deployment_kind,
                        )

    # One additional bounded hop. SUPPORTS_CONTEXT is retained only when the
    # target already has membership from another establishing relation.
    for expected in (ContextPropagation.CAN_PROPAGATE_CONTEXT, ContextPropagation.SUPPORTS_CONTEXT):
        for source, target, kind, relation_id, refs, propagation, deployment_kind in candidates:
            if propagation != expected:
                continue
            for via, subject in context_direction_pairs(source, target, kind):
                for root, subjects in direct_subjects.items():
                    if via not in subjects:
                        continue
                    if subject != root and (expected == ContextPropagation.CAN_PROPAGATE_CONTEXT or subject in direct_subjects[root]):
                        add_link(
                            root, subject, kind, relation_id, refs, [root, via, subject], propagation,
                            establishes_membership=expected == ContextPropagation.CAN_PROPAGATE_CONTEXT,
                            deployment_kind=deployment_kind,
                        )

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
        deployment_kind = _deployment_provenance_for_subjects(ir, source, target, edge.metadata, list(edge.evidence_refs)) if edge.type == EdgeType.DEPLOYS else None
        if context_propagation_kind(edge.type, raw_relation_types=raw_types, deployment_provenance=deployment_kind) == ContextPropagation.DOES_NOT_PROPAGATE_CONTEXT:
            for origin, destination in context_direction_pairs(source, target, edge.type):
                adjacency[origin].add(destination)
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
        deployment_kind = _deployment_provenance_for_subjects(ir, source, target, relation.metadata, list(relation.evidence_refs)) if canonical_relation_type(relation.type) == EdgeType.DEPLOYS.value else None
        if context_propagation_kind(relation.type, deployment_provenance=deployment_kind) == ContextPropagation.DOES_NOT_PROPAGATE_CONTEXT:
            for origin, destination in context_direction_pairs(source, target, relation.type):
                adjacency[origin].add(destination)
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

def _build_positive_evidence_ledger(
    ir: ArchitectureIR,
    projection: HighLevelArchitectureProjection,
    explanations: list[ProjectionExplanation],
    links: dict[str, list[ProjectionContextLink]],
    framework_assessments: dict[str, dict[str, Any]],
    raw_edges: dict[str, Any],
) -> list[PositiveEvidenceLedgerEntry]:
    """Explain where positive context evidence was produced and consumed."""

    positive_facts = {"APPLICATION", "ROUTER", "HTTP_ENDPOINT", "ROUTER_INCLUSION", "CONTROLLER_LIKE"}
    positive_relations = {
        EdgeType.ROUTES_TO.value,
        EdgeType.QUERIES.value,
        EdgeType.CONNECTS_TO.value,
        EdgeType.PUBLISHES.value,
        EdgeType.CONSUMES.value,
        EdgeType.DEPLOYS.value,
    }
    roots = set(projection.context_root_ids)
    arch_nodes = {node.id: node for node in ir.architectural_graph.nodes}
    raw_to_arch = _raw_to_arch(ir)
    established = roots | {
        subject
        for subject, subject_links in links.items()
        if any(link.establishes_membership for link in subject_links)
    }
    entries: list[PositiveEvidenceLedgerEntry] = []

    def add(
        *,
        subject: str,
        evidence_kind: str,
        producer: str,
        source_relation: str | None,
        owner_id: str | None,
        direction: str | None,
        provenance: str,
        accepted: bool,
        rejection_reason: str | None,
        role: str | None,
        refs: list[str],
    ) -> None:
        entries.append(PositiveEvidenceLedgerEntry(
            subject_id=subject,
            evidence_kind=evidence_kind,
            producer=producer,
            source_relation=source_relation,
            owner_id=owner_id,
            direction=direction,
            provenance=provenance,
            accepted=accepted,
            rejection_reason=rejection_reason,
            architectural_role=role,
            evidence_refs=sorted(set(refs)),
        ))

    def resolved(value: str | None) -> str | None:
        return _resolve(value, arch_nodes, raw_to_arch) or value

    for entrypoint in sorted(ir.entrypoints, key=lambda item: item.id):
        subject = entrypoint.owner_id or entrypoint.resolved_target or f"entrypoint:{entrypoint.id}"
        add(
            subject=subject,
            evidence_kind="executable_entrypoint",
            producer="EntrypointAnalyzer",
            source_relation=entrypoint.declared_target,
            owner_id=entrypoint.owner_id,
            direction="declaration_to_target_to_owner",
            provenance=entrypoint.provenance,
            accepted=entrypoint.accepted,
            rejection_reason=entrypoint.rejection_reason,
            role="EXECUTABLE_ENTRYPOINT",
            refs=list(entrypoint.evidence_refs),
        )
    # Application nodes are producer outputs, even when their boundary evidence
    # is rejected. This distinguishes a rejected aggregate from no producer.
    for node in sorted(ir.architectural_graph.nodes, key=lambda item: item.id):
        if node.type != NodeType.APPLICATION:
            continue
        provenance = str(node.metadata.get("application_provenance", "detected_application"))
        accepted = node.id in roots
        add(
            subject=node.id,
            evidence_kind="application_boundary",
            producer="GraphAggregation",
            source_relation="APPLICATION_BOUNDARY",
            owner_id=node.id,
            direction=None,
            provenance=provenance,
            accepted=accepted,
            rejection_reason=None if accepted else "application boundary was not admitted as a global root",
            role="APPLICATION",
            refs=list(node.evidence_refs),
        )

    for fact in sorted(ir.framework_facts, key=lambda item: (item.kind, item.subject or "", tuple(item.evidence_refs))):
        if fact.kind not in positive_facts:
            continue
        values = [fact.subject, fact.target, fact.attributes.get("owner"), fact.attributes.get("application"), fact.attributes.get("router"), fact.attributes.get("endpoint"), fact.attributes.get("module")]
        subjects = sorted({item for value in values if (item := resolved(value)) and item in arch_nodes})
        for subject in subjects:
            assessment = framework_assessments.get(subject, {})
            accepted = subject in established
            provenance = assessment.get("ownership") or "framework_fact"
            add(
                subject=subject,
                evidence_kind="framework_boundary",
                producer="FrameworkAdapter",
                source_relation=fact.kind,
                owner_id=resolved(fact.attributes.get("owner") or fact.attributes.get("application") or fact.attributes.get("router")) or subject,
                direction="fact",
                provenance=str(provenance),
                accepted=accepted,
                rejection_reason=None if accepted else "framework fact lacks an accepted global context association",
                role=fact.kind,
                refs=list(fact.evidence_refs),
            )

    arch_node_ids = {node.id for node in ir.architectural_graph.nodes}
    relation_items: list[tuple[str, str, str, str | None, list[str], dict[str, Any], str]] = []
    for edge in ir.architectural_graph.edges:
        kind = canonical_relation_type(edge.type)
        if kind in positive_relations:
            source = resolved(edge.source) or edge.source
            target = resolved(edge.target) or edge.target
            relation_items.append((source, target, kind, edge.id, list(edge.evidence_refs), edge.metadata, "GraphAggregation"))
    resource_ids = {resource.id for resource in ir.infrastructure_resources}
    for relation in ir.infrastructure_relations:
        kind = canonical_relation_type(relation.type)
        if kind not in positive_relations:
            continue
        source = relation.source if relation.source in resource_ids or relation.source in arch_node_ids else resolved(relation.source) or relation.source
        target = relation.target if relation.target in resource_ids or relation.target in arch_node_ids else resolved(relation.target) or relation.target
        relation_items.append((source, target, kind, relation.id, list(relation.evidence_refs), relation.metadata, "InfrastructureAnalyzer"))

    aggregated_raw_ids = {
        raw_id
        for edge in ir.architectural_graph.edges
        for raw_id in edge.raw_edge_ids
    }
    for raw_edge in sorted(raw_edges.values(), key=lambda item: item.id or ""):
        kind = canonical_relation_type(raw_edge.type)
        if not raw_edge.id or kind not in positive_relations or raw_edge.id in aggregated_raw_ids:
            continue
        source = resolved(raw_edge.source) or raw_edge.source
        target = resolved(raw_edge.target) or raw_edge.target
        add(
            subject=target,
            evidence_kind="raw_relation",
            producer="RawGraph",
            source_relation=f"{kind}:{raw_edge.id}",
            owner_id=source,
            direction="forward" if kind == EdgeType.DEPLOYS.value else "observed",
            provenance="lost_before_architecture",
            accepted=False,
            rejection_reason="raw positive relation has no architectural aggregation",
            role=kind,
            refs=list(raw_edge.evidence_refs),
        )

    for source, target, kind, relation_id, refs, metadata, producer in sorted(relation_items, key=lambda item: (item[0], item[1], item[2], item[3] or "")):
        deployment_kind = _deployment_provenance_for_subjects(ir, source, target, metadata, refs) if kind == EdgeType.DEPLOYS.value else None
        propagation = context_propagation_kind(kind, deployment_provenance=deployment_kind)
        accepted = any(
            origin in roots and destination in established
            for origin, destination in context_direction_pairs(source, target, kind)
        ) and propagation == ContextPropagation.CAN_PROPAGATE_CONTEXT
        deployment_label = deployment_kind.value if deployment_kind else None
        provenance = deployment_label or "inferred_architectural_relation"
        reason = None
        if not accepted:
            if kind == EdgeType.DEPLOYS.value and propagation != ContextPropagation.CAN_PROPAGATE_CONTEXT:
                reason = "deployment provenance does not establish global context"
            else:
                reason = "relation does not connect a root to an established context member"
        add(
            subject=target,
            evidence_kind="deployment_ownership" if kind == EdgeType.DEPLOYS.value else "semantic_relation",
            producer=producer,
            source_relation=f"{kind}:{relation_id or ''}",
            owner_id=source,
            direction="forward" if kind == EdgeType.DEPLOYS.value else "directed",
            provenance=provenance,
            accepted=accepted,
            rejection_reason=reason,
            role=kind,
            refs=refs,
        )

    ledger_subjects = {entry.subject_id for entry in entries}
    significance = {item.subject_id: item for item in explanations}
    for item in sorted(explanations, key=lambda value: value.subject_id):
        if item.significance not in {SignificanceLevel.HIGH, SignificanceLevel.MEDIUM} or item.subject_id in ledger_subjects:
            continue
        add(
            subject=item.subject_id,
            evidence_kind="global_context",
            producer="not_observed",
            source_relation=None,
            owner_id=None,
            direction=None,
            provenance="absent",
            accepted=False,
            rejection_reason="no positive architectural context evidence was produced",
            role=item.role,
            refs=[],
        )
    return sorted(entries, key=lambda item: (item.subject_id, item.evidence_kind, item.source_relation or "", item.provenance, item.evidence_refs))

def audit_projection(ir: ArchitectureIR, projection: HighLevelArchitectureProjection) -> ProjectionAudit:
    """Build a deterministic audit without modifying IR, projection or ReadModel."""

    arch_nodes = {node.id: node for node in ir.architectural_graph.nodes}
    raw_to_arch = _raw_to_arch(ir)
    selected = set(projection.projected_node_ids)
    significance = {item.subject: item for item in projection.significances}
    framework_assessments = ArchitecturalProjectionBuilder()._framework_boundary_assessments(ir, arch_nodes, raw_to_arch)
    roots = set(projection.context_root_ids)
    arch_nodes = {node.id: node for node in ir.architectural_graph.nodes}
    raw_to_arch = _raw_to_arch(ir)
    raw_edges = {edge.id: edge for edge in ir.raw_graph.edges if edge.id}
    entrypoint_owner_ids = {item.owner_id for item in ir.entrypoints if item.owner_id}
    entrypoint_refs_by_owner: dict[str, set[str]] = defaultdict(set)
    for item in ir.entrypoints:
        if item.owner_id:
            entrypoint_refs_by_owner[item.owner_id].update(item.evidence_refs)
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
    resource_ids = {resource.id for resource in ir.infrastructure_resources}
    deployment_subjects = {
        endpoint
        for edge in ir.architectural_graph.edges
        if edge.type == EdgeType.DEPLOYS
        for endpoint in (edge.source, edge.target)
    }
    deployment_records: list[tuple[str, str, DeploymentProvenance, ContextPropagation, list[str]]] = []
    for edge in ir.architectural_graph.edges:
        if edge.type != EdgeType.DEPLOYS:
            continue
        source = _resolve(edge.source, arch_nodes, raw_to_arch) or edge.source
        target = _resolve(edge.target, arch_nodes, raw_to_arch) or edge.target
        provenance = _deployment_provenance_for_subjects(ir, source, target, edge.metadata, list(edge.evidence_refs))
        propagation = context_propagation_kind(edge.type, deployment_provenance=provenance)
        deployment_records.append((source, target, provenance, propagation, list(edge.evidence_refs)))
    for relation in ir.infrastructure_relations:
        if canonical_relation_type(relation.type) != EdgeType.DEPLOYS.value:
            continue
        source = relation.source if relation.source in resource_ids or relation.source in arch_nodes else _resolve(relation.source, arch_nodes, raw_to_arch)
        target = relation.target if relation.target in resource_ids or relation.target in arch_nodes else _resolve(relation.target, arch_nodes, raw_to_arch)
        if not source or not target:
            continue
        provenance = _deployment_provenance_for_subjects(ir, source, target, relation.metadata, list(relation.evidence_refs))
        propagation = context_propagation_kind(relation.type, deployment_provenance=provenance)
        deployment_records.append((source, target, provenance, propagation, list(relation.evidence_refs)))
    deployment_provenance_counts = Counter(item[2].value for item in deployment_records)
    deploys_can_propagate = sum(item[3] == ContextPropagation.CAN_PROPAGATE_CONTEXT for item in deployment_records)
    deploys_supporting = sum(item[3] == ContextPropagation.SUPPORTS_CONTEXT for item in deployment_records)
    deploys_non_propagating = sum(item[3] == ContextPropagation.DOES_NOT_PROPAGATE_CONTEXT for item in deployment_records)
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
        target
        for source, target, provenance, propagation, refs in deployment_records
        if propagation == ContextPropagation.CAN_PROPAGATE_CONTEXT and target in selected
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
        executable_entrypoint_evidence = subject in entrypoint_owner_ids
        framework_application_evidence = bool(application_fact_subjects.get(subject))
        deployment_evidence = subject in deployment_subjects
        if node and node.type == NodeType.APPLICATION:
            application_provenance = str(node.metadata.get("application_provenance", "")) or (
                "standalone_application" if not node.metadata.get("raw_node_ids") else "detected_application"
            )
            boundary_evidence_kind = str(node.metadata.get("boundary_evidence_kind", "")) or "unspecified"
            executable_entrypoint_evidence = executable_entrypoint_evidence or bool(
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
        framework_assessment = framework_assessments.get(subject, {})
        ownership_kind = "architectural" if ownership_links else (
            "structural_rejected" if subject in structural_ownership_subjects else "none"
        )
        root_ids = sorted({link.root_id for link in subject_links if link.establishes_membership})
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
        independent_global_role = bool(
            node and node.type in {NodeType.API, NodeType.EXTERNAL_SERVICE}
        )
        global_context = bool(root_ids or global_boundary_reasons or subject in globally_linked_boundaries)
        if boundary and not root_ids:
            membership_source = "independent_boundary"
            membership_strength = "strong" if global_context else "weak"
        local = item.significance in {SignificanceLevel.HIGH, SignificanceLevel.MEDIUM} and not global_context and not independent_global_role
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
            evidence_refs=sorted(set(item.evidence_refs) | entrypoint_refs_by_owner.get(subject, set())),
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
            framework_boundary_qualification=("QUALIFIED_GLOBAL" if framework_assessment.get("global_qualified") else "QUALIFIED_LOCAL" if framework_assessment.get("qualified") else "REJECTED") if framework_assessment else None,
            framework_boundary_scope=framework_assessment.get("boundary_scope"),
            framework_fact_ownership=framework_assessment.get("ownership"),
            framework_boundary_evidence=list(framework_assessment.get("boundary_evidence", [])),
            framework_ownership_relations=list(framework_assessment.get("ownership_relations", [])),
            framework_ownership_evidence_refs=list(framework_assessment.get("ownership_evidence_refs", [])),
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
        deployment_kind = None
        if canonical_relation_type(edge.kind) == EdgeType.DEPLOYS.value:
            original_edge = next(
                (candidate for candidate in ir.architectural_graph.edges
                 if candidate.id and candidate.id in edge.raw_edge_ids),
                None,
            )
            original_relation = next(
                (candidate for candidate in ir.infrastructure_relations
                 if candidate.id in edge.raw_edge_ids),
                None,
            )
            deployment_kind = _deployment_provenance_for_subjects(
                ir,
                edge.source,
                edge.target,
                original_edge.metadata if original_edge else original_relation.metadata if original_relation else None,
                list(edge.evidence_refs),
            )
        propagation = context_propagation_kind(
            edge.kind,
            raw_relation_types=raw_types,
            deployment_provenance=deployment_kind,
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
            deployment_provenance=deployment_kind.value if deployment_kind else None,
        ))
    positive_evidence_ledger = _build_positive_evidence_ledger(ir, projection, explanations, links, framework_assessments, raw_edges)
    positive_evidence_produced = [item for item in positive_evidence_ledger if item.provenance != "absent"]
    positive_evidence_accepted = [item for item in positive_evidence_produced if item.accepted]
    positive_evidence_rejected = [item for item in positive_evidence_produced if not item.accepted]
    positive_evidence_absent = [item for item in positive_evidence_ledger if item.provenance == "absent"]
    rejection_reasons = Counter(item.rejection_reason for item in positive_evidence_rejected if item.rejection_reason)
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
    def has_global_justification(item: ProjectionExplanation) -> bool:
        node = arch_nodes.get(item.subject_id)
        independent_role = bool(
            node and node.type in {NodeType.API, NodeType.EXTERNAL_SERVICE}
        )
        return bool(item.globally_contextualized or item.context_root_ids or independent_role)

    globally_justified_projected = [
        item for item in projected_explanations if has_global_justification(item)
    ]
    local_only_significant = sum(item.locally_significant for item in explanations)
    local_only_projected = sum(
        item.projection_eligible and item.locally_significant
        for item in explanations
    )
    projected_without_global = sum(
        not has_global_justification(item) for item in projected_explanations
    )
    navigation_only_projected = sum(
        item.projection_eligible
        and item.subject_id in set(projection.navigation_root_ids)
        and not has_global_justification(item)
        for item in explanations
    )
    independent_global_boundary_projected = sum(
        item.projection_eligible
        and bool(item.boundary_justification)
        and has_global_justification(item)
        and not item.context_root_ids
        for item in explanations
    )
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
    membership_established_counts = defaultdict(int)
    membership_supported_counts = defaultdict(int)
    supporting_only_membership = 0
    for item in projected_explanations:
        establishing = [
            link for link in item.context_chain
            if link.establishes_membership and link.relation_kind != "CONTEXT_ROOT"
        ]
        supporting = [
            link for link in item.context_chain
            if not link.establishes_membership
        ]
        for link in establishing:
            membership_established_counts[link.relation_kind] += 1
        for link in supporting:
            membership_supported_counts[link.relation_kind] += 1
        if supporting and not establishing and item.globally_contextualized:
            supporting_only_membership += 1
    qualified_framework = sum(1 for item in framework_assessments.values() if item["qualified"])
    framework_candidate_subjects = {subject for subject, item in framework_assessments.items() if item["candidate"]}
    framework_candidates = len(framework_candidate_subjects)
    owned_framework = sum(1 for item in framework_assessments.values() if item["ownership"] == "OWNED_APPLICATION_BOUNDARY")
    related_framework = sum(1 for item in framework_assessments.values() if item["ownership"] == "RELATED_FRAMEWORK_BOUNDARY")
    unresolved_framework = sum(1 for item in framework_assessments.values() if item["ownership"] == "UNRESOLVED")
    qualified_local_framework = sum(1 for item in framework_assessments.values() if item["qualified"] and not item["global_qualified"])
    framework_ownership_evidence = sum(len(item.get("ownership_evidence_refs", [])) for item in framework_assessments.values())
    framework_ownership_lost = len(framework_candidate_subjects - set(framework_assessments))
    local_framework_usage = sum(1 for item in framework_assessments.values() if item["ownership"] == "LOCAL_FRAMEWORK_USAGE")
    weak_only_projected = sum(
        item.subject_id in weak_reachable
        and not item.context_root_ids
        and not item.boundary_justification
        for item in projected_explanations
    )
    navigation_ids = {
        node.id for node in arch_nodes.values() if node.type == NodeType.REPOSITORY
    }
    membership_deployed = sum(
        link.relation_kind == EdgeType.DEPLOYS.value and link.establishes_membership
        for links_for_subject in links.values()
        for link in links_for_subject
    )
    navigation_transit_memberships = sum(
        link.relation_kind == EdgeType.DEPLOYS.value
        and any(intermediate in navigation_ids for intermediate in link.chain[1:-1])
        for links_for_subject in links.values()
        for link in links_for_subject
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
        framework_context_root_count=sum(1 for subject, item in framework_assessments.items() if item["qualified"] and subject in roots),
        framework_boundary_candidate_count=framework_candidates,
        qualified_framework_boundary_count=qualified_framework,
        rejected_framework_boundary_count=max(0, framework_candidates - qualified_framework),
        owned_framework_application_count=owned_framework,
        related_framework_boundary_count=related_framework,
        unresolved_framework_boundary_count=unresolved_framework,
        qualified_local_framework_boundary_count=qualified_local_framework,
        framework_ownership_evidence_count=framework_ownership_evidence,
        framework_ownership_lost_count=framework_ownership_lost,
        framework_local_false_promotion_count=sum(
            item.subject_id in selected
            and item.framework_boundary_scope == "local"
            and not item.globally_contextualized
            for item in projected_explanations
        ),
        local_framework_usage_count=local_framework_usage,
        supporting_only_global_membership_count=supporting_only_membership,
        membership_established_by_relation_kind=dict(sorted(membership_established_counts.items())),
        membership_supported_by_relation_kind=dict(sorted(membership_supported_counts.items())),
        globally_eligible_projected_count=len(globally_justified_projected),
        local_only_significant_count=local_only_significant,
        local_only_projected_count=local_only_projected,
        projected_without_global_justification_count=projected_without_global,
        navigation_only_projected_count=navigation_only_projected,
        independent_global_boundary_projected_count=independent_global_boundary_projected,
        deploys_total=len(deployment_records),
        deploys_by_provenance=dict(sorted(deployment_provenance_counts.items())),
        deploys_can_propagate_count=deploys_can_propagate,
        deploys_supporting_count=deploys_supporting,
        deploys_non_propagating_count=deploys_non_propagating,
        membership_established_by_deploys=membership_deployed,
        deployment_boundary_candidate_count=len(deployment_records),
        qualified_global_deployment_boundary_count=sum(
            provenance in {
                DeploymentProvenance.EXPLICIT_EXECUTION_DEPLOYMENT,
                DeploymentProvenance.EXPLICIT_DEPLOYMENT_OWNERSHIP,
            }
            for _, _, provenance, _, _ in deployment_records
        ),
        rejected_local_deployment_boundary_count=sum(
            provenance not in {
                DeploymentProvenance.EXPLICIT_EXECUTION_DEPLOYMENT,
                DeploymentProvenance.EXPLICIT_DEPLOYMENT_OWNERSHIP,
            }
            for _, _, provenance, _, _ in deployment_records
        ),
        navigation_transit_membership_count=navigation_transit_memberships,
        positive_evidence_produced_count=len(positive_evidence_produced),
        positive_evidence_accepted_count=len(positive_evidence_accepted),
        positive_evidence_rejected_count=len(positive_evidence_rejected),
        positive_evidence_absent_count=len(positive_evidence_absent),
        rejection_reason_counts=dict(sorted(rejection_reasons.items())),
        executable_root_count=sum(item.executable_entrypoint_evidence for item in projected_explanations if item.subject_id in roots),
        owned_framework_boundary_count=sum(item["ownership"] == "OWNED_APPLICATION_BOUNDARY" for item in framework_assessments.values()),
        semantic_membership_count=sum(item.accepted and item.evidence_kind == "semantic_relation" for item in positive_evidence_ledger),
        explicit_deployment_ownership_count=sum(item.provenance == DeploymentProvenance.EXPLICIT_DEPLOYMENT_OWNERSHIP.value for item in positive_evidence_ledger),
        directional_propagation_count=sum(item.accepted and item.evidence_kind == "deployment_ownership" and item.direction == "forward" for item in positive_evidence_ledger),
        executable_entrypoint_count=len(ir.entrypoints),
        resolved_entrypoint_count=sum(item.resolved_target is not None for item in ir.entrypoints),
        unresolved_entrypoint_count=sum(item.resolved_target is None for item in ir.entrypoints),
        first_party_entrypoint_count=sum(item.accepted for item in ir.entrypoints),
        accepted_entrypoint_evidence_count=sum(item.evidence_kind == "executable_entrypoint" and item.accepted for item in positive_evidence_ledger),
        rejected_entrypoint_evidence_count=sum(item.evidence_kind == "executable_entrypoint" and not item.accepted for item in positive_evidence_ledger),
        entrypoint_root_count=len({item.owner_id for item in ir.entrypoints if item.accepted and item.owner_id in roots}),
        traceability=traceability,
        evidence_coverage=round(evidence_coverage, 6),
        node_explanations=explanations,
        relation_explanations=relation_explanations,
        hypothesis_explanations=hypothesis_explanations,
        positive_evidence_ledger=positive_evidence_ledger,
    )


__all__ = [
    "HypothesisContextExplanation",
    "ProjectedRelationExplanation",
    "ProjectionAudit",
    "ProjectionContextLink",
    "ProjectionExplanation",
    "audit_projection",
]
