from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from architecture_recovery.ir import (
    ArchitectureAnalysis,
    ArchitectureHypothesis,
    ArchitectureIR,
    Edge,
    EdgeType,
    EvidenceStatus,
    Node,
    NodeType,
)

_STATUS_FACTOR = {
    EvidenceStatus.OBSERVED: 1.0,
    EvidenceStatus.INFERRED: 0.7,
    EvidenceStatus.UNCERTAIN: 0.35,
    EvidenceStatus.UNKNOWN: 0.0,
}
_LAYER_ORDER = {
    "controllers": 0, "views": 0, "api": 0, "application": 1,
    "services": 1, "domain": 1, "repositories": 2,
    "infrastructure": 2, "models": 2, "database": 3, "storage": 3,
    "cache": 3, "queue": 3, "message_broker": 3,
}
_RELATION_WEIGHT = {
    EdgeType.CALLS: 4.0,
    EdgeType.INSTANTIATES: 4.0,
    EdgeType.DEPENDS_ON: 3.0,
    EdgeType.IMPORTS: 1.5,
    EdgeType.ROUTES_TO: 3.0,
    EdgeType.QUERIES: 3.0,
}
_INFRASTRUCTURE_TYPES = {
    NodeType.DATABASE, NodeType.CACHE, NodeType.QUEUE,
    NodeType.MESSAGE_BROKER, NodeType.CONTAINER,
}


@dataclass(frozen=True)
class EvidenceContribution:
    evidence_refs: tuple[str, ...]
    weight: float
    reason: str
    status: EvidenceStatus = EvidenceStatus.OBSERVED


class EvidenceScorer:
    """Small deterministic scorer: (support - contradiction) / (total + 1)."""

    @staticmethod
    def score(
        supporting: Iterable[EvidenceContribution],
        contradicting: Iterable[EvidenceContribution],
    ) -> tuple[float, EvidenceStatus]:
        support_score = sum(item.weight * _STATUS_FACTOR[item.status] for item in supporting)
        contradiction_score = sum(item.weight * _STATUS_FACTOR[item.status] for item in contradicting)
        confidence = max(
            0.0,
            min(1.0, (support_score - contradiction_score) / (support_score + contradiction_score + 1.0)),
        )
        if support_score <= 0.0:
            status = EvidenceStatus.UNKNOWN
        elif confidence >= 0.20 and support_score > contradiction_score:
            status = EvidenceStatus.INFERRED
        else:
            status = EvidenceStatus.UNCERTAIN
        return round(confidence, 6), status


class ArchitectureHypothesisEngine:
    """Evaluate hypotheses from an existing ArchitectureIR only."""

    def infer(self, ir: ArchitectureIR) -> ArchitectureAnalysis:
        supporting, contradicting = self._layered_signals(ir)
        confidence, status = EvidenceScorer.score(supporting, contradicting)
        support_refs = _refs(supporting)
        contradiction_refs = _refs(contradicting)
        refs = sorted(set(support_refs + contradiction_refs))
        if status is EvidenceStatus.UNKNOWN:
            explanation = (
                "No evidence-bearing cross-layer relation was available; "
                "layer names alone are insufficient for Layered."
            )
        else:
            explanation = (
                f"Layered hypothesis uses {len(supporting)} supporting relation(s) "
                f"and {len(contradicting)} contradicting relation(s). "
                "Dependency direction is weighted above structural naming metadata."
            )
            if contradiction_refs:
                explanation += " Reverse or skip-layer relations were preserved as contradictory evidence."
        return ArchitectureAnalysis(
            hypotheses=[ArchitectureHypothesis(
                pattern="layered",
                status=status,
                confidence=confidence,
                supporting_evidence=support_refs,
                contradicting_evidence=contradiction_refs,
                evidence_refs=refs,
                explanation=explanation,
            )],
            metrics={
                "hypothesis_engine": "m6.2",
                "hypothesis_evidence_scoring": "(support - contradiction) / (support + contradiction + 1)",
                "layered_support_count": len(supporting),
                "layered_contradiction_count": len(contradicting),
                "layered_signal_sources": sorted({item.reason.split(":", 1)[0] for item in supporting + contradicting}),
            },
        )

    def _layered_signals(self, ir: ArchitectureIR) -> tuple[list[EvidenceContribution], list[EvidenceContribution]]:
        raw_nodes = {node.id: node for node in ir.raw_graph.nodes}
        arch_nodes = _architectural_node_index(ir, raw_nodes)
        evidence = {item.id: item for item in ir.evidence}
        roles = _role_index(ir)
        supporting: list[EvidenceContribution] = []
        contradicting: list[EvidenceContribution] = []
        seen: set[tuple[str, ...]] = set()

        for edge in sorted(ir.raw_graph.edges, key=_edge_key):
            signal = self._edge_signal(edge, raw_nodes, evidence, roles)
            if signal is None or signal.evidence_refs in seen:
                continue
            seen.add(signal.evidence_refs)
            (supporting if signal.reason.startswith("support:") else contradicting).append(signal)

        for edge in sorted(ir.architectural_graph.edges, key=_edge_key):
            signal = self._edge_signal(edge, arch_nodes, evidence, roles, architectural=True)
            if signal is None or signal.evidence_refs in seen:
                continue
            seen.add(signal.evidence_refs)
            (supporting if signal.reason.startswith("support:") else contradicting).append(signal)

        for relation in sorted(ir.infrastructure_relations, key=lambda item: (item.source, item.target, item.type, item.id)):
            source = _node_for_relation(relation.source, raw_nodes, arch_nodes, ir)
            target = _node_for_relation(relation.target, raw_nodes, arch_nodes, ir)
            if not source or not target or not _is_infrastructure_target(target):
                continue
            refs = tuple(sorted(ref for ref in relation.evidence_refs if ref in evidence))
            if not refs or source.layer not in _LAYER_ORDER:
                continue
            contribution = EvidenceContribution(refs, 3.0 * relation.confidence, f"support:infrastructure:{source.layer} -> {target.name}", relation.status)
            supporting.append(contribution)
        return supporting, contradicting

    def _edge_signal(self, edge: Edge, nodes: dict[str, Node], evidence: dict, roles: dict[str, set[str]], architectural: bool = False) -> EvidenceContribution | None:
        source, target = nodes.get(edge.source), nodes.get(edge.target)
        if not source or not target:
            return None
        source_layer = source.layer
        target_layer = target.layer
        if target.type in _INFRASTRUCTURE_TYPES and source_layer in _LAYER_ORDER:
            target_layer = target.layer or target.type.value
        if source_layer not in _LAYER_ORDER or target_layer not in _LAYER_ORDER or source_layer == target_layer:
            return None
        base = _RELATION_WEIGHT.get(edge.type)
        if base is None:
            return None
        refs = tuple(sorted(ref for ref in edge.evidence_refs if ref in evidence))
        if not refs:
            return None
        if _LAYER_ORDER[source_layer] < _LAYER_ORDER[target_layer]:
            direction = "support"
        else:
            direction = "contradiction"
        distance = abs(_LAYER_ORDER[source_layer] - _LAYER_ORDER[target_layer])
        weight = base * edge.confidence
        if edge.metadata.get("flow_evidence"):
            weight += 1.0
        if "http_entrypoint" in roles.get(edge.source, set()) or "application_entrypoint" in roles.get(edge.source, set()):
            weight += 0.5
        if direction == "contradiction" and distance > 1:
            weight *= 1.5
        origin = "architectural" if architectural else "raw"
        return EvidenceContribution(refs, weight, f"{direction}:{origin}:{source_layer} -> {target_layer} via {edge.type.value}", edge.status)


def _architectural_node_index(ir: ArchitectureIR, raw_nodes: dict[str, Node]) -> dict[str, Node]:
    index: dict[str, Node] = {}
    for node in ir.architectural_graph.nodes:
        if node.layer in _LAYER_ORDER:
            index[node.id] = node
            continue
        raw_ids = node.metadata.get("raw_node_ids", [])
        layers = [raw_nodes[item].layer for item in raw_ids if item in raw_nodes and raw_nodes[item].layer in _LAYER_ORDER]
        if layers:
            index[node.id] = node.model_copy(update={"layer": sorted(layers, key=lambda value: _LAYER_ORDER[value])[0]})
        else:
            index[node.id] = node
    return index

def _role_index(ir: ArchitectureIR) -> dict[str, set[str]]:
    roles: dict[str, set[str]] = {}
    for component in ir.component_candidates:
        for node_id in component.node_ids:
            roles.setdefault(node_id, set()).update(component.roles)
    for fact in ir.framework_facts:
        if fact.kind in {"HTTP_ENDPOINT", "APPLICATION"} and fact.subject:
            roles.setdefault(fact.subject, set()).add("http_entrypoint")
    return roles


def _node_for_relation(resource_id: str, raw_nodes: dict[str, Node], arch_nodes: dict[str, Node], ir: ArchitectureIR) -> Node | None:
    if resource_id in raw_nodes:
        return raw_nodes[resource_id]
    if resource_id in arch_nodes:
        node = arch_nodes[resource_id]
        raw_ids = node.metadata.get("raw_node_ids", [])
        layers = [raw_nodes[item].layer for item in raw_ids if item in raw_nodes and raw_nodes[item].layer in _LAYER_ORDER]
        if layers:
            return node.model_copy(update={"layer": sorted(layers, key=lambda value: _LAYER_ORDER[value])[0]})
        return node
    return None


def _is_infrastructure_target(node: Node) -> bool:
    return node.type in _INFRASTRUCTURE_TYPES or node.layer in {"database", "storage", "cache", "queue", "message_broker"}


def _edge_key(edge: Edge) -> tuple[str, str, str, str]:
    return edge.source, edge.target, edge.type.value, edge.id or ""


def _refs(contributions: Iterable[EvidenceContribution]) -> list[str]:
    return sorted({ref for item in contributions for ref in item.evidence_refs})


__all__ = ["ArchitectureHypothesisEngine", "EvidenceContribution", "EvidenceScorer"]
