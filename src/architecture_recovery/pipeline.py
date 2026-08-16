from __future__ import annotations

from pathlib import Path
from urllib.parse import unquote, urlparse

from architecture_recovery.architecture import ArchitectureInferer
from architecture_recovery.graph import GraphBuilder
from architecture_recovery.infrastructure import InfrastructureAnalyzer
from architecture_recovery.ir import (
    ArchitectureIR,
    Component,
    Evidence,
    EvidenceSource,
    EvidenceStatus,
    RepositoryInfo,
    SourceRef,
)
from architecture_recovery.parsing import ParseFacts, PythonParser
from architecture_recovery.repository import cloned_repository, is_repository_url
from architecture_recovery.scanner import FileKind, RepositoryScanner
from architecture_recovery.stack import StackDetector
from architecture_recovery.symbols import SymbolResolver
from architecture_recovery.validation import ArchitectureValidator


def analyze_repository(repository: str | Path, ref: str | None = None) -> ArchitectureIR:
    """Analyze a local repository or clone and analyze a repository URL."""
    repository_value = str(repository)
    if is_repository_url(repository_value):
        with cloned_repository(repository_value, ref=ref) as local_path:
            return _analyze_local_repository(local_path, source_url=repository_value)
    if ref:
        raise ValueError("--ref/--branch can only be used with a repository URL")
    return _analyze_local_repository(repository_value)


def _analyze_local_repository(repository_path: str | Path, source_url: str | None = None) -> ArchitectureIR:
    scanner = RepositoryScanner()
    snapshot = scanner.scan(repository_path)
    stack, stack_evidence = StackDetector().detect(snapshot)

    parser = PythonParser()
    parsed_files: list[ParseFacts] = []
    parse_warnings: list[str] = []
    for file in snapshot.by_kind(FileKind.SOURCE):
        if file.language != "python":
            continue
        try:
            facts = parser.parse(file.path, file.absolute_path.read_text(encoding="utf-8", errors="ignore"))
        except OSError as exc:
            facts = ParseFacts(path=file.path, module_name=parser.module_name(file.path), errors=[str(exc)])
        parsed_files.append(facts)
        parse_warnings.extend(f"{file.path}: {error}" for error in facts.errors)

    symbols = SymbolResolver().resolve(parsed_files)
    graph = GraphBuilder().build(snapshot, parsed_files, symbols)
    InfrastructureAnalyzer().augment(graph, snapshot)
    architecture = ArchitectureInferer().infer(graph, stack)
    components, component_evidence = _components(snapshot, graph)

    ir = ArchitectureIR(
        repository=RepositoryInfo(
            name=_repository_name(snapshot, source_url),
            path=snapshot.root.as_posix(),
            source_url=source_url,
        ),
        stack=stack,
        nodes=list(graph.nodes.values()),
        edges=graph.edges,
        components=components,
        architecture=architecture,
        evidence=[*stack_evidence, *graph.evidence.values(), *component_evidence],
    ).canonicalize()
    report = ArchitectureValidator().validate(ir)
    report.warnings.extend(parse_warnings)
    ir.validation = report
    return ir.canonicalize()


def _repository_name(snapshot, source_url: str | None) -> str:
    if not source_url:
        return snapshot.root.name
    path = unquote(urlparse(source_url).path.rstrip("/"))
    name = Path(path).name
    return name[:-4] if name.endswith(".git") else name or snapshot.root.name


def _components(snapshot, graph):
    groups: dict[str, list[str]] = {}
    evidence: list[Evidence] = []
    for node in graph.nodes.values():
        if not node.source or node.type.value not in {"file", "module", "class", "function"}:
            continue
        prefix = node.source.path.split("/", 1)[0] if "/" in node.source.path else "root"
        groups.setdefault(prefix, []).append(node.id)

    components = []
    for prefix, node_ids in sorted(groups.items()):
        evidence_id = f"evidence:directory:{prefix}"
        evidence.append(
            Evidence(
                id=evidence_id,
                source_type=EvidenceSource.DIRECTORY_STRUCTURE,
                detail=f"Component grouped by source directory {prefix}",
                source=SourceRef(path=prefix),
            )
        )
        components.append(
            Component(
                id=f"component:{prefix}",
                name=prefix,
                level="component",
                node_ids=sorted(set(node_ids)),
                confidence=0.65,
                status=EvidenceStatus.INFERRED,
                evidence_refs=[evidence_id],
            )
        )
    return components, evidence
