"""Deterministic executable-entrypoint evidence extraction."""

from __future__ import annotations

import ast
import configparser
import hashlib
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from architecture_recovery.graph.builder import PropertyGraph
from architecture_recovery.ir import (
    ArchitecturalGraph,
    Evidence,
    EvidenceSource,
    EvidenceStatus,
    ExecutableEntrypoint,
    Node,
    NodeType,
    RawCodeGraph,
    SourceOrigin,
    SourceRef,
)
from architecture_recovery.parsing import ParseFacts, PythonParser
from architecture_recovery.scanner import FileKind, RepositorySnapshot


@dataclass(frozen=True)
class EntrypointAnalysis:
    entrypoints: tuple[ExecutableEntrypoint, ...]
    evidence: tuple[Evidence, ...]


@dataclass(frozen=True)
class _Declaration:
    provenance: str
    declared_name: str
    declared_target: str
    path: str
    line: int
    source_type: EvidenceSource
    dynamic: bool = False


class EntrypointAnalyzer:
    """Extract packaging/module entrypoints without executing configuration."""

    def analyze(
        self,
        snapshot: RepositorySnapshot,
        parsed_files: list[ParseFacts],
        raw_graph: PropertyGraph | RawCodeGraph,
        architectural_graph: ArchitecturalGraph,
    ) -> EntrypointAnalysis:
        raw_nodes = self._nodes(raw_graph)
        architectural_nodes = {node.id: node for node in architectural_graph.nodes}
        owners = self._owner_index(architectural_nodes)
        declarations = self._declarations(snapshot, parsed_files)
        entrypoints: list[ExecutableEntrypoint] = []
        evidence: list[Evidence] = []
        for declaration in sorted(declarations, key=self._declaration_key):
            entrypoint, item = self._resolve_declaration(
                declaration,
                raw_nodes,
                architectural_nodes,
                owners,
            )
            entrypoints.append(entrypoint)
            evidence.append(item)
        return EntrypointAnalysis(
            entrypoints=tuple(sorted(entrypoints, key=lambda item: item.id)),
            evidence=tuple(sorted(evidence, key=lambda item: item.id)),
        )

    @staticmethod
    def _nodes(graph: PropertyGraph | RawCodeGraph) -> dict[str, Node]:
        nodes = graph.nodes
        return dict(nodes) if isinstance(nodes, dict) else {node.id: node for node in nodes}

    @staticmethod
    def _owner_index(nodes: dict[str, Node]) -> dict[str, tuple[str, ...]]:
        index: dict[str, list[str]] = {}
        for node in nodes.values():
            if node.type == NodeType.APPLICATION and node.metadata.get("application_provenance") == "repository_aggregate":
                continue
            if node.type not in {NodeType.COMPONENT, NodeType.APPLICATION}:
                continue
            raw_ids = node.metadata.get("raw_node_ids", node.metadata.get("node_ids", []))
            if not isinstance(raw_ids, list):
                continue
            for raw_id in raw_ids:
                if isinstance(raw_id, str):
                    index.setdefault(raw_id, []).append(node.id)
        return {raw_id: tuple(sorted(set(values))) for raw_id, values in index.items()}

    def _declarations(
        self,
        snapshot: RepositorySnapshot,
        parsed_files: list[ParseFacts],
    ) -> list[_Declaration]:
        declarations: list[_Declaration] = []
        for record in snapshot.files:
            lower = record.path.lower()
            if lower.endswith("pyproject.toml"):
                declarations.extend(self._pyproject(record.path, record.absolute_path))
            elif lower.endswith("setup.cfg"):
                declarations.extend(self._setup_cfg(record.path, record.absolute_path))
            elif lower.endswith("setup.py"):
                declarations.extend(self._setup_py(record.path, record.absolute_path))
        parsed_by_path = {item.path: item.module_name for item in parsed_files}
        for record in snapshot.by_kind(FileKind.SOURCE):
            if Path(record.path).name != "__main__.py":
                continue
            module_name = parsed_by_path.get(record.path) or PythonParser.module_name(record.path)
            package = module_name.removesuffix(".__main__") or "__main__"
            declarations.append(_Declaration(
                provenance="MAIN_MODULE",
                declared_name=f"python -m {package}",
                declared_target=module_name,
                path=record.path,
                line=1,
                source_type=EvidenceSource.AST,
            ))
        return declarations

    def _pyproject(self, path: str, file_path: Path) -> list[_Declaration]:
        try:
            document = tomllib.loads(file_path.read_text(encoding="utf-8", errors="ignore"))
        except (OSError, tomllib.TOMLDecodeError):
            return self._unknown_sections(path, file_path, ("project.scripts", "project.gui-scripts", "tool.poetry.scripts"))
        declarations: list[_Declaration] = []
        project = document.get("project", {})
        if isinstance(project, dict):
            for key, provenance in (("scripts", "PROJECT_SCRIPT"), ("gui-scripts", "PROJECT_GUI_SCRIPT")):
                declarations.extend(self._mapping_declarations(path, file_path, project.get(key), provenance))
            entry_points = project.get("entry-points")
            if isinstance(entry_points, dict):
                for group, values in sorted(entry_points.items()):
                    declarations.extend(self._mapping_declarations(path, file_path, values, f"PROJECT_ENTRY_POINT:{group}"))
        poetry = document.get("tool", {}).get("poetry", {}) if isinstance(document.get("tool"), dict) else {}
        if isinstance(poetry, dict):
            declarations.extend(self._mapping_declarations(path, file_path, poetry.get("scripts"), "POETRY_SCRIPT"))
        return declarations

    def _mapping_declarations(
        self,
        path: str,
        file_path: Path,
        value: Any,
        provenance: str,
    ) -> list[_Declaration]:
        if value is None:
            return []
        if not isinstance(value, dict):
            return [self._dynamic(path, file_path, provenance, "<dynamic>", "<dynamic>", "dynamic entrypoint table")]
        declarations: list[_Declaration] = []
        text = self._read(file_path)
        for name, target_value in sorted(value.items(), key=lambda item: str(item[0])):
            declared_name = str(name)
            target = target_value
            if isinstance(target_value, dict):
                target = target_value.get("reference")
            if not isinstance(target, str):
                declarations.append(self._dynamic(path, file_path, provenance, declared_name, "<dynamic>", "entrypoint target is not a literal string"))
                continue
            declarations.append(_Declaration(
                provenance=provenance,
                declared_name=declared_name,
                declared_target=target.strip(),
                path=path,
                line=self._line_for(text, target) or 1,
                source_type=EvidenceSource.CONFIGURATION,
            ))
        return declarations

    def _setup_cfg(self, path: str, file_path: Path) -> list[_Declaration]:
        text = self._read(file_path)
        parser = configparser.ConfigParser(interpolation=None, strict=False)
        try:
            parser.read_string(text)
        except (configparser.Error, ValueError):
            return self._unknown_sections(path, file_path, ("options.entry_points",))
        if not parser.has_section("options.entry_points"):
            return []
        declarations: list[_Declaration] = []
        for group, raw_values in sorted(parser.items("options.entry_points")):
            provenance = "CONSOLE_SCRIPT" if group == "console_scripts" else f"ENTRY_POINT:{group}"
            lines = str(raw_values).splitlines()
            for raw_line in lines:
                line = raw_line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" not in line:
                    declarations.append(self._dynamic(path, file_path, provenance, "<unresolved>", line, "entrypoint declaration has no target separator"))
                    continue
                name, target = (item.strip() for item in line.split("=", 1))
                declarations.append(_Declaration(
                    provenance=provenance,
                    declared_name=name,
                    declared_target=target,
                    path=path,
                    line=self._line_for(text, raw_line.strip()) or 1,
                    source_type=EvidenceSource.CONFIGURATION,
                ))
        return declarations

    def _setup_py(self, path: str, file_path: Path) -> list[_Declaration]:
        text = self._read(file_path)
        try:
            tree = ast.parse(text, filename=path)
        except SyntaxError:
            return [self._dynamic(path, file_path, "SETUP_PY", "<unresolved>", "<dynamic>", "setup.py is not statically parseable")]
        declarations: list[_Declaration] = []
        found_dynamic = False
        for call in self._setup_calls(tree):
            keyword = next((item for item in call.keywords if item.arg == "entry_points"), None)
            if keyword is None:
                continue
            try:
                value = ast.literal_eval(keyword.value)
            except (ValueError, TypeError, MemoryError, RecursionError):
                found_dynamic = True
                continue
            declarations.extend(self._literal_entry_points(path, file_path, text, value, keyword.value.lineno))
        if found_dynamic and not declarations:
            declarations.append(self._dynamic(path, file_path, "SETUP_PY", "<dynamic>", "<dynamic>", "entry_points expression is dynamic"))
        return declarations

    @staticmethod
    def _setup_calls(tree: ast.AST) -> list[ast.Call]:
        calls: list[ast.Call] = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            function = node.func.id if isinstance(node.func, ast.Name) else node.func.attr if isinstance(node.func, ast.Attribute) else ""
            if function == "setup":
                calls.append(node)
        return calls

    def _literal_entry_points(
        self,
        path: str,
        file_path: Path,
        text: str,
        value: Any,
        line: int,
    ) -> list[_Declaration]:
        if not isinstance(value, dict):
            return [self._dynamic(path, file_path, "SETUP_PY", "<unresolved>", "<dynamic>", "entry_points literal is not a mapping")]
        declarations: list[_Declaration] = []
        for group, values in sorted(value.items(), key=lambda item: str(item[0])):
            if not isinstance(values, (list, tuple)):
                declarations.append(self._dynamic(path, file_path, f"SETUP_PY:{group}", "<unresolved>", "<dynamic>", "entry point group is not a literal sequence"))
                continue
            for item in values:
                if not isinstance(item, str) or "=" not in item:
                    declarations.append(self._dynamic(path, file_path, f"SETUP_PY:{group}", "<unresolved>", str(item), "entry point item is not a literal name = target"))
                    continue
                name, target = (part.strip() for part in item.split("=", 1))
                declarations.append(_Declaration(
                    provenance="CONSOLE_SCRIPT" if group == "console_scripts" else f"SETUP_PY:{group}",
                    declared_name=name,
                    declared_target=target,
                    path=path,
                    line=self._line_for(text, item) or line,
                    source_type=EvidenceSource.CONFIGURATION,
                ))
        return declarations

    @staticmethod
    def _dynamic(path: str, file_path: Path, provenance: str, name: str, target: str, reason: str) -> _Declaration:
        return _Declaration(provenance=f"{provenance}:UNKNOWN:{reason}", declared_name=name, declared_target=target, path=path, line=1, source_type=EvidenceSource.CONFIGURATION, dynamic=True)

    def _unknown_sections(self, path: str, file_path: Path, sections: tuple[str, ...]) -> list[_Declaration]:
        text = self._read(file_path)
        result: list[_Declaration] = []
        for section in sections:
            marker = f"[{section}]"
            if marker.lower() in text.lower():
                result.append(self._dynamic(path, file_path, section.upper(), "<unresolved>", "<dynamic>", "metadata section could not be parsed"))
        return result

    def _resolve_declaration(
        self,
        declaration: _Declaration,
        raw_nodes: dict[str, Node],
        architectural_nodes: dict[str, Node],
        owners: dict[str, tuple[str, ...]],
    ) -> tuple[ExecutableEntrypoint, Evidence]:
        target_module, target_symbol = self._target_parts(declaration.declared_target)
        if declaration.provenance == "MAIN_MODULE" and target_module is None:
            target_module = declaration.declared_target
        resolved_target, target_node, reason = self._resolve_target(
            target_module,
            target_symbol,
            raw_nodes,
        )
        owner_ids = owners.get(resolved_target or "", ())
        owner_id = owner_ids[0] if len(owner_ids) == 1 else None
        if len(owner_ids) > 1:
            reason = "ambiguous first-party owner"
        if target_node is not None and target_node.origin != SourceOrigin.FIRST_PARTY:
            reason = "target is not first-party"
            owner_id = None
        if target_node is not None and owner_id is None and reason is None:
            reason = "first-party target has no unambiguous architectural owner"
        if declaration.dynamic:
            reason = declaration.provenance.split(":UNKNOWN:", 1)[-1]
        accepted = not declaration.dynamic and target_node is not None and target_node.origin == SourceOrigin.FIRST_PARTY and owner_id is not None and reason is None
        status = EvidenceStatus.OBSERVED if accepted else EvidenceStatus.UNKNOWN
        evidence_id = self._stable_id(declaration)
        evidence = Evidence(
            id=evidence_id,
            source_type=declaration.source_type,
            detail=f"Executable entrypoint {declaration.declared_name} -> {declaration.declared_target}",
            source=SourceRef(path=declaration.path, start_line=max(1, declaration.line)),
        )
        entrypoint = ExecutableEntrypoint(
            id=evidence_id,
            provenance=declaration.provenance.split(":UNKNOWN:", 1)[0],
            declared_name=declaration.declared_name,
            declared_target=declaration.declared_target,
            target_module=target_module,
            target_symbol=target_symbol,
            resolved_target=resolved_target,
            owner_id=owner_id,
            declaration_source=SourceRef(path=declaration.path, start_line=max(1, declaration.line)),
            status=status,
            accepted=accepted,
            rejection_reason=None if accepted else (reason or "unresolved target or owner"),
            evidence_refs=[evidence_id],
        )
        return entrypoint, evidence

    @staticmethod
    def _target_parts(target: str) -> tuple[str | None, str | None]:
        if not target or target.startswith("<") or ":" not in target:
            return None, None
        module, symbol = (item.strip() for item in target.split(":", 1))
        return (module or None, symbol or None)

    @staticmethod
    def _resolve_target(
        module: str | None,
        symbol: str | None,
        raw_nodes: dict[str, Node],
    ) -> tuple[str | None, Node | None, str | None]:
        if not module:
            return None, None, "unresolved target module"
        if symbol is None:
            target_id = f"module:{module}"
            node = raw_nodes.get(target_id)
            return (target_id, node, None if node else "unresolved target module")
        exact = f"{module}.{symbol}"
        node = raw_nodes.get(exact)
        if node:
            return exact, node, None
        module_node = raw_nodes.get(f"module:{module}")
        if module_node:
            return f"module:{module}", module_node, "unresolved target symbol"
        return None, None, "unresolved target module or symbol"

    @staticmethod
    def _declaration_key(item: _Declaration) -> tuple[str, str, str, str, int]:
        return item.path, item.provenance, item.declared_name, item.declared_target, item.line

    @staticmethod
    def _stable_id(item: _Declaration) -> str:
        token = "|".join((item.path, item.provenance, item.declared_name, item.declared_target))
        return f"evidence:entrypoint:{hashlib.sha1(token.encode()).hexdigest()[:16]}"

    @staticmethod
    def _read(path: Path) -> str:
        try:
            return path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            return ""

    @staticmethod
    def _line_for(text: str, value: str) -> int | None:
        if not value:
            return None
        for index, line in enumerate(text.splitlines(), start=1):
            if value in line:
                return index
        return None


__all__ = ["EntrypointAnalysis", "EntrypointAnalyzer"]