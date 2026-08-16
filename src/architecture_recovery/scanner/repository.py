from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path


class FileKind(StrEnum):
    SOURCE = "source"
    DEPENDENCY = "dependency"
    INFRASTRUCTURE = "infrastructure"
    CI = "ci"
    DOCUMENTATION = "documentation"
    OTHER = "other"


@dataclass(frozen=True)
class FileRecord:
    path: str
    absolute_path: Path
    kind: FileKind
    language: str | None = None


@dataclass(frozen=True)
class RepositorySnapshot:
    root: Path
    files: tuple[FileRecord, ...]

    def by_kind(self, kind: FileKind) -> tuple[FileRecord, ...]:
        return tuple(record for record in self.files if record.kind == kind)


class RepositoryScanner:
    """Deterministically enumerate relevant repository files."""

    ignored_directories = {
        ".git",
        ".hg",
        ".svn",
        ".venv",
        "venv",
        "__pycache__",
        "node_modules",
        "dist",
        "build",
        ".mypy_cache",
        ".pytest_cache",
        "coverage",
    }

    source_extensions = {
        ".py": "python",
        ".pyi": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".java": "java",
        ".go": "go",
        ".rs": "rust",
        ".rb": "ruby",
        ".php": "php",
        ".c": "c",
        ".h": "c",
        ".cpp": "cpp",
        ".hpp": "cpp",
    }

    dependency_names = {
        "requirements.txt",
        "requirements-dev.txt",
        "pyproject.toml",
        "package.json",
        "package-lock.json",
        "pom.xml",
        "build.gradle",
        "go.mod",
        "cargo.toml",
        "composer.json",
        "gemfile",
    }

    infrastructure_names = {
        "dockerfile",
        "docker-compose.yml",
        "docker-compose.yaml",
        "compose.yml",
        "compose.yaml",
        "nginx.conf",
    }

    def scan(self, repository_path: str | Path) -> RepositorySnapshot:
        root = Path(repository_path).expanduser().resolve()
        if not root.is_dir():
            raise ValueError(f"Repository path is not a directory: {root}")

        records: list[FileRecord] = []
        for path in sorted(root.rglob("*")):
            if not path.is_file() or any(part in self.ignored_directories for part in path.parts):
                continue
            relative = path.relative_to(root).as_posix()
            records.append(
                FileRecord(
                    path=relative,
                    absolute_path=path,
                    kind=self.classify(path, relative),
                    language=self.source_extensions.get(path.suffix.lower()),
                )
            )
        return RepositorySnapshot(root=root, files=tuple(records))

    def classify(self, path: Path, relative: str) -> FileKind:
        name = path.name.lower()
        if path.suffix.lower() in self.source_extensions:
            return FileKind.SOURCE
        if name in self.dependency_names:
            return FileKind.DEPENDENCY
        if name in self.infrastructure_names or name.endswith((".yaml", ".yml", ".tf")):
            return FileKind.INFRASTRUCTURE
        if relative.startswith(".github/workflows/") or name in {"jenkinsfile", ".gitlab-ci.yml"}:
            return FileKind.CI
        if name.startswith("readme") or relative.startswith("docs/"):
            return FileKind.DOCUMENTATION
        return FileKind.OTHER
