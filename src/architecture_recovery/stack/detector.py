from __future__ import annotations

import re
from pathlib import Path

from architecture_recovery.ir import Evidence, EvidenceSource, SourceRef, StackProfile, Technology
from architecture_recovery.scanner import FileKind, RepositorySnapshot


class StackDetector:
    """Combine dependency-file and source-level signals into a stack profile."""

    def detect(self, snapshot: RepositorySnapshot) -> tuple[StackProfile, list[Evidence]]:
        evidence: list[Evidence] = []
        technologies: dict[tuple[str, str], Technology] = {}

        python_files = [file for file in snapshot.by_kind(FileKind.SOURCE) if file.language == "python"]
        if python_files:
            ref = self._evidence(evidence, EvidenceSource.AST, python_files[0].path, "Python source file detected")
            self._add(technologies, "Python", "language", 1.0, ref)
            self._add(technologies, "Python", "runtime", 1.0, ref)

        dependency_text = "\n".join(
            self._read(file.absolute_path) for file in snapshot.by_kind(FileKind.DEPENDENCY)
        ).lower()
        source_text = "\n".join(
            self._read(file.absolute_path) for file in python_files
        ).lower()
        combined = f"{dependency_text}\n{source_text}"

        for package, name, category, confidence in (
            ("django", "Django", "framework", 0.99),
            ("fastapi", "FastAPI", "framework", 0.99),
            ("flask", "Flask", "framework", 0.99),
            ("sqlalchemy", "SQLAlchemy", "framework", 0.90),
            ("psycopg", "PostgreSQL", "database", 0.85),
            ("redis", "Redis", "database", 0.85),
        ):
            if re.search(rf"\b{re.escape(package)}\b", combined):
                ref = self._evidence(
                    evidence,
                    EvidenceSource.DEPENDENCY_FILE if package in dependency_text else EvidenceSource.AST,
                    "requirements.txt" if package in dependency_text else self._first_python(python_files),
                    f"Detected technology through {package}",
                )
                self._add(technologies, name, category, confidence, ref)

        infrastructure = []
        for file in snapshot.by_kind(FileKind.INFRASTRUCTURE):
            name = file.path.lower()
            technology = "Docker" if Path(name).name == "dockerfile" else "Docker Compose"
            ref = self._evidence(evidence, EvidenceSource.DOCKERFILE if technology == "Docker" else EvidenceSource.DOCKER_COMPOSE, file.path, f"Infrastructure file {file.path}")
            infrastructure.append(Technology(name=technology, category="infrastructure", evidence_refs=[ref.id]))

        return StackProfile(
            languages=self._items(technologies, "language"),
            runtimes=self._items(technologies, "runtime"),
            frameworks=self._items(technologies, "framework"),
            databases=self._items(technologies, "database"),
            infrastructure=infrastructure,
        ), evidence

    @staticmethod
    def _read(path: Path) -> str:
        try:
            return path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            return ""

    @staticmethod
    def _first_python(files) -> str:
        return files[0].path if files else "repository"

    @staticmethod
    def _evidence(items, source_type, path, detail):
        evidence = Evidence(
            id=f"evidence:{source_type.value.lower()}:{path}:{len(items)}",
            source_type=source_type,
            detail=detail,
            source=SourceRef(path=path),
        )
        items.append(evidence)
        return evidence

    @staticmethod
    def _add(target, name, category, confidence, evidence):
        key = (name, category)
        if key not in target:
            target[key] = Technology(name=name, category=category, confidence=confidence, evidence_refs=[evidence.id])
        else:
            target[key].confidence = max(target[key].confidence, confidence)
            target[key].evidence_refs.append(evidence.id)

    @staticmethod
    def _items(target, category):
        return sorted((item for (name, kind), item in target.items() if kind == category), key=lambda item: item.name)
