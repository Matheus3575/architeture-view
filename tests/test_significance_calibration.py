from architecture_recovery.ir import (
    ArchitecturalGraph,
    ArchitectureIR,
    Component,
    Edge,
    EdgeType,
    Evidence,
    EvidenceSource,
    EvidenceStatus,
    FrameworkFact,
    InfrastructureRelation,
    InfrastructureResource,
    Node,
    NodeType,
    RawCodeGraph,
    RepositoryInfo,
    SourceOrigin,
    SourceRef,
    StackProfile,
    Technology,
)
from architecture_recovery.visualization import (
    ArchitecturalProjectionBuilder,
    SignificanceLevel,
    VisualizationReadModelBuilder,
)


def _calibration_ir():
    evidence_ids = [
        "app", "entry", "core", "utility", "tests", "framework", "helper", "driver",
        "endpoint", "dependency", "database", "flow", "import", "infra",
    ]
    evidence = [
        Evidence(
            id=item,
            source_type=EvidenceSource.AST,
            detail=item,
            source=SourceRef(path=f"{item}.py", start_line=1),
        )
        for item in evidence_ids
    ]
    raw_nodes = [
        Node(id="module:entry", type=NodeType.MODULE, name="entry", source=SourceRef(path="app/entry.py", start_line=1), evidence_refs=["entry"]),
        Node(id="module:core", type=NodeType.MODULE, name="core", source=SourceRef(path="app/core.py", start_line=1), evidence_refs=["core"]),
        Node(id="module:utility", type=NodeType.MODULE, name="utility", source=SourceRef(path="app/utility.py", start_line=1), evidence_refs=["utility"]),
        Node(id="module:tests", type=NodeType.MODULE, name="tests", source=SourceRef(path="tests/test_app.py", start_line=1), evidence_refs=["tests"]),
        Node(id="external:mainframework", type=NodeType.MODULE, name="mainframework", origin=SourceOrigin.THIRD_PARTY, evidence_refs=["framework"]),
        Node(id="external:helperlib", type=NodeType.MODULE, name="helperlib", origin=SourceOrigin.THIRD_PARTY, evidence_refs=["helper"]),
        Node(id="external:dbdriver", type=NodeType.MODULE, name="dbdriver", origin=SourceOrigin.THIRD_PARTY, evidence_refs=["driver"]),
    ]
    arch_nodes = [
        Node(id="repository:calibration", type=NodeType.REPOSITORY, name="calibration", evidence_refs=["app"]),
        Node(id="application:calibration", type=NodeType.APPLICATION, name="calibration", evidence_refs=["app"]),
        Node(id="component:entry", type=NodeType.COMPONENT, name="entry", evidence_refs=["entry"], metadata={"raw_node_ids": ["module:entry"]}),
        Node(id="component:core", type=NodeType.COMPONENT, name="core", evidence_refs=["core"], metadata={"raw_node_ids": ["module:core"]}),
        Node(id="module:utility", type=NodeType.MODULE, name="utility", evidence_refs=["utility"], metadata={"raw_node_ids": ["module:utility"]}),
        Node(id="component:tests", type=NodeType.COMPONENT, name="tests", evidence_refs=["tests"], metadata={"raw_node_ids": ["module:tests"]}),
        Node(id="external.mainframework", type=NodeType.EXTERNAL_DEPENDENCY, name="mainframework", origin=SourceOrigin.THIRD_PARTY, evidence_refs=["framework"], metadata={"external_package": "mainframework", "raw_node_ids": ["external:mainframework"]}),
        Node(id="external.helperlib", type=NodeType.EXTERNAL_DEPENDENCY, name="helperlib", origin=SourceOrigin.THIRD_PARTY, evidence_refs=["helper"], metadata={"external_package": "helperlib", "raw_node_ids": ["external:helperlib"]}),
        Node(id="external.dbdriver", type=NodeType.EXTERNAL_DEPENDENCY, name="dbdriver", origin=SourceOrigin.THIRD_PARTY, evidence_refs=["driver"], metadata={"external_package": "dbdriver", "architectural_role": "database_driver", "raw_node_ids": ["external:dbdriver"]}),
        Node(id="module:unknown", type=NodeType.MODULE, name="unknown"),
    ]
    raw_edges = [
        Edge(id="raw-flow", source="module:entry", target="module:core", type=EdgeType.CALLS, evidence_refs=["flow"]),
        Edge(id="raw-import", source="module:core", target="module:utility", type=EdgeType.IMPORTS, evidence_refs=["import"]),
        Edge(id="raw-test-import", source="module:tests", target="module:entry", type=EdgeType.IMPORTS, evidence_refs=["tests"]),
    ]
    architectural_edges = [
        Edge(id="arch-entry-core", source="component:entry", target="component:core", type=EdgeType.DEPENDS_ON, evidence_refs=["dependency"], raw_edge_ids=["raw-flow"]),
        Edge(id="arch-core-utility", source="component:core", target="module:utility", type=EdgeType.DEPENDS_ON, evidence_refs=["import"], raw_edge_ids=["raw-import"]),
        Edge(id="arch-tests-entry", source="component:tests", target="component:entry", type=EdgeType.DEPENDS_ON, evidence_refs=["tests"], raw_edge_ids=["raw-test-import"]),
        Edge(id="arch-entry-framework", source="component:entry", target="external.mainframework", type=EdgeType.DEPENDS_ON, evidence_refs=["framework"]),
        Edge(id="arch-core-helper", source="component:core", target="external.helperlib", type=EdgeType.DEPENDS_ON, evidence_refs=["helper"]),
        Edge(id="arch-core-driver", source="component:core", target="external.dbdriver", type=EdgeType.DEPENDS_ON, evidence_refs=["driver"]),
    ]
    facts = [
        FrameworkFact(kind="APPLICATION", subject="application", attributes={"symbol": "mainframework.App", "module": "entry"}, evidence_refs=["app"]),
        FrameworkFact(kind="HTTP_ENDPOINT", subject="entry.handler", attributes={"module": "entry", "path": "/items"}, evidence_refs=["endpoint"]),
        FrameworkFact(kind="FRAMEWORK_DEPENDENCY", subject="core.service", target="core.service", attributes={"module": "core"}, evidence_refs=["dependency"]),
    ]
    return ArchitectureIR(
        repository=RepositoryInfo(name="calibration", path="."),
        raw_graph=RawCodeGraph(nodes=raw_nodes, edges=raw_edges),
        architectural_graph=ArchitecturalGraph(nodes=arch_nodes, edges=architectural_edges),
        framework_facts=facts,
        infrastructure_resources=[InfrastructureResource(id="database:primary", name="primary", kind="DATABASE", evidence_refs=["database"])],
        infrastructure_relations=[InfrastructureRelation(id="infra-core-db", source="component:core", target="database:primary", type="queries", evidence_refs=["infra"])],
        component_candidates=[Component(id="candidate:core", name="core", node_ids=["module:core", "module:utility"], evidence_refs=["core"])],
        evidence=evidence,
        stack=StackProfile(frameworks=[Technology(name="MainFramework", category="framework", evidence_refs=["framework"])]),
    )


def test_significance_uses_semantic_evidence_not_degree_or_structural_presence():
    projection = ArchitecturalProjectionBuilder().build(_calibration_ir())
    levels = {item.subject: item.significance for item in projection.significances}
    assert levels["application:calibration"] == SignificanceLevel.HIGH
    assert levels["component:entry"] == SignificanceLevel.HIGH
    assert levels["component:core"] == SignificanceLevel.HIGH
    assert levels["database:primary"] == SignificanceLevel.HIGH
    assert levels["external.mainframework"] == SignificanceLevel.HIGH
    assert levels["external.dbdriver"] == SignificanceLevel.MEDIUM
    assert levels["external.helperlib"] == SignificanceLevel.LOW
    assert levels["module:utility"] == SignificanceLevel.LOW
    assert levels["component:tests"] == SignificanceLevel.LOW
    assert levels["module:unknown"] == SignificanceLevel.UNKNOWN


def test_external_dependency_precision_and_projection_traceability():
    ir = _calibration_ir()
    projection = ArchitecturalProjectionBuilder().build(ir)
    expected = {
        "repository:calibration",
        "application:calibration",
        "component:entry",
        "component:core",
        "external.mainframework",
        "external.dbdriver",
        "database:primary",
    }
    projected = set(projection.projected_node_ids)
    assert expected <= projected
    assert not {"external.helperlib", "module:utility", "component:tests"} & projected
    assert all(edge.source in projected and edge.target in projected for edge in projection.projected_edges)
    assert all(ref in {item.id for item in ir.evidence} for item in projection.significances for ref in item.evidence_refs)
    ext = {item.subject: item.significance for item in projection.significances if item.subject.startswith("external.")}
    assert ext == {
        "external.dbdriver": SignificanceLevel.MEDIUM,
        "external.helperlib": SignificanceLevel.LOW,
        "external.mainframework": SignificanceLevel.HIGH,
    }


def test_detailed_model_is_preserved_and_projection_is_deterministic():
    ir = _calibration_ir()
    first = VisualizationReadModelBuilder().build(ir)
    second = VisualizationReadModelBuilder().build(ir)
    assert first.model_dump_json() == second.model_dump_json()
    assert first.metadata["detailed_node_count"] == 11
    assert first.metadata["high_level_node_count"] < first.metadata["detailed_node_count"]
    assert first.metadata["projection_traceability"] is True
    assert first.metadata["projected_edge_validity"] is True
    assert {item.subject for item in first.architectural_significance} >= {
        "external.helperlib", "module:utility", "component:tests", "module:unknown",
    }


def test_significance_precision_recall_metrics_are_perfect_for_controlled_fixture():
    projection = ArchitecturalProjectionBuilder().build(_calibration_ir())
    expected = {
        "application:calibration", "component:entry", "component:core",
        "external.mainframework", "external.dbdriver", "database:primary",
    }
    actual = {
        item.subject for item in projection.significances
        if item.significance in {SignificanceLevel.HIGH, SignificanceLevel.MEDIUM}
    }
    assert expected <= actual
    assert len(expected & actual) / len(expected) == 1.0
    assert len(expected & actual) / len(actual) == 1.0
