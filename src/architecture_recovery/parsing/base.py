from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class DefinitionFact:
    kind: str
    name: str
    qualified_name: str
    module_name: str
    path: str
    start_line: int
    end_line: int
    parent: str | None = None
    bases: tuple[str, ...] = ()


@dataclass(frozen=True)
class ImportFact:
    module_name: str
    imported_name: str
    local_name: str
    path: str
    line: int


@dataclass(frozen=True)
class CallFact:
    caller: str
    callee: str
    path: str
    line: int


@dataclass
class ParseFacts:
    path: str
    module_name: str
    definitions: list[DefinitionFact] = field(default_factory=list)
    imports: list[ImportFact] = field(default_factory=list)
    calls: list[CallFact] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
