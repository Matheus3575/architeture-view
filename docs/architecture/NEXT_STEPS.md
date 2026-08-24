# Algorithm Next Steps

This roadmap is subordinate to accepted ADRs and is an implementation guide,
not a new architectural decision.

## M4 result

M4 is complete. The engine produces conservative, evidence-based first-party
component candidates and preserves unassigned modules. Component detection and
architecture pattern inference remain separate.

## M5 result

M5 is complete. Docker and Compose now produce infrastructure-neutral,
evidence-backed resources and relations without changing Component Detection.
UNKNOWN and unsupported configuration remain explicit.

## Recommended next milestone: M6.3 Additional Pattern Detector

M6.2 now provides a conservative evidence-based Layered detector. The next
step is to add one separately validated pattern detector while preserving UNKNOWN
and traceability.

## Alternatives

### Repository Boundary Advanced

This remains important for editable installs, multiple Python environments,
complex Poetry configurations, namespace packages and local/installed module
name collisions. Choose it before inference only if source-origin errors appear
in a real target repository or these cases become a priority.

## Later sequence

Component Detection
        -> Infrastructure Semantics
        -> Architecture Pattern Inference
        -> Optional LLM interpretation

## Do not do next

- Do not add LLM reasoning to compensate for weak observations.
- Do not implement general Python data-flow analysis as part of M2.2.
- Do not infer MVC, Clean, Hexagonal or Microservices from directory names.
- Do not make the renderer responsible for analysis.
- Do not turn Infrastructure Semantics into a generic DevOps analyzer.

## M6.1 result

M6.1 is complete with one bounded Layered detector. MVC, Clean, Hexagonal,
Microservices and LLM-assisted interpretation remain future work.



## M6.2 result

M6.2 is complete. Layered hypotheses require evidence-bearing directional
relations; names-only structures remain UNKNOWN and reverse/conflicting
relations remain traceable.
## M6.3 result

M6.3 is complete. MVC is an independent evidence-based hypothesis and does not force a single winning architecture. The next recommended milestone is a bounded additional detector or repository-boundary hardening; Clean, Hexagonal, Microservices and LLM reasoning remain deferred.
## M6.4 result

M6.4 is complete. Framework Facts are richer and more traceable while remaining separate from architectural inference. The next recommended milestone is a bounded visualization/read-model preparation layer or additional framework adapter coverage, subject to preserving UNKNOWN and the renderer boundary.
