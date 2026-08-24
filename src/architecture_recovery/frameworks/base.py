from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from architecture_recovery.graph.builder import PropertyGraph
from architecture_recovery.ir import Evidence, FrameworkFact
from architecture_recovery.parsing import ParseFacts
from architecture_recovery.symbols import SymbolIndex


@dataclass(frozen=True)
class FrameworkAnalysisContext:
    """Read-only inputs already produced by the core analysis pipeline."""

    raw_graph: PropertyGraph
    parsed_files: tuple[ParseFacts, ...]
    symbols: SymbolIndex


@dataclass(frozen=True)
class FrameworkDetection:
    framework: str
    detected: bool
    evidence_refs: tuple[str, ...] = ()
    reason: str = ""


@dataclass
class FrameworkAnalysis:
    framework: str
    detection: FrameworkDetection
    facts: list[FrameworkFact] = field(default_factory=list)
    evidence: list[Evidence] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)


class FrameworkAdapter(ABC):
    """Small framework-neutral contract for semantic interpretation."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Stable adapter name, independent from architectural categories."""

    @abstractmethod
    def detect(self, context: FrameworkAnalysisContext) -> FrameworkDetection:
        """Determine whether sufficiently strong framework evidence exists."""

    @abstractmethod
    def analyze(self, context: FrameworkAnalysisContext) -> FrameworkAnalysis:
        """Interpret existing observations into framework semantic facts."""


class FrameworkAdapterRegistry:
    """Runs registered adapters without making the pipeline framework-specific."""

    def __init__(self, adapters: tuple[FrameworkAdapter, ...] = ()) -> None:
        self.adapters = adapters

    def analyze(self, context: FrameworkAnalysisContext) -> list[FrameworkAnalysis]:
        return [adapter.analyze(context) for adapter in self.adapters]
