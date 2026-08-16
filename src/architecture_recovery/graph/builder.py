from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path

from architecture_recovery.ir import (
    Edge,
    EdgeType,
    Evidence,
    EvidenceSource,
    EvidenceStatus,
    Node,
    NodeType,
    SourceRef,
)
from architecture_recovery.parsing import ParseFacts
from architecture_recovery.scanner import FileKind, RepositorySnapshot
from architecture_recovery.symbols import SymbolIndex


@dataclass
class PropertyGraph:
    nodes: dict[str, Node] = field(default_factory=dict)
    edges: list[Edge] = field(default_factory=list)
    evidence: dict[str, Evidence] = field(default_factory=dict)

    def add_evidence(self, evidence: Evidence) -> str:
        self.evidence[evidence.id] = evidence
        return evidence.id

    def add_node(self, node: Node) -> None:
        self.nodes.setdefault(node.id, node)

    def add_edge(self, edge: Edge) -> None:
        if edge.source in self.nodes and edge.target in self.nodes:
            if not any(
                existing.source == edge.source
                and existing.target == edge.target
                and existing.type == edge.type
                for existing in self.edges
            ):
                self.edges.append(edge)


class GraphBuilder:
    def build(
        self,
        snapshot: RepositorySnapshot,
        parsed_files: list[ParseFacts],
        symbols: SymbolIndex,
    ) -> PropertyGraph:
        graph = PropertyGraph()
        repository_id = f"repository:{snapshot.root.name}"
        graph.add_node(Node(id=repository_id, type=NodeType.REPOSITORY, name=snapshot.root.name))
        module_ids = {facts.module_name: f"module:{facts.module_name}" for facts in parsed_files}

        for file in snapshot.by_kind(FileKind.SOURCE):
            file_id = f"file:{file.path}"
            file_ref = self._evidence(graph, EvidenceSource.AST, file.path, None, "Source file discovered")
            graph.add_node(
                Node(
                    id=file_id,
                    type=NodeType.FILE,
                    name=Path(file.path).name,
                    source=SourceRef(path=file.path),
                    evidence_refs=[file_ref],
                )
            )
            graph.add_edge(self._edge(repository_id, file_id, EdgeType.CONTAINS, file_ref))

        for facts in parsed_files:
            module_id = module_ids[facts.module_name]
            module_ref = self._evidence(graph, EvidenceSource.AST, facts.path, 1, "Python module discovered")
            graph.add_node(
                Node(
                    id=module_id,
                    type=NodeType.MODULE,
                    name=facts.module_name,
                    source=SourceRef(path=facts.path),
                    evidence_refs=[module_ref],
                )
            )
            graph.add_edge(self._edge(f"file:{facts.path}", module_id, EdgeType.CONTAINS, module_ref))
            self._add_definitions(graph, facts, module_id)
            self._add_imports(graph, facts, module_ids)
            self._add_calls(graph, facts, symbols)

        return graph

    def _add_definitions(self, graph: PropertyGraph, facts: ParseFacts, module_id: str) -> None:
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
            graph.add_node(
                Node(
                    id=node_id,
                    type=node_type,
                    name=definition.name,
                    layer=self._layer(definition.path),
                    source=SourceRef(
                        path=definition.path,
                        start_line=definition.start_line,
                        end_line=definition.end_line,
                        symbol=definition.qualified_name,
                    ),
                    evidence_refs=[ref],
                )
            )
            parent_id = definition.parent and f"{facts.module_name}.{definition.parent}"
            container = parent_id if parent_id in graph.nodes else module_id
            graph.add_edge(self._edge(container, node_id, EdgeType.CONTAINS, ref))
            for base in definition.bases:
                target = self._find_symbol(graph, base)
                if target:
                    graph.add_edge(self._edge(node_id, target, EdgeType.EXTENDS, ref))

    def _add_imports(self, graph: PropertyGraph, facts: ParseFacts, module_ids: dict[str, str]) -> None:
        source_id = f"module:{facts.module_name}"
        for item in facts.imports:
            target_module = item.imported_name.lstrip(".")
            if target_module in module_ids:
                target_id = module_ids[target_module]
            else:
                target_id = f"external:{target_module}"
                ref = self._evidence(graph, EvidenceSource.IMPORT, item.path, item.line, f"Import {item.imported_name}")
                graph.add_node(
                    Node(
                        id=target_id,
                        type=NodeType.EXTERNAL_SERVICE,
                        name=target_module,
                        status=EvidenceStatus.OBSERVED,
                        confidence=0.75,
                        evidence_refs=[ref],
                    )
                )
            ref = self._evidence(graph, EvidenceSource.IMPORT, item.path, item.line, f"Import {item.imported_name}")
            graph.add_edge(self._edge(source_id, target_id, EdgeType.IMPORTS, ref))

    def _add_calls(self, graph: PropertyGraph, facts: ParseFacts, symbols: SymbolIndex) -> None:
        for call in facts.calls:
            target = symbols.resolve(facts.module_name, call.callee)
            if target is None:
                continue
            source_id = call.caller if call.caller in graph.nodes else f"module:{facts.module_name}"
            if target not in graph.nodes or source_id not in graph.nodes:
                continue
            ref = self._evidence(
                graph,
                EvidenceSource.CALL_GRAPH,
                call.path,
                call.line,
                f"{call.caller} calls {target}",
                call.caller,
            )
            graph.add_edge(self._edge(source_id, target, EdgeType.CALLS, ref))

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
    def _edge(source: str, target: str, edge_type: EdgeType, evidence_id: str) -> Edge:
        return Edge(source=source, target=target, type=edge_type, evidence_refs=[evidence_id])

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
