from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
import tomllib


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
class RepositoryBoundary:
    root: Path
    first_party_roots: tuple[Path, ...] = ()
    import_roots: tuple[Path, ...] = ()

    dependency_markers = frozenset(
        {
            ".venv",
            "venv",
            "site-packages",
            "dist-packages",
            "node_modules",
            ".tox",
            ".nox",
        }
    )

    def contains(self, path: Path) -> bool:
        try:
            path.resolve().relative_to(self.root)
        except ValueError:
            return False
        return True

    def is_dependency_path(self, path: Path) -> bool:
        if not self.contains(path):
            return False
        relative_parts = path.resolve().relative_to(self.root).parts
        return any(part.lower() in self.dependency_markers for part in relative_parts)

    def is_first_party_path(self, path: Path) -> bool:
        if not self.contains(path) or self.is_dependency_path(path):
            return False
        resolved = path.resolve()
        return any(
            resolved == candidate or self._is_relative_to(resolved, candidate)
            for candidate in self.first_party_roots
        )

    def module_candidates(self, module_name: str) -> tuple[Path, ...]:
        """Return repository-local paths that can provide ``module_name``.

        A directory is also a candidate so namespace packages remain
        discoverable even when they do not contain ``__init__.py``.
        Dependency/vendor paths are excluded before classification.
        """
        if not module_name or any(not part or part == "*" for part in module_name.split(".")):
            return ()
        parts = tuple(module_name.split("."))
        candidates: set[Path] = set()
        for import_root in self.import_roots or (self.root,):
            package_path = import_root.joinpath(*parts)
            if package_path.with_suffix(".py").is_file():
                possible = (package_path.with_suffix(".py"),)
            elif (package_path / "__init__.py").is_file():
                possible = (package_path / "__init__.py",)
            elif package_path.is_dir():
                possible = (package_path,)
            else:
                possible = ()
            for path in possible:
                if not path.exists() or self.is_dependency_path(path):
                    continue
                if path.is_file() or path.is_dir():
                    candidates.add(path.resolve())
        return tuple(sorted(candidates))

    def resolve_local_module(self, module_name: str) -> Path | None:
        candidates = self.module_candidates(module_name)
        return candidates[0] if len(candidates) == 1 else None

    @staticmethod
    def _is_relative_to(path: Path, parent: Path) -> bool:
        try:
            path.relative_to(parent)
        except ValueError:
            return False
        return True


@dataclass(frozen=True)
class RepositorySnapshot:
    root: Path
    files: tuple[FileRecord, ...]
    boundary: RepositoryBoundary

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
        source_roots = set()
        for record in records:
            if record.kind != FileKind.SOURCE:
                continue
            source_roots.add(root if "/" not in record.path else root / record.path.split("/", 1)[0])
        import_roots = self._discover_import_roots(root, records)
        return RepositorySnapshot(
            root=root,
            files=tuple(records),
            boundary=RepositoryBoundary(
                root=root,
                first_party_roots=tuple(sorted(source_roots)),
                import_roots=tuple(sorted(import_roots)),
            ),
        )

    def _discover_import_roots(self, root: Path, records: list[FileRecord]) -> set[Path]:
        roots: set[Path] = {root}
        for record in records:
            if record.kind == FileKind.SOURCE:
                for parent in record.absolute_path.parents:
                    if parent == root.parent:
                        break
                    if parent.name.lower() == "src" and self._safe_project_path(root, parent):
                        roots.add(parent)
            if record.path.lower().endswith("pyproject.toml"):
                project_root = record.absolute_path.parent
                if self._safe_project_path(root, project_root):
                    roots.add(project_root)
                    roots.update(self._pyproject_import_roots(project_root, record.absolute_path))
        return roots

    def _pyproject_import_roots(self, project_root: Path, path: Path) -> set[Path]:
        try:
            document = tomllib.loads(path.read_text(encoding="utf-8", errors="ignore"))
        except (OSError, tomllib.TOMLDecodeError):
            return set()

        roots: set[Path] = set()
        package_dir = document.get("tool", {}).get("setuptools", {}).get("package-dir", {})
        if isinstance(package_dir, dict):
            for relative in package_dir.values():
                if isinstance(relative, str):
                    candidate = (project_root / relative).resolve()
                    if candidate.is_dir():
                        roots.add(candidate)

        poetry_packages = document.get("tool", {}).get("poetry", {}).get("packages", [])
        if isinstance(poetry_packages, list):
            for package in poetry_packages:
                if not isinstance(package, dict):
                    continue
                relative = package.get("from", ".")
                if isinstance(relative, str):
                    candidate = (project_root / relative).resolve()
                    if candidate.is_dir():
                        roots.add(candidate)
        return roots

    def _safe_project_path(self, root: Path, path: Path) -> bool:
        if not self._is_relative_to(path.resolve(), root.resolve()):
            return False
        relative_parts = path.resolve().relative_to(root.resolve()).parts
        return not any(
            part.lower() in RepositoryBoundary.dependency_markers for part in relative_parts
        )

    @staticmethod
    def _is_relative_to(path: Path, parent: Path) -> bool:
        try:
            path.relative_to(parent)
        except ValueError:
            return False
        return True

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
