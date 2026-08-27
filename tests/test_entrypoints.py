from __future__ import annotations

from pathlib import Path

from architecture_recovery import analyze_repository
from architecture_recovery.entrypoints import EntrypointAnalyzer
from architecture_recovery.graph import PropertyGraph
from architecture_recovery.ir import ArchitecturalGraph, Node, NodeType, SourceOrigin
from architecture_recovery.scanner import RepositoryScanner
from architecture_recovery.visualization import ArchitecturalProjectionBuilder, audit_projection


def _write(root: Path, files: dict[str, str]) -> None:
    for name, content in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def _entrypoints(ir):
    return {item.declared_name: item for item in ir.entrypoints}


def test_project_script_resolves_first_party_target_and_qualifies_owner(tmp_path):
    _write(tmp_path, {
        "pyproject.toml": """
[project]
name = "neutral-app"
version = "0.1"
[project.scripts]
neutral-command = "pkg.main:run"
""",
        "pkg/__init__.py": "",
        "pkg/main.py": "def run():\n    return 1\n",
    })

    ir = analyze_repository(tmp_path)
    entrypoint = _entrypoints(ir)["neutral-command"]

    assert entrypoint.provenance == "PROJECT_SCRIPT"
    assert entrypoint.declared_target == "pkg.main:run"
    assert entrypoint.resolved_target == "pkg.main.run"
    assert entrypoint.owner_id == "component:pkg"
    assert entrypoint.accepted is True
    assert entrypoint.status.value == "observed"
    assert entrypoint.evidence_refs[0] in {item.id for item in ir.evidence}
    projection = ArchitecturalProjectionBuilder().build(ir)
    assert "component:pkg" in projection.context_root_ids
    audit = audit_projection(ir, projection)
    assert audit.executable_entrypoint_count == 1
    assert audit.accepted_entrypoint_evidence_count == 1
    assert audit.entrypoint_root_count == 1


def test_unresolved_project_script_is_unknown_and_not_projected(tmp_path):
    _write(tmp_path, {
        "pyproject.toml": """
[project]
name = "neutral-app"
version = "0.1"
[project.scripts]
missing-command = "pkg.missing:run"
""",
        "pkg/main.py": "def helper():\n    return 1\n",
    })

    ir = analyze_repository(tmp_path)
    entrypoint = _entrypoints(ir)["missing-command"]

    assert entrypoint.resolved_target is None
    assert entrypoint.owner_id is None
    assert entrypoint.accepted is False
    assert entrypoint.status.value == "unknown"
    assert "unresolved" in (entrypoint.rejection_reason or "")
    assert "component:pkg" not in ArchitecturalProjectionBuilder().build(ir).context_root_ids
    audit = audit_projection(ir, ArchitecturalProjectionBuilder().build(ir))
    assert audit.unresolved_entrypoint_count == 1
    assert audit.rejected_entrypoint_evidence_count == 1


def test_setup_cfg_and_literal_setup_py_are_supported_deterministically(tmp_path):
    _write(tmp_path, {
        "setup.cfg": """
[options]
name = neutral-app
[options.entry_points]
console_scripts =
    cfg-command = pkg.cfg:run
""",
        "setup.py": """
from setuptools import setup
setup(name='neutral-app', entry_points={'console_scripts': ['py-command = pkg.py:run']})
""",
        "pkg/cfg.py": "def run():\n    return 1\n",
        "pkg/py.py": "def run():\n    return 1\n",
    })

    first = analyze_repository(tmp_path)
    second = analyze_repository(tmp_path)
    first_entries = _entrypoints(first)
    second_entries = _entrypoints(second)

    assert set(first_entries) == {"cfg-command", "py-command"}
    assert all(item.accepted for item in first_entries.values())
    assert first.model_dump_json() == second.model_dump_json()


def test_main_module_is_positive_evidence_with_first_party_owner(tmp_path):
    _write(tmp_path, {
        "pkg/__init__.py": "",
        "pkg/__main__.py": "def main():\n    return 1\n",
    })

    ir = analyze_repository(tmp_path)
    entrypoint = _entrypoints(ir)["python -m pkg"]

    assert entrypoint.provenance == "MAIN_MODULE"
    assert entrypoint.resolved_target == "module:pkg.__main__"
    assert entrypoint.owner_id == "component:pkg"
    assert entrypoint.accepted is True


def test_dynamic_setup_py_remains_unknown(tmp_path):
    _write(tmp_path, {
        "setup.py": """
from setuptools import setup

def make_entries():
    return {}
setup(name='neutral-app', entry_points=make_entries())
""",
    })

    ir = analyze_repository(tmp_path)
    entrypoint = _entrypoints(ir)["<dynamic>"]

    assert entrypoint.accepted is False
    assert entrypoint.status.value == "unknown"
    assert ir.entrypoints[0].provenance == "SETUP_PY"


def test_third_party_target_and_unowned_main_are_not_first_party_boundaries(tmp_path):
    _write(tmp_path, {"pyproject.toml": """\n[project]\nname='neutral-app'\nversion='0.1'\n[project.scripts]\nthird-party='third.party:run'\n"""})
    snapshot = RepositoryScanner().scan(tmp_path)
    raw_node = Node(
        id="third.party.run",
        type=NodeType.FUNCTION,
        name="run",
        origin=SourceOrigin.THIRD_PARTY,
    )
    result = EntrypointAnalyzer().analyze(
        snapshot,
        [],
        PropertyGraph(nodes={raw_node.id: raw_node}),
        ArchitecturalGraph(nodes=[], edges=[]),
    )
    assert result.entrypoints[0].accepted is False
    assert result.entrypoints[0].status.value == "unknown"
    assert result.entrypoints[0].rejection_reason == "target is not first-party"

    _write(tmp_path, {"__main__.py": "print('run')\n"})
    snapshot = RepositoryScanner().scan(tmp_path)
    raw_main = Node(id="module:__main__", type=NodeType.MODULE, name="__main__", origin=SourceOrigin.FIRST_PARTY)
    result = EntrypointAnalyzer().analyze(
        snapshot,
        [],
        PropertyGraph(nodes={raw_main.id: raw_main}),
        ArchitecturalGraph(nodes=[], edges=[]),
    )
    assert result.entrypoints[-1].owner_id is None
    assert result.entrypoints[-1].accepted is False