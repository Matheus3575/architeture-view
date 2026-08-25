from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path

from architecture_recovery.classification import PythonRepositoryClassifier
from architecture_recovery.ir import (
    Edge,
    EdgeType,
    Evidence,
    EvidenceSource,
    EvidenceStatus,
    Node,
    NodeType,
    SourceRef,
    SourceOrigin,
    UnresolvedCall,
)
from architecture_recovery.parsing import ParseFacts
from architecture_recovery.scanner import FileKind, RepositorySnapshot
from architecture_recovery.symbols import SymbolIndex


@dataclass
class PropertyGraph:
    nodes: dict[str, Node] = field(default_factory=dict)
    edges: list[Edge] = field(default_factory=list)
    evidence: dict[str, Evidence] = field(default_factory=dict)
    unresolved_calls: list[UnresolvedCall] = field(default_factory=list)
    _edge_index: dict[tuple[str, str, EdgeType], int] = field(default_factory=dict, init=False, repr=False)

    def __post_init__(self) -> None:
        for index, edge in enumerate(self.edges):
            self._edge_index.setdefault((edge.source, edge.target, edge.type), index)

    def add_evidence(self, evidence: Evidence) -> str:
        self.evidence[evidence.id] = evidence
        return evidence.id

    def add_node(self, node: Node) -> None:
        self.nodes.setdefault(node.id, node)

    def add_edge(self, edge: Edge) -> None:
        if edge.source in self.nodes and edge.target in self.nodes:
            key = (edge.source, edge.target, edge.type)
            existing_index = self._edge_index.get(key)
            if existing_index is None:
                if edge.id is None:
                    token = f"{edge.source}:{edge.target}:{edge.type.value}".encode()
                    edge = edge.model_copy(update={"id": f"edge:{hashlib.sha1(token).hexdigest()[:16]}"})
                if edge.metadata.get("support_count") is None:
                    edge = edge.model_copy(
                        update={"metadata": {**edge.metadata, "support_count": 1}}
                    )
                self.edges.append(edge)
                self._edge_index[key] = len(self.edges) - 1
                return

            existing = self.edges[existing_index]
            merged_evidence = sorted(set(existing.evidence_refs + edge.evidence_refs))
            merged_raw_edges = sorted(set(existing.raw_edge_ids + edge.raw_edge_ids))
            merged_metadata = {**existing.metadata}
            support_count = int(existing.metadata.get("support_count", 1)) + int(
                edge.metadata.get("support_count", 1)
            )
            merged_metadata["support_count"] = support_count
            if edge.metadata and edge.metadata != existing.metadata:
                observations = list(existing.metadata.get("supporting_observations", []))
                observations.append(dict(edge.metadata))
                merged_metadata["supporting_observations"] = observations
            self.edges[existing_index] = existing.model_copy(
                update={
                    "evidence_refs": merged_evidence,
                    "raw_edge_ids": merged_raw_edges,
                    "metadata": merged_metadata,
                }
            )


class GraphBuilder:
    def build(
        self,
        snapshot: RepositorySnapshot,
        parsed_files: list[ParseFacts],
        symbols: SymbolIndex,
        classifier: PythonRepositoryClassifier | None = None,
    ) -> PropertyGraph:
        classifier = classifier or PythonRepositoryClassifier(snapshot, parsed_files)
        graph = PropertyGraph()
        repository_id = f"repository:{snapshot.root.name}"
        graph.add_node(
            Node(
                id=repository_id,
                type=NodeType.REPOSITORY,
                name=snapshot.root.name,
                origin=SourceOrigin.FIRST_PARTY,
            )
        )
        module_ids = {facts.module_name: f"module:{facts.module_name}" for facts in parsed_files}

        for file in snapshot.by_kind(FileKind.SOURCE):
            file_id = f"file:{file.path}"
            file_ref = self._evidence(graph, EvidenceSource.AST, file.path, None, "Source file discovered")
            origin, origin_reason = classifier.classify_path(file.path)
            graph.add_node(
                Node(
                    id=file_id,
                    type=NodeType.FILE,
                    name=Path(file.path).name,
                    origin=origin,
                    source=SourceRef(path=file.path),
                    evidence_refs=[file_ref],
                    metadata={"origin_reason": origin_reason},
                )
            )
            graph.add_edge(self._edge(repository_id, file_id, EdgeType.CONTAINS, file_ref))

        for facts in parsed_files:
            module_id = module_ids[facts.module_name]
            module_ref = self._evidence(graph, EvidenceSource.AST, facts.path, 1, "Python module discovered")
            origin, origin_reason = classifier.classify_path(facts.path)
            graph.add_node(
                Node(
                    id=module_id,
                    type=NodeType.MODULE,
                    name=facts.module_name,
                    origin=origin,
                    source=SourceRef(path=facts.path),
                    evidence_refs=[module_ref],
                    metadata={"origin_reason": origin_reason},
                )
            )
            graph.add_edge(self._edge(f"file:{facts.path}", module_id, EdgeType.CONTAINS, module_ref))
            self._add_definitions(graph, facts, module_id, classifier, symbols)

        # Definitions are materialized before relationships so cross-module
        # inheritance, calls, and imports can target symbols declared later in
        # the scan order.
        for facts in parsed_files:
            module_id = module_ids[facts.module_name]
            self._add_imports(graph, facts, module_ids, symbols, classifier)
            self._add_assignments(graph, facts, symbols)
            self._add_calls(graph, facts, symbols, classifier)

        return graph

    def _add_definitions(
        self,
        graph: PropertyGraph,
        facts: ParseFacts,
        module_id: str,
        classifier,
        symbols: SymbolIndex,
    ) -> None:
        for definition in facts.definitions:
            node_type = NodeType.CLASS if definition.kind == "class" else NodeType.FUNCTION
            node_id = definition.qualified_name
            ref = self._evidence(
                graph,
                EvidenceSource.AST,
                definition.path,
                definition.start_line,
                f"Defined {definition.kind} {definition.qualified_name}",
                definition.qualified_name,
            )
            decorator_facts = [
                decorator for decorator in facts.decorators if decorator.owner == definition.qualified_name
            ]
            decorator_evidence = [
                self._evidence(
                    graph,
                    EvidenceSource.AST,
                    decorator.path,
                    decorator.line,
                    f"Decorator {decorator.expression} on {decorator.owner}",
                    decorator.owner,
                )
                for decorator in decorator_facts
            ]
            decorator_metadata = []
            for decorator in decorator_facts:
                item = {
                    "owner": decorator.owner,
                    "expression": decorator.expression,
                    "arguments": list(decorator.arguments),
                    "path": decorator.path,
                    "line": decorator.line,
                }
                if decorator.keywords:
                    item["keywords"] = dict(decorator.keywords)
                decorator_metadata.append(item)
            graph.add_node(
                Node(
                    id=node_id,
                    type=node_type,
                    name=definition.name,
                    origin=classifier.classify_path(definition.path)[0],
                    layer=self._layer(definition.path),
                    source=SourceRef(
                        path=definition.path,
                        start_line=definition.start_line,
                        end_line=definition.end_line,
                        symbol=definition.qualified_name,
                    ),
                    evidence_refs=[ref, *decorator_evidence],
                    metadata={
                        "decorators": list(definition.decorators),
                        "decorator_evidence": decorator_metadata,
                        "type_hints": {
                            hint.name: hint.annotation
                            for hint in facts.type_hints
                            if hint.scope == definition.qualified_name
                        },
                    },
                )
            )
            parent_id = definition.parent and f"{facts.module_name}.{definition.parent}"
            container = parent_id if parent_id in graph.nodes else module_id
            graph.add_edge(self._edge(container, node_id, EdgeType.CONTAINS, ref))
            for base in definition.bases:
                target = symbols.resolve_reference(facts.module_name, base, caller=definition.qualified_name)
                if target not in graph.nodes:
                    target = self._find_symbol(graph, base)
                if target:
                    graph.add_edge(self._edge(node_id, target, EdgeType.EXTENDS, ref))

    def _add_imports(self, graph: PropertyGraph, facts: ParseFacts, module_ids: dict[str, str], symbols: SymbolIndex, classifier) -> None:
        source_id = f"module:{facts.module_name}"
        for item in facts.imports:
            resolution = classifier.resolve_import(item)
            local_module = classifier.local_module_for_import(item)
            evidence_id = self._evidence(graph, EvidenceSource.IMPORT, item.path, item.line, f"Import {item.imported_name}")
            if local_module:
                canonical = resolution.canonical_name
                resolved = symbols.resolve_reference(facts.module_name, item.local_name)
                if resolved:
                    target_id = resolved
                elif canonical in symbols.symbols:
                    target_id = canonical
                else:
                    target_id = module_ids.get(local_module)
                if target_id is None:
                    target_id = f"module:{local_module}"
            else:
                target_id = self._external_target(graph, resolution, item, evidence_id)
            if target_id not in graph.nodes:
                continue
            graph.add_edge(
                self._edge(
                    source_id,
                    target_id,
                    EdgeType.IMPORTS,
                    evidence_id,
                    metadata={
                        "local_name": item.local_name,
                        "imported_name": item.imported_name,
                        "resolved_target": target_id,
                    },
                )
            )

    def _add_assignments(self, graph: PropertyGraph, facts: ParseFacts, symbols: SymbolIndex) -> None:
        for assignment in facts.assignments:
            if not assignment.value_is_call or assignment.value_is_dynamic:
                continue
            target = symbols.resolve_reference(
                facts.module_name, assignment.value, caller=assignment.scope
            )
            if target in symbols.return_targets:
                target = symbols.return_targets[target]
            if not target or target not in symbols.symbols or symbols.symbols[target].kind != "class":
                continue
            source_id = assignment.scope if assignment.scope in graph.nodes else f"module:{facts.module_name}"
            if source_id not in graph.nodes or target not in graph.nodes:
                continue
            evidence_id = self._evidence(
                graph,
                EvidenceSource.SYMBOL_RESOLUTION,
                assignment.path,
                assignment.line,
                f"{assignment.target} instantiated from {target}",
                assignment.scope,
            )
            graph.add_edge(
                self._edge(
                    source_id,
                    target,
                    EdgeType.INSTANTIATES,
                    evidence_id,
                    metadata={"target_variable": assignment.target},
                )
            )

    def _add_calls(self, graph: PropertyGraph, facts: ParseFacts, symbols: SymbolIndex, classifier) -> None:
        for call in facts.calls:
            target = symbols.resolve(facts.module_name, call.callee, caller=call.caller)
            if target is None:
                reason = symbols.reason_for(call) or "unresolved_symbol"
                resolution = classifier.resolve_call(facts.module_name, call.callee)
                if resolution is None or reason == "dynamic_dispatch":
                    graph.unresolved_calls.append(
                        UnresolvedCall(
                            caller=call.caller,
                            callee=call.callee,
                            source=SourceRef(path=call.path, start_line=call.line, end_line=call.line),
                            reason=reason,
                        )
                    )
                    continue
                evidence_id = self._evidence(
                    graph,
                    EvidenceSource.CALL_GRAPH,
                    call.path,
                    call.line,
                    f"{call.caller} calls {resolution.canonical_name}",
                    call.caller,
                )
                target = self._external_target(graph, resolution, call, evidence_id)
                call_metadata = {
                    "caller": call.caller,
                    "callee": call.callee,
                    "call_path": call.path,
                    "call_line": call.line,
                    "resolution_status": "resolved_external",
                    "resolved_target": target,
                }
            else:
                evidence_id = self._evidence(
                    graph,
                    EvidenceSource.CALL_GRAPH,
                    call.path,
                    call.line,
                    f"{call.caller} calls {target}",
                    call.caller,
                )
                call_metadata = {
                    "caller": call.caller,
                    "callee": call.callee,
                    "call_path": call.path,
                    "call_line": call.line,
                    "resolution_status": "resolved",
                    "resolved_target": target,
                }
            source_id = call.caller if call.caller in graph.nodes else f"module:{facts.module_name}"
            if target not in graph.nodes or source_id not in graph.nodes:
                continue
            evidence_refs = [evidence_id]
            flow_details = symbols.evidence_for(call.caller, call.callee)
            if flow_details:
                flow_evidence_id = self._evidence(
                    graph,
                    EvidenceSource.SYMBOL_RESOLUTION,
                    call.path,
                    call.line,
                    "; ".join(flow_details),
                    call.caller,
                )
                evidence_refs.append(flow_evidence_id)
                call_metadata["flow_evidence"] = list(flow_details)
            graph.add_edge(
                self._edge(
                    source_id,
                    target,
                    EdgeType.CALLS,
                    evidence_refs,
                    metadata=call_metadata,
                )
            )

    def _external_target(self, graph: PropertyGraph, resolution, source, evidence_id: str) -> str:
        package_id = f"external:{resolution.package}"
        graph.add_node(
            Node(
                id=package_id,
                type=NodeType.EXTERNAL_DEPENDENCY,
                name=resolution.display_name,
                origin=resolution.origin,
                status=EvidenceStatus.OBSERVED,
                confidence=0.9 if resolution.origin != SourceOrigin.UNKNOWN else 0.45,
                evidence_refs=[evidence_id],
                metadata={
                    "external_package": resolution.package,
                    "external_origin": resolution.origin.value,
                    "origin_reason": resolution.reason,
                },
            )
        )
        canonical_name = resolution.canonical_name
        if canonical_name == resolution.package:
            return package_id
        symbol_id = f"external_symbol:{canonical_name}"
        graph.add_node(
            Node(
                id=symbol_id,
                type=NodeType.FUNCTION,
                name=canonical_name.rsplit(".", 1)[-1],
                origin=resolution.origin,
                status=EvidenceStatus.OBSERVED,
                confidence=0.8 if resolution.origin != SourceOrigin.UNKNOWN else 0.4,
                source=SourceRef(path=source.path, start_line=source.line, end_line=source.line),
                evidence_refs=[evidence_id],
                metadata={
                    "external_package": resolution.package,
                    "external_origin": resolution.origin.value,
                    "origin_reason": resolution.reason,
                    "qualified_name": canonical_name,
                },
            )
        )
        graph.add_edge(self._edge(package_id, symbol_id, EdgeType.CONTAINS, evidence_id))
        return symbol_id

    @staticmethod
    def _find_symbol(graph: PropertyGraph, name: str) -> str | None:
        matches = [node_id for node_id, node in graph.nodes.items() if node.name == name and node.type == NodeType.CLASS]
        return matches[0] if len(matches) == 1 else None

    @staticmethod
    def _layer(path: str) -> str | None:
        parts = Path(path).parts
        for candidate in ("controllers", "views", "services", "repositories", "domain", "infrastructure", "models"):
            if candidate in parts:
                return candidate
        return None

    @staticmethod
    def _edge(source: str, target: str, edge_type: EdgeType, evidence_id: str | list[str], metadata=None) -> Edge:
        return Edge(
            source=source,
            target=target,
            type=edge_type,
            evidence_refs=[evidence_id] if isinstance(evidence_id, str) else evidence_id,
            metadata=metadata or {},
        )

    @staticmethod
    def _evidence(graph, source_type, path, line, detail, symbol=None):
        token = f"{source_type.value}:{path}:{line}:{detail}".encode()
        evidence_id = f"evidence:{hashlib.sha1(token).hexdigest()[:16]}"
        evidence = Evidence(
            id=evidence_id,
            source_type=source_type,
            detail=detail,
            source=SourceRef(path=path, start_line=line, end_line=line, symbol=symbol),
        )
        return graph.add_evidence(evidence)
