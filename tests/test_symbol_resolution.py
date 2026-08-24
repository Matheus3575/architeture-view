from architecture_recovery.ir import EdgeType
from architecture_recovery.ir import Edge, Node, NodeType
from architecture_recovery.graph import PropertyGraph
from architecture_recovery.parsing import PythonParser
from architecture_recovery.pipeline import analyze_repository
from architecture_recovery.symbols import SymbolResolver


def _parse(files: dict[str, str]):
    parser = PythonParser()
    return [parser.parse(path, source) for path, source in files.items()]


def test_alias_instantiation_and_attribute_call_resolve_to_real_method():
    facts = _parse(
        {
            "app/services.py": "class UserService:\n    def get_user(self):\n        pass\n",
            "app/main.py": (
                "from app.services import UserService as US\n"
                "def load():\n"
                "    service = US()\n"
                "    return service.get_user()\n"
            ),
        }
    )

    index = SymbolResolver().resolve(facts)

    assert index.resolve("app.main", "US") == "app.services.UserService"
    assert index.instances_by_scope["app.main.load"]["service"] == "app.services.UserService"
    assert index.resolve("app.main", "service.get_user", caller="app.main.load") == (
        "app.services.UserService.get_user"
    )
    assert not index.unresolved_calls


def test_relative_import_and_reexport_resolve_without_string_concatenation_only():
    facts = _parse(
        {
            "app/services.py": "class UserService:\n    pass\n",
            "app/public.py": "from .services import UserService\n",
            "app/api/main.py": "from ..public import UserService as Service\n",
        }
    )

    index = SymbolResolver().resolve(facts)

    assert index.aliases_by_module["app.api.main"]["Service"] == "app.services.UserService"
    assert index.resolve("app.api.main", "Service") == "app.services.UserService"


def test_cross_module_inheritance_resolves_base_symbol():
    facts = _parse(
        {
            "app/base.py": "class BaseRepository:\n    pass\n",
            "app/repositories.py": (
                "from .base import BaseRepository\n"
                "class UserRepository(BaseRepository):\n"
                "    pass\n"
            ),
        }
    )

    index = SymbolResolver().resolve(facts)

    assert index.resolve_reference("app.repositories", "BaseRepository") == "app.base.BaseRepository"


def test_decorators_and_type_hints_are_preserved_as_resolution_evidence():
    facts = _parse(
        {
            "app/services.py": "class UserService:\n    def execute(self):\n        pass\n",
            "app/api.py": (
                "from app.services import UserService\n"
                "router = object()\n"
                "@router.get('/users')\n"
                "def endpoint(service: UserService):\n"
                "    return service.execute()\n"
            ),
        }
    )

    index = SymbolResolver().resolve(facts)
    api = next(item for item in facts if item.module_name == "app.api")

    assert api.decorators[0].expression == "router.get"
    assert api.decorators[0].arguments == ("/users",)
    assert index.resolve("app.api", "service.execute", caller="app.api.endpoint") == (
        "app.services.UserService.execute"
    )


def test_dynamic_dispatch_remains_unresolved_with_reason():
    facts = _parse(
        {
            "app/main.py": (
                "def run(registry, name):\n"
                "    handler = registry[name]\n"
                "    return handler()\n"
            )
        }
    )

    index = SymbolResolver().resolve(facts)

    assert [call.callee for call in index.unresolved_calls] == ["handler"]
    assert index.reason_for(index.unresolved_calls[0]) == "dynamic_dispatch"


def test_short_name_collision_stays_unknown_without_import_evidence():
    facts = _parse(
        {
            "module_a.py": "def save():\n    pass\n",
            "module_b.py": "def save():\n    pass\n",
            "consumer.py": "def execute():\n    return save()\n",
            "consumer_explicit.py": (
                "from module_a import save\n"
                "def execute():\n"
                "    return save()\n"
            ),
        }
    )

    index = SymbolResolver().resolve(facts)

    assert index.resolve("consumer", "save", caller="consumer.execute") is None
    assert index.resolve(
        "consumer_explicit", "save", caller="consumer_explicit.execute"
    ) == "module_a.save"
    unresolved = next(call for call in index.unresolved_calls if call.caller == "consumer.execute")
    assert index.reason_for(unresolved) == "unresolved_symbol"


def test_type_hints_are_isolated_by_function_and_module_scope():
    facts = _parse(
        {
            "app/a.py": "class UserService:\n    def execute(self):\n        pass\n",
            "app/b.py": "class UserService:\n    def execute(self):\n        pass\n",
            "consumer_a.py": (
                "from app.a import UserService as A\n"
                "def process(service: A):\n"
                "    return service.execute()\n"
            ),
            "consumer_b.py": (
                "from app.b import UserService as B\n"
                "def process(service: B):\n"
                "    return service.execute()\n"
            ),
        }
    )

    index = SymbolResolver().resolve(facts)

    assert index.resolve("consumer_a", "service.execute", caller="consumer_a.process") == (
        "app.a.UserService.execute"
    )
    assert index.resolve("consumer_b", "service.execute", caller="consumer_b.process") == (
        "app.b.UserService.execute"
    )


def test_duplicate_edges_merge_evidence_without_creating_duplicate_edges():
    graph = PropertyGraph()
    graph.add_node(Node(id="a", type=NodeType.FUNCTION, name="a"))
    graph.add_node(Node(id="b", type=NodeType.FUNCTION, name="b"))

    graph.add_edge(
        Edge(
            source="a",
            target="b",
            type=EdgeType.CALLS,
            evidence_refs=["evidence:1"],
            metadata={"call_line": 1},
        )
    )
    graph.add_edge(
        Edge(
            source="a",
            target="b",
            type=EdgeType.CALLS,
            evidence_refs=["evidence:2"],
            metadata={"call_line": 2},
        )
    )

    assert len(graph.edges) == 1
    assert graph.edges[0].evidence_refs == ["evidence:1", "evidence:2"]
    assert graph.edges[0].metadata["support_count"] == 2
    assert graph.edges[0].metadata["supporting_observations"] == [{"call_line": 2}]


def test_raw_graph_exposes_structured_decorator_and_alias_evidence(tmp_path):
    app = tmp_path / "app"
    app.mkdir()
    (app / "__init__.py").write_text("", encoding="utf-8")
    (app / "services.py").write_text(
        "class UserService:\n"
        "    def execute(self):\n"
        "        pass\n",
        encoding="utf-8",
    )
    (app / "api.py").write_text(
        "from app.services import UserService as US\n"
        "router = object()\n"
        "@router.get('/users')\n"
        "def endpoint(service: US):\n"
        "    return service.execute()\n",
        encoding="utf-8",
    )

    ir = analyze_repository(tmp_path)
    endpoint = next(node for node in ir.raw_graph.nodes if node.id == "app.api.endpoint")
    import_edge = next(
        edge
        for edge in ir.raw_graph.edges
        if edge.type == EdgeType.IMPORTS
        and edge.source == "module:app.api"
        and edge.target == "app.services.UserService"
    )

    assert endpoint.metadata["decorator_evidence"] == [
        {
            "owner": "app.api.endpoint",
            "expression": "router.get",
            "arguments": ["/users"],
            "path": "app/api.py",
            "line": 3,
        }
    ]
    assert import_edge.metadata["local_name"] == "US"
    assert import_edge.metadata["imported_name"] == "app.services.UserService"
    assert import_edge.evidence_refs


def test_pipeline_emits_resolved_instance_edges_and_keeps_dynamic_calls(tmp_path):
    app = tmp_path / "app"
    app.mkdir()
    (app / "__init__.py").write_text("", encoding="utf-8")
    (app / "services.py").write_text(
        "class UserService:\n"
        "    def get_user(self):\n"
        "        pass\n",
        encoding="utf-8",
    )
    (app / "main.py").write_text(
        "from app.services import UserService as US\n"
        "def load():\n"
        "    service = US()\n"
        "    return service.get_user()\n"
        "def dynamic(registry, name):\n"
        "    handler = registry[name]\n"
        "    return handler()\n",
        encoding="utf-8",
    )

    ir = analyze_repository(tmp_path)

    instantiation_edges = [
        edge
        for edge in ir.raw_graph.edges
        if edge.type == EdgeType.INSTANTIATES
        and edge.source == "app.main.load"
        and edge.target == "app.services.UserService"
    ]
    assert instantiation_edges
    assert instantiation_edges[0].evidence_refs
    assert any(
        edge.type == EdgeType.CALLS
        and edge.source == "app.main.load"
        and edge.target == "app.services.UserService.get_user"
        for edge in ir.raw_graph.edges
    )
    assert any(
        call.caller == "app.main.dynamic"
        and call.callee == "handler"
        and call.reason == "dynamic_dispatch"
        for call in ir.raw_graph.unresolved_calls
    )
    assert not any(
        edge.source == "app.main.dynamic" and edge.type == EdgeType.CALLS
        for edge in ir.raw_graph.edges
    )


def test_src_layout_uses_import_package_names_and_relative_package_imports(tmp_path):
    package = tmp_path / "src" / "app"
    package.mkdir(parents=True)
    (package / "__init__.py").write_text(
        "from .services import UserService\n",
        encoding="utf-8",
    )
    (package / "services.py").write_text(
        "class UserService:\n"
        "    def get_user(self):\n"
        "        pass\n",
        encoding="utf-8",
    )
    (package / "main.py").write_text(
        "from app import UserService\n"
        "def load():\n"
        "    service = UserService()\n"
        "    return service.get_user()\n",
        encoding="utf-8",
    )

    ir = analyze_repository(tmp_path)

    assert "module:app.main" in {node.id for node in ir.raw_graph.nodes}
    assert any(
        edge.type == EdgeType.CALLS
        and edge.target == "app.services.UserService.get_user"
        for edge in ir.raw_graph.edges
    )


def test_plain_name_decorator_has_no_call_keywords():
    facts = _parse(
        {
            "app/module.py": (
                "def marker(function):\n"
                "    return function\n"
                "@marker\n"
                "def endpoint():\n"
                "    pass\n"
            )
        }
    )

    decorators = facts[0].decorators
    assert decorators[0].expression == "marker"
    assert decorators[0].arguments == ()
    assert decorators[0].keywords == ()
