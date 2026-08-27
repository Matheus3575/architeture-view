"""Bounded, semantic context propagation helpers.

The helpers deliberately separate relation validity/visual strength from its
ability to establish architectural context membership.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Iterable

from architecture_recovery.ir import EdgeType, NodeType, canonical_relation_type


class ContextPropagation(StrEnum):
    CAN_PROPAGATE_CONTEXT = "can_propagate_context"
    SUPPORTS_CONTEXT = "supports_context"
    DOES_NOT_PROPAGATE_CONTEXT = "does_not_propagate_context"


class DeploymentProvenance(StrEnum):
    EXPLICIT_EXECUTION_DEPLOYMENT = "explicit_execution_deployment"
    EXPLICIT_DEPLOYMENT_OWNERSHIP = "explicit_deployment_ownership"
    AGGREGATED_DEPLOYMENT = "aggregated_deployment"
    NAVIGATION_DERIVED = "navigation_derived"
    LOCAL_DEPLOYMENT = "local_deployment"
    UNRESOLVED = "unresolved"


class ContextStrength(StrEnum):
    STRONG = "strong"
    SUPPORTING = "supporting"
    WEAK = "weak"


_SEMANTIC_RELATIONS = {
    EdgeType.ROUTES_TO.value,
    EdgeType.QUERIES.value,
    EdgeType.PUBLISHES.value,
    EdgeType.CONSUMES.value,
    EdgeType.CONNECTS_TO.value,
    EdgeType.DEPLOYS.value,
}
_PROVENANCE_RELATIONS = {
    EdgeType.CALLS.value,
    EdgeType.INSTANTIATES.value,
    EdgeType.EXTENDS.value,
}
_SEMANTIC_RAW_RELATIONS = {
    EdgeType.CALLS,
    EdgeType.INSTANTIATES,
    EdgeType.EXTENDS,
}
_DEPLOYABLE_NODE_TYPES = {
    NodeType.CONTAINER.value,
    NodeType.DATABASE.value,
    NodeType.CACHE.value,
    NodeType.QUEUE.value,
    NodeType.MESSAGE_BROKER.value,
    NodeType.INFRASTRUCTURE.value,
    NodeType.EXTERNAL_SERVICE.value,
}


def deployment_provenance(
    relation_type: EdgeType | str,
    *,
    source_id: str | None = None,
    target_id: str | None = None,
    source_type: NodeType | str | None = None,
    target_type: NodeType | str | None = None,
    metadata: dict[str, object] | None = None,
    evidence_sources: Iterable[str] = (),
) -> DeploymentProvenance:
    """Classify deployment provenance without changing the observed relation."""

    if canonical_relation_type(relation_type) != EdgeType.DEPLOYS.value:
        return DeploymentProvenance.UNRESOLVED
    details = dict(metadata or {})
    explicit = str(details.get("deployment_provenance", "")).lower()
    explicit_values = {item.value: item for item in DeploymentProvenance}
    if explicit in explicit_values:
        return explicit_values[explicit]
    if details.get("deployment_execution_boundary") or details.get("execution_boundary"):
        return DeploymentProvenance.EXPLICIT_EXECUTION_DEPLOYMENT
    if details.get("deployment_ownership") or details.get("architectural_ownership"):
        return DeploymentProvenance.EXPLICIT_DEPLOYMENT_OWNERSHIP
    if details.get("local_deployment") or details.get("scope") == "local":
        return DeploymentProvenance.LOCAL_DEPLOYMENT

    def node_kind(value: NodeType | str | None) -> str:
        return value.value if isinstance(value, NodeType) else str(value or "").lower()

    source_kind = node_kind(source_type)
    target_kind = node_kind(target_type)
    if source_kind == NodeType.REPOSITORY.value or target_kind == NodeType.REPOSITORY.value:
        return DeploymentProvenance.NAVIGATION_DERIVED
    if (source_kind == NodeType.APPLICATION.value and target_kind in _DEPLOYABLE_NODE_TYPES) or (
        target_kind == NodeType.APPLICATION.value and source_kind in _DEPLOYABLE_NODE_TYPES
    ):
        return DeploymentProvenance.EXPLICIT_EXECUTION_DEPLOYMENT
    if source_kind == NodeType.COMPONENT.value and target_kind in _DEPLOYABLE_NODE_TYPES:
        return DeploymentProvenance.AGGREGATED_DEPLOYMENT
    if target_kind == NodeType.COMPONENT.value and source_kind in _DEPLOYABLE_NODE_TYPES:
        return DeploymentProvenance.AGGREGATED_DEPLOYMENT
    evidence_kinds = {str(value).upper() for value in evidence_sources}
    if evidence_kinds & {"DOCKERFILE", "DOCKER_COMPOSE"}:
        return DeploymentProvenance.LOCAL_DEPLOYMENT
    if (source_id and source_id.startswith("repository:")) or (target_id and target_id.startswith("repository:")):
        return DeploymentProvenance.NAVIGATION_DERIVED
    return DeploymentProvenance.UNRESOLVED


def context_propagation_kind(
    relation_type: EdgeType | str,
    *,
    raw_relation_types: Iterable[EdgeType | str] = (),
    semantic_ownership: bool = False,
    deployment_provenance: DeploymentProvenance | str | None = None,
) -> ContextPropagation:
    """Classify whether one relation can establish bounded context membership."""

    kind = canonical_relation_type(relation_type)
    if kind == EdgeType.DEPLOYS.value:
        provenance = str(deployment_provenance or "").lower()
        if provenance in {
            DeploymentProvenance.EXPLICIT_EXECUTION_DEPLOYMENT.value,
            DeploymentProvenance.EXPLICIT_DEPLOYMENT_OWNERSHIP.value,
        }:
            return ContextPropagation.CAN_PROPAGATE_CONTEXT
        if provenance in {
            DeploymentProvenance.AGGREGATED_DEPLOYMENT.value,
            DeploymentProvenance.LOCAL_DEPLOYMENT.value,
        }:
            return ContextPropagation.SUPPORTS_CONTEXT
        return ContextPropagation.DOES_NOT_PROPAGATE_CONTEXT
    if kind in _SEMANTIC_RELATIONS - {EdgeType.DEPLOYS.value}:
        return ContextPropagation.CAN_PROPAGATE_CONTEXT
    if kind in _PROVENANCE_RELATIONS:
        return ContextPropagation.SUPPORTS_CONTEXT
    if kind == EdgeType.CONTAINS.value and semantic_ownership:
        return ContextPropagation.CAN_PROPAGATE_CONTEXT
    # A generic DEPENDS_ON is retained as a valid relation, but only an
    # attached observed call/instantiation/extension provenance can make it
    # context-supporting. Weak aggregation alone never propagates context.
    if kind == EdgeType.DEPENDS_ON.value:
        raw_kinds = {canonical_relation_type(item) for item in raw_relation_types}
        if raw_kinds & {item.value for item in _SEMANTIC_RAW_RELATIONS}:
            return ContextPropagation.SUPPORTS_CONTEXT
    return ContextPropagation.DOES_NOT_PROPAGATE_CONTEXT


def context_direction_pairs(
    source: str,
    target: str,
    relation_type: EdgeType | str,
) -> tuple[tuple[str, str], ...]:
    """Return bounded propagation directions for a relation.

    Existing semantic relations are treated as associative context links by
    the projection policy. Deployment is directional: an application deploys
    to a runtime boundary, and the reverse edge must not establish application
    membership merely because the relation is otherwise valid.
    """

    if canonical_relation_type(relation_type) == EdgeType.DEPLOYS.value:
        return ((source, target),)
    return ((source, target), (target, source))

def context_strength(propagation: ContextPropagation) -> ContextStrength:
    if propagation == ContextPropagation.CAN_PROPAGATE_CONTEXT:
        return ContextStrength.STRONG
    if propagation == ContextPropagation.SUPPORTS_CONTEXT:
        return ContextStrength.SUPPORTING
    return ContextStrength.WEAK


def is_navigation_root(node_type: NodeType) -> bool:
    return node_type == NodeType.REPOSITORY


__all__ = [
    "ContextPropagation",
    "ContextStrength",
    "DeploymentProvenance",
    "context_propagation_kind",
    "context_direction_pairs",
    "context_strength",
    "deployment_provenance",
    "is_navigation_root",
]
