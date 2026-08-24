from __future__ import annotations

import re
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import yaml

from architecture_recovery.graph.builder import PropertyGraph
from architecture_recovery.ir import (
    Component,
    Edge,
    EdgeType,
    Evidence,
    EvidenceSource,
    EvidenceStatus,
    InfrastructureRelation,
    InfrastructureResource,
    Node,
    NodeType,
    SourceOrigin,
    SourceRef,
)
from architecture_recovery.parsing import ParseFacts
from architecture_recovery.scanner import FileKind, RepositorySnapshot

from .base import (
    InfrastructureAdapter,
    InfrastructureAnalysisContext,
    InfrastructureAnalysisResult,
)


def parse_environment(env_config: Any) -> dict[str, str]:
    if isinstance(env_config, dict):
        return {str(key): "" if value is None else str(value) for key, value in env_config.items()}
    if isinstance(env_config, list):
        values: dict[str, str] = {}
        for item in env_config:
            if isinstance(item, str) and "=" in item:
                key, value = item.split("=", 1)
                values[key.strip()] = value.strip()
        return values
    return {}


def parse_dockerfile(content: str) -> dict[str, Any]:
    metadata: dict[str, Any] = {
        "from": None,
        "expose": [],
        "env": {},
        "workdir": None,
        "copy": [],
        "entrypoint": None,
        "cmd": None,
    }
    for raw_line in content.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        instruction, _, value = line.partition(" ")
        if not value:
            continue
        instruction = instruction.upper()
        value = value.strip()
        if instruction == "FROM":
            metadata["from"] = value.split()[0]
        elif instruction == "EXPOSE":
            metadata["expose"].extend(value.split())
        elif instruction == "ENV":
            parts = value.split()
            if len(parts) == 1 and "=" in parts[0]:
                key, env_value = parts[0].split("=", 1)
                metadata["env"][key] = env_value
            elif len(parts) >= 2:
                metadata["env"][parts[0]] = " ".join(parts[1:])
        elif instruction == "WORKDIR":
            metadata["workdir"] = value
        elif instruction == "COPY":
            metadata["copy"].append(value)
        elif instruction == "ENTRYPOINT":
            metadata["entrypoint"] = value
        elif instruction == "CMD":
            metadata["cmd"] = value
    return metadata


def classify_service(name: str, config: Any) -> tuple[str, float]:
    config = config if isinstance(config, dict) else {}
    image = str(config.get("image", "")).lower()
    service_name = name.lower()
    database_terms = ("postgres", "postgresql", "mysql", "mariadb", "mongo", "mongodb")
    cache_terms = ("redis", "memcached")
    broker_terms = ("rabbitmq", "kafka", "nats", "activemq")

    if any(term in image for term in database_terms):
        return "DATABASE", 1.0
    if any(term in image for term in cache_terms):
        return "CACHE", 1.0
    if any(term in image for term in broker_terms):
        return "MESSAGE_BROKER", 1.0
    if any(term in service_name for term in database_terms):
        return "DATABASE", 0.8
    if any(term in service_name for term in cache_terms):
        return "CACHE", 0.8
    if any(term in service_name for term in broker_terms):
        return "MESSAGE_BROKER", 0.8
    if service_name in {"db", "database", "cache", "broker", "queue", "message"}:
        return "UNKNOWN", 0.5
    if config.get("build") or config.get("image"):
        return "CONTAINER", 0.7
    return "UNKNOWN", 0.0


def find_referenced_service(value: str, services: set[str]) -> str | None:
    text = str(value).strip()
    if not text:
        return None
    if "://" in text:
        try:
            host = urlparse(text).hostname
        except ValueError:
            host = None
        return host.lower() if host and host.lower() in services else None
    return text.lower() if text.lower() in services else None


def extract_env_var_accesses(
    parsed_files: tuple[ParseFacts, ...],
) -> list[tuple[str, str, SourceRef]]:
    accesses: list[tuple[str, str, SourceRef]] = []
    for parsed in parsed_files:
        for call in parsed.calls:
            if call.callee not in {"os.getenv", "getenv", "os.environ.get", "environ.get"}:
                continue
            if not call.arguments:
                continue
            argument = call.arguments[0].strip()
            if not re.fullmatch(r"[A-Z][A-Z0-9_]*", argument):
                continue
            accesses.append(
                (
                    parsed.module_name,
                    argument,
                    SourceRef(path=parsed.path, start_line=call.line),
                )
            )
        for assignment in parsed.assignments:
            match = re.search(r'environ\[[^]]+\]', assignment.value)
            if match:
                raw_name = match.group(0)[len("environ["):-1].strip()
                if len(raw_name) >= 2 and ord(raw_name[0]) in (39, 34) and raw_name[-1] == raw_name[0]:
                    accesses.append(
                        (
                            parsed.module_name,
                            raw_name[1:-1],
                            SourceRef(path=parsed.path, start_line=assignment.line),
                        )
                    )
    return accesses


def find_component_for_module(
    module_id: str,
    component_candidates: list[Component],
    architectural_graph: Any,
) -> str:
    for candidate in component_candidates:
        if module_id in candidate.node_ids:
            return candidate.id
    nodes = getattr(architectural_graph, "nodes", ()) if architectural_graph else ()
    for node in sorted(
        nodes,
        key=lambda item: (
            0 if item.type == NodeType.COMPONENT else 1,
            0 if item.type != NodeType.APPLICATION else 1,
            item.id,
        ),
    ):
        if module_id in node.metadata.get("raw_node_ids", []):
            return node.id
    return module_id


def _resource_node_type(kind: str) -> NodeType:
    return {
        "DATABASE": NodeType.DATABASE,
        "CACHE": NodeType.CACHE,
        "MESSAGE_BROKER": NodeType.MESSAGE_BROKER,
        "CONTAINER": NodeType.CONTAINER,
        "SERVICE": NodeType.EXTERNAL_SERVICE,
        "CONFIGURATION": NodeType.CONFIGURATION,
    }.get(kind.upper(), NodeType.CONTAINER)


def _resource_origin(resource: InfrastructureResource) -> SourceOrigin:
    kind = resource.kind.upper()
    if kind in {"DATABASE", "CACHE", "MESSAGE_BROKER"}:
        return SourceOrigin.THIRD_PARTY
    if kind == "UNKNOWN":
        return SourceOrigin.UNKNOWN
    if resource.metadata.get("build"):
        return SourceOrigin.FIRST_PARTY
    if resource.metadata.get("image"):
        return SourceOrigin.THIRD_PARTY
    return SourceOrigin.FIRST_PARTY if kind == "CONFIGURATION" else SourceOrigin.UNKNOWN


class DockerfileAdapter(InfrastructureAdapter):
    @property
    def name(self) -> str:
        return "Dockerfile"

    def analyze(self, context: InfrastructureAnalysisContext) -> InfrastructureAnalysisResult:
        result = InfrastructureAnalysisResult()
        for record in context.snapshot.by_kind(FileKind.INFRASTRUCTURE):
            name = Path(record.path).name.lower()
            if name != "dockerfile" and not name.startswith("dockerfile.") and not name.endswith(".dockerfile"):
                continue
            try:
                metadata = parse_dockerfile(record.absolute_path.read_text(encoding="utf-8", errors="ignore"))
            except OSError:
                continue
            evidence_id = f"evidence:dockerfile:{record.path}"
            result.evidence.append(
                Evidence(
                    id=evidence_id,
                    source_type=EvidenceSource.DOCKERFILE,
                    detail=f"Parsed Dockerfile from {record.path}",
                    source=SourceRef(path=record.path),
                )
            )
            result.resources.append(
                InfrastructureResource(
                    id=f"infrastructure:dockerfile:{record.path}",
                    name=record.path,
                    kind="CONTAINER",
                    source=SourceRef(path=record.path),
                    evidence_refs=[evidence_id],
                    confidence=1.0,
                    metadata=metadata,
                )
            )
        return result


class DockerComposeAdapter(InfrastructureAdapter):
    @property
    def name(self) -> str:
        return "DockerCompose"

    def analyze(self, context: InfrastructureAnalysisContext) -> InfrastructureAnalysisResult:
        result = InfrastructureAnalysisResult()
        for record in context.snapshot.by_kind(FileKind.INFRASTRUCTURE):
            filename = Path(record.path).name.lower()
            if filename not in {"docker-compose.yml", "docker-compose.yaml", "compose.yml", "compose.yaml"}:
                continue
            try:
                document = yaml.safe_load(
                    record.absolute_path.read_text(encoding="utf-8", errors="ignore")
                ) or {}
            except (OSError, yaml.YAMLError):
                continue
            services = document.get("services")
            if not isinstance(services, dict):
                continue

            service_ids: dict[str, str] = {}
            for raw_name, config in sorted(services.items(), key=lambda item: str(item[0]).lower()):
                name = str(raw_name)
                evidence_id = f"evidence:docker_compose:{record.path}:{name}"
                result.evidence.append(
                    Evidence(
                        id=evidence_id,
                        source_type=EvidenceSource.DOCKER_COMPOSE,
                        detail=f"Compose service {name} in {record.path}",
                        source=SourceRef(path=record.path, symbol=f"services.{name}"),
                    )
                )
                kind, confidence = classify_service(name, config)
                resource_id = f"infrastructure:compose:{record.path}:{name}"
                service_ids[name.lower()] = resource_id
                config_dict = config if isinstance(config, dict) else {}
                metadata = {
                    "image": config_dict.get("image"),
                    "build": config_dict.get("build"),
                    "ports": config_dict.get("ports", []),
                    "environment": parse_environment(config_dict.get("environment")),
                    "env_file": config_dict.get("env_file", []),
                    "volumes": config_dict.get("volumes", []),
                    "networks": config_dict.get("networks", []),
                    "depends_on": config_dict.get("depends_on", []),
                }
                result.resources.append(
                    InfrastructureResource(
                        id=resource_id,
                        name=name,
                        kind=kind,
                        source=SourceRef(path=record.path, symbol=f"services.{name}"),
                        evidence_refs=[evidence_id],
                        confidence=confidence,
                        metadata=metadata,
                    )
                )

            for raw_name, config in sorted(services.items(), key=lambda item: str(item[0]).lower()):
                name = str(raw_name)
                config_dict = config if isinstance(config, dict) else {}
                dependencies = config_dict.get("depends_on", [])
                if isinstance(dependencies, dict):
                    dependencies = dependencies.keys()
                elif isinstance(dependencies, str):
                    dependencies = [dependencies]
                if not isinstance(dependencies, (list, tuple, set)):
                    continue
                for dependency in dependencies:
                    dependency_name = str(dependency).lower()
                    if dependency_name not in service_ids:
                        continue
                    evidence_id = f"evidence:docker_compose_relation:{record.path}:{name}_depends_{dependency_name}"
                    result.evidence.append(
                        Evidence(
                            id=evidence_id,
                            source_type=EvidenceSource.DOCKER_COMPOSE,
                            detail=f"Compose service {name} depends on {dependency_name}",
                            source=SourceRef(path=record.path, symbol=f"services.{name}.depends_on"),
                        )
                    )
                    result.relations.append(
                        InfrastructureRelation(
                            id=f"infra-relation:{record.path}:{name}:{dependency_name}",
                            source=service_ids[name.lower()],
                            target=service_ids[dependency_name],
                            type="depends_on",
                            status=EvidenceStatus.OBSERVED,
                            confidence=1.0,
                            evidence_refs=[evidence_id],
                        )
                    )
        return result


class InfrastructureAnalyzer:
    """Collects bounded Docker/Compose facts and maps explicit code configuration."""

    def __init__(self) -> None:
        self.resources: list[InfrastructureResource] = []
        self.relations: list[InfrastructureRelation] = []
        self.evidence: list[Evidence] = []

    def augment(self, graph: PropertyGraph, snapshot: RepositorySnapshot) -> None:
        context = InfrastructureAnalysisContext(
            raw_graph=graph,
            parsed_files=(),
            symbols=None,
            snapshot=snapshot,
        )
        for adapter in (DockerfileAdapter(), DockerComposeAdapter()):
            result = adapter.analyze(context)
            self.resources.extend(result.resources)
            self.relations.extend(result.relations)
            self.evidence.extend(result.evidence)

        repository_id = f"repository:{snapshot.root.name}"
        for resource in self.resources:
            raw_id = f"container:{resource.name}"
            graph.add_node(
                Node(
                    id=raw_id,
                    type=_resource_node_type(resource.kind),
                    name=resource.name,
                    origin=_resource_origin(resource),
                    source=resource.source,
                    confidence=resource.confidence,
                    evidence_refs=resource.evidence_refs,
                )
            )
            graph.add_edge(
                Edge(
                    source=repository_id,
                    target=raw_id,
                    type=EdgeType.DEPLOYS,
                    evidence_refs=resource.evidence_refs,
                )
            )
        for relation in self.relations:
            graph.add_edge(
                Edge(
                    source=f"container:{relation.source.rsplit(':', 1)[-1]}",
                    target=f"container:{relation.target.rsplit(':', 1)[-1]}",
                    type=EdgeType.CONNECTS_TO,
                    evidence_refs=relation.evidence_refs,
                )
            )
        for evidence in self.evidence:
            graph.add_evidence(evidence)

    def _ensure_architectural_resources(self, architectural_graph: Any) -> None:
        if architectural_graph is None:
            return
        existing = {node.id for node in architectural_graph.nodes}
        for resource in self.resources:
            if resource.id in existing:
                continue
            architectural_graph.nodes.append(
                Node(
                    id=resource.id,
                    type=_resource_node_type(resource.kind),
                    name=resource.name,
                    origin=_resource_origin(resource),
                    source=resource.source,
                    confidence=resource.confidence,
                    evidence_refs=resource.evidence_refs,
                )
            )
            existing.add(resource.id)

    def _append_relation(self, relation: InfrastructureRelation) -> None:
        key = (relation.source, relation.target, relation.type)
        if not any((item.source, item.target, item.type) == key for item in self.relations):
            self.relations.append(relation)

    def resolve(
        self,
        graph: PropertyGraph,
        parsed_files: tuple[ParseFacts, ...],
        component_candidates: list[Component],
        architectural_graph: Any,
    ) -> None:
        self._ensure_architectural_resources(architectural_graph)
        accesses = extract_env_var_accesses(parsed_files)
        if not accesses:
            return

        services = {
            resource.name.lower(): resource
            for resource in self.resources
            if resource.id.startswith("infrastructure:compose:")
        }
        for application_service in sorted(services):
            application_resource = services[application_service]
            environment = application_resource.metadata.get("environment", {})
            for variable_name, variable_value in sorted(environment.items()):
                matching = [item for item in accesses if item[1] == variable_name]
                if not matching:
                    continue
                target_service = find_referenced_service(variable_value, set(services))
                for module_name, _, source_ref in matching:
                    module_id = f"module:{module_name}"
                    component_id = find_component_for_module(
                        module_id, component_candidates, architectural_graph
                    )
                    code_evidence_id = f"evidence:env_var_access:{module_name}:{variable_name}"
                    self.evidence.append(
                        Evidence(
                            id=code_evidence_id,
                            source_type=EvidenceSource.AST,
                            detail=f"Module {module_name} accesses env var {variable_name}",
                            source=source_ref,
                        )
                    )
                    graph.add_evidence(self.evidence[-1])

                    config_id = f"configuration:{variable_name}"
                    if not any(resource.id == config_id for resource in self.resources):
                        config_resource = InfrastructureResource(
                            id=config_id,
                            name=variable_name,
                            kind="CONFIGURATION",
                            source=source_ref,
                            evidence_refs=[code_evidence_id],
                            confidence=1.0,
                            metadata={"env_var": variable_name},
                        )
                        self.resources.append(config_resource)
                        node = Node(
                            id=config_id,
                            type=NodeType.CONFIGURATION,
                            name=variable_name,
                            origin=SourceOrigin.FIRST_PARTY,
                            source=source_ref,
                            evidence_refs=[code_evidence_id],
                        )
                        graph.add_node(node)
                        if architectural_graph is not None:
                            architectural_graph.nodes.append(node)

                    self._append_relation(
                        InfrastructureRelation(
                            id=f"infra-relation:{module_name}:{config_id}",
                            source=module_id,
                            target=config_id,
                            type="depends_on",
                            status=EvidenceStatus.OBSERVED,
                            confidence=1.0,
                            evidence_refs=[code_evidence_id],
                        )
                    )
                    graph.add_edge(
                        Edge(
                            source=module_id,
                            target=config_id,
                            type=EdgeType.DEPENDS_ON,
                            status=EvidenceStatus.OBSERVED,
                            evidence_refs=[code_evidence_id],
                        )
                    )
                    if architectural_graph is not None:
                        architectural_graph.edges.append(
                            Edge(
                                id=f"arch-edge-env-{component_id}-{config_id}",
                                source=component_id,
                                target=config_id,
                                type=EdgeType.DEPENDS_ON,
                                status=EvidenceStatus.INFERRED,
                                evidence_refs=[code_evidence_id],
                            )
                        )

                    if target_service is None:
                        continue
                    target_resource = services[target_service]
                    compose_evidence_id = (
                        f"evidence:compose_env:{application_resource.source.path}:"
                        f"{application_service}:{variable_name}"
                    )
                    compose_evidence = Evidence(
                        id=compose_evidence_id,
                        source_type=EvidenceSource.DOCKER_COMPOSE,
                        detail=(
                            f"Compose service {application_service} configures "
                            f"{variable_name} to reference service {target_service}"
                        ),
                        source=SourceRef(
                            path=application_resource.source.path,
                            symbol=f"services.{application_service}.environment.{variable_name}",
                        ),
                    )
                    self.evidence.append(compose_evidence)
                    graph.add_evidence(compose_evidence)
                    evidence_refs = [code_evidence_id, compose_evidence_id]

                    self._append_relation(
                        InfrastructureRelation(
                            id=f"infra-relation:{config_id}:{target_resource.id}",
                            source=config_id,
                            target=target_resource.id,
                            type="connects_to",
                            status=EvidenceStatus.OBSERVED,
                            confidence=0.9,
                            evidence_refs=evidence_refs,
                        )
                    )
                    graph.add_edge(
                        Edge(
                            source=config_id,
                            target=f"container:{target_service}",
                            type=EdgeType.CONNECTS_TO,
                            status=EvidenceStatus.OBSERVED,
                            confidence=0.9,
                            evidence_refs=evidence_refs,
                        )
                    )
                    if architectural_graph is not None:
                        architectural_graph.edges.append(
                            Edge(
                                id=f"arch-edge-env-{config_id}-{target_resource.id}",
                                source=config_id,
                                target=target_resource.id,
                                type=EdgeType.CONNECTS_TO,
                                status=EvidenceStatus.INFERRED,
                                confidence=0.9,
                                evidence_refs=evidence_refs,
                            )
                        )

                    self._append_relation(
                        InfrastructureRelation(
                            id=f"infra-relation:{component_id}:{target_resource.id}",
                            source=component_id,
                            target=target_resource.id,
                            type="depends_on",
                            status=EvidenceStatus.INFERRED,
                            confidence=0.9,
                            evidence_refs=evidence_refs,
                        )
                    )
                    graph.add_edge(
                        Edge(
                            source=module_id,
                            target=f"container:{target_service}",
                            type=EdgeType.DEPENDS_ON,
                            status=EvidenceStatus.INFERRED,
                            confidence=0.9,
                            evidence_refs=evidence_refs,
                        )
                    )
                    if architectural_graph is not None:
                        architectural_graph.edges.append(
                            Edge(
                                id=f"arch-edge-direct-{component_id}-{target_resource.id}",
                                source=component_id,
                                target=target_resource.id,
                                type=EdgeType.DEPENDS_ON,
                                status=EvidenceStatus.INFERRED,
                                confidence=0.9,
                                evidence_refs=evidence_refs,
                            )
                        )
