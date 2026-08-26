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


def context_propagation_kind(
    relation_type: EdgeType | str,
    *,
    raw_relation_types: Iterable[EdgeType | str] = (),
    semantic_ownership: bool = False,
) -> ContextPropagation:
    """Classify whether one relation can establish bounded context membership."""

    kind = canonical_relation_type(relation_type)
    if kind in _SEMANTIC_RELATIONS:
        return ContextPropagation.CAN_PROPAGATE_CONTEXT
    if kind in _PROVENANCE_RELATIONS:
        return ContextPropagation.SUPPORTS_CONTEXT
    if kind == EdgeType.CONTAINS.value and semantic_ownership:
        return ContextPropagation.CAN_PROPAGATE_CONTEXT
    # A generic DEPENDS_ON is retained as a valid relation, but only an
    # attached observed call/instantiation/extension provenance can make it
    # context-supporting.  Weak aggregation alone never propagates context.
    if kind == EdgeType.DEPENDS_ON.value:
        raw_kinds = {canonical_relation_type(item) for item in raw_relation_types}
        if raw_kinds & {item.value for item in _SEMANTIC_RAW_RELATIONS}:
            return ContextPropagation.SUPPORTS_CONTEXT
    return ContextPropagation.DOES_NOT_PROPAGATE_CONTEXT


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
    "context_propagation_kind",
    "context_strength",
    "is_navigation_root",
]
