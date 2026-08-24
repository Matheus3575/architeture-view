from architecture_recovery.parsing import PythonParser
from architecture_recovery.symbols import SymbolResolver


def _parse(files: dict[str, str]):
    parser = PythonParser()
    return [parser.parse(path, source) for path, source in files.items()]


def test_local_assignment_and_alias_propagate_to_attribute_call():
    facts = _parse(
        {
            "storage.py": "class Repo:\n    def find(self):\n        pass\n",
            "consumer.py": (
                "from storage import Repo\n"
                "def execute():\n"
                "    repo = Repo()\n"
                "    other = repo\n"
                "    return other.find()\n"
            ),
        }
    )

    index = SymbolResolver().resolve(facts)

    assert index.instances_by_scope["consumer.execute"]["repo"] == "storage.Repo"
    assert index.instances_by_scope["consumer.execute"]["other"] == "storage.Repo"
    assert index.resolve("consumer", "other.find", caller="consumer.execute") == "storage.Repo.find"
    assert any(detail.startswith("alias:") for detail in index.evidence_for("consumer.execute", "other.find"))


def test_constructor_binding_feeds_contextual_self_attribute_resolution():
    facts = _parse(
        {
            "storage.py": "class Repo:\n    def find(self):\n        pass\n",
            "logic.py": (
                "from storage import Repo\n"
                "class Service:\n"
                "    def __init__(self, dependency):\n"
                "        self.dependency = dependency\n"
                "    def execute(self):\n"
                "        return self.dependency.find()\n"
            ),
            "main.py": (
                "from storage import Repo\n"
                "from logic import Service\n"
                "repo = Repo()\n"
                "service = Service(repo)\n"
                "service.execute()\n"
            ),
        }
    )

    index = SymbolResolver().resolve(facts)

    assert index.attribute_instances[("logic.Service", "dependency")] == "storage.Repo"
    assert index.resolve(
        "logic", "self.dependency.find", caller="logic.Service.execute"
    ) == "storage.Repo.find"
    assert any(
        detail.startswith("self_attribute:")
        for detail in index.evidence_for("logic.Service.execute", "self.dependency.find")
    )


def test_simple_factory_return_propagates_once_to_local_instance():
    facts = _parse(
        {
            "storage.py": "class Repo:\n    def find(self):\n        pass\n",
            "factory.py": (
                "from storage import Repo\n"
                "def create_repository():\n"
                "    return Repo()\n"
            ),
            "consumer.py": (
                "from factory import create_repository\n"
                "def execute():\n"
                "    repo = create_repository()\n"
                "    return repo.find()\n"
            ),
        }
    )

    index = SymbolResolver().resolve(facts)

    assert index.return_targets["factory.create_repository"] == "storage.Repo"
    assert index.instances_by_scope["consumer.execute"]["repo"] == "storage.Repo"
    assert index.resolve("consumer", "repo.find", caller="consumer.execute") == "storage.Repo.find"


def test_conflicting_local_assignments_remain_unknown():
    facts = _parse(
        {
            "a.py": "class A:\n    def execute(self):\n        pass\n",
            "b.py": "class B:\n    def execute(self):\n        pass\n",
            "consumer.py": (
                "from a import A\n"
                "from b import B\n"
                "def execute(condition):\n"
                "    if condition:\n"
                "        dependency = A()\n"
                "    else:\n"
                "        dependency = B()\n"
                "    return dependency.execute()\n"
            ),
        }
    )

    index = SymbolResolver().resolve(facts)

    assert ("consumer.execute", "dependency") in index.ambiguous_bindings
    assert index.resolve("consumer", "dependency.execute", caller="consumer.execute") is None


def test_dynamic_factory_stays_unresolved():
    facts = _parse(
        {
            "consumer.py": (
                "def execute(registry, name):\n"
                "    factory = registry[name]\n"
                "    dependency = factory()\n"
                "    return dependency.execute()\n"
            )
        }
    )

    index = SymbolResolver().resolve(facts)

    assert index.resolve("consumer", "dependency.execute", caller="consumer.execute") is None
    assert {call.callee for call in index.unresolved_calls} >= {"factory", "dependency.execute"}
