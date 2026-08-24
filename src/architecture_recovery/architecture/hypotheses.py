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
    "controllers": 0, "views": 0, "api": 0, "adapters": 0,
    "presentation": 0, "application": 1, "services": 1, "domain": 1,
    "ports": 1, "repositories": 2, "infrastructure": 2, "models": 2,
    "database": 3, "storage": 3, "cache": 3, "queue": 3,
    "message_broker": 3,
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
_MVC_CONTROLLER_LAYERS = {"controllers", "api"}
_MVC_MODEL_LAYERS = {"models", "domain"}
_MVC_PERSISTENCE_LAYERS = {"repositories", "infrastructure", "database", "storage"}
_MVC_VIEW_LAYERS = {"views"}
_HEX_INPUT_LAYERS = {"controllers", "api", "adapters", "presentation", "views"}
_HEX_CORE_LAYERS = {"application", "services", "domain"}
_HEX_PORT_LAYERS = {"ports"}
_HEX_OUTPUT_LAYERS = {"adapters", "repositories", "infrastructure"}
_HEX_INFRASTRUCTURE_TYPES = _INFRASTRUCTURE_TYPES | {
    NodeType.EXTERNAL_SERVICE,
    NodeType.EXTERNAL_DEPENDENCY,
}
_HEX_PORT_EDGE_TYPES = {
    EdgeType.IMPORTS,
    EdgeType.DEPENDS_ON,
    EdgeType.CALLS,
    EdgeType.INSTANTIATES,
    EdgeType.IMPLEMENTS,
    EdgeType.EXTENDS,
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
        layered_supporting, layered_contradicting = self._layered_signals(ir)
        layered = self._hypothesis("layered", layered_supporting, layered_contradicting, "Layered", "cross-layer relation", "layer names alone are insufficient")
        mvc_supporting, mvc_contradicting = self._mvc_signals(ir)
        mvc = self._hypothesis("mvc", mvc_supporting, mvc_contradicting, "MVC", "semantic MVC relation", "controller/model/persistence evidence is insufficient")
        hexagonal_supporting, hexagonal_contradicting = self._hexagonal_signals(ir)
        hexagonal = self._hypothesis(
            "hexagonal",
            hexagonal_supporting,
            hexagonal_contradicting,
            "Hexagonal",
            "semantic ports-and-adapters relation",
            "ports, adapters and directional boundaries are insufficient",
            minimum_support_categories=2,
        )
        return ArchitectureAnalysis(
            hypotheses=[layered, mvc, hexagonal],
            metrics={
                "hypothesis_engine": "m6.5",
                "hypothesis_evidence_scoring": "(support - contradiction) / (support + contradiction + 1)",
                "layered_support_count": len(layered_supporting),
                "layered_contradiction_count": len(layered_contradicting),
                "layered_signal_sources": sorted({item.reason.split(":", 1)[0] for item in layered_supporting + layered_contradicting}),
                "mvc_support_count": len(mvc_supporting),
                "mvc_contradiction_count": len(mvc_contradicting),
                "mvc_signal_sources": sorted({item.reason.split(":", 1)[0] for item in mvc_supporting + mvc_contradicting}),
                "hexagonal_support_count": len(hexagonal_supporting),
                "hexagonal_contradiction_count": len(hexagonal_contradicting),
                "hexagonal_signal_sources": sorted({item.reason.split(":", 1)[0] for item in hexagonal_supporting + hexagonal_contradicting}),
            },
        )

    @staticmethod
    def _hypothesis(
        pattern,
        supporting,
        contradicting,
        label,
        relation_label,
        unknown_detail,
        minimum_support_categories=0,
    ):
        confidence, status = EvidenceScorer.score(supporting, contradicting)
        categories = {
            item.reason.split(":", 2)[1]
            for item in supporting
            if item.reason.startswith("support:") and ":" in item.reason
        }
        if minimum_support_categories and len(categories) < minimum_support_categories:
            confidence, status = 0.0, EvidenceStatus.UNKNOWN
        support_refs = _refs(supporting)
        contradiction_refs = _refs(contradicting)
        if status is EvidenceStatus.UNKNOWN:
            explanation = f"No evidence-bearing {relation_label} was available; {unknown_detail}."
        else:
            explanation = f"{label} hypothesis uses {len(supporting)} supporting relation(s) and {len(contradicting)} contradicting relation(s)."
            if contradiction_refs:
                explanation += " Contradicting evidence was preserved."
        return ArchitectureHypothesis(pattern=pattern, status=status, confidence=confidence, supporting_evidence=support_refs, contradicting_evidence=contradiction_refs, evidence_refs=sorted(set(support_refs + contradiction_refs)), explanation=explanation)

    def _hexagonal_signals(self, ir: ArchitectureIR):
        """Collect bounded ports-and-adapters signals from the existing IR."""
        raw_nodes = {node.id: node for node in ir.raw_graph.nodes}
        arch_nodes = _architectural_node_index(ir, raw_nodes)
        evidence = {item.id: item for item in ir.evidence}
        roles = _role_index(ir)
        supporting: list[EvidenceContribution] = []
        contradicting: list[EvidenceContribution] = []
        seen: set[tuple[str, ...]] = set()

        edges = [
            *sorted(ir.raw_graph.edges, key=_edge_key),
            *sorted(ir.architectural_graph.edges, key=_edge_key),
        ]
        port_ids = {
            edge.target
            for edge in edges
            if (
                edge.type in {EdgeType.IMPLEMENTS, EdgeType.EXTENDS}
                and self._hex_is_output(
                    _node_for_relation(edge.source, raw_nodes, arch_nodes, None)
                )
            )
        }
        port_ids.update(
            node.id
            for node in [*raw_nodes.values(), *arch_nodes.values()]
            if node.type == NodeType.INTERFACE or node.layer in _HEX_PORT_LAYERS
        )
        for edge in edges:
            signal = self._hexagonal_edge_signal(
                edge, raw_nodes, arch_nodes, evidence, roles, port_ids
            )
            if signal is None or signal.evidence_refs in seen:
                continue
            seen.add(signal.evidence_refs)
            (supporting if signal.reason.startswith("support:") else contradicting).append(signal)

        for fact in sorted(
            ir.framework_facts,
            key=lambda item: (item.kind, item.subject or "", item.target or ""),
        ):
            if fact.kind not in {"HTTP_ENDPOINT", "CONTROLLER_LIKE", "ROUTER", "ROUTER_INCLUSION"}:
                continue
            subject = _node_for_relation(fact.subject or "", raw_nodes, arch_nodes, ir)
            refs = tuple(sorted(ref for ref in fact.evidence_refs if ref in evidence))
            if not subject or not refs or refs in seen:
                continue
            if self._hex_is_input(subject, roles, fact.kind):
                seen.add(refs)
                supporting.append(EvidenceContribution(
                    refs,
                    2.0 * fact.confidence,
                    f"support:input_boundary:framework {fact.kind.lower()}",
                    fact.status,
                ))
        support_categories = {
            item.reason.split(":", 2)[1]
            for item in supporting
            if item.reason.startswith("support:") and ":" in item.reason
        }
        if len(support_categories) < 2:
            supporting = []
        return supporting, contradicting

    @classmethod
    def _hexagonal_edge_signal(cls, edge, raw_nodes, arch_nodes, evidence, roles, port_ids):
        source = _node_for_relation(edge.source, raw_nodes, arch_nodes, None)
        target = _node_for_relation(edge.target, raw_nodes, arch_nodes, None)
        if not source or not target:
            return None
        refs = tuple(sorted(ref for ref in edge.evidence_refs if ref in evidence))
        if not refs:
            return None
        source_layer = source.layer
        target_layer = target.layer
        relation = edge.type
        if cls._hex_is_input(source, roles) and cls._hex_is_core(target):
            return EvidenceContribution(
                refs, 3.5 * edge.confidence,
                f"support:input_boundary:{source_layer} -> {target_layer} via {relation.value}",
                edge.status,
            )
        if cls._hex_is_core(source) and cls._hex_is_port(target, port_ids) and relation in _HEX_PORT_EDGE_TYPES:
            return EvidenceContribution(
                refs, 3.5 * edge.confidence,
                f"support:port_dependency:{source_layer} -> port via {relation.value}",
                edge.status,
            )
        if cls._hex_is_output(source) and cls._hex_is_port(target, port_ids) and relation in {
            EdgeType.IMPLEMENTS, EdgeType.EXTENDS, EdgeType.DEPENDS_ON, EdgeType.IMPORTS,
        }:
            return EvidenceContribution(
                refs, 4.0 * edge.confidence,
                f"support:adapter_implementation:{source_layer} -> port via {relation.value}",
                edge.status,
            )
        if cls._hex_is_core(source) and cls._hex_is_concrete_infrastructure(target):
            return EvidenceContribution(
                refs, 4.5 * edge.confidence,
                f"contradiction:core_to_concrete_infrastructure:{source_layer} -> {target.type.value} via {relation.value}",
                edge.status,
            )
        return None

    @staticmethod
    def _hex_is_input(node: Node, roles: dict[str, set[str]], fact_kind: str | None = None) -> bool:
        return (
            node.layer in _HEX_INPUT_LAYERS
            or bool(roles.get(node.id, set()) & {"http_entrypoint", "controller_like"})
            or fact_kind in {"HTTP_ENDPOINT", "CONTROLLER_LIKE", "ROUTER"}
        )

    @staticmethod
    def _hex_is_core(node: Node) -> bool:
        return node.layer in _HEX_CORE_LAYERS

    @staticmethod
    def _hex_is_port(node: Node | None, port_ids: set[str]) -> bool:
        return bool(node) and (node.id in port_ids or node.layer in _HEX_PORT_LAYERS or node.type == NodeType.INTERFACE)

    @staticmethod
    def _hex_is_output(node: Node | None) -> bool:
        return bool(node) and node.layer in _HEX_OUTPUT_LAYERS

    @staticmethod
    def _hex_is_concrete_infrastructure(node: Node) -> bool:
        return node.type in _HEX_INFRASTRUCTURE_TYPES or node.layer in {
            "database", "storage", "cache", "queue", "message_broker", "infrastructure"
        }

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

    def _mvc_signals(self, ir: ArchitectureIR):
        raw_nodes = {node.id: node for node in ir.raw_graph.nodes}
        arch_nodes = _architectural_node_index(ir, raw_nodes)
        evidence = {item.id: item for item in ir.evidence}
        mvc_layers = _mvc_layer_index(raw_nodes, arch_nodes)
        supporting, contradicting, seen = [], [], set()
        edges = [*sorted(ir.raw_graph.edges, key=_edge_key), *sorted(ir.architectural_graph.edges, key=_edge_key)]
        for edge in edges:
            signal = self._mvc_edge_signal(edge, raw_nodes, arch_nodes, evidence, mvc_layers)
            if signal is None or signal.evidence_refs in seen:
                continue
            seen.add(signal.evidence_refs)
            (supporting if signal.reason.startswith("support:") else contradicting).append(signal)
        for fact in sorted(ir.framework_facts, key=lambda item: (item.kind, item.subject or "", item.target or "")):
            if fact.kind not in {"HTTP_ENDPOINT", "CONTROLLER_LIKE", "ROUTER", "ROUTER_INCLUSION"}:
                continue
            subject = _node_for_relation(fact.subject or "", raw_nodes, arch_nodes, ir)
            refs = tuple(sorted(ref for ref in fact.evidence_refs if ref in evidence))
            if (
                subject
                and refs
                and (
                    mvc_layers.get(subject.id) in _MVC_CONTROLLER_LAYERS
                    or fact.kind == "CONTROLLER_LIKE"
                )
                and refs not in seen
            ):
                seen.add(refs)
                supporting.append(EvidenceContribution(
                    refs,
                    3.0 * fact.confidence,
                    f"support:mvc:{fact.kind.lower()} -> controller",
                    fact.status,
                ))
        return supporting, contradicting

    @staticmethod
    def _mvc_edge_signal(edge, raw_nodes, arch_nodes, evidence, mvc_layers):
        source = _node_for_relation(edge.source, raw_nodes, arch_nodes, None)
        target = _node_for_relation(edge.target, raw_nodes, arch_nodes, None)
        if not source or not target:
            return None
        refs = tuple(sorted(ref for ref in edge.evidence_refs if ref in evidence))
        if not refs:
            return None
        source_layer = mvc_layers.get(source.id)
        target_layer = mvc_layers.get(target.id)
        if source_layer in _MVC_CONTROLLER_LAYERS and target_layer in _MVC_MODEL_LAYERS:
            return EvidenceContribution(refs, 4.0 * edge.confidence, f"support:mvc:controller -> model via {edge.type.value}", edge.status)
        if source_layer in _MVC_CONTROLLER_LAYERS and target_layer in _MVC_VIEW_LAYERS:
            return EvidenceContribution(refs, 2.0 * edge.confidence, f"support:mvc:controller -> view via {edge.type.value}", edge.status)
        if source_layer in _MVC_MODEL_LAYERS and target_layer in _MVC_PERSISTENCE_LAYERS:
            return EvidenceContribution(refs, 4.0 * edge.confidence, f"support:mvc:model -> persistence via {edge.type.value}", edge.status)
        if source_layer in _MVC_CONTROLLER_LAYERS and target_layer in _MVC_PERSISTENCE_LAYERS:
            return EvidenceContribution(refs, 4.0 * edge.confidence, f"contradiction:mvc:controller -> persistence via {edge.type.value}", edge.status)
        if source_layer in _MVC_PERSISTENCE_LAYERS and target_layer in _MVC_CONTROLLER_LAYERS:
            return EvidenceContribution(refs, 4.0 * edge.confidence, f"contradiction:mvc:persistence -> controller via {edge.type.value}", edge.status)
        return None

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


def _mvc_layer_index(raw_nodes: dict[str, Node], arch_nodes: dict[str, Node]) -> dict[str, str]:
    layers = {node_id: node.layer for node_id, node in raw_nodes.items() if node.layer}
    path_layers: dict[str, list[str]] = {}
    for node in raw_nodes.values():
        if node.layer and node.source:
            path_layers.setdefault(node.source.path, []).append(node.layer)
    for node_id, node in raw_nodes.items():
        if node.layer:
            continue
        if node.source and node.source.path in path_layers:
            layers[node_id] = sorted(path_layers[node.source.path], key=lambda item: (_LAYER_ORDER.get(item, 99), item))[0]
            continue
        lookup_id = node_id.removeprefix("module:")
        parts = lookup_id.split(".")
        for end in range(len(parts) - 1, 0, -1):
            prefix = ".".join(parts[:end])
            if prefix in layers:
                layers[node_id] = layers[prefix]
                break
    for node_id, node in arch_nodes.items():
        if node.layer:
            layers[node_id] = node.layer
            continue
        candidates = [layers[item] for item in node.metadata.get("raw_node_ids", []) if item in layers]
        if candidates:
            layers[node_id] = sorted(candidates, key=lambda item: (_LAYER_ORDER.get(item, 99), item))[0]
    return layers


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
        if fact.kind == "CONTROLLER_LIKE" and fact.subject:
            roles.setdefault(fact.subject, set()).add("controller_like")
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
