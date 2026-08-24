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
    decorators: tuple[str, ...] = ()
    parameters: tuple[str, ...] = ()


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
    call_kind: str = "direct"
    receiver: str | None = None
    arguments: tuple[str, ...] = ()
    keywords: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True)
class DecoratorFact:
    owner: str
    expression: str
    arguments: tuple[str, ...]
    path: str
    line: int
    keywords: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True)
class AssignmentFact:
    scope: str
    target: str
    value: str
    path: str
    line: int
    value_is_call: bool = False
    value_is_dynamic: bool = False
    arguments: tuple[str, ...] = ()


@dataclass(frozen=True)
class ReturnFact:
    scope: str
    value: str
    path: str
    line: int
    value_is_call: bool = False
    value_is_dynamic: bool = False


@dataclass(frozen=True)
class TypeHintFact:
    scope: str
    name: str
    annotation: str
    path: str
    line: int


@dataclass
class ParseFacts:
    path: str
    module_name: str
    definitions: list[DefinitionFact] = field(default_factory=list)
    imports: list[ImportFact] = field(default_factory=list)
    calls: list[CallFact] = field(default_factory=list)
    decorators: list[DecoratorFact] = field(default_factory=list)
    assignments: list[AssignmentFact] = field(default_factory=list)
    returns: list[ReturnFact] = field(default_factory=list)
    type_hints: list[TypeHintFact] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
