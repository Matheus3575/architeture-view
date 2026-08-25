from pathlib import Path

from benchmarks.refinement_investigation import analyze_scenario, run_investigation


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_investigation_report_is_structural_and_deterministic():
    scenario = PROJECT_ROOT / "benchmarks" / "fixtures" / "significance_calibration"
    report = run_investigation(
        scenarios=(("significance_calibration", scenario),),
        include_generated=True,
    )

    assert report["algorithm_changes_applied"] is False
    assert report["timing_is_diagnostic"] is True
    assert {item["name"] for item in report["scenarios"]} == {
        "significance_calibration",
        "neutral_context_generated",
    }
    calibration = next(item for item in report["scenarios"] if item["name"] == "significance_calibration")
    assert calibration["quality"] == {
        "ground_truth_available": True,
        "significance_precision": 1.0,
        "significance_recall": 1.0,
        "false_architectural_promotions": 0,
        "expected_significant_count": 9,
        "actual_projected_count": 9,
    }
    for item in report["scenarios"]:
        assert all(item["determinism"].values())
        assert item["nodes"]["projection_closure_valid"] is True
        assert item["nodes"]["projection_traceability"] is True
        assert item["svg"]["static"]["valid"] is True
        assert item["svg"]["animated"]["valid"] is True
        assert item["svg"]["static"]["node_elements"] == item["nodes"]["projected_node_count"]


def test_investigation_detects_relation_representation_drift():
    repository = PROJECT_ROOT / "benchmarks" / "fixtures" / "infrastructure_semantics"
    result = analyze_scenario("infrastructure", repository)
    relation_metrics = result["relations"]

    assert "depends_on" in relation_metrics["infrastructure_type_counts"]
    assert "DEPENDS_ON" in relation_metrics["architectural_type_counts"]
    assert relation_metrics["mixed_case_relation_groups"]["DEPENDS_ON"] == [
        "DEPENDS_ON",
        "depends_on",
    ]
    assert 0.0 <= relation_metrics["projected_edge_evidence_coverage"] <= 1.0
    assert relation_metrics["projected_edge_count"] >= 1


def test_investigation_keeps_visual_metrics_separate_from_quality_metrics():
    repository = PROJECT_ROOT / "benchmarks" / "fixtures" / "visualization_read_model"
    result = analyze_scenario("visualization", repository)

    assert "significance_counts" in result["nodes"]
    assert "projected_edge_evidence_coverage" in result["relations"]
    assert "layout_groups" in result["svg"]["static"]
    assert result["svg"]["static"]["bytes"] != result["svg"]["animated"]["bytes"]