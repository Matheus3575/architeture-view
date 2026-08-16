from architecture_recovery.parsing import PythonParser
from architecture_recovery.symbols import SymbolResolver


def test_python_parser_extracts_definitions_imports_and_calls():
    facts = PythonParser().parse(
        "src/example.py",
        "from src.repository import find\n\ndef load():\n    return find()\n",
    )
    assert {item.name for item in facts.definitions} == {"load"}
    assert facts.imports[0].imported_name == "src.repository.find"
    assert facts.calls[0].callee == "find"
    index = SymbolResolver().resolve([facts])
    assert "src.example.load" in index.symbols
    assert len(index.unresolved_calls) == 1
