from __future__ import annotations

from pathlib import Path

from architecture_recovery.frameworks import FastAPIAdapter
from architecture_recovery.pipeline import analyze_repository


ROOT = Path(__file__).parents[1]
FIXTURE = ROOT / "benchmarks" / "fixtures" / "fastapi_semantics"


def facts(ir, kind):
    return [fact for fact in ir.framework_facts if fact.kind == kind]


def test_fastapi_application_and_router_use_resolved_api_symbols():
    ir = analyze_repository(FIXTURE)

    application = facts(ir, "APPLICATION")
    routers = facts(ir, "ROUTER")
    assert any(item.attributes["application"] == "application" for item in application)
    assert any(
        item.attributes["router"] == "users_router"
        and item.attributes["symbol"] == "fastapi.APIRouter"
        and item.attributes["module"] == "api"
        for item in routers
    )


def test_fastapi_routes_preserve_method_path_and_handler():
    ir = analyze_repository(FIXTURE)

    endpoints = {(
        item.attributes["method"],
        item.attributes["path"],
        item.attributes["handler"],
    ) for item in facts(ir, "HTTP_ENDPOINT")}
    assert ("GET", "/users", "api.list_users") in endpoints
    assert ("POST", "/users", "api.create_user") in endpoints
    assert ("GET", "/ambiguous", "api.ambiguous_dependency") in endpoints


def test_fastapi_depends_response_schema_and_pydantic_model_are_semantic_facts():
    ir = analyze_repository(FIXTURE)

    assert any(
        item.attributes["consumer"] == "api.list_users"
        and item.attributes["provider"] == "logic.get_service"
        for item in facts(ir, "FRAMEWORK_DEPENDENCY")
    )
    assert any(
        item.attributes["endpoint"] == "api.list_users"
        and item.attributes["schema"] == "schemas.UserResponse"
        for item in facts(ir, "RESPONSE_SCHEMA")
    )
    assert any(
        item.attributes["model"] == "schemas.UserResponse"
        and item.attributes["base"] == "pydantic.BaseModel"
        for item in facts(ir, "SCHEMA")
    )


def test_fastapi_include_router_preserves_observed_metadata_without_path_composition():
    ir = analyze_repository(FIXTURE)
    inclusion = facts(ir, "ROUTER_INCLUSION")

    assert len(inclusion) == 1
    assert inclusion[0].attributes == {
        "application": "application",
        "router": "users_router",
        "prefix": "/v1",
        "tags": "['users']",
    }


def test_dynamic_dependency_is_unknown_and_traceable():
    ir = analyze_repository(FIXTURE)
    unknown = [
        item
        for item in facts(ir, "FRAMEWORK_DEPENDENCY")
        if item.subject == "api.ambiguous_dependency"
    ]

    assert len(unknown) == 1
    assert unknown[0].status.value == "unknown"
    assert unknown[0].target == "UNKNOWN"
    assert unknown[0].evidence_refs
    assert set(unknown[0].evidence_refs) <= {item.id for item in ir.evidence}


def test_generic_router_names_do_not_create_fastapi_endpoints():
    ir = analyze_repository(FIXTURE)
    paths = {item.attributes["path"] for item in facts(ir, "HTTP_ENDPOINT")}

    assert "/not-fastapi" not in paths
    assert "/other" not in paths


def test_adapter_does_not_destroy_raw_graph_or_add_architecture_hypotheses():
    ir = analyze_repository(FIXTURE)

    assert any(node.id == "external_symbol:fastapi.FastAPI" for node in ir.raw_graph.nodes)
    assert any(edge.type.value == "IMPORTS" for edge in ir.raw_graph.edges)
    assert all(fact.kind not in {"MVC", "CLEAN", "HEXAGONAL", "LAYERED", "MICROSERVICES"} for fact in ir.framework_facts)
    assert not any(hypothesis.pattern in {"MVC", "Clean", "Hexagonal", "Microservices"} for hypothesis in ir.architecture.hypotheses)


def test_framework_facts_are_deterministic_and_adapter_is_reference_implementation():
    first = analyze_repository(FIXTURE)
    second = analyze_repository(FIXTURE)

    assert first.model_dump_json() == second.model_dump_json()
    assert FastAPIAdapter().name == "FastAPI"
