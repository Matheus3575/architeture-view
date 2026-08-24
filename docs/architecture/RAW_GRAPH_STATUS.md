# Raw Graph Semantic Status

## Purpose

The Raw Code Graph is the evidence-bearing observation layer. It may contain
internal implementation details and external symbols; third-party symbols are
not removed merely because they are not architectural components.

## Supported observations

| Capability | Current behavior | Confidence policy |
|---|---|---|
| Definitions | Modules, classes, functions and methods | Observed from parser |
| Imports | Absolute, relative, aliases and simple re-exports | Resolved when module evidence exists |
| Calls | Direct calls and attribute calls | Unknown when receiver identity is insufficient |
| Inheritance | Cross-module base resolution when imported | No guessed short-name target |
| Type hints | Scoped by module/function/method | Evidence, not runtime truth |
| Decorators | Owner, expression, arguments, source location | Preserved for future adapters |
| Source origin | First-party, third-party, standard library, generated, unknown | Repository boundary evidence |
| Dynamic dispatch | Recorded as unresolved with reason | Conservative |

## M2.2 local data flow

The resolver performs bounded local propagation using indexed facts. Supported
patterns include:

```python
repo = UserRepository()
other = repo
other.find()
```

```python
service = UserService(repo)
# __init__(self, repository): self.repository = repository
self.repository.find()
```

```python
def create_repository():
    return UserRepository()

repo = create_repository()
repo.find()
```

The parser preserves assignment arguments, function parameters and simple
return facts. Flow evidence is attached to resolved call edges through
`SYMBOL_RESOLUTION` evidence and `flow_evidence` metadata.

## Deliberately unresolved

The current implementation does not attempt general static analysis. These
cases should remain `UNKNOWN` unless future evidence changes the policy:

- path-sensitive branches and loops;
- multiple possible assignments or returns;
- dynamic registries and factory lookup;
- `getattr`, reflection and runtime imports;
- general interprocedural return propagation;
- monkey patching and overloaded dispatch;
- complete points-to, SSA or CFG analysis.

## Graph invariants

1. Raw observations are not discarded because their origin is third-party.
2. An unresolved target is safer than a guessed target.
3. Every emitted call edge has source and target nodes.
4. Deduplication merges evidence references and support counts.
5. Architectural edges are produced after Raw Graph construction and retain traceability.
6. No framework or architecture pattern is inferred by the parser/resolver.

## Main implementation locations

- Parser facts: `src/architecture_recovery/parsing/base.py` and `python.py`
- Symbol resolution and local flow: `src/architecture_recovery/symbols/resolver.py`
- Raw Graph construction and evidence: `src/architecture_recovery/graph/builder.py`
- Pipeline orchestration: `src/architecture_recovery/pipeline.py`
