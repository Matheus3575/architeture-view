from __future__ import annotations

import importlib.util
import importlib.metadata
import re
import sys
import sysconfig
import tomllib
from dataclasses import dataclass
from pathlib import Path

from architecture_recovery.ir import (
    ClassificationRecord,
    ClassificationReport,
    Node,
    SourceOrigin,
)
from architecture_recovery.parsing import ImportFact, ParseFacts
from architecture_recovery.scanner import FileKind, RepositorySnapshot


@dataclass(frozen=True)
class ImportResolution:
    canonical_name: str
    package: str
    display_name: str
    origin: SourceOrigin
    reason: str


class PythonRepositoryClassifier:
    """Classify Python source and imports against an explicit repository boundary."""

    display_names = {
        "fastapi": "FastAPI",
        "starlette": "Starlette",
        "pydantic": "Pydantic",
        "sqlalchemy": "SQLAlchemy",
        "django": "Django",
        "flask": "Flask",
        "redis": "Redis",
    }
    generated_markers = frozenset({"generated", "__generated__", "gen"})
    third_party_markers = frozenset(
        {
            "vendor",
            "third_party",
            "external",
            "site-packages",
            "dist-packages",
        }
    )

    def __init__(self, snapshot: RepositorySnapshot, parsed_files: list[ParseFacts]) -> None:
        self.snapshot = snapshot
        self.parsed_files = parsed_files
        self._classify_path_cache: dict[str, tuple[SourceOrigin, str]] = {}
        self._local_resolution_cache: dict[
            str, tuple[str | None, str, SourceOrigin | None]
        ] = {}
        self.local_modules = frozenset(
            facts.module_name
            for facts in parsed_files
            if self.classify_path(facts.path)[0] == SourceOrigin.FIRST_PARTY
        )
        self.local_top_levels = frozenset(module.split(".", 1)[0] for module in self.local_modules)
        self.imports_by_module = {
            facts.module_name: tuple(facts.imports) for facts in parsed_files
        }
        self.dependency_packages = self._dependency_packages()
        self.stdlib_modules = frozenset(getattr(sys, "stdlib_module_names", ()))
        self.distribution_packages = {
            package.lower().replace("-", "_"): tuple(distributions)
            for package, distributions in importlib.metadata.packages_distributions().items()
        }

    def classify_path(self, path: str) -> tuple[SourceOrigin, str]:
        cache_key = str(path)
        cached = self._classify_path_cache.get(cache_key)
        if cached is not None:
            return cached
        absolute = (self.snapshot.root / path).resolve()
        try:
            parts = {part.lower() for part in absolute.relative_to(self.snapshot.root).parts}
        except ValueError:
            result = (SourceOrigin.UNKNOWN, "Path is outside the repository boundary")
        else:
            if parts & self.generated_markers or absolute.name.lower().endswith("_generated.py"):
                result = (SourceOrigin.GENERATED, "Path uses a generated-code marker")
            elif parts & (self.third_party_markers | self.snapshot.boundary.dependency_markers):
                result = (SourceOrigin.THIRD_PARTY, "Path is inside a dependency or vendor boundary")
            elif self.snapshot.boundary.is_first_party_path(absolute):
                result = (SourceOrigin.FIRST_PARTY, "Path is inside the repository boundary")
            else:
                result = (SourceOrigin.UNKNOWN, "Path is outside the repository boundary")
        self._classify_path_cache[cache_key] = result
        return result

    def resolve_import(self, item: ImportFact) -> ImportResolution:
        canonical = self.canonical_import(item)
        package = canonical.split(".", 1)[0]
        local_status, local_reason, local_origin = self._local_resolution(canonical)
        if local_status == "ambiguous":
            return ImportResolution(
                canonical_name=canonical,
                package=package,
                display_name=package,
                origin=SourceOrigin.UNKNOWN,
                reason=local_reason,
            )
        if local_status == "local":
            return ImportResolution(
                canonical_name=canonical,
                package=package,
                display_name=package,
                origin=local_origin or SourceOrigin.FIRST_PARTY,
                reason=local_reason,
            )
        if package in self.stdlib_modules:
            return ImportResolution(
                canonical_name=canonical,
                package=package,
                display_name=package,
                origin=SourceOrigin.STANDARD_LIBRARY,
                reason="Top-level package is part of the Python standard library",
            )
        if package in self.dependency_packages:
            return ImportResolution(
                canonical_name=canonical,
                package=package,
                display_name=self.dependency_packages[package],
                origin=SourceOrigin.THIRD_PARTY,
                reason="Package is declared by a repository dependency manifest",
            )
        if package in self.distribution_packages:
            distributions = ", ".join(self.distribution_packages[package])
            return ImportResolution(
                canonical_name=canonical,
                package=package,
                display_name=self.display_names.get(package, package),
                origin=SourceOrigin.THIRD_PARTY,
                reason=f"Package is provided by installed distribution(s): {distributions}",
            )
        installed_origin = self._installed_origin(package)
        if installed_origin:
            return ImportResolution(
                canonical_name=canonical,
                package=package,
                display_name=self.display_names.get(package, package),
                origin=installed_origin[0],
                reason=installed_origin[1],
            )
        return ImportResolution(
            canonical_name=canonical,
            package=package,
            display_name=self.display_names.get(package, package),
            origin=SourceOrigin.UNKNOWN,
            reason="Import could not be matched to local, standard-library, or installed code",
        )

    def resolve_call(self, module_name: str, callee: str) -> ImportResolution | None:
        for item in self.imports_by_module.get(module_name, ()):
            if callee == item.local_name:
                return self.resolve_import(item)
            prefix = f"{item.local_name}."
            if callee.startswith(prefix):
                imported = self.resolve_import(item)
                suffix = callee[len(prefix) :]
                return ImportResolution(
                    canonical_name=f"{imported.canonical_name}.{suffix}",
                    package=imported.package,
                    display_name=imported.display_name,
                    origin=imported.origin,
                    reason=imported.reason,
                )
        return None

    def classify_graph(self, graph) -> ClassificationReport:
        records: list[ClassificationRecord] = []
        counts: dict[str, int] = {origin.value: 0 for origin in SourceOrigin}
        for node_id in sorted(graph.nodes):
            node = graph.nodes[node_id]
            origin, reason, package = self._classify_node(node)
            graph.nodes[node_id] = node.model_copy(
                update={"origin": origin, "metadata": {**node.metadata, "origin_reason": reason}}
            )
            counts[origin.value] += 1
            records.append(
                ClassificationRecord(
                    node_id=node_id,
                    origin=origin,
                    reason=reason,
                    package=package,
                )
            )
        return ClassificationReport(records=records, counts=counts)

    def local_module_for_import(self, item: ImportFact) -> str | None:
        resolution = self.resolve_import(item)
        if resolution.origin != SourceOrigin.FIRST_PARTY:
            return None
        return self._longest_local_module(resolution.canonical_name)

    @staticmethod
    def canonical_import(item: ImportFact) -> str:
        value = item.imported_name
        if not value.startswith("."):
            return value
        level = len(value) - len(value.lstrip("."))
        remainder = value[level:]
        current_parts = item.module_name.split(".")
        is_package_module = item.path.rsplit("/", 1)[-1] == "__init__.py"
        package_parts = current_parts if is_package_module else current_parts[:-1]
        base = package_parts[: max(0, len(package_parts) - (level - 1))] if level else package_parts
        return ".".join((*base, remainder)) if remainder else ".".join(base)

    def _classify_node(self, node: Node) -> tuple[SourceOrigin, str, str | None]:
        if node.type.value == "repository":
            return SourceOrigin.FIRST_PARTY, "Repository root", None
        package = node.metadata.get("external_package")
        if package:
            return (
                SourceOrigin(node.metadata.get("external_origin", SourceOrigin.UNKNOWN.value)),
                node.metadata.get("origin_reason", "External import resolution"),
                package,
            )
        if node.source:
            origin, reason = self.classify_path(node.source.path)
            return origin, reason, None
        return SourceOrigin.UNKNOWN, "Node has no source location or dependency metadata", None

    def _is_local(self, canonical: str) -> bool:
        return self._local_resolution(canonical)[0] == "local"

    def _local_resolution(
        self, canonical: str
    ) -> tuple[str | None, str, SourceOrigin | None]:
        cached = self._local_resolution_cache.get(canonical)
        if cached is not None:
            return cached
        module_name = self._longest_local_module(canonical)
        module_matches = module_name != canonical or canonical in self.local_modules
        candidates = self.snapshot.boundary.module_candidates(module_name)
        if len(candidates) > 1:
            result = (
                "ambiguous",
                f"Multiple repository package roots provide module {module_name}",
                SourceOrigin.UNKNOWN,
            )
        elif len(candidates) == 1:
            path = candidates[0]
            relative = path.relative_to(self.snapshot.root).as_posix()
            origin, reason = self.classify_path(relative)
            if origin in {SourceOrigin.FIRST_PARTY, SourceOrigin.GENERATED}:
                result = ("local", reason, origin)
            else:
                result = (None, "", None)
        elif module_matches:
            result = (
                "local",
                "Import matches a parsed module inside the repository boundary",
                SourceOrigin.FIRST_PARTY,
            )
        else:
            result = (None, "", None)
        self._local_resolution_cache[canonical] = result
        return result

    def _longest_local_module(self, canonical: str) -> str:
        parts = canonical.split(".")
        for end in range(len(parts), 0, -1):
            candidate = ".".join(parts[:end])
            if candidate in self.local_modules:
                return candidate
        return canonical

    def _installed_origin(self, package: str) -> tuple[SourceOrigin, str] | None:
        try:
            spec = importlib.util.find_spec(package)
        except (ImportError, ModuleNotFoundError, ValueError):
            return None
        if not spec or not spec.origin or spec.origin in {"built-in", "frozen"}:
            return (SourceOrigin.STANDARD_LIBRARY, "Import resolves to a built-in or frozen module") if spec else None
        origin_path = Path(spec.origin).resolve()
        if self.snapshot.boundary.contains(origin_path):
            return SourceOrigin.FIRST_PARTY, "Installed module resolves inside the repository boundary"
        if any(marker in {part.lower() for part in origin_path.parts} for marker in self.third_party_markers):
            return SourceOrigin.THIRD_PARTY, "Import resolves to an installed third-party package"
        stdlib_path = Path(sysconfig.get_paths()["stdlib"]).resolve()
        try:
            origin_path.relative_to(stdlib_path)
        except ValueError:
            pass
        else:
            return SourceOrigin.STANDARD_LIBRARY, "Import resolves to the Python standard library"
        return SourceOrigin.UNKNOWN, "Installed module location is outside known boundaries"

    def _dependency_packages(self) -> dict[str, str]:
        packages: dict[str, str] = {}
        for record in self.snapshot.by_kind(FileKind.DEPENDENCY):
            try:
                text = record.absolute_path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            if record.path.lower().endswith(".txt"):
                for line in text.splitlines():
                    match = re.match(r"\s*([A-Za-z0-9][A-Za-z0-9_.-]*)", line)
                    if match and not match.group(1).startswith(("-", "git+")):
                        self._add_package(packages, match.group(1))
            elif record.path.lower().endswith(".toml"):
                try:
                    document = tomllib.loads(text)
                except tomllib.TOMLDecodeError:
                    continue
                project = document.get("project", {})
                for dependency in project.get("dependencies", []):
                    match = re.match(r"\s*([A-Za-z0-9][A-Za-z0-9_.-]*)", dependency)
                    if match:
                        self._add_package(packages, match.group(1))
                for values in project.get("optional-dependencies", {}).values():
                    for dependency in values:
                        match = re.match(r"\s*([A-Za-z0-9][A-Za-z0-9_.-]*)", dependency)
                        if match:
                            self._add_package(packages, match.group(1))
                poetry = document.get("tool", {}).get("poetry", {}).get("dependencies", {})
                for dependency in poetry:
                    if dependency.lower() != "python":
                        self._add_package(packages, dependency)
        return packages

    def _add_package(self, packages: dict[str, str], value: str) -> None:
        package = value.lower().replace("-", "_")
        packages.setdefault(package, self.display_names.get(package, value))
