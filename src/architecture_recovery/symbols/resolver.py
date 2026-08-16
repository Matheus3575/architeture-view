from __future__ import annotations

from dataclasses import dataclass, field

from architecture_recovery.parsing import CallFact, DefinitionFact, ImportFact, ParseFacts


@dataclass(frozen=True)
class Symbol:
    id: str
    name: str
    kind: str
    module_name: str
    path: str
    start_line: int
    end_line: int


@dataclass
class SymbolIndex:
    symbols: dict[str, Symbol] = field(default_factory=dict)
    by_short_name: dict[str, list[str]] = field(default_factory=dict)
    imports_by_module: dict[str, list[ImportFact]] = field(default_factory=dict)
    unresolved_calls: list[CallFact] = field(default_factory=list)

    def resolve(self, module_name: str, callee: str) -> str | None:
        candidates = [callee, f"{module_name}.{callee}"]
        if "." in callee:
            candidates.append(f"{module_name}.{callee.split('.', 1)[-1]}")
        for candidate in candidates:
            if candidate in self.symbols:
                return candidate
        short = callee.split(".")[-1]
        matches = self.by_short_name.get(short, [])
        return matches[0] if len(matches) == 1 else None


class SymbolResolver:
    def resolve(self, parsed_files: list[ParseFacts]) -> SymbolIndex:
        index = SymbolIndex()
        for facts in parsed_files:
            for definition in facts.definitions:
                symbol = self._symbol(definition)
                index.symbols[symbol.id] = symbol
                index.by_short_name.setdefault(symbol.name, []).append(symbol.id)
            index.imports_by_module.setdefault(facts.module_name, []).extend(facts.imports)

        for facts in parsed_files:
            for call in facts.calls:
                if index.resolve(facts.module_name, call.callee) is None:
                    index.unresolved_calls.append(call)
        return index

    @staticmethod
    def _symbol(definition: DefinitionFact) -> Symbol:
        return Symbol(
            id=definition.qualified_name,
            name=definition.name,
            kind=definition.kind,
            module_name=definition.module_name,
            path=definition.path,
            start_line=definition.start_line,
            end_line=definition.end_line,
        )
