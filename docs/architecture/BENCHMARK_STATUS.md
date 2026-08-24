# Benchmark and Quality Status

## M2.2 baseline

The benchmark has 10 deterministic fixtures. Ground truth is separated by
responsibility: source origins, symbol resolutions, Raw Graph edges,
Architectural Graph edges, expected unresolved calls, decorator/alias
evidence and edge support.

Partial ground truth does not define Raw Graph precision over every observed
edge. `wrong_resolution_rate` is calculated only over explicitly evaluated
symbol-resolution entries.

| Fixture | Correct | Correct unknown | Wrong | Flow resolutions | Deterministic |
|---|---:|---:|---:|---:|---|
| `fastapi_sample` | 2 | 1 | 0 | 0 | yes |
| `simple_python_layered` | 2 | 0 | 0 | 0 | yes |
| `src_layout` | 2 | 0 | 0 | 1 | yes |
| `monorepo` | n/a | 0 | 0 | 0 | yes |
| `namespace_package` | 1 | 0 | 0 | 0 | yes |
| `ambiguous_short_name` | 1 | 1 | 0 | 0 | yes |
| `scoped_type_hints` | 2 | 0 | 0 | 2 | yes |
| `duplicate_edge_evidence` | 2 | 0 | 0 | 0 | yes |
| `dynamic_dispatch` | 0 | 1 | 0 | 0 | yes |
| `basic_data_flow` | 2 | 0 | 0 | 2 | yes |

Aggregate covered-resolution results:

```yaml
resolution_evaluated: 14
correct_resolution_count: 14
correct_unresolved_count: 3
unresolved_resolution_count: 0
wrong_resolution_count: 0
wrong_resolution_rate: 0.0
symbol_precision: 1.0
symbol_recall: 1.0
deterministic: true
```

These values are a baseline, not a universal accuracy claim. They measure
only the facts represented in the current ground truths.

## M3 status

The benchmark now contains 11 deterministic fixtures, including
`benchmarks/fixtures/fastapi_semantics/`. Its ground truth evaluates required
framework facts, forbidden generic-router facts, expected UNKNOWN dependency
resolution, `FRAMEWORK_ADAPTER` evidence and repeatability. The M3 fixture and
the ten previous fixtures pass the quality gate.

The runner reports elapsed time for the two analyses used by each determinism
check. This is an operational measurement, not a hard performance threshold.
The adapter performs bounded indexed interpretation and does not add a source
parse or repository scan.

## M4 status

The benchmark now contains 12 deterministic fixtures, including
`benchmarks/fixtures/component_detection/`. The M4 ground truth evaluates
exact candidate membership, required evidence types, forbidden groupings,
unassigned modules, evidence traceability and determinism.

The M4 fixture results are:

```yaml
component_recall: 1.0
member_precision: 1.0
member_recall: 1.0
false_grouping_rate: 0.0
unassigned_recall: 1.0
evidence_recall: 1.0
deterministic: true
```

The candidate detector is module-level and uses a bounded affinity pass. It
does not use directory/name-only grouping, machine learning, LLMs, CFG/SSA or
additional parsing.

## Test status

- Before M2.2: 42 tests.
- After M2.2: 47 tests collected and passing.
- After M3: 55 tests collected and passing.
- After M4: 61 tests collected and passing.
- Required checks: pytest, benchmark runner and `compileall`.

The controlled M2.2 fixture is `benchmarks/fixtures/basic_data_flow/`.

The final M4 benchmark run passed all 12 fixtures. Its aggregate reported
analysis time was 44.087 seconds across the runner's two deterministic
analyses per fixture; the new component fixture reported 5.580 seconds. No
pre-M4 aggregate timing was retained, so a before/after speedup is not claimed.

## Quality gates

Execution status and quality status are separate. A benchmark can execute
successfully while failing its ground-truth quality gate. The current M2.2
baseline passes both for all fixtures.

## Limitations of the measurement

- Architectural Graph precision is not measured from Raw Graph ground truth.
- Unlisted valid observations are not classified as false positives.
- Performance is observed operationally, not used as a pass/fail threshold.
- New benchmark cases are required before claiming coverage for new semantics.

## M5 status

The benchmark now contains 13 deterministic fixtures, including
benchmarks/fixtures/infrastructure_semantics/. Its ground truth covers
Dockerfile and Compose resource discovery, database/cache/container/UNKNOWN
classification, service dependencies, environment configuration mapping,
code-to-infrastructure relations, forbidden false relations, evidence
traceability and repeatability.

The M5 fixture results are:

infrastructure_resource_precision: 1.0
infrastructure_resource_recall: 1.0
infrastructure_relation_precision: 1.0
infrastructure_relation_recall: 1.0
infrastructure_evidence_recall: 1.0
false_infrastructure_relation_rate: 0.0
deterministic: true

The fixture analysis remained bounded and static. It does not execute Docker,
make network calls or inspect local container state.
## M6.1 status

A 14th fixture, `benchmarks/fixtures/hypothesis_engine/`, validates the
minimal hypothesis engine. It requires a Layered hypothesis, traceability and
forbids MVC and Microservices. The fixture is analyzed twice and must remain
deterministic. The observed Layered result is `inferred` with confidence
`0.666667` from two evidence-bearing cross-layer relations; no pattern certainty
is asserted.
