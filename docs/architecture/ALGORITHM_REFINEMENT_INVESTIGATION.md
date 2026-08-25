# Algorithm Refinement Investigation

## Scope

This investigation is diagnostic only. It observes the existing ArchitectureIR,
ArchitecturalProjection, VisualizationReadModel and SVG renderer without
changing their semantics. Timing is operational data; structural metrics are
the reproducible evidence.

The baseline revision is `b38c3f8` (M8.1.5). No repository-specific rule,
blacklist, whitelist, renderer filter or algorithm optimization was introduced.

## Observed baseline

| Scenario | Architectural nodes | Projected nodes | Semantic details | Projected edges | External detailed/projected | SVG |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| significance calibration | 21 | 9 | 16 | 11 | 9 / 1 | 1,115 × 784, 72,717 bytes |
| visualization read model | 6 | 5 | 9 | 5 | 1 / 1 | 760 × 740, 47,019 bytes |
| infrastructure semantics | 13 | 10 | 6 | 20 | 0 / 0 | 1,670 × 740, 93,144 bytes |
| projection many modules | 6 | 5 | 5 | 5 | 1 / 1 | 760 × 740, 55,691 bytes |
| workspace | 52 | 16 | 131 | 19 | 24 / 1 | 2,040 × 784, 322,733 bytes |
| generated neutral context | 7 | 6 | 9 | 8 | 1 / 1 | 930 × 740, 58,235 bytes |

All scenarios were deterministic. Effective projected-edge evidence coverage
was 1.0 in every scenario after counting both inline references and
`EvidenceGroups`. The workspace used four evidence-group bindings on projected
edges; this is compacted traceability, not missing evidence.

## Findings

### F1 — Residual contextual promotion of auxiliary components

Priority: P0 semantic quality.

The generated neutral scenario contains an isolated local framework application
in `component:support.py`. It was classified MEDIUM and projected even though it
has no observed flow to the primary application. In the workspace, analogous
signals appear in `component:benchmarks` (HIGH) and `component:examples`
(MEDIUM). The workspace also contains benchmark fixtures and multiple Compose
stacks, so those values are a boundary-contamination witness rather than real
product ground truth.

The likely cause is that application/framework context is still shared too
broadly through aggregate application/component relations. The next refinement
should require an explicit evidence chain to the primary application or an
independent architectural boundary before local framework facts promote an
auxiliary component.

Required regression cases: isolated framework application, framework application
connected to the main flow, and two independent applications with explicit
boundaries. Expectations must be structural, not name-based.

### F2 — Relation vocabulary is not canonical across stages

Priority: P1 semantic contract.

`InfrastructureRelation` emits lowercase values such as `depends_on` and
`connects_to`, while ArchitectureIR edges use `DEPENDS_ON` and `CONNECTS_TO`.
The infrastructure fixture produces both forms in the ReadModel. This can split
relation counts and visual classes, and makes downstream consumers reason about
case instead of architectural meaning.

No semantic normalization was applied in this investigation. The next change
must define the compatibility boundary, preserve source evidence, and add tests
for canonical relation identity and deterministic rendering.

### F3 — SVG width is dominated by fixed-band layout

Priority: P1 visualization after semantic fixes.

The workspace renders 16 nodes and 19 edges into a 2,040-pixel-wide SVG. The
infrastructure fixture renders 10 nodes and 20 edges into 1,670 pixels. The
current layout uses fixed 150-pixel nodes, 35-pixel gaps and a 320-pixel
inspection panel. This is a layout-density limitation, not evidence that more
nodes should be removed from the projection.

The next visualization change should measure group width, label length, degree
concentration and route crossings before changing layout. It must remain a
renderer-only change over an unchanged ReadModel.

### F4 — Evidence coverage needs group-aware diagnostics

An inline-only check falsely reported four workspace edges without evidence.
Those edges had valid `EvidenceGroups`. The harness now reports effective
coverage using inline refs or group refs and therefore reports 1.0 coverage.
This diagnostic correction is complete; no core evidence behavior was changed.

## Priority order

1. Context boundary calibration for component/application/framework promotion.
2. Canonical relation vocabulary and relation-strength reporting.
3. Renderer layout density and edge readability.
4. Optional manual comparison against a local large repository.

The workspace is not a substitute for a real repository: it intentionally
contains fixtures, examples and multiple infrastructure scenarios. No Prefect
or other network-dependent run was performed.

## Reproduction

```text
python -m benchmarks.refinement_investigation
python -m benchmarks.refinement_investigation --json
```

The machine-readable structural baseline is stored in
`benchmarks/refinement_investigation_baseline.json`.

Architecture context reviewed:

- `docs/architecture/README.md`
- `docs/architecture/DECISIONS.md`
- `docs/architecture/ANALYSIS_LOG.md`
- `docs/architecture/adr/ADR-001-architecture-ir.md`
- `docs/architecture/adr/ADR-002-evidence-and-traceability.md`
- `docs/architecture/adr/ADR-003-graph-separation-and-source-origin.md`

Architectural decisions affected: none.

Unresolved questions:

- Whether canonical relation normalization belongs in `InfrastructureRelation`,
  ArchitectureIR construction, or only the renderer-neutral ReadModel.
- What existing evidence is sufficient to distinguish an isolated application
  boundary from an auxiliary framework usage.
## Quality metrics

The controlled `significance_calibration` ground truth reports:

- significance precision: 1.0;
- significance recall: 1.0;
- false architectural promotions: 0;
- projected external dependencies: 1 of 9 detailed dependencies.

The generated neutral context intentionally has no persisted ground truth; its
observed auxiliary framework promotion is recorded as a diagnostic negative:
`component:support.py` is MEDIUM/projected despite having no observed flow to the
primary application. This is the principal candidate for the next semantic
refinement.
