from __future__ import annotations

import pytest

from architecture_recovery.pipeline import analyze_repository
from architecture_recovery.profiling import AnalysisProfile
from architecture_recovery.visualization import VisualizationReadModelBuilder
from benchmarks.scale_profile import generate_scale_repository


@pytest.mark.parametrize("module_count", (50, 200, 400))
def test_scale_profile_counts_remain_linear(tmp_path, module_count):
    repository = generate_scale_repository(tmp_path / f"scale-{module_count}", module_count)
    profile = AnalysisProfile()
    ir = analyze_repository(repository, profile=profile)

    assert profile.stages["scanner"].counts["files"] == module_count + 1
    assert profile.stages["parser"].counts["parsed_files"] == module_count + 1
    assert len(ir.raw_graph.nodes) == 5 * module_count + 4
    assert len(ir.raw_graph.edges) == 7 * module_count + 2
    assert profile.stages["raw_graph"].counts["evidence"] == 7 * module_count + 2
    assert profile.total_seconds >= 0


def test_profile_registers_macro_stages_and_preserves_ir(tmp_path):
    repository = generate_scale_repository(tmp_path / "profile", 3)
    unprofiled = analyze_repository(repository)
    profile = AnalysisProfile()
    profiled = analyze_repository(repository, profile=profile)

    assert profiled.model_dump_json() == unprofiled.model_dump_json()
    assert set(profile.stages) >= {
        "scanner",
        "stack_detection",
        "parser",
        "symbol_resolution",
        "basic_data_flow",
        "raw_graph",
        "framework_adapters",
        "infrastructure_semantics",
        "source_origin",
        "architectural_graph",
        "component_detection",
        "architecture_ir",
        "architecture_hypotheses",
        "architecture_validation",
    }
    assert profile.stages["raw_graph"].counts["nodes"] == len(profiled.raw_graph.nodes)
    assert profile.stages["architecture_ir"].counts["raw_nodes"] == len(profiled.raw_graph.nodes)
    assert profile.stages["architecture_ir"].counts["architectural_nodes"] == len(profiled.architectural_graph.nodes)
    assert profile.stages["basic_data_flow"].counts["assignments"] >= 0


def test_boolean_profile_flag_is_semantically_additive(tmp_path):
    repository = generate_scale_repository(tmp_path / "boolean-profile", 2)
    assert analyze_repository(repository, profile=False).model_dump_json() == analyze_repository(
        repository, profile=True
    ).model_dump_json()


def test_profile_render_is_bounded_and_structured(tmp_path):
    repository = generate_scale_repository(tmp_path / "report", 2)
    profile = AnalysisProfile()
    analyze_repository(repository, profile=profile)
    report = profile.render_text()

    assert report.startswith("Architecture Recovery Profile")
    assert "raw_graph" in report
    assert "total" in report
    assert "module_0" not in report

def test_profile_separates_projection_and_read_model(tmp_path):
    repository = generate_scale_repository(tmp_path / "read-model-profile", 3)
    ir = analyze_repository(repository)
    profile = AnalysisProfile()

    model = VisualizationReadModelBuilder().build(ir, profile=profile)

    assert model.metadata["projected_edge_validity"] is True
    assert set(profile.stages) >= {
        "architectural_significance_projection",
        "visualization_read_model",
    }
    assert profile.stages["architectural_significance_projection"].seconds >= 0
    assert profile.stages["visualization_read_model"].seconds >= 0

