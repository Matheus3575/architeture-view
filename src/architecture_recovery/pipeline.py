from __future__ import annotations

from pathlib import Path
from urllib.parse import unquote, urlparse

from architecture_recovery.architecture import ArchitectureInferer
from architecture_recovery.classification import PythonRepositoryClassifier
from architecture_recovery.components import ComponentDetectionContext, ComponentDetector
from architecture_recovery.graph import (
    ArchitecturalGraphBuilder,
    GraphAggregationConfig,
    GraphBuilder,
    PropertyGraph,
)
from architecture_recovery.infrastructure import InfrastructureAnalyzer
from architecture_recovery.frameworks import (
    FrameworkAdapter,
    FrameworkAnalysisContext,
    FrameworkAdapterRegistry,
    default_registry,
)
from architecture_recovery.ir import (
    ArchitecturalGraph,
    ArchitectureIR,
    Component,
    Evidence,
    EvidenceSource,
    EvidenceStatus,
    RepositoryInfo,
    RawCodeGraph,
    SourceRef,
)
from architecture_recovery.parsing import ParseFacts, PythonParser
from architecture_recovery.repository import cloned_repository, is_repository_url
from architecture_recovery.scanner import FileKind, RepositoryScanner
from architecture_recovery.stack import StackDetector
from architecture_recovery.symbols import SymbolResolver
from architecture_recovery.validation import ArchitectureValidator


def analyze_repository(
    repository: str | Path,
    ref: str | None = None,
    aggregation_config: GraphAggregationConfig | None = None,
    framework_adapters: tuple[FrameworkAdapter, ...] | None = None,
) -> ArchitectureIR:
    """Analyze a local repository or clone and analyze a repository URL."""
    repository_value = str(repository)
    if is_repository_url(repository_value):
        with cloned_repository(repository_value, ref=ref) as local_path:
            return _analyze_local_repository(
                local_path,
                source_url=repository_value,
                aggregation_config=aggregation_config,
                framework_adapters=framework_adapters,
            )
    if ref:
        raise ValueError("--ref/--branch can only be used with a repository URL")
    return _analyze_local_repository(
        repository_value,
        aggregation_config=aggregation_config,
        framework_adapters=framework_adapters,
    )


def _analyze_local_repository(
    repository_path: str | Path,
    source_url: str | None = None,
    aggregation_config: GraphAggregationConfig | None = None,
    framework_adapters: tuple[FrameworkAdapter, ...] | None = None,
) -> ArchitectureIR:
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
            facts = parser.parse(
                file.path,
                file.absolute_path.read_text(encoding="utf-8", errors="ignore"),
                module_name_override=_python_module_name(snapshot, file.path),
            )
        except OSError as exc:
            facts = ParseFacts(
                path=file.path,
                module_name=_python_module_name(snapshot, file.path),
                errors=[str(exc)],
            )
        parsed_files.append(facts)
        parse_warnings.extend(f"{file.path}: {error}" for error in facts.errors)

    symbols = SymbolResolver().resolve(parsed_files)
    classifier = PythonRepositoryClassifier(snapshot, parsed_files)
    graph = GraphBuilder().build(snapshot, parsed_files, symbols, classifier=classifier)
    framework_context = FrameworkAnalysisContext(
        raw_graph=graph,
        parsed_files=tuple(parsed_files),
        symbols=symbols,
    )
    registry = FrameworkAdapterRegistry(framework_adapters) if framework_adapters is not None else default_registry()
    framework_results = registry.analyze(framework_context)
    framework_facts = [fact for result in framework_results for fact in result.facts]
    framework_evidence = [evidence for result in framework_results for evidence in result.evidence]
    infra_analyzer = InfrastructureAnalyzer()
    infra_analyzer.augment(graph, snapshot)
    classifications = classifier.classify_graph(graph)
    aggregated = ArchitecturalGraphBuilder(aggregation_config).build(graph, snapshot)
    architectural_graph = PropertyGraph(
        nodes=aggregated.nodes,
        edges=aggregated.edges,
        evidence=aggregated.evidence,
    )

    arch_graph_model = ArchitecturalGraph(
        nodes=list(aggregated.nodes.values()),
        edges=aggregated.edges,
    )

    component_detection = ComponentDetector().detect(
        ComponentDetectionContext(
            raw_graph=graph,
            architectural_graph=arch_graph_model,
            framework_facts=tuple(framework_facts),
        )
    )

    infra_analyzer.resolve(
        graph,
        tuple(parsed_files),
        component_detection.candidates,
        arch_graph_model,
    )

    evidence_by_id = {
        item.id: item
        for item in [
            *stack_evidence,
            *graph.evidence.values(),
            *framework_evidence,
            *aggregated.evidence.values(),
            *component_detection.evidence,
            *infra_analyzer.evidence,
        ]
    }
    ir = ArchitectureIR(
        repository=RepositoryInfo(
            name=_repository_name(snapshot, source_url),
            path=snapshot.root.as_posix(),
            source_url=source_url,
        ),
        raw_graph=RawCodeGraph(
            nodes=list(graph.nodes.values()),
            edges=graph.edges,
            unresolved_calls=graph.unresolved_calls,
        ),
        architectural_graph=arch_graph_model,
        classifications=classifications,
        stack=stack,
        nodes=list(graph.nodes.values()),
        edges=graph.edges,
        components=aggregated.components,
        component_candidates=component_detection.candidates,
        component_unassigned_node_ids=component_detection.unassigned_node_ids,
        component_detection_metrics=component_detection.metrics,
        evidence=list(evidence_by_id.values()),
        framework_facts=framework_facts,
        infrastructure_resources=infra_analyzer.resources,
        infrastructure_relations=infra_analyzer.relations,
    ).canonicalize()
    validator = ArchitectureValidator()
    structural_report = validator.validate(ir)
    structural_report.warnings.extend(parse_warnings)
    ir.validation = structural_report

    if structural_report.valid:
        ir.architecture = ArchitectureInferer().infer(graph, stack)

    final_report = validator.validate(ir)
    final_report.warnings = sorted(set(structural_report.warnings + final_report.warnings))
    ir.validation = final_report
    return ir.canonicalize()


def _repository_name(snapshot, source_url: str | None) -> str:
    if not source_url:
        return snapshot.root.name
    path = unquote(urlparse(source_url).path.rstrip("/"))
    name = Path(path).name
    return name[:-4] if name.endswith(".git") else name or snapshot.root.name


def _python_module_name(snapshot, relative_path: str) -> str:
    """Derive import names from the most specific discovered import root."""
    absolute = (snapshot.root / relative_path).resolve()
    candidates: list[tuple[int, str]] = []
    for import_root in snapshot.boundary.import_roots or (snapshot.root,):
        try:
            relative = absolute.relative_to(import_root)
        except ValueError:
            continue
        candidates.append((len(import_root.parts), PythonParser.module_name(relative.as_posix())))
    if not candidates:
        return PythonParser.module_name(relative_path)
    return max(candidates, key=lambda item: item[0])[1]


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
