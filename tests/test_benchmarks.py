from benchmarks.runner import evaluate_case, run_benchmarks
from architecture_recovery.pipeline import analyze_repository


def test_controlled_benchmarks_pass_and_report_metrics():
    results = run_benchmarks()

    assert {result["name"] for result in results} == {
        "component_detection",
        "fastapi_semantics",
        "fastapi_sample",
        "simple_python_layered",
        "src_layout",
        "monorepo",
        "namespace_package",
        "ambiguous_short_name",
        "scoped_type_hints",
        "duplicate_edge_evidence",
        "dynamic_dispatch",
        "basic_data_flow",
        "infrastructure_semantics",
    }
    assert all(result["passed"] for result in results)
    assert all(result["execution_passed"] for result in results)
    assert all(result["quality_gate_passed"] for result in results)
    assert all(result["metrics"]["deterministic"] for result in results)
    assert all(
        result["metrics"]["source_origin_accuracy"] in {1.0, None}
        for result in results
    )
    assert all(result["metrics"]["raw_edge_precision"] is None for result in results)


def test_benchmark_detects_wrong_resolution_separately_from_unknown():
    ir = analyze_repository("benchmarks/fixtures/ambiguous_short_name")
    result = evaluate_case(
        ir,
        ir,
        {
            "symbol_resolutions": [
                {
                    "path": "consumer_explicit.py",
                    "line": 5,
                    "caller": "consumer_explicit.execute",
                    "callee": "save",
                    "status": "resolved",
                    "target": "module_b.save",
                }
            ]
        },
    )

    assert result["quality_gate_passed"] is False
    assert result["metrics"]["correct_resolution_count"] == 0
    assert result["metrics"]["unresolved_resolution_count"] == 0
    assert result["metrics"]["wrong_resolution_count"] == 1
    assert result["metrics"]["wrong_resolution_rate"] == 1.0
