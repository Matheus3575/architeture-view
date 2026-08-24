from architecture_recovery.architecture import ArchitectureHypothesisEngine
from architecture_recovery.ir import ArchitectureIR, ArchitecturalGraph, Edge, EdgeType, Evidence, EvidenceSource, EvidenceStatus, Node, NodeType, RawCodeGraph, RepositoryInfo, SourceOrigin, SourceRef


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
