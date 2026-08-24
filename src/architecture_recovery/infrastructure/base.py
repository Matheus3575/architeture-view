from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from architecture_recovery.graph.builder import PropertyGraph
from architecture_recovery.ir import (
    Evidence,
    InfrastructureResource,
    InfrastructureRelation,
)
from architecture_recovery.parsing import ParseFacts
from architecture_recovery.scanner import RepositorySnapshot
from architecture_recovery.symbols import SymbolIndex


@dataclass(frozen=True)
class InfrastructureAnalysisContext:
    """Read-only inputs for infrastructure analysis."""

    raw_graph: PropertyGraph
    parsed_files: tuple[ParseFacts, ...]
    symbols: SymbolIndex
    snapshot: RepositorySnapshot


@dataclass
class InfrastructureAnalysisResult:
    """Results returned by an infrastructure adapter."""

    resources: list[InfrastructureResource] = field(default_factory=list)
    relations: list[InfrastructureRelation] = field(default_factory=list)
    evidence: list[Evidence] = field(default_factory=list)


class InfrastructureAdapter(ABC):
    """Abstract base class for infrastructure adapters."""

    @property
    @abstractmethod
    def name(self) -> str:
        """The name of the adapter."""

    @abstractmethod
    def analyze(self, context: InfrastructureAnalysisContext) -> InfrastructureAnalysisResult:
        """Analyze the repository snapshot and return infrastructure facts."""
