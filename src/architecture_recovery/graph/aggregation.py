from __future__ import annotations

import hashlib
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from architecture_recovery.graph.builder import PropertyGraph
from architecture_recovery.ir import (
    Component,
    Edge,
    EdgeType,
    Evidence,
    EvidenceSource,
    EvidenceStatus,
    Node,
    NodeType,
    SourceOrigin,
    SourceRef,
)
from architecture_recovery.scanner import RepositorySnapshot


@dataclass(frozen=True)
class GraphAggregationConfig:
    include_standard_library: bool = False
    include_unknown: bool = True
    include_generated: bool = True


@dataclass
class AggregatedArchitecture:
    nodes: dict[str, Node]
    edges: list[Edge]
    evidence: dict[str, Evidence]
    components: list[Component]


class ArchitecturalGraphBuilder:
    """Collapse observed code into repository, component, and dependency nodes."""

    def __init__(self, config: GraphAggregationConfig | None = None) -> None:
        self.config = config or GraphAggregationConfig()

    def build(self, raw: PropertyGraph, snapshot: RepositorySnapshot) -> AggregatedArchitecture:
        evidence = dict(raw.evidence)
        nodes: dict[str, Node] = {}
        node_mapping: dict[str, str | None] = {}
        component_members: dict[str, list[str]] = defaultdict(list)

        repository_nodes = [node for node in raw.nodes.values() if node.type == NodeType.REPOSITORY]
        repository = repository_nodes[0] if repository_nodes else Node(
            id=f"repository:{snapshot.root.name}",
            type=NodeType.REPOSITORY,
            name=snapshot.root.name,
            origin=SourceOrigin.FIRST_PARTY,
        )
        nodes[repository.id] = repository
        application_id = f"application:{snapshot.root.name}"
        application_members = [
            node.id
            for node in raw.nodes.values()
            if node.origin in {SourceOrigin.FIRST_PARTY, SourceOrigin.GENERATED}
            and node.type != NodeType.REPOSITORY
        ]
        application_evidence = self._add_evidence(
            evidence,
            "application",
            f"Application boundary for repository {snapshot.root.name}",
            application_members,
            raw,
        )
        nodes[application_id] = Node(
            id=application_id,
            type=NodeType.APPLICATION,
            name=snapshot.root.name,
            origin=SourceOrigin.FIRST_PARTY,
            status=EvidenceStatus.INFERRED,
            confidence=0.8,
            evidence_refs=[application_evidence.id],
            metadata={
                "raw_node_ids": application_members,
                "application_provenance": "repository_aggregate",
                "boundary_evidence_kind": "repository_membership",
                "architectural_boundary": False,
            },
        )
        for node in raw.nodes.values():
            if node.type == NodeType.REPOSITORY:
                node_mapping[node.id] = repository.id
                continue
            aggregate_id = self._aggregate_id(node)
            if aggregate_id is None:
                node_mapping[node.id] = None
                continue
            node_mapping[node.id] = aggregate_id
            component_members[aggregate_id].append(node.id)

        for aggregate_id, raw_node_ids in sorted(component_members.items()):
            representative = raw.nodes[raw_node_ids[0]]
            is_infrastructure = representative.type in {
                NodeType.CONTAINER,
                NodeType.DATABASE,
                NodeType.CACHE,
                NodeType.QUEUE,
                NodeType.MESSAGE_BROKER,
            }
            is_external = representative.origin in {
                SourceOrigin.THIRD_PARTY,
                SourceOrigin.STANDARD_LIBRARY,
                SourceOrigin.UNKNOWN,
            } and not is_infrastructure
            if is_infrastructure:
                name = representative.name
                node_type = representative.type
                status = representative.status
                confidence = representative.confidence
                origin = representative.origin
                level = "infrastructure"
            elif is_external:
                package = representative.metadata.get("external_package")
                name = representative.name if package else aggregate_id.removeprefix("external.")
                node_type = NodeType.EXTERNAL_DEPENDENCY
                status = EvidenceStatus.OBSERVED
                confidence = representative.confidence
                origin = representative.origin
                level = "external_dependency"
            else:
                name = aggregate_id.removeprefix("component:")
                node_type = NodeType.COMPONENT
                status = EvidenceStatus.INFERRED
                confidence = 0.75
                origin = representative.origin
                level = "component"
            aggregate_evidence = self._add_evidence(
                evidence,
                aggregate_id,
                f"Aggregated {len(raw_node_ids)} raw nodes into {name}",
                raw_node_ids,
                raw,
            )
            nodes[aggregate_id] = Node(
                id=aggregate_id,
                type=node_type,
                name=name,
                origin=origin,
                status=status,
                confidence=confidence,
                evidence_refs=[aggregate_evidence.id, *self._node_evidence(raw, raw_node_ids)],
                metadata={
                    "raw_node_ids": sorted(raw_node_ids),
                    "level": level,
                    "external_package": representative.metadata.get("external_package") if is_external else None,
                },
            )

        edges = self._hierarchy_edges(
            repository,
            nodes[application_id],
            nodes,
            component_members,
            raw,
            evidence,
            application_evidence.id,
        )
        edges.extend(self._aggregate_edges(raw, node_mapping, evidence))
        components = [
            Component(
                id=node_id,
                name=node.name,
                level=str(node.metadata.get("level", "component")),
                node_ids=sorted(raw_ids),
                confidence=node.confidence,
                status=node.status,
                evidence_refs=list(node.evidence_refs),
            )
            for node_id, raw_ids in sorted(component_members.items())
            if nodes[node_id].type == NodeType.COMPONENT
        ]
        return AggregatedArchitecture(nodes=nodes, edges=edges, evidence=evidence, components=components)

    def _aggregate_id(self, node: Node) -> str | None:
        if node.origin == SourceOrigin.STANDARD_LIBRARY and not self.config.include_standard_library:
            return None
        if node.origin == SourceOrigin.UNKNOWN and not self.config.include_unknown:
            return None
        if node.origin == SourceOrigin.GENERATED and not self.config.include_generated:
            return None
        if node.origin in {
            SourceOrigin.THIRD_PARTY,
            SourceOrigin.STANDARD_LIBRARY,
            SourceOrigin.UNKNOWN,
        }:
            package = node.metadata.get("external_package")
            if package:
                return f"external.{package}"
            if node.source:
                path_parts = Path(node.source.path).parts
                if path_parts:
                    return f"external.{path_parts[0]}"
            return f"external.unknown.{node.id.replace(':', '.')}"
        if node.source:
            return f"component:{self._component_key(node.source.path)}"
        return "component:unknown"

    @staticmethod
    def _component_key(path: str) -> str:
        parts = [part for part in Path(path).parts if part not in {".", ""}]
        if not parts:
            return "root"
        if parts[0] in {"src", "lib", "packages", "apps"} and len(parts) > 1:
            return parts[1]
        return parts[0]

    def _hierarchy_edges(self, repository, application, nodes, members, raw, evidence, application_evidence_id):
        edges = [
            self._inferred_edge(
                repository.id,
                application.id,
                EdgeType.CONTAINS,
                [application_evidence_id],
                self._raw_ids_for_nodes(raw, members),
            )
        ]
        for component_id, raw_node_ids in sorted(members.items()):
            if component_id not in nodes or nodes[component_id].type == NodeType.EXTERNAL_DEPENDENCY:
                continue
            raw_edge_ids = self._raw_ids_for_node_group(raw, raw_node_ids)
            evidence_id = self._add_evidence(
                evidence,
                f"hierarchy:{component_id}",
                f"Application contains structural component {nodes[component_id].name}",
                raw_node_ids,
                raw,
            ).id
            edges.append(
                self._inferred_edge(application.id, component_id, EdgeType.CONTAINS, [evidence_id], raw_edge_ids, metadata={"ownership_kind": "structural", "ownership_source": "repository_aggregation"})
            )
        return edges

    def _aggregate_edges(self, raw, node_mapping, evidence):
        grouped: dict[tuple[str, str, EdgeType], dict[str, list[str]]] = {}
        for raw_edge in raw.edges:
            if raw_edge.type == EdgeType.CONTAINS:
                continue
            source = node_mapping.get(raw_edge.source)
            target = node_mapping.get(raw_edge.target)
            if not source or not target or source == target:
                continue
            edge_type = raw_edge.type if raw_edge.type in {EdgeType.DEPLOYS, EdgeType.CONNECTS_TO} else EdgeType.DEPENDS_ON
            key = (source, target, edge_type)
            item = grouped.setdefault(key, {"raw_edge_ids": [], "evidence_refs": []})
            if raw_edge.id:
                item["raw_edge_ids"].append(raw_edge.id)
            item["evidence_refs"].extend(raw_edge.evidence_refs)
        result = []
        for (source, target, edge_type), item in sorted(grouped.items()):
            aggregation_evidence = Evidence(
                id=self._stable_id("aggregation", source, target, edge_type.value),
                source_type=EvidenceSource.GRAPH_AGGREGATION,
                detail=f"Aggregated raw relations into {source} {edge_type.value} {target}",
                source=SourceRef(path="architecture-graph"),
            )
            evidence[aggregation_evidence.id] = aggregation_evidence
            result.append(
                self._inferred_edge(
                    source,
                    target,
                    edge_type,
                    [aggregation_evidence.id, *sorted(set(item["evidence_refs"]))],
                    sorted(set(item["raw_edge_ids"])),
                )
            )
        return result

    @staticmethod
    def _inferred_edge(source, target, edge_type, evidence_refs, raw_edge_ids, metadata=None):
        token = f"{source}:{target}:{edge_type.value}".encode()
        return Edge(
            id=f"arch-edge:{hashlib.sha1(token).hexdigest()[:16]}",
            source=source,
            target=target,
            type=edge_type,
            status=EvidenceStatus.INFERRED,
            confidence=0.97 if raw_edge_ids else 0.8,
            evidence_refs=sorted(set(evidence_refs)),
            raw_edge_ids=sorted(set(raw_edge_ids)),
            metadata=dict(metadata or {}),
        )

    @staticmethod
    def _stable_id(*parts: str) -> str:
        return f"evidence:{hashlib.sha1(':'.join(parts).encode()).hexdigest()[:16]}"

    def _add_evidence(self, evidence, key, detail, raw_node_ids, raw):
        item = Evidence(
            id=self._stable_id("aggregation", key),
            source_type=EvidenceSource.GRAPH_AGGREGATION,
            detail=detail,
            source=SourceRef(path="architecture-graph", symbol=key),
        )
        evidence[item.id] = item
        return item

    @staticmethod
    def _node_evidence(raw, node_ids):
        refs = []
        for node_id in node_ids:
            refs.extend(raw.nodes[node_id].evidence_refs)
        return sorted(set(refs))

    @staticmethod
    def _raw_ids_for_node_group(raw, node_ids):
        ids = []
        members = set(node_ids)
        for edge in raw.edges:
            if edge.source in members or edge.target in members:
                if edge.id:
                    ids.append(edge.id)
        return sorted(set(ids))

    def _raw_ids_for_nodes(self, raw, members_for_application):
        return self._raw_ids_for_node_group(
            raw,
            [node_id for values in members_for_application.values() for node_id in values],
        )
