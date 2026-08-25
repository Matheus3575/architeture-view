from __future__ import annotations

from dataclasses import dataclass, field

from architecture_recovery.parsing import (
    AssignmentFact,
    CallFact,
    DefinitionFact,
    ImportFact,
    ParseFacts,
    ReturnFact,
    TypeHintFact,
)
from architecture_recovery.profiling import AnalysisProfile, profile_stage


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
    aliases_by_module: dict[str, dict[str, str]] = field(default_factory=dict)
    instances_by_scope: dict[str, dict[str, str]] = field(default_factory=dict)
    attribute_instances: dict[tuple[str, str], str] = field(default_factory=dict)
    type_hints_by_scope: dict[str, dict[str, str]] = field(default_factory=dict)
    ambiguous_bindings: set[tuple[str, str]] = field(default_factory=set)
    ambiguous_attributes: set[tuple[str, str]] = field(default_factory=set)
    constructor_attributes: dict[tuple[str, str], str] = field(default_factory=dict)
    return_targets: dict[str, str] = field(default_factory=dict)
    binding_evidence: dict[tuple[str, str], set[str]] = field(default_factory=dict)
    attribute_evidence: dict[tuple[str, str], set[str]] = field(default_factory=dict)
    flow_evidence: dict[tuple[str, str], set[str]] = field(default_factory=dict)
    flow_stats: dict[str, int] = field(default_factory=dict)
    dynamic_targets: set[tuple[str, str]] = field(default_factory=set)
    unresolved_calls: list[CallFact] = field(default_factory=list)
    unresolved_reasons: dict[tuple[str, int, str], str] = field(default_factory=dict)

    def resolve(self, module_name: str, callee: str, caller: str | None = None) -> str | None:
        if caller and "." in callee:
            receiver, member = callee.rsplit(".", 1)
            instance_binding = self._lookup_instance_binding(caller, receiver)
            instance = instance_binding[0] if instance_binding else None
            if instance:
                candidate = f"{instance}.{member}"
                if candidate in self.symbols:
                    if instance_binding:
                        self._record_flow(
                            caller,
                            callee,
                            *self.binding_evidence.get((instance_binding[1], receiver), set()),
                        )
                    self._record_flow(caller, callee, f"local_instance:{receiver}={instance}")
                    return candidate
            if receiver.startswith("self."):
                class_id = self.enclosing_class(caller)
                attribute = receiver.removeprefix("self.")
                if class_id and (class_id, attribute) not in self.ambiguous_attributes:
                    instance = self.attribute_instances.get((class_id, attribute))
                    if instance:
                        candidate = f"{instance}.{member}"
                        if candidate in self.symbols:
                            for detail in self.attribute_evidence.get((class_id, attribute), set()):
                                self._record_flow(caller, callee, detail)
                            self._record_flow(
                                caller,
                                callee,
                                f"self_attribute:{class_id}.self.{attribute}={instance}",
                            )
                            return candidate
            annotation = self._lookup_scoped(self.type_hints_by_scope, caller, receiver)
            if annotation:
                target = self.resolve_reference(module_name, annotation, caller=caller)
                if target:
                    candidate = f"{target}.{member}"
                    if candidate in self.symbols:
                        self._record_flow(caller, callee, f"type_hint:{receiver}:{target}")
                        return candidate

        return self.resolve_reference(module_name, callee, caller=caller)

    def resolve_reference(
        self, module_name: str, reference: str, caller: str | None = None
    ) -> str | None:
        reference = reference.strip()
        alias_map = self.aliases_by_module.get(module_name, {})
        first, _, rest = reference.partition(".")
        alias_target = alias_map.get(first)
        candidates = [reference, f"{module_name}.{reference}"]
        if alias_target:
            candidates.insert(0, f"{alias_target}.{rest}" if rest else alias_target)
        if caller:
            candidates.insert(0, f"{caller}.{reference}")
        for candidate in candidates:
            if candidate in self.symbols:
                return candidate
        # A repository-wide short-name match is not sufficient evidence of
        # identity. The caller must provide lexical/module/import evidence.
        return None

    def reason_for(self, call: CallFact) -> str | None:
        return self.unresolved_reasons.get((call.path, call.line, call.callee))

    def evidence_for(self, caller: str, callee: str) -> tuple[str, ...]:
        return tuple(sorted(self.flow_evidence.get((caller, callee), set())))

    def enclosing_class(self, scope: str) -> str | None:
        current = scope
        while "." in current:
            current = current.rsplit(".", 1)[0]
            symbol = self.symbols.get(current)
            if symbol and symbol.kind == "class":
                return current
        return None

    def _lookup_instance(self, scope: str, name: str) -> str | None:
        binding = self._lookup_instance_binding(scope, name)
        return binding[0] if binding else None

    def _lookup_instance_binding(self, scope: str, name: str) -> tuple[str, str] | None:
        current = scope
        while current:
            if (current, name) in self.ambiguous_bindings:
                return None
            value = self.instances_by_scope.get(current, {}).get(name)
            if value:
                return value, current
            if "." not in current:
                break
            current = current.rsplit(".", 1)[0]
        return None

    def _record_flow(self, caller: str, callee: str, *details: str) -> None:
        if not details:
            return
        self.flow_evidence.setdefault((caller, callee), set()).update(details)

    def _lookup_scoped(self, values: dict[str, dict[str, str]], scope: str, name: str) -> str | None:
        current = scope
        while current:
            value = values.get(current, {}).get(name)
            if value:
                return value
            if "." not in current:
                break
            current = current.rsplit(".", 1)[0]
        return None


class SymbolResolver:
    def resolve(
        self,
        parsed_files: list[ParseFacts],
        profile: AnalysisProfile | None = None,
    ) -> SymbolIndex:
        index = SymbolIndex()
        for facts in parsed_files:
            for definition in facts.definitions:
                symbol = self._symbol(definition)
                index.symbols[symbol.id] = symbol
                index.by_short_name.setdefault(symbol.name, []).append(symbol.id)
            index.imports_by_module.setdefault(facts.module_name, []).extend(facts.imports)

        for facts in parsed_files:
            aliases = index.aliases_by_module.setdefault(facts.module_name, {})
            for item in facts.imports:
                canonical = self._canonical_import(facts.module_name, item)
                aliases[item.local_name] = canonical

        # Resolve the common re-export form (``public.User`` imported from a
        # module that itself imported ``User``) without executing modules.
        for module_name, aliases in index.aliases_by_module.items():
            for local_name, target in list(aliases.items()):
                aliases[local_name] = self._resolve_alias_chain(index, target)

        for facts in parsed_files:
            for hint in facts.type_hints:
                index.type_hints_by_scope.setdefault(hint.scope, {})[hint.name] = hint.annotation

        with profile_stage(profile, "basic_data_flow") as timer:
            self._collect_return_targets(index, parsed_files)
            self._collect_local_flow(index, parsed_files)
            if timer:
                timer.set_counts(
                    assignments=sum(len(facts.assignments) for facts in parsed_files),
                    returns=sum(len(facts.returns) for facts in parsed_files),
                    scopes=len(index.instances_by_scope),
                    flow_entries=len(index.flow_evidence),
                )

        index.flow_stats["scope_count"] = len(index.instances_by_scope)
        index.flow_stats["assignment_count"] = sum(len(facts.assignments) for facts in parsed_files)
        index.flow_stats["return_count"] = sum(len(facts.returns) for facts in parsed_files)
        index.flow_stats["passes"] = 3

        for facts in parsed_files:
            for call in facts.calls:
                if index.resolve(facts.module_name, call.callee, caller=call.caller) is None:
                    index.unresolved_calls.append(call)
                    reason = "dynamic_dispatch" if call.call_kind == "dynamic" else "unresolved_symbol"
                    if (call.caller, call.callee.split(".", 1)[0]) in index.dynamic_targets:
                        reason = "dynamic_dispatch"
                    index.unresolved_reasons[(call.path, call.line, call.callee)] = reason
        return index

    def _collect_return_targets(self, index: SymbolIndex, parsed_files: list[ParseFacts]) -> None:
        returns_by_scope: dict[str, list[ReturnFact]] = {}
        for facts in parsed_files:
            for item in facts.returns:
                returns_by_scope.setdefault(item.scope, []).append(item)
        for scope, returns in returns_by_scope.items():
            # Multiple returns may be path-dependent. Keeping them unknown is
            # safer than selecting one branch without a CFG.
            if len(returns) != 1:
                continue
            item = returns[0]
            if not item.value_is_call or item.value_is_dynamic:
                continue
            module_name = index.symbols.get(scope, Symbol("", "", "", "", "", 0, 0)).module_name
            target = index.resolve_reference(module_name, item.value, caller=scope)
            if target and index.symbols.get(target) and index.symbols[target].kind == "class":
                index.return_targets[scope] = target

    def _collect_local_flow(self, index: SymbolIndex, parsed_files: list[ParseFacts]) -> None:
        definitions = {item.qualified_name: item for facts in parsed_files for item in facts.definitions}
        # Pass 1: direct constructors and safe factory returns create the
        # local type index used by the later, bounded propagation pass.
        for facts in parsed_files:
            for assignment in facts.assignments:
                if assignment.value_is_dynamic:
                    index.dynamic_targets.add((assignment.scope, assignment.target))
                    continue
                if not assignment.value_is_call or "." in assignment.target:
                    continue
                target = self._assignment_target(index, facts, assignment)
                if self._is_class(index, target):
                    self._bind_instance(
                        index,
                        assignment.scope,
                        assignment.target,
                        target,
                        f"assignment:{assignment.path}:{assignment.line}",
                    )

        # Index the explicit ``self.attribute = parameter`` relationship once
        # per class. The key includes the class, so same-named attributes in
        # unrelated classes cannot leak into each other.
        for facts in parsed_files:
            for assignment in facts.assignments:
                if not assignment.target.startswith("self."):
                    continue
                class_id = index.enclosing_class(assignment.scope)
                if not class_id:
                    continue
                attribute = assignment.target.removeprefix("self.")
                parameter = assignment.value
                if parameter.startswith("self.") or "." in parameter:
                    continue
                if assignment.scope.endswith(".__init__"):
                    index.constructor_attributes[(class_id, parameter)] = attribute

        # Pass 2: aliases, constructor argument bindings, and type-hint-backed
        # attributes. All updates are monotonic except an explicit conflict,
        # which becomes UNKNOWN.
        for facts in parsed_files:
            for assignment in facts.assignments:
                if assignment.value_is_dynamic or assignment.value_is_call:
                    continue
                if assignment.target.startswith("self."):
                    self._bind_attribute_from_value(index, facts, assignment)
                elif "." not in assignment.target:
                    target = self._value_target(index, facts, assignment.scope, assignment.value)
                    if target:
                        self._bind_instance(
                            index,
                            assignment.scope,
                            assignment.target,
                            target,
                            f"alias:{assignment.path}:{assignment.line}:{assignment.value}",
                        )

        for facts in parsed_files:
            for definition in facts.definitions:
                if definition.name != "__init__":
                    continue
                class_id = index.enclosing_class(definition.qualified_name)
                if not class_id:
                    continue
                hints = index.type_hints_by_scope.get(definition.qualified_name, {})
                for parameter, attribute in index.constructor_attributes.items():
                    if parameter[0] != class_id:
                        continue
                    annotation = hints.get(parameter[1])
                    if annotation:
                        target = index.resolve_reference(
                            facts.module_name, annotation, caller=definition.qualified_name
                        )
                        if self._is_class(index, target):
                            self._bind_attribute(
                                index,
                                class_id,
                                attribute,
                                target,
                                f"type_hint:{facts.path}:{definition.start_line}:{parameter[1]}",
                            )

            for assignment in facts.assignments:
                if not assignment.value_is_call or assignment.value_is_dynamic:
                    continue
                target = self._assignment_target(index, facts, assignment)
                if not self._is_class(index, target):
                    continue
                definition = definitions.get(f"{target}.__init__")
                if not definition:
                    continue
                parameters = [item for item in definition.parameters if item != "self"]
                for parameter, argument in zip(parameters, assignment.arguments):
                    source = self._value_target(index, facts, assignment.scope, argument)
                    if not source:
                        continue
                    attribute = index.constructor_attributes.get((target, parameter))
                    if attribute:
                        self._bind_attribute(
                            index,
                            target,
                            attribute,
                            source,
                            f"constructor:{assignment.path}:{assignment.line}:{parameter}<-{argument}",
                        )

    @staticmethod
    def _is_class(index: SymbolIndex, target: str | None) -> bool:
        return bool(target and index.symbols.get(target) and index.symbols[target].kind == "class")

    def _assignment_target(self, index: SymbolIndex, facts: ParseFacts, assignment: AssignmentFact) -> str | None:
        target = index.resolve_reference(facts.module_name, assignment.value, caller=assignment.scope)
        if self._is_class(index, target):
            return target
        if target and target in index.return_targets:
            return index.return_targets[target]
        return None

    def _value_target(self, index: SymbolIndex, facts: ParseFacts, scope: str, value: str) -> str | None:
        if value.startswith("self."):
            class_id = index.enclosing_class(scope)
            attribute = value.removeprefix("self.")
            if class_id and (class_id, attribute) not in index.ambiguous_attributes:
                return index.attribute_instances.get((class_id, attribute))
        return index._lookup_instance(scope, value)

    def _bind_instance(self, index: SymbolIndex, scope: str, name: str, target: str, detail: str) -> None:
        key = (scope, name)
        if key in index.ambiguous_bindings:
            return
        values = index.instances_by_scope.setdefault(scope, {})
        existing = values.get(name)
        if existing and existing != target:
            values.pop(name, None)
            index.ambiguous_bindings.add(key)
            return
        values[name] = target
        index.binding_evidence.setdefault(key, set()).add(detail)

    def _bind_attribute(self, index: SymbolIndex, class_id: str, name: str, target: str, detail: str) -> None:
        key = (class_id, name)
        if key in index.ambiguous_attributes:
            return
        existing = index.attribute_instances.get(key)
        if existing and existing != target:
            index.attribute_instances.pop(key, None)
            index.ambiguous_attributes.add(key)
            return
        index.attribute_instances[key] = target
        index.attribute_evidence.setdefault(key, set()).add(detail)

    def _bind_attribute_from_value(self, index: SymbolIndex, facts: ParseFacts, assignment: AssignmentFact) -> None:
        class_id = index.enclosing_class(assignment.scope)
        if not class_id:
            return
        target = self._value_target(index, facts, assignment.scope, assignment.value)
        if target:
            self._bind_attribute(
                index,
                class_id,
                assignment.target.removeprefix("self."),
                target,
                f"attribute:{assignment.path}:{assignment.line}",
            )

    @staticmethod
    def _canonical_import(module_name: str, item: ImportFact) -> str:
        imported = item.imported_name
        if not imported.startswith("."):
            return imported
        level = len(imported) - len(imported.lstrip("."))
        remainder = imported[level:]
        module_parts = module_name.split(".")
        is_package_module = item.path.rsplit("/", 1)[-1] == "__init__.py"
        package_parts = module_parts if is_package_module else module_parts[:-1]
        base = package_parts[: max(0, len(package_parts) - (level - 1))]
        return ".".join([*base, remainder]).strip(".")

    @classmethod
    def _resolve_alias_chain(cls, index: SymbolIndex, target: str) -> str:
        current = target
        seen: set[str] = set()
        while current not in index.symbols and current not in seen and "." in current:
            seen.add(current)
            module, local = current.rsplit(".", 1)
            replacement = index.aliases_by_module.get(module, {}).get(local)
            if not replacement:
                break
            current = replacement
        return current

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
