from __future__ import annotations

from typing import Protocol

from architecture_recovery.ir import ClassificationReport, SourceOrigin


class RepositoryClassifier(Protocol):
    """Language-neutral contract for future repository classifiers."""

    def classify_path(self, path: str) -> tuple[SourceOrigin, str]: ...

    def classify_graph(self, graph) -> ClassificationReport: ...
