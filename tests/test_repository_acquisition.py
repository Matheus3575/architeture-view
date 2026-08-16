from pathlib import Path

import pytest

from architecture_recovery.repository import RepositoryAcquisitionError, cloned_repository, is_repository_url
from architecture_recovery.repository import acquisition


def test_is_repository_url():
    assert is_repository_url("https://github.com/org/project.git")
    assert is_repository_url("ssh://git@github.com/org/project.git")
    assert not is_repository_url("C:/work/project")


def test_clone_uses_shallow_clone_and_ref(monkeypatch):
    captured = {}

    def fake_run(command, **kwargs):
        captured["command"] = command
        captured["kwargs"] = kwargs
        target = Path(command[-1])
        target.mkdir(parents=True)
        return type("Result", (), {"returncode": 0, "stdout": "", "stderr": ""})()

    monkeypatch.setattr(acquisition.subprocess, "run", fake_run)
    with cloned_repository("https://github.com/org/project.git", ref="main") as path:
        assert path.is_dir()
    assert captured["command"][:5] == ["git", "clone", "--depth", "1", "--branch"]
    assert "main" in captured["command"]
    assert captured["kwargs"]["timeout"] == 300


def test_clone_failure_is_reported(monkeypatch):
    def fake_run(command, **kwargs):
        return type("Result", (), {"returncode": 128, "stdout": "", "stderr": "repository not found"})()

    monkeypatch.setattr(acquisition.subprocess, "run", fake_run)
    with pytest.raises(RepositoryAcquisitionError, match="repository not found"):
        with cloned_repository("https://github.com/org/missing.git"):
            pass
