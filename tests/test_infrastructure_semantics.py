from __future__ import annotations

from pathlib import Path

from architecture_recovery.pipeline import analyze_repository


ROOT = Path(__file__).parents[1]
FIXTURE = ROOT / "benchmarks" / "fixtures" / "infrastructure_semantics"


def test_infrastructure_semantics_discovers_and_classifies_resources():
    ir = analyze_repository(FIXTURE)

    # 1. Check resources
    resources_by_id = {res.id: res for res in ir.infrastructure_resources}

    assert "infrastructure:compose:docker-compose.yml:postgres" in resources_by_id
    postgres = resources_by_id["infrastructure:compose:docker-compose.yml:postgres"]
    assert postgres.name == "postgres"
    assert postgres.kind == "DATABASE"
    assert postgres.confidence == 1.0

    assert "infrastructure:compose:docker-compose.yml:redis" in resources_by_id
    redis = resources_by_id["infrastructure:compose:docker-compose.yml:redis"]
    assert redis.name == "redis"
    assert redis.kind == "CACHE"
    assert redis.confidence == 1.0

    assert "infrastructure:compose:docker-compose.yml:api" in resources_by_id
    api = resources_by_id["infrastructure:compose:docker-compose.yml:api"]
    assert api.name == "api"
    assert api.kind == "CONTAINER"
    assert api.confidence == 0.7

    assert "infrastructure:compose:docker-compose.yml:database" in resources_by_id
    database = resources_by_id["infrastructure:compose:docker-compose.yml:database"]
    assert database.name == "database"
    # generic name with non-db image alpine -> UNKNOWN
    assert database.kind == "UNKNOWN"
    assert database.confidence == 0.5

    assert "infrastructure:dockerfile:Dockerfile" in resources_by_id
    dockerfile = resources_by_id["infrastructure:dockerfile:Dockerfile"]
    assert dockerfile.name == "Dockerfile"
    assert dockerfile.kind == "CONTAINER"
    assert dockerfile.confidence == 1.0


def test_infrastructure_semantics_resolves_relations_and_connections():
    ir = analyze_repository(FIXTURE)

    # Check relations
    relations = ir.infrastructure_relations

    # We expect:
    # 1. api depends_on postgres (compose)
    # 2. api depends_on redis (compose)
    # 3. module:main depends_on configuration:DATABASE_URL (code to config)
    # 4. module:main depends_on configuration:REDIS_URL (code to config)
    # 5. configuration:DATABASE_URL connects_to postgres (config to compose)
    # 6. configuration:REDIS_URL connects_to redis (config to compose)
    # 7. component:root depends_on postgres (projected code/component to compose)
    # 8. component:root depends_on redis (projected code/component to compose)

    assert any(
        r.source == "infrastructure:compose:docker-compose.yml:api"
        and r.target == "infrastructure:compose:docker-compose.yml:postgres"
        and r.type == "depends_on"
        for r in relations
    )

    assert any(
        r.source == "infrastructure:compose:docker-compose.yml:api"
        and r.target == "infrastructure:compose:docker-compose.yml:redis"
        and r.type == "depends_on"
        for r in relations
    )

    assert any(
        r.source == "module:main"
        and r.target == "configuration:DATABASE_URL"
        and r.type == "depends_on"
        for r in relations
    )

    assert any(
        r.source == "configuration:DATABASE_URL"
        and r.target == "infrastructure:compose:docker-compose.yml:postgres"
        and r.type == "connects_to"
        for r in relations
    )

    assert any(
        r.source == "component:main.py"
        and r.target == "infrastructure:compose:docker-compose.yml:postgres"
        and r.type == "depends_on"
        for r in relations
    )


def test_fake_database_and_unresolved_env_vars_remain_unknown():
    ir = analyze_repository(FIXTURE)
    relations = ir.infrastructure_relations

    # 1. FAKE_DB is accessed in code, but NOT configured in Compose.
    # Therefore, no configuration:FAKE_DB resource or relation to it should be created.
    assert not any(r.target == "configuration:FAKE_DB" for r in relations)

    # 2. UNKNOWN_URL is configured in Compose, but not referenced by target services in Compose.
    # So configuration:UNKNOWN_URL connects_to some target is NOT created.
    assert not any(r.source == "configuration:UNKNOWN_URL" and r.type == "connects_to" for r in relations)

    # 3. database (alpine) does NOT get related to main since no env var points to it.
    assert not any(
        r.target == "infrastructure:compose:docker-compose.yml:database"
        for r in relations
    )


def test_infrastructure_traceability_and_evidence():
    ir = analyze_repository(FIXTURE)
    evidence_ids = {ev.id for ev in ir.evidence}

    # All resources and relations must trace to valid evidence refs
    for res in ir.infrastructure_resources:
        assert res.evidence_refs
        assert set(res.evidence_refs) <= evidence_ids

    for rel in ir.infrastructure_relations:
        assert rel.evidence_refs
        assert set(rel.evidence_refs) <= evidence_ids


def test_raw_graph_preservation_and_integrity():
    ir = analyze_repository(FIXTURE)
    nodes = {node.id: node for node in ir.raw_graph.nodes}
    edges = {(edge.source, edge.target, edge.type.value) for edge in ir.raw_graph.edges}

    # Verify that raw nodes contain the containers
    assert "container:postgres" in nodes
    assert nodes["container:postgres"].type.value == "database"

    assert "container:redis" in nodes
    assert nodes["container:redis"].type.value == "cache"

    assert "container:api" in nodes
    assert nodes["container:api"].type.value == "container"

    assert "container:database" in nodes
    assert nodes["container:database"].type.value == "container"

    # Verify relationships in raw graph
    assert ("container:api", "container:postgres", "CONNECTS_TO") in edges
    assert ("module:main", "configuration:DATABASE_URL", "DEPENDS_ON") in edges
    assert ("configuration:DATABASE_URL", "container:postgres", "CONNECTS_TO") in edges
