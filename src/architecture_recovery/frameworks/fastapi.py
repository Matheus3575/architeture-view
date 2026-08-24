from __future__ import annotations

import hashlib
from dataclasses import dataclass

from architecture_recovery.frameworks.base import (
    FrameworkAdapter,
    FrameworkAnalysis,
    FrameworkAnalysisContext,
    FrameworkDetection,
)
from architecture_recovery.graph.builder import PropertyGraph
from architecture_recovery.ir import (
    Evidence,
    EvidenceSource,
    EvidenceStatus,
    FrameworkFact,
    SourceRef,
)
from architecture_recovery.parsing import AssignmentFact, CallFact, DecoratorFact, ParseFacts


_FASTAPI_CALLABLES = {"FastAPI", "APIRouter", "Depends"}
_FASTAPI_CANONICAL = {f"fastapi.{name}" for name in _FASTAPI_CALLABLES}
_HTTP_METHODS = {"get", "post", "put", "patch", "delete", "options", "head", "trace"}


@dataclass(frozen=True)
class _Binding:
    kind: str
    symbol: str
    path: str
    line: int
    scope: str


class FastAPIAdapter(FrameworkAdapter):
    """Reference adapter that interprets existing Python analysis facts.

    It never reads source files and never parses Python. Unknown receiver or
    provider identity remains unknown instead of being inferred from names.
    """

    @property
    def name(self) -> str:
        return "FastAPI"

    def detect(self, context: FrameworkAnalysisContext) -> FrameworkDetection:
        imports = self._imports(context.parsed_files)
        refs = self._framework_import_evidence(context.raw_graph, imports)
        known_import = any(
            canonical in _FASTAPI_CANONICAL or canonical == "fastapi"
            for canonical in imports.values()
        )
        known_use = any(
            self._canonical_callable(facts.module_name, assignment.value, imports)
            in _FASTAPI_CANONICAL
            for facts in context.parsed_files
            for assignment in facts.assignments
            if assignment.value_is_call and not assignment.value_is_dynamic
        )
        detected = known_import and (known_use or bool(refs))
        return FrameworkDetection(
            framework=self.name,
            detected=detected,
            evidence_refs=tuple(sorted(refs)),
            reason=("FastAPI import and known API evidence" if detected else "No sufficient FastAPI evidence"),
        )

    def analyze(self, context: FrameworkAnalysisContext) -> FrameworkAnalysis:
        imports = self._imports(context.parsed_files)
        bindings, shadowed = self._bindings(context.parsed_files, imports)
        detection = self.detect(context)
        result = FrameworkAnalysis(framework=self.name, detection=detection)
        if not detection.detected:
            return result

        for facts in context.parsed_files:
            for assignment in facts.assignments:
                binding = bindings.get((facts.module_name, assignment.scope, assignment.target))
                if not binding:
                    continue
                if binding.kind == "application":
                    result.facts.append(
                        self._fact(
                            "APPLICATION",
                            subject=assignment.target,
                            attributes={
                                "application": assignment.target,
                                "symbol": binding.symbol,
                                "module": facts.module_name,
                            },
                            path=assignment.path,
                            line=assignment.line,
                            context=context,
                            raw_refs=self._matching_instantiation_refs(context.raw_graph, assignment),
                            result=result,
                        )
                    )
                elif binding.kind == "router":
                    result.facts.append(
                        self._fact(
                            "ROUTER",
                            subject=assignment.target,
                            attributes={
                                "router": assignment.target,
                                "symbol": binding.symbol,
                                "module": facts.module_name,
                            },
                            path=assignment.path,
                            line=assignment.line,
                            context=context,
                            raw_refs=self._matching_instantiation_refs(context.raw_graph, assignment),
                            result=result,
                        )
                    )

            for call in facts.calls:
                self._analyze_include_router(call, facts, bindings, shadowed, context, result)
                self._analyze_dependency(call, facts, bindings, shadowed, context, result)

            for decorator in facts.decorators:
                self._analyze_route(decorator, facts, bindings, shadowed, imports, context, result)

            for definition in facts.definitions:
                if definition.kind != "class":
                    continue
                schema_base = self._schema_base(facts, definition.bases, imports)
                if schema_base:
                    result.facts.append(
                        self._fact(
                            "SCHEMA",
                            subject=definition.qualified_name,
                            attributes={
                                "model": definition.qualified_name,
                                "base": schema_base,
                                "framework": "Pydantic",
                            },
                            path=definition.path,
                            line=definition.start_line,
                            context=context,
                            raw_refs=self._definition_refs(context.raw_graph, definition.qualified_name),
                            result=result,
                        )
                    )

        result.facts = self._deduplicate_facts(result.facts)
        result.limitations = [
            "Dynamic route receivers and dynamic Depends providers remain UNKNOWN.",
            "Path composition across include_router is not performed in v1.",
            "Pydantic model internals are not analyzed beyond clear BaseModel inheritance.",
        ]
        return result

    def _analyze_route(
        self,
        decorator: DecoratorFact,
        facts: ParseFacts,
        bindings: dict[tuple[str, str, str], _Binding],
        shadowed: set[tuple[str, str, str]],
        imports: dict[tuple[str, str], str],
        context: FrameworkAnalysisContext,
        result: FrameworkAnalysis,
    ) -> None:
        receiver, _, method = decorator.expression.rpartition(".")
        if not receiver or method not in _HTTP_METHODS:
            return
        binding = self._lookup_binding(bindings, facts.module_name, facts.module_name, receiver)
        if not binding or binding.kind not in {"application", "router"}:
            return
        if (facts.module_name, facts.module_name, receiver) in shadowed:
            return
        path = decorator.arguments[0] if decorator.arguments else "UNKNOWN"
        status = EvidenceStatus.OBSERVED if decorator.arguments else EvidenceStatus.UNKNOWN
        confidence = 1.0 if status == EvidenceStatus.OBSERVED else 0.35
        attributes = {
            "method": method.upper(),
            "path": path,
            "handler": decorator.owner,
            "owner": receiver,
        }
        response_model = dict(decorator.keywords).get("response_model")
        raw_refs = self._decorator_refs(context.raw_graph, decorator)
        endpoint = self._fact(
            "HTTP_ENDPOINT",
            subject=decorator.owner,
            target=decorator.owner,
            attributes=attributes,
            path=decorator.path,
            line=decorator.line,
            context=context,
            raw_refs=raw_refs,
            result=result,
            status=status,
            confidence=confidence,
        )
        result.facts.append(endpoint)
        if response_model is not None:
            schema = context.symbols.resolve_reference(facts.module_name, response_model, caller=decorator.owner)
            schema_value = schema or "UNKNOWN"
            schema_status = EvidenceStatus.OBSERVED if schema else EvidenceStatus.UNKNOWN
            schema_fact = self._fact(
                "RESPONSE_SCHEMA",
                subject=decorator.owner,
                target=schema_value,
                attributes={
                    "endpoint": decorator.owner,
                    "schema": schema_value,
                    "response_model": response_model,
                },
                path=decorator.path,
                line=decorator.line,
                context=context,
                raw_refs=raw_refs,
                result=result,
                status=schema_status,
                confidence=1.0 if schema else 0.35,
            )
            result.facts.append(schema_fact)

    def _analyze_dependency(
        self,
        call: CallFact,
        facts: ParseFacts,
        bindings: dict[tuple[str, str, str], _Binding],
        shadowed: set[tuple[str, str, str]],
        context: FrameworkAnalysisContext,
        result: FrameworkAnalysis,
    ) -> None:
        imported = self._import_for_local(facts.module_name, call.callee, context.parsed_files)
        if imported != "fastapi.Depends" or (facts.module_name, facts.module_name, call.callee) in shadowed:
            return
        provider_expression = call.arguments[0] if call.arguments else "UNKNOWN"
        provider = context.symbols.resolve_reference(facts.module_name, provider_expression, caller=call.caller)
        provider_value = provider or "UNKNOWN"
        status = EvidenceStatus.OBSERVED if provider else EvidenceStatus.UNKNOWN
        result.facts.append(
            self._fact(
                "FRAMEWORK_DEPENDENCY",
                subject=call.caller,
                target=provider_value,
                attributes={
                    "consumer": call.caller,
                    "provider": provider_value,
                    "provider_expression": provider_expression,
                },
                path=call.path,
                line=call.line,
                context=context,
                raw_refs=self._call_refs(context.raw_graph, call),
                result=result,
                status=status,
                confidence=1.0 if provider else 0.35,
            )
        )

    def _analyze_include_router(
        self,
        call: CallFact,
        facts: ParseFacts,
        bindings: dict[tuple[str, str, str], _Binding],
        shadowed: set[tuple[str, str, str]],
        context: FrameworkAnalysisContext,
        result: FrameworkAnalysis,
    ) -> None:
        receiver, _, method = call.callee.rpartition(".")
        if method != "include_router" or not call.arguments:
            return
        application = self._lookup_binding(bindings, facts.module_name, call.caller, receiver)
        router_name = call.arguments[0]
        router = self._lookup_binding(bindings, facts.module_name, call.caller, router_name)
        if not application or application.kind != "application" or not router or router.kind != "router":
            return
        if (facts.module_name, facts.module_name, receiver) in shadowed:
            return
        attributes = {
            "application": receiver,
            "router": router_name,
        }
        for key in ("prefix", "tags"):
            value = dict(call.keywords).get(key)
            if value is not None:
                attributes[key] = value
        result.facts.append(
            self._fact(
                "ROUTER_INCLUSION",
                subject=receiver,
                target=router_name,
                attributes=attributes,
                path=call.path,
                line=call.line,
                context=context,
                raw_refs=self._call_refs(context.raw_graph, call),
                result=result,
            )
        )

    def _bindings(
        self, parsed_files: tuple[ParseFacts, ...], imports: dict[tuple[str, str], str]
    ) -> tuple[dict[tuple[str, str, str], _Binding], set[tuple[str, str, str]]]:
        bindings: dict[tuple[str, str, str], _Binding] = {}
        shadowed: set[tuple[str, str, str]] = set()
        for facts in parsed_files:
            for assignment in facts.assignments:
                if assignment.target.startswith("self."):
                    continue
                key = (facts.module_name, assignment.scope, assignment.target)
                if assignment.value_is_call and not assignment.value_is_dynamic:
                    canonical = self._canonical_callable(facts.module_name, assignment.value, imports)
                    kind = {"fastapi.FastAPI": "application", "fastapi.APIRouter": "router"}.get(canonical or "")
                    if kind:
                        bindings[key] = _Binding(kind, canonical or "UNKNOWN", assignment.path, assignment.line, assignment.scope)
                        continue
                if assignment.target in _FASTAPI_CALLABLES or assignment.target in {"Depends", "FastAPI", "APIRouter"}:
                    shadowed.add(key)
                parent = self._lookup_binding(bindings, facts.module_name, assignment.scope, assignment.value)
                if parent and not assignment.value_is_call:
                    bindings[key] = _Binding(parent.kind, parent.symbol, assignment.path, assignment.line, assignment.scope)
        # A first-party router imported from another analyzed module keeps its
        # resolved framework identity. This uses import facts and the binding
        # index; it does not scan or parse the source again.
        for facts in parsed_files:
            for item in facts.imports:
                canonical = self._canonical_import(facts, item)
                if not canonical or "." not in canonical:
                    continue
                source_module, source_name = canonical.rsplit(".", 1)
                source = bindings.get((source_module, source_module, source_name))
                if source:
                    bindings[(facts.module_name, facts.module_name, item.local_name)] = source
        return bindings, shadowed

    @staticmethod
    def _imports(parsed_files: tuple[ParseFacts, ...]) -> dict[tuple[str, str], str]:
        imports: dict[tuple[str, str], str] = {}
        for facts in parsed_files:
            for item in facts.imports:
                imports[(facts.module_name, item.local_name)] = FastAPIAdapter._canonical_import(facts, item)
        return imports

    @staticmethod
    def _canonical_import(facts: ParseFacts, item) -> str:
        imported = item.imported_name
        if not imported.startswith("."):
            return imported
        level = len(imported) - len(imported.lstrip("."))
        remainder = imported[level:]
        module_parts = facts.module_name.split(".")
        package_parts = module_parts if facts.path.rsplit("/", 1)[-1] == "__init__.py" else module_parts[:-1]
        base = package_parts[: max(0, len(package_parts) - (level - 1))]
        return ".".join([*base, remainder]).strip(".")

    def _canonical_callable(self, module: str, value: str, imports: dict[tuple[str, str], str]) -> str | None:
        first, _, rest = value.partition(".")
        imported = imports.get((module, first))
        if imported:
            return f"{imported}.{rest}" if rest else imported
        return value if value in _FASTAPI_CANONICAL else None

    @staticmethod
    def _import_for_local(module: str, local: str, parsed_files: tuple[ParseFacts, ...]) -> str | None:
        for facts in parsed_files:
            if facts.module_name != module:
                continue
            for item in facts.imports:
                if item.local_name == local:
                    return item.imported_name.lstrip(".")
        return None

    @staticmethod
    def _lookup_binding(bindings, module: str, scope: str, name: str) -> _Binding | None:
        current = scope
        while current:
            value = bindings.get((module, current, name))
            if value:
                return value
            if "." not in current:
                break
            current = current.rsplit(".", 1)[0]
        return bindings.get((module, module, name))

    def _fact_evidence(self, framework, kind, path, line, attributes, subject):
        evidence_id = self._semantic_evidence_id(framework, kind, path, line, attributes, subject)
        return Evidence(
            id=evidence_id,
            source_type=EvidenceSource.FRAMEWORK_ADAPTER,
            detail=f"{framework} semantic fact {kind}: {attributes}",
            source=SourceRef(path=path, start_line=line, end_line=line, symbol=subject),
        )

    @staticmethod
    def _semantic_evidence_id(framework, kind, path, line, attributes, subject):
        token = f"{framework}:{kind}:{path}:{line}:{subject}:{sorted(attributes.items())}".encode()
        return f"evidence:{hashlib.sha1(token).hexdigest()[:16]}"

    def _register_evidence(self, result, kind, path, line, attributes, subject):
        evidence = self._fact_evidence(result.framework, kind, path, line, attributes, subject)
        if not any(item.id == evidence.id for item in result.evidence):
            result.evidence.append(evidence)
        return evidence.id

    def _fact(self, kind, *, subject, target=None, attributes, path, line, context, raw_refs, result, status=EvidenceStatus.OBSERVED, confidence=1.0):
        refs = sorted(set(raw_refs))
        refs.append(self._register_evidence(result, kind, path, line, attributes, subject))
        return FrameworkFact(
            kind=kind,
            subject=subject,
            target=target,
            attributes=attributes,
            status=status,
            confidence=confidence,
            evidence_refs=sorted(set(refs)),
            source=SourceRef(path=path, start_line=line, end_line=line, symbol=subject),
            metadata={"adapter": result.framework},
        )

    @staticmethod
    def _deduplicate_facts(facts):
        unique = {}
        for fact in facts:
            key = (fact.kind, fact.subject, fact.target, tuple(sorted(fact.attributes.items())))
            unique[key] = fact
        return sorted(unique.values(), key=lambda fact: (fact.kind, fact.subject or "", fact.target or ""))

    @staticmethod
    def _framework_import_evidence(graph: PropertyGraph, imports):
        refs = set()
        for edge in graph.edges:
            if edge.type.value != "IMPORTS":
                continue
            if edge.target == "external:fastapi" or edge.target.startswith("external_symbol:fastapi."):
                refs.update(edge.evidence_refs)
        return refs

    @staticmethod
    def _matching_instantiation_refs(graph, assignment: AssignmentFact):
        refs = set()
        # The edge metadata is the stable Raw Graph link for this observation.
        for edge in graph.edges:
            if edge.type.value == "INSTANTIATES" and edge.metadata.get("target_variable") == assignment.target:
                refs.update(edge.evidence_refs)
        return refs

    @staticmethod
    def _call_refs(graph, call: CallFact):
        refs = set()
        for edge in graph.edges:
            if edge.type.value != "CALLS":
                continue
            metadata = [edge.metadata, *edge.metadata.get("supporting_observations", [])]
            if any(item.get("call_path") == call.path and item.get("call_line") == call.line and item.get("callee") == call.callee for item in metadata):
                refs.update(edge.evidence_refs)
        return refs

    @staticmethod
    def _decorator_refs(graph, decorator: DecoratorFact):
        refs = set()
        for evidence in graph.evidence.values():
            source = evidence.source
            if source and source.path == decorator.path and source.start_line == decorator.line and evidence.source_type == EvidenceSource.AST:
                if decorator.expression in evidence.detail:
                    refs.add(evidence.id)
        return refs

    @staticmethod
    def _definition_refs(graph, symbol):
        for node in graph.nodes.values():
            if node.id == symbol:
                return set(node.evidence_refs)
        return set()

    @staticmethod
    def _schema_base(facts, bases, imports):
        for base in bases:
            first, _, rest = base.partition(".")
            imported = imports.get((facts.module_name, first))
            canonical = f"{imported}.{rest}" if imported and rest else imported or base
            if canonical in {"pydantic.BaseModel", "pydantic.main.BaseModel"}:
                return canonical
        return None
