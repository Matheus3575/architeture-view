from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass, field
from time import perf_counter
from typing import Iterator


@dataclass
class StageProfile:
    name: str
    seconds: float = 0.0
    counts: dict[str, int | float | str] = field(default_factory=dict)


@dataclass
class _StageTimer:
    profile: "AnalysisProfile"
    name: str
    started: float
    counts: dict[str, int | float | str] = field(default_factory=dict)
    child_seconds: float = 0.0

    def set_counts(self, **counts: int | float | str) -> None:
        self.counts.update(counts)


@dataclass
class AnalysisProfile:
    """Lightweight opt-in macro profile for one deterministic execution."""

    stages: dict[str, StageProfile] = field(default_factory=dict)
    enabled: bool = True
    _stage_stack: list[_StageTimer] = field(default_factory=list, init=False, repr=False)

    @contextmanager
    def stage(self, name: str) -> Iterator[_StageTimer]:
        if not self.enabled:
            yield _StageTimer(self, name, 0.0)
            return
        timer = _StageTimer(self, name, perf_counter())
        self._stage_stack.append(timer)
        try:
            yield timer
        finally:
            elapsed = perf_counter() - timer.started
            self._stage_stack.pop()
            if self._stage_stack:
                self._stage_stack[-1].child_seconds += elapsed
            self.record(name, max(0.0, elapsed - timer.child_seconds), timer.counts)

    def record(
        self,
        name: str,
        seconds: float,
        counts: dict[str, int | float | str] | None = None,
    ) -> None:
        item = self.stages.setdefault(name, StageProfile(name=name))
        item.seconds += seconds
        if counts:
            item.counts.update(counts)

    @property
    def total_seconds(self) -> float:
        return sum(item.seconds for item in self.stages.values())

    def as_dict(self) -> dict[str, object]:
        return {
            "total_seconds": self.total_seconds,
            "stages": {
                name: {
                    "seconds": item.seconds,
                    "counts": dict(item.counts),
                }
                for name, item in self.stages.items()
            },
        }

    def render_text(self) -> str:
        lines = ["Architecture Recovery Profile", ""]
        counter_aliases = (
            ("files", ("file_count", "files")),
            ("symbols", ("symbol_count", "symbols")),
            ("raw_nodes", ("raw_node_count", "raw_nodes")),
            ("raw_edges", ("raw_edge_count", "raw_edges")),
            ("evidence", ("evidence_count", "evidence")),
            ("architectural_nodes", ("architectural_node_count", "architectural_nodes")),
            ("architectural_edges", ("architectural_edge_count", "architectural_edges")),
            ("components", ("component_count", "components")),
            ("projected_nodes", ("projected_node_count", "projected_nodes")),
            ("projected_edges", ("projected_edge_count", "projected_edges")),
            ("evidence_groups", ("evidence_group_count", "evidence_groups")),
        )
        cardinality: dict[str, int | float | str] = {}
        for label, keys in counter_aliases:
            for item in reversed(tuple(self.stages.values())):
                value = next((item.counts[key] for key in keys if key in item.counts), None)
                if value is not None:
                    cardinality[label] = value
                    break
        if cardinality:
            for key, value in cardinality.items():
                rendered = f"{value:,}" if isinstance(value, int) else str(value)
                lines.append(f"{key:<28}{rendered:>10}")
            lines.append("")
        for item in self.stages.values():
            lines.append(f"{item.name:<28}{item.seconds:>9.3f} s")
        lines.append(f"{'total':<28}{self.total_seconds:>9.3f} s")
        return "\n".join(lines)

def profile_stage(profile: AnalysisProfile | None, name: str):
    if profile is None:
        return _NullStage()
    return profile.stage(name)


class _NullStage:
    def __enter__(self):
        return None

    def __exit__(self, exc_type, exc_value, traceback):
        return False


__all__ = ["AnalysisProfile", "StageProfile", "profile_stage"]