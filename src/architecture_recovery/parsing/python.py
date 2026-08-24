from __future__ import annotations

import ast
from pathlib import Path

from .base import (
    AssignmentFact,
    CallFact,
    DecoratorFact,
    DefinitionFact,
    ImportFact,
    ParseFacts,
    ReturnFact,
    TypeHintFact,
)


class PythonParser:
    """Normalize Python syntax into facts used by the symbol and graph stages.

    Tree-sitter is probed first when installed, so syntax errors can be captured
    consistently across future language adapters. The standard-library AST is
    used for the MVP's semantic extraction because it is available everywhere.
    """

    def __init__(self) -> None:
        self._tree_sitter = self._load_tree_sitter()

    def parse(self, path: str, source: str, module_name_override: str | None = None) -> ParseFacts:
        module_name = module_name_override or self.module_name(path)
        facts = ParseFacts(path=path, module_name=module_name)
        if self._tree_sitter is not None:
            try:
                tree = self._tree_sitter(source.encode("utf-8"))
                if getattr(tree.root_node, "has_error", False):
                    facts.errors.append(f"Tree-sitter syntax errors in {path}")
            except Exception as exc:  # pragma: no cover - depends on optional native package
                facts.errors.append(f"Tree-sitter failed for {path}: {exc}")
        try:
            tree = ast.parse(source, filename=path)
        except SyntaxError as exc:
            facts.errors.append(f"Python syntax error at line {exc.lineno}: {exc.msg}")
            return facts
        visitor = _PythonFactVisitor(path, module_name, facts)
        visitor.visit(tree)
        return facts

    @staticmethod
    def module_name(path: str) -> str:
        value = Path(path).with_suffix("").as_posix()
        if value.endswith("/__init__"):
            value = value[: -len("/__init__")]
        return value.replace("/", ".").replace("-", "_")

    @staticmethod
    def _load_tree_sitter():
        try:
            from tree_sitter import Language, Parser
            import tree_sitter_python

            language = Language(tree_sitter_python.language())
            parser = Parser(language)
            return parser.parse
        except (ImportError, AttributeError, TypeError):
            return None


class _PythonFactVisitor(ast.NodeVisitor):
    def __init__(self, path: str, module_name: str, facts: ParseFacts) -> None:
        self.path = path
        self.module_name = module_name
        self.facts = facts
        self.scope: list[str] = []

    @property
    def current_symbol(self) -> str:
        return ".".join([self.module_name, *self.scope])

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            local = alias.asname or alias.name.split(".")[0]
            self.facts.imports.append(
                ImportFact(self.module_name, alias.name, local, self.path, node.lineno)
            )
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        module = "." * node.level + (node.module or "")
        for alias in node.names:
            local = alias.asname or alias.name
            imported = f"{module}.{alias.name}" if module else alias.name
            self.facts.imports.append(
                ImportFact(self.module_name, imported, local, self.path, node.lineno)
            )
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        qualified = self._qualified(node.name)
        decorators = tuple(self._expr_name(item) for item in node.decorator_list)
        self._record_decorators(qualified, node.decorator_list)
        self.facts.definitions.append(
            DefinitionFact(
                kind="class",
                name=node.name,
                qualified_name=qualified,
                module_name=self.module_name,
                path=self.path,
                start_line=node.lineno,
                end_line=getattr(node, "end_lineno", node.lineno),
                parent=self.scope[-1] if self.scope else None,
                bases=tuple(self._expr_name(base) for base in node.bases),
                decorators=decorators,
            )
        )
        self.scope.append(node.name)
        # Decorator expressions are recorded as DecoratorFacts above. Do not
        # also misclassify registration syntax such as ``@router.get(...)``
        # as a call made by the endpoint body.
        for statement in node.body:
            self.visit(statement)
        self.scope.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._visit_function(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._visit_function(node)

    def _visit_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        qualified = self._qualified(node.name)
        decorators = tuple(self._expr_name(item) for item in node.decorator_list)
        self._record_decorators(qualified, node.decorator_list)
        self.facts.definitions.append(
            DefinitionFact(
                kind="function" if not self.scope else "method",
                name=node.name,
                qualified_name=qualified,
                module_name=self.module_name,
                path=self.path,
                start_line=node.lineno,
                end_line=getattr(node, "end_lineno", node.lineno),
                parent=self.scope[-1] if self.scope else None,
                decorators=decorators,
                parameters=tuple(
                    argument.arg
                    for argument in (
                        *node.args.posonlyargs,
                        *node.args.args,
                        *node.args.kwonlyargs,
                    )
                ),
            )
        )
        for argument in (*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs):
            if argument.annotation is not None:
                self.facts.type_hints.append(
                    TypeHintFact(
                        scope=qualified,
                        name=argument.arg,
                        annotation=self._expr_name(argument.annotation),
                        path=self.path,
                        line=getattr(argument.annotation, "lineno", node.lineno),
                    )
        )
        if node.args.vararg and node.args.vararg.annotation is not None:
            self.facts.type_hints.append(
                TypeHintFact(
                    scope=qualified,
                    name=node.args.vararg.arg,
                    annotation=self._expr_name(node.args.vararg.annotation),
                    path=self.path,
                    line=getattr(node.args.vararg.annotation, "lineno", node.lineno),
                )
            )
        if node.returns is not None:
            self.facts.type_hints.append(
                TypeHintFact(
                    scope=qualified,
                    name="__return__",
                    annotation=self._expr_name(node.returns),
                    path=self.path,
                    line=getattr(node.returns, "lineno", node.lineno),
                )
            )
        self.scope.append(node.name)
        # Defaults are part of the function declaration and may contain
        # framework calls such as ``Depends(provider)``.
        for default in (*node.args.defaults, *(item for item in node.args.kw_defaults if item)):
            self.visit(default)
        for statement in node.body:
            self.visit(statement)
        self.scope.pop()

    def visit_Call(self, node: ast.Call) -> None:
        callee = self._expr_name(node.func)
        call_kind = "dynamic" if self._is_dynamic_call(node) else "direct"
        self.facts.calls.append(
            CallFact(
                caller=self.current_symbol,
                callee=callee,
                path=self.path,
                line=node.lineno,
                call_kind=call_kind,
                receiver=self._receiver_name(node.func),
                arguments=tuple(self._expr_name(argument) for argument in node.args),
                keywords=tuple(
                    (keyword.arg or "**", self._expr_name(keyword.value))
                    for keyword in node.keywords
                ),
            )
        )
        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign) -> None:
        value, value_is_call, value_is_dynamic, arguments = self._assignment_value(node.value)
        for target in node.targets:
            target_name = self._target_name(target)
            if target_name:
                self.facts.assignments.append(
                    AssignmentFact(
                        scope=self.current_symbol,
                        target=target_name,
                        value=value,
                        path=self.path,
                        line=node.lineno,
                        value_is_call=value_is_call,
                        value_is_dynamic=value_is_dynamic,
                        arguments=arguments,
                    )
                )
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        target_name = self._target_name(node.target)
        if target_name:
            self.facts.type_hints.append(
                TypeHintFact(
                    scope=self.current_symbol,
                    name=target_name,
                    annotation=self._expr_name(node.annotation),
                    path=self.path,
                    line=getattr(node.annotation, "lineno", node.lineno),
                )
            )
            if node.value is not None:
                value, value_is_call, value_is_dynamic, arguments = self._assignment_value(node.value)
                self.facts.assignments.append(
                    AssignmentFact(
                        scope=self.current_symbol,
                        target=target_name,
                        value=value,
                        path=self.path,
                        line=node.lineno,
                        value_is_call=value_is_call,
                        value_is_dynamic=value_is_dynamic,
                        arguments=arguments,
                    )
                )
        self.generic_visit(node)

    def visit_Return(self, node: ast.Return) -> None:
        if node.value is not None:
            value, value_is_call, value_is_dynamic, _ = self._assignment_value(node.value)
            self.facts.returns.append(
                ReturnFact(
                    scope=self.current_symbol,
                    value=value,
                    path=self.path,
                    line=node.lineno,
                    value_is_call=value_is_call,
                    value_is_dynamic=value_is_dynamic,
                )
            )
        self.generic_visit(node)

    def _record_decorators(self, owner: str, decorators: list[ast.expr]) -> None:
        for decorator in decorators:
            if isinstance(decorator, ast.Call):
                expression = self._expr_name(decorator.func)
                arguments = tuple(self._expr_name(argument) for argument in decorator.args)
            else:
                expression = self._expr_name(decorator)
                arguments = ()
            self.facts.decorators.append(
                DecoratorFact(
                    owner=owner,
                    expression=expression,
                    arguments=arguments,
                    path=self.path,
                    line=getattr(decorator, "lineno", 0),
                    keywords=tuple(
                        (keyword.arg or "**", self._expr_name(keyword.value))
                        for keyword in decorator.keywords
                    ),
                )
            )

    def _assignment_value(self, node: ast.AST) -> tuple[str, bool, bool, tuple[str, ...]]:
        if isinstance(node, ast.Call):
            return (
                self._expr_name(node.func),
                True,
                self._is_dynamic_call(node),
                tuple(self._expr_name(argument) for argument in node.args),
            )
        return self._expr_name(node), False, self._is_dynamic_expression(node), ()

    @staticmethod
    def _target_name(node: ast.AST) -> str | None:
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            return _PythonFactVisitor._expr_name(node)
        return None

    @staticmethod
    def _receiver_name(node: ast.AST) -> str | None:
        if isinstance(node, ast.Attribute):
            return _PythonFactVisitor._expr_name(node.value)
        return None

    @staticmethod
    def _is_dynamic_call(node: ast.Call) -> bool:
        return isinstance(node.func, (ast.Subscript, ast.Call)) or (
            isinstance(node.func, ast.Name) and node.func.id in {"getattr", "globals", "locals"}
        )

    @staticmethod
    def _is_dynamic_expression(node: ast.AST) -> bool:
        return isinstance(node, (ast.Subscript, ast.Lambda, ast.Dict, ast.ListComp, ast.GeneratorExp))

    def _qualified(self, name: str) -> str:
        return ".".join([self.module_name, *self.scope, name])

    @staticmethod
    def _expr_name(node: ast.AST) -> str:
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            prefix = _PythonFactVisitor._expr_name(node.value)
            return f"{prefix}.{node.attr}" if prefix else node.attr
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        return ast.unparse(node) if hasattr(ast, "unparse") else type(node).__name__
