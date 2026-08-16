from __future__ import annotations

from pathlib import Path

import yaml

from architecture_recovery.graph.builder import PropertyGraph
from architecture_recovery.ir import Edge, EdgeType, Evidence, EvidenceSource, Node, NodeType, SourceRef
from architecture_recovery.scanner import FileKind, RepositorySnapshot


class InfrastructureAnalyzer:
    """Extract deployable services and explicit Compose relationships."""

    def augment(self, graph: PropertyGraph, snapshot: RepositorySnapshot) -> None:
        repository_id = f"repository:{snapshot.root.name}"
        for file in snapshot.by_kind(FileKind.INFRASTRUCTURE):
            name = Path(file.path).name.lower()
            if name in {"docker-compose.yml", "docker-compose.yaml", "compose.yml", "compose.yaml"}:
                self._compose(graph, file.path, file.absolute_path, repository_id)
            elif name == "dockerfile":
                self._dockerfile(graph, file.path, repository_id)

    def _dockerfile(self, graph, path: str, repository_id: str) -> None:
        evidence = self._evidence(graph, EvidenceSource.DOCKERFILE, path, "Dockerfile deployable unit")
        node_id = f"container:{path}"
        graph.add_node(Node(id=node_id, type=NodeType.CONTAINER, name=path, source=SourceRef(path=path), evidence_refs=[evidence.id]))
        graph.add_edge(Edge(source=repository_id, target=node_id, type=EdgeType.DEPLOYS, evidence_refs=[evidence.id]))

    def _compose(self, graph, path: str, absolute_path: Path, repository_id: str) -> None:
        try:
            document = yaml.safe_load(absolute_path.read_text(encoding="utf-8")) or {}
        except (OSError, yaml.YAMLError):
            return
        services = document.get("services", {})
        if not isinstance(services, dict):
            return
        service_ids = {}
        for name, config in sorted(services.items()):
            evidence = self._evidence(graph, EvidenceSource.DOCKER_COMPOSE, path, f"Compose service {name}")
            node_id = f"container:{name}"
            service_ids[name] = node_id
            graph.add_node(Node(id=node_id, type=self._service_type(config), name=name, source=SourceRef(path=path, symbol=f"services.{name}"), evidence_refs=[evidence.id]))
            graph.add_edge(Edge(source=repository_id, target=node_id, type=EdgeType.DEPLOYS, evidence_refs=[evidence.id]))

        for name, config in sorted(services.items()):
            dependencies = config.get("depends_on", []) if isinstance(config, dict) else []
            if isinstance(dependencies, dict):
                dependencies = dependencies.keys()
            elif isinstance(dependencies, str):
                dependencies = [dependencies]
            elif not isinstance(dependencies, (list, tuple, set)):
                dependencies = []
            for dependency in dependencies:
                if dependency in service_ids:
                    evidence = self._evidence(graph, EvidenceSource.DOCKER_COMPOSE, path, f"{name} depends on {dependency}")
                    graph.add_edge(Edge(source=service_ids[name], target=service_ids[dependency], type=EdgeType.CONNECTS_TO, evidence_refs=[evidence.id]))

    @staticmethod
    def _service_type(config) -> NodeType:
        image = str(config.get("image", "")).lower() if isinstance(config, dict) else ""
        if any(value in image for value in ("postgres", "mysql", "mariadb", "mongo")):
            return NodeType.DATABASE
        if "redis" in image or "memcached" in image:
            return NodeType.CACHE
        if any(value in image for value in ("rabbitmq", "kafka", "nats")):
            return NodeType.MESSAGE_BROKER
        return NodeType.CONTAINER

    @staticmethod
    def _evidence(graph, source_type, path, detail):
        evidence_id = f"evidence:{source_type.value.lower()}:{path}:{len(graph.evidence)}"
        evidence = Evidence(id=evidence_id, source_type=source_type, detail=detail, source=SourceRef(path=path))
        graph.add_evidence(evidence)
        return evidence
