from __future__ import annotations

from pathlib import Path

import architecture_recovery.classification.python as python_classification
from architecture_recovery.ir import EdgeType, NodeType, SourceOrigin
from architecture_recovery.graph import GraphAggregationConfig
from architecture_recovery.pipeline import analyze_repository
from architecture_recovery.parsing import ImportFact
from architecture_recovery.scanner import RepositoryScanner
from architecture_recovery.classification import PythonRepositoryClassifier


ROOT = Path(__file__).parents[1]
FASTAPI_FIXTURE = ROOT / "examples" / "fastapi_sample"


def test_raw_graph_preserves_external_symbols_but_architecture_aggregates_packages():
    ir = analyze_repository(FASTAPI_FIXTURE)

    raw_external = [node for node in ir.raw_graph.nodes if node.origin == SourceOrigin.THIRD_PARTY]
    assert any(node.name == "Depends" for node in raw_external)
    assert any(node.name == "BaseModel" for node in raw_external)
    assert any(node.name == "FastAPI" for node in raw_external)

    architectural_ids = {node.id for node in ir.architectural_graph.nodes}
    architectural_names = {node.name for node in ir.architectural_graph.nodes}
    assert "external.fastapi" in architectural_ids
    assert "external.pydantic" in architectural_ids
    assert "Depends" not in architectural_names
    assert "BaseModel" not in architectural_names
    assert all(edge.evidence_refs for edge in ir.architectural_graph.edges)
    assert all(edge.raw_edge_ids for edge in ir.architectural_graph.edges)
    assert ir.validation.valid


def test_classification_report_exposes_first_party_third_party_and_stdlib():
    ir = analyze_repository(FASTAPI_FIXTURE)

    assert ir.classifications.counts[SourceOrigin.FIRST_PARTY.value] > 0
    assert ir.classifications.counts[SourceOrigin.THIRD_PARTY.value] > 0
    assert ir.classifications.counts[SourceOrigin.STANDARD_LIBRARY.value] > 0
    assert any(node.name == "os" and node.origin == SourceOrigin.STANDARD_LIBRARY for node in ir.raw_graph.nodes)


def test_src_layout_and_vendor_boundary_are_distinguished():
    ir = analyze_repository(FASTAPI_FIXTURE)

    core = next(node for node in ir.raw_graph.nodes if node.id == "app.core.core_value")
    vendor = next(node for node in ir.raw_graph.nodes if node.id == "vendor.third_party.vendored_helper")
    assert core.origin == SourceOrigin.FIRST_PARTY
    assert vendor.origin == SourceOrigin.THIRD_PARTY


def test_generated_code_has_a_distinct_origin():
    ir = analyze_repository(FASTAPI_FIXTURE)

    generated = next(node for node in ir.raw_graph.nodes if node.id == "generated.schema_generated.generated_schema")
    assert generated.origin == SourceOrigin.GENERATED


def test_unknown_import_remains_unknown_and_is_aggregated_without_invention(tmp_path):
    (tmp_path / "app").mkdir()
    (tmp_path / "app" / "main.py").write_text(
        "import mystery_package\n\n\ndef run():\n    return mystery_package.run()\n",
        encoding="utf-8",
    )

    ir = analyze_repository(tmp_path)

    unknown = [node for node in ir.raw_graph.nodes if node.origin == SourceOrigin.UNKNOWN]
    assert any(node.metadata.get("external_package") == "mystery_package" for node in unknown)
    assert any(node.origin == SourceOrigin.UNKNOWN for node in ir.architectural_graph.nodes)
    assert all(edge.source in {node.id for node in ir.architectural_graph.nodes} for edge in ir.architectural_graph.edges)
    assert ir.validation.valid


def test_pyproject_dependency_is_used_as_classification_evidence(tmp_path):
    (tmp_path / "pyproject.toml").write_text(
        "[project]\ndependencies = [\"pydantic>=2.7\"]\n",
        encoding="utf-8",
    )
    (tmp_path / "main.py").write_text(
        "from pydantic import BaseModel\n\n\nclass Item(BaseModel):\n    pass\n",
        encoding="utf-8",
    )

    ir = analyze_repository(tmp_path)

    pydantic = next(node for node in ir.raw_graph.nodes if node.name == "BaseModel")
    assert pydantic.origin == SourceOrigin.THIRD_PARTY
    record = next(record for record in ir.classifications.records if record.node_id == pydantic.id)
    assert "dependency manifest" in record.reason


def test_installed_distribution_metadata_is_used_when_module_location_is_unavailable(monkeypatch, tmp_path):
    (tmp_path / "main.py").write_text("import distribution_only\n", encoding="utf-8")
    monkeypatch.setattr(python_classification.importlib.util, "find_spec", lambda package: None)
    monkeypatch.setattr(
        python_classification.importlib.metadata,
        "packages_distributions",
        lambda: {"distribution_only": ["distribution-only"]},
    )

    ir = analyze_repository(tmp_path)

    dependency = next(node for node in ir.raw_graph.nodes if node.name == "distribution_only")
    assert dependency.origin == SourceOrigin.THIRD_PARTY
    record = next(record for record in ir.classifications.records if record.node_id == dependency.id)
    assert "installed distribution" in record.reason


def test_similar_local_and_external_module_names_keep_their_origins(tmp_path):
    (tmp_path / "app").mkdir()
    (tmp_path / "vendor").mkdir()
    (tmp_path / "app" / "utils.py").write_text("def local_value():\n    return 1\n", encoding="utf-8")
    (tmp_path / "vendor" / "utils.py").write_text("def external_value():\n    return 2\n", encoding="utf-8")
    (tmp_path / "main.py").write_text(
        "from app.utils import local_value\nfrom vendor.utils import external_value\n",
        encoding="utf-8",
    )

    ir = analyze_repository(tmp_path)

    local = next(node for node in ir.raw_graph.nodes if node.id == "app.utils.local_value")
    external = next(node for node in ir.raw_graph.nodes if node.id == "vendor.utils.external_value")
    assert local.origin == SourceOrigin.FIRST_PARTY
    assert external.origin == SourceOrigin.THIRD_PARTY


def test_architectural_edges_keep_dependency_semantics():
    ir = analyze_repository(FASTAPI_FIXTURE)

    assert any(edge.type == EdgeType.DEPENDS_ON and edge.target == "external.fastapi" for edge in ir.architectural_graph.edges)
    assert not any(edge.type == EdgeType.CALLS for edge in ir.architectural_graph.edges)


def test_aggregation_policy_can_include_standard_library():
    ir = analyze_repository(
        FASTAPI_FIXTURE,
        aggregation_config=GraphAggregationConfig(include_standard_library=True),
    )

    assert any(node.id == "external.os" for node in ir.architectural_graph.nodes)


def test_aggregation_policy_can_exclude_unknown(tmp_path):
    (tmp_path / "main.py").write_text("import unresolved_package\n", encoding="utf-8")

    ir = analyze_repository(
        tmp_path,
        aggregation_config=GraphAggregationConfig(include_unknown=False),
    )

    assert not any(node.origin == SourceOrigin.UNKNOWN for node in ir.architectural_graph.nodes)


def test_boundary_discovers_src_and_monorepo_pyproject_import_roots(tmp_path):
    for package in ("catalog", "billing"):
        package_root = tmp_path / "packages" / package
        source = package_root / "src" / package
        source.mkdir(parents=True)
        (package_root / "pyproject.toml").write_text(
            '[tool.setuptools.package-dir]\n"" = "src"\n',
            encoding="utf-8",
        )
        (source / "models.py").write_text("class Item: pass\n", encoding="utf-8")

    snapshot = RepositoryScanner().scan(tmp_path)

    assert tmp_path / "packages/catalog/src" in snapshot.boundary.import_roots
    assert tmp_path / "packages/billing/src" in snapshot.boundary.import_roots
    assert snapshot.boundary.resolve_local_module("catalog.models") == (
        tmp_path / "packages/catalog/src/catalog/models.py"
    ).resolve()


def test_namespace_package_without_init_is_a_local_module_candidate(tmp_path):
    module = tmp_path / "src" / "shared_namespace" / "utilities.py"
    module.parent.mkdir(parents=True)
    module.write_text("def value(): return 1\n", encoding="utf-8")

    snapshot = RepositoryScanner().scan(tmp_path)

    candidates = snapshot.boundary.module_candidates("shared_namespace")
    assert candidates == ((tmp_path / "src/shared_namespace").resolve(),)


def test_ambiguous_local_module_origin_is_unknown(tmp_path):
    for root in (tmp_path / "src", tmp_path / "alternate"):
        module = root / "shared" / "utils.py"
        module.parent.mkdir(parents=True)
        module.write_text("def value(): return 1\n", encoding="utf-8")
    (tmp_path / "alternate" / "pyproject.toml").write_text(
        '[tool.setuptools.package-dir]\n"" = "."\n',
        encoding="utf-8",
    )

    snapshot = RepositoryScanner().scan(tmp_path)
    classifier = PythonRepositoryClassifier(snapshot, [])
    resolution = classifier.resolve_import(
        ImportFact("main", "shared.utils", "utils", "main.py", 1)
    )

    assert resolution.origin == SourceOrigin.UNKNOWN
    assert "Multiple repository package roots" in resolution.reason


def test_local_module_resolution_precedes_environment_lookup(tmp_path, monkeypatch):
    (tmp_path / "local_package.py").write_text("value = 1\n", encoding="utf-8")
    snapshot = RepositoryScanner().scan(tmp_path)
    classifier = PythonRepositoryClassifier(snapshot, [])
    monkeypatch.setattr(
        python_classification.importlib.util,
        "find_spec",
        lambda package: (_ for _ in ()).throw(AssertionError("environment lookup should not run")),
    )

    resolution = classifier.resolve_import(
        ImportFact("main", "local_package", "local_package", "main.py", 1)
    )

    assert resolution.origin == SourceOrigin.FIRST_PARTY
