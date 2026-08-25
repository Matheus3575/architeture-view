# Algorithm Refinement Investigation

## Scope

The initial baseline portion of this investigation was diagnostic-only. The
follow-up phases implement the smallest bounded changes identified by that
baseline while preserving the ArchitectureIR, ReadModel and evidence contracts.
Timing is operational data; structural metrics are
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

- Whether a future bounded hypothesis-context model is needed after a real
  large-repository run; no subsystem-level hypothesis engine is part of this
  goal.
## Quality metrics

The controlled `significance_calibration` ground truth reports:

- significance precision: 1.0;
- significance recall: 1.0;
- false architectural promotions: 0;
- projected external dependencies: 1 of 9 detailed dependencies.

Historical baseline note: the generated neutral context intentionally has no
persisted ground truth; before Phase 1, `component:support.py` was MEDIUM/
projected despite having no observed flow to the primary application. Phase 1
removes that promotion and records the negative as a regression fixture.

## Final refinement result — context, relations and layout

The refinement plan was executed in four bounded phases. The former baseline is
preserved under `previous_baseline` in
`benchmarks/refinement_investigation_baseline.json`; the file now records the
validated post-change structural baseline and an explicit change log.

### Phase 1 — architectural context boundaries

The measured negative case was the generated neutral repository: an isolated
local framework application in `component:support.py` was previously
`MEDIUM` and projected. The cause was local framework evidence being treated as
system context without an independent architectural boundary.

The projection now builds a deterministic set of justified context roots from
observed application boundaries and bounded semantic flow. Infrastructure and
framework facts outside those roots do not provide contextual promotion. A
single application-fact fallback is retained only for the unambiguous one-app
case, preserving existing standalone application behavior. No directory, name,
package or repository rule was added.

Measured result:

- generated neutral context: projected nodes `6 -> 5`;
- isolated auxiliary framework promotion: `component:support.py -> none`;
- context roots: `1`, the observed application boundary;
- significance calibration: precision `1.0`, recall `1.0`, false promotions `0`;
- controlled projected-edge evidence coverage: `1.0`;
- all repeated IR, ReadModel and SVG outputs remained deterministic.

The implementation is set-based and bounded: context-root discovery and
context checks are linear in architectural nodes, facts and relations.

### Phase 2 — canonical relation vocabulary

Known infrastructure relation values are canonicalized at the IR semantic
boundary. `DEPENDS_ON`, `CONNECTS_TO` and other existing `EdgeType` values have
one downstream identity. If an upstream producer supplied lowercase spelling,
`source_relation_type` is retained in relation metadata. Unknown relation names
remain unchanged rather than being guessed.

The infrastructure fixture changed from `20` projected edges with mixed
`DEPENDS_ON/depends_on` and `CONNECTS_TO/connects_to` groups to `13` projected
edges with no mixed-case groups. The reduction is deterministic semantic
aggregation of equivalent relations, not filtering. Evidence, raw edge IDs,
support counts and observations remain attached. Relation strength is now
reported by one central helper; weights and significance semantics were not
changed by canonicalization.

The implementation is linear in relation count and does not rescan source or
rerun resolution.

### Phase 3 — relation composition diagnostics

The harness now reports relation kind and strength, degree extrema, neutral top
hubs, parallel semantic aggregation, cross-group relation count and effective
evidence coverage including EvidenceGroups. It also reports hypothesis evidence
refs classified by significant versus auxiliary/unknown significance context.

Current representative measurements:

- significance fixture: `11` projected edges; `10` weak and `1` medium;
  `8` cross-group relations;
- infrastructure fixture: `13` projected edges; `9` weak and `4` medium;
  maximum out-degree `6`;
- workspace: `19` projected edges; `16` weak and `3` medium; maximum out-degree
  `4`, maximum in-degree `3`, `9` cross-group relations;
- workspace hypothesis refs were predominantly linked to significant context;
  the microservices result had `20` significant refs and `1` unclassified ref.

These metrics remain diagnostic. No generic `DEPENDS_ON` edge was hidden and no
new relation kind was invented. No hypothesis detector was changed because the
controlled measurements did not establish a broad detector regression.

### Phase 4 — deterministic SVG layout density

The renderer still consumes the same immutable VisualizationReadModel. The
layout now packs at most four nodes per semantic band row, preserving semantic
groups and deterministic ID ordering. It does not change node/edge selection,
evidence, significance, projection, or ArchitectureIR.

Representative layout comparison:

| scenario | before | after | semantic node/edge change |
| --- | --- | --- | --- |
| infrastructure | `1670 x 740`, `10/20` | `1080 x 740`, `9/13` | context calibration plus canonical relation aggregation |
| significance | `1115 x 784`, `9/11` | `1080 x 784`, `9/11` | none |
| workspace | `2040 x 784`, `16/19` | `1080 x 937`, `16/19` | none |

The final harness records content width, inspection-panel width, rows per
semantic group, route-length proxy, crossing proxy, approximate whitespace,
label-overflow proxy and overlap count. The current representative workspace
has `2` route-crossing proxy hits, `6100` route-length proxy units, zero node
overlap and `0.754114` approximate whitespace ratio. These are diagnostics,
not quality gates.

The renderer test uses a long neutral label and verifies the same ReadModel,
node IDs and edge IDs before and after rendering. No adaptive semantic
filtering, force-directed layout or external dependency was introduced.

### Stop-condition review

- Existing controlled precision/recall: preserved at `1.0/1.0`.
- UNKNOWN behavior: no speculative resolver or promotion was introduced.
- Evidence traceability: projected controlled-edge coverage remains `1.0`.
- Canonical provenance: lowercase source relation metadata is preserved.
- ReadModel immutability: validated by renderer tests.
- Project-specific heuristics: none.
- Real-world manual run: not performed; no large repository was available
  locally and no network access was used.

The remaining visual limitation is edge routing/readability in crossing-heavy
large graphs. The remaining semantic limitation is that hypothesis evidence is
measured by context but not yet represented by a subsystem-level hypothesis
model. Both are candidates for later milestones.
