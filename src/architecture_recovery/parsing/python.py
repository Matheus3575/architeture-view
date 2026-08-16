from __future__ import annotations

import ast
from pathlib import Path

from .base import CallFact, DefinitionFact, ImportFact, ParseFacts


class PythonParser:
    """Normalize Python syntax into facts used by the symbol and graph stages.

    Tree-sitter is probed first when installed, so syntax errors can be captured
    consistently across future language adapters. The standard-library AST is
    used for the MVP's semantic extraction because it is available everywhere.
    """

    def __init__(self) -> None:
        self._tree_sitter = self._load_tree_sitter()

    def parse(self, path: str, source: str) -> ParseFacts:
        module_name = self.module_name(path)
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
            )
        )
        self.scope.append(node.name)
        self.generic_visit(node)
        self.scope.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._visit_function(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._visit_function(node)

    def _visit_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        qualified = self._qualified(node.name)
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
            )
        )
        self.scope.append(node.name)
        self.generic_visit(node)
        self.scope.pop()

    def visit_Call(self, node: ast.Call) -> None:
        self.facts.calls.append(
            CallFact(
                caller=self.current_symbol,
                callee=self._expr_name(node.func),
                path=self.path,
                line=node.lineno,
            )
        )
        self.generic_visit(node)

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
