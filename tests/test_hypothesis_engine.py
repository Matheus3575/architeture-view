from architecture_recovery.architecture import ArchitectureHypothesisEngine
from architecture_recovery.ir import ArchitectureIR, ArchitecturalGraph, Edge, EdgeType, Evidence, EvidenceSource, EvidenceStatus, FrameworkFact, Node, NodeType, RawCodeGraph, RepositoryInfo, SourceOrigin, SourceRef


def _ir(with_contradiction=True):
    nodes = [
        Node(id="api", type=NodeType.MODULE, name="api", layer="controllers", origin=SourceOrigin.FIRST_PARTY, evidence_refs=["ev-api"]),
        Node(id="service", type=NodeType.MODULE, name="service", layer="services", origin=SourceOrigin.FIRST_PARTY, evidence_refs=["ev-service"]),
        Node(id="repo", type=NodeType.MODULE, name="repo", layer="repositories", origin=SourceOrigin.FIRST_PARTY, evidence_refs=["ev-repo"]),
    ]
    edges = [
        Edge(id="edge-api-service", source="api", target="service", type=EdgeType.CALLS, evidence_refs=["ev-api-service"]),
        Edge(id="edge-service-repo", source="service", target="repo", type=EdgeType.CALLS, evidence_refs=["ev-service-repo"]),
    ]
    if with_contradiction:
        edges.append(Edge(id="edge-repo-api", source="repo", target="api", type=EdgeType.CALLS, evidence_refs=["ev-repo-api"]))
    evidence = [Evidence(id=item, source_type=EvidenceSource.CALL_GRAPH, detail=item, source=SourceRef(path="fixture.py", start_line=1)) for item in ["ev-api", "ev-service", "ev-repo", "ev-api-service", "ev-service-repo", "ev-repo-api"]]
    return ArchitectureIR(repository=RepositoryInfo(name="fixture", path="."), raw_graph=RawCodeGraph(nodes=nodes, edges=edges), architectural_graph=ArchitecturalGraph(nodes=nodes, edges=edges), evidence=evidence)


def test_layered_hypothesis_preserves_support_and_contradiction():
    hypothesis = ArchitectureHypothesisEngine().infer(_ir()).hypotheses[0]
    assert hypothesis.status == EvidenceStatus.UNCERTAIN
    assert hypothesis.confidence > 0
    assert hypothesis.supporting_evidence == ["ev-api-service", "ev-service-repo"]
    assert hypothesis.contradicting_evidence == ["ev-repo-api"]
    assert hypothesis.evidence_refs == sorted(set(hypothesis.supporting_evidence + hypothesis.contradicting_evidence))
    assert "contradicting" in hypothesis.explanation


def test_hypothesis_engine_is_deterministic():
    engine = ArchitectureHypothesisEngine()
    assert engine.infer(_ir()).model_dump_json() == engine.infer(_ir()).model_dump_json()


def test_layered_hypothesis_is_unknown_without_evidence_bearing_relations():
    ir = _ir(False)
    ir.raw_graph.edges = []
    ir.architectural_graph.edges = []
    result = ArchitectureHypothesisEngine().infer(ir).hypotheses[0]
    assert result.status == EvidenceStatus.UNKNOWN
    assert result.confidence == 0
    assert result.evidence_refs == []




def test_layered_hypothesis_can_use_infrastructure_as_terminal_layer():
    ir = _ir(False)
    ir.raw_graph.nodes.append(Node(id="database", type=NodeType.DATABASE, name="postgres", origin=SourceOrigin.UNKNOWN))
    ir.raw_graph.edges.append(Edge(id="edge-repo-database", source="repo", target="database", type=EdgeType.DEPENDS_ON, evidence_refs=["ev-repo-database"]))
    ir.evidence.append(Evidence(id="ev-repo-database", source_type=EvidenceSource.DOCKER_COMPOSE, detail="repo depends on postgres", source=SourceRef(path="docker-compose.yml", start_line=3)))
    hypothesis = ArchitectureHypothesisEngine().infer(ir).hypotheses[0]
    assert hypothesis.status == EvidenceStatus.INFERRED
    assert "ev-repo-database" in hypothesis.supporting_evidence


def _mvc_ir(with_contradiction=False, names_only=False):
    nodes = [
        Node(id="controller", type=NodeType.MODULE, name="controllers", layer="controllers", origin=SourceOrigin.FIRST_PARTY),
        Node(id="model", type=NodeType.MODULE, name="models", layer="models", origin=SourceOrigin.FIRST_PARTY),
        Node(id="repo", type=NodeType.MODULE, name="repository", layer="repositories", origin=SourceOrigin.FIRST_PARTY),
    ]
    edges = []
    evidence = []
    if not names_only:
        edges = [
            Edge(id="mvc-controller-model", source="controller", target="model", type=EdgeType.CALLS, evidence_refs=["mvc-controller-model"]),
            Edge(id="mvc-model-repo", source="model", target="repo", type=EdgeType.CALLS, evidence_refs=["mvc-model-repo"]),
        ]
        evidence.extend(
            Evidence(id=ref, source_type=EvidenceSource.CALL_GRAPH, detail=ref, source=SourceRef(path="fixture.py", start_line=1))
            for ref in ["mvc-controller-model", "mvc-model-repo", "mvc-http", "mvc-contradiction"]
        )
    if with_contradiction:
        edges.append(Edge(id="mvc-controller-repo", source="controller", target="repo", type=EdgeType.CALLS, evidence_refs=["mvc-contradiction"]))
    facts = [] if names_only else [
        FrameworkFact(kind="HTTP_ENDPOINT", subject="controller", evidence_refs=["mvc-http"])
    ]
    return ArchitectureIR(
        repository=RepositoryInfo(name="mvc", path="."),
        raw_graph=RawCodeGraph(nodes=nodes, edges=edges),
        architectural_graph=ArchitecturalGraph(nodes=nodes, edges=edges),
        framework_facts=facts,
        evidence=evidence,
    )


def test_mvc_hypothesis_requires_semantic_relations_and_is_traceable():
    result = ArchitectureHypothesisEngine().infer(_mvc_ir())
    hypotheses = {item.pattern: item for item in result.hypotheses}
    assert hypotheses["mvc"].status == EvidenceStatus.INFERRED
    assert hypotheses["mvc"].supporting_evidence
    assert hypotheses["mvc"].evidence_refs == sorted(set(hypotheses["mvc"].supporting_evidence))
    assert "layered" in hypotheses


def test_mvc_names_only_remains_unknown():
    hypothesis = {item.pattern: item for item in ArchitectureHypothesisEngine().infer(_mvc_ir(names_only=True)).hypotheses}["mvc"]
    assert hypothesis.status == EvidenceStatus.UNKNOWN
    assert hypothesis.confidence == 0
    assert hypothesis.supporting_evidence == []


def test_mvc_preserves_direct_controller_persistence_contradiction():
    hypothesis = {item.pattern: item for item in ArchitectureHypothesisEngine().infer(_mvc_ir(with_contradiction=True)).hypotheses}["mvc"]
    assert hypothesis.status == EvidenceStatus.INFERRED
    assert "mvc-contradiction" in hypothesis.contradicting_evidence
    assert "mvc-contradiction" in hypothesis.evidence_refs


def _hexagonal_ir(with_contradiction=False, names_only=False):
    nodes = [
        Node(id="http", type=NodeType.MODULE, name="http", layer="controllers", origin=SourceOrigin.FIRST_PARTY),
        Node(id="service", type=NodeType.MODULE, name="service", layer="domain", origin=SourceOrigin.FIRST_PARTY),
        Node(id="port", type=NodeType.INTERFACE, name="UserPort", layer="ports", origin=SourceOrigin.FIRST_PARTY),
        Node(id="adapter", type=NodeType.MODULE, name="SqlAdapter", layer="infrastructure", origin=SourceOrigin.FIRST_PARTY),
        Node(id="database", type=NodeType.DATABASE, name="postgres", origin=SourceOrigin.THIRD_PARTY),
    ]
    edges = []
    facts = []
    refs = ["hex-input", "hex-port", "hex-adapter", "hex-http", "hex-contradiction"]
    if not names_only:
        edges = [
            Edge(id="hex-edge-input", source="http", target="service", type=EdgeType.CALLS, evidence_refs=["hex-input"]),
            Edge(id="hex-edge-port", source="service", target="port", type=EdgeType.DEPENDS_ON, evidence_refs=["hex-port"]),
            Edge(id="hex-edge-adapter", source="adapter", target="port", type=EdgeType.IMPLEMENTS, evidence_refs=["hex-adapter"]),
        ]
        facts = [FrameworkFact(kind="HTTP_ENDPOINT", subject="http", evidence_refs=["hex-http"])]
        if with_contradiction:
            edges.append(Edge(id="hex-edge-contradiction", source="service", target="database", type=EdgeType.DEPENDS_ON, evidence_refs=["hex-contradiction"]))
    evidence = [
        Evidence(id=ref, source_type=EvidenceSource.CALL_GRAPH, detail=ref, source=SourceRef(path="fixture.py", start_line=1))
        for ref in refs
    ]
    return ArchitectureIR(
        repository=RepositoryInfo(name="hexagonal", path="."),
        raw_graph=RawCodeGraph(nodes=nodes, edges=edges),
        architectural_graph=ArchitecturalGraph(nodes=nodes, edges=edges),
        framework_facts=facts,
        evidence=evidence,
    )


def test_hexagonal_hypothesis_requires_multiple_directional_signal_categories():
    hypotheses = {item.pattern: item for item in ArchitectureHypothesisEngine().infer(_hexagonal_ir()).hypotheses}
    hypothesis = hypotheses["hexagonal"]
    assert hypothesis.status == EvidenceStatus.INFERRED
    assert {"hex-input", "hex-port", "hex-adapter", "hex-http"} <= set(hypothesis.supporting_evidence)
    assert hypothesis.evidence_refs == sorted(set(hypothesis.supporting_evidence + hypothesis.contradicting_evidence))


def test_hexagonal_names_only_remains_unknown():
    hypothesis = {item.pattern: item for item in ArchitectureHypothesisEngine().infer(_hexagonal_ir(names_only=True)).hypotheses}["hexagonal"]
    assert hypothesis.status == EvidenceStatus.UNKNOWN
    assert hypothesis.confidence == 0
    assert hypothesis.supporting_evidence == []


def test_hexagonal_preserves_direct_core_infrastructure_contradiction():
    hypothesis = {item.pattern: item for item in ArchitectureHypothesisEngine().infer(_hexagonal_ir(with_contradiction=True)).hypotheses}["hexagonal"]
    assert hypothesis.status == EvidenceStatus.INFERRED
    assert "hex-contradiction" in hypothesis.contradicting_evidence
    assert "hex-contradiction" in hypothesis.evidence_refs


def test_hexagonal_core_infrastructure_only_is_not_confirmed():
    ir = _hexagonal_ir(names_only=True)
    ir.raw_graph.edges = [Edge(id="hex-edge-contradiction", source="service", target="database", type=EdgeType.DEPENDS_ON, evidence_refs=["hex-contradiction"])]
    ir.architectural_graph.edges = list(ir.raw_graph.edges)
    hypothesis = {item.pattern: item for item in ArchitectureHypothesisEngine().infer(ir).hypotheses}["hexagonal"]
    assert hypothesis.status == EvidenceStatus.UNKNOWN
    assert hypothesis.supporting_evidence == []
    assert hypothesis.contradicting_evidence == ["hex-contradiction"]
