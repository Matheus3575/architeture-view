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
## M7.1 result

M7.1 is complete. ArchitectureIR can now be projected into a renderer-neutral read model without exposing Raw Graph interpretation to a future renderer. The next recommended milestone is a renderer-specific consumer or a read-model contract review before implementing visual layout.
## M7.2 result

M7.2 is complete. The engine now has a first semantic SVG presentation layer consuming only VisualizationReadModel. The next recommended milestone is renderer/read-model contract hardening or a separate interactive consumer, while keeping discovery and layout responsibilities separated.

## M7.3 result

M7.3 is complete. The SVG renderer now provides semantic grouping, bounded orthogonal routing, relation prioritization and inspection metadata while preserving all Read Model elements and hypotheses. The next recommended milestone is a small evidence inspection consumer or a renderer contract hardening pass; interactive UI remains deferred.

## M7.4 result

M7.4 is complete as interactive inspection only. The SVG can select nodes, edges and hypotheses, highlight related elements, clear selection and expose traceable evidence without rerunning analysis. The next recommended milestone is a dedicated evidence/read-model API or a browser consumer if richer navigation is required; discovery remains outside the renderer.

## M7.5 result

M7.5 is complete as optional motion and visual semantics only. STATIC remains the default; ANIMATED provides restrained CSS-based flow/resource indicators without runtime simulation or architectural inference. The next recommended milestone is an optional browser-facing delivery layer or accessibility hardening, while the renderer boundary remains unchanged.

## M7.6 result

M7.6 is complete. Pre-generated SVG files can be opened offline or served locally through the fixed-route standard-library web consumer. STATIC is the default browser presentation and ANIMATED remains optional. The next recommended milestone is accessibility hardening or packaging a small user-facing command, without moving inference into the web layer.

Operational usage:

~~~powershell
python -c "from pathlib import Path; from architecture_recovery.pipeline import analyze_repository; from architecture_recovery.visualization import VisualizationReadModelBuilder; from architecture_recovery.rendering import render_svg; model=VisualizationReadModelBuilder().build(analyze_repository('URL_DO_REPOSITORIO')); Path('architecture.svg').write_text(render_svg(model, mode='static'), encoding='utf-8'); Path('architecture-animated.svg').write_text(render_svg(model, mode='animated'), encoding='utf-8')"
Start-Process .\architecture.svg
python -m architecture_recovery.web --static-svg architecture.svg --animated-svg architecture-animated.svg
~~~

The web consumer serves only pre-generated files at fixed routes and performs no repository analysis.

## M7.7 result

M7.7 is complete. Generate a static visualization with:

    architecture-recovery visualize <repository>

Generate both modes with `architecture-recovery visualize <repository> --animated`. Start the local consumer with `architecture-recovery serve <repository> --animated --host 127.0.0.1 --port 8000`. The CLI only orchestrates existing analysis, read-model construction, rendering and artifact serving; it does not participate in inference.

## M6.5 result

M6.5 is complete. Hexagonal is an independent conservative hypothesis based on directional ports-and-adapters evidence. Names-only structures remain UNKNOWN, contradictions remain traceable and Layered/MVC hypotheses remain independent. The next recommended milestone is another bounded detector only if a distinct evidence contract is available; otherwise prioritize improving evidence coverage without adding new scans.

## M6.6 result

M6.6 is complete as a conservative Microservices detector. Independent application facts plus explicit cross-unit communication are required for inference; modular monoliths and infrastructure-only layouts remain UNKNOWN. The next recommended step is improving existing boundary evidence coverage, not adding another inference heuristic.

## M8.1 result

M8.1 is complete. High-level projection now decides architectural visibility before the renderer while preserving detailed significance records and traceability. The next recommended milestone is materialized Architectural Decision Recovery over existing evidence, not more visual filtering.
