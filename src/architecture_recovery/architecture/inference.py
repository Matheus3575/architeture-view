from __future__ import annotations

from architecture_recovery.architecture.hypotheses import ArchitectureHypothesisEngine
from architecture_recovery.graph.analysis import graph_metrics
from architecture_recovery.graph.builder import PropertyGraph
from architecture_recovery.ir import (
    ArchitecturalGraph,
    ArchitectureIR,
    ArchitectureAnalysis,
    ArchitectureHypothesis,
    EvidenceStatus,
    RawCodeGraph,
    RepositoryInfo,
    StackProfile,
)


class ArchitectureInferer:
    """Backward-compatible facade; new callers should pass an ArchitectureIR to the engine."""

    def infer(self, graph: PropertyGraph, stack: StackProfile):
        ir = ArchitectureIR(
            repository=RepositoryInfo(name="legacy", path="."),
            raw_graph=RawCodeGraph(nodes=list(graph.nodes.values()), edges=graph.edges),
            architectural_graph=ArchitecturalGraph(nodes=list(graph.nodes.values()), edges=graph.edges),
            evidence=list(graph.evidence.values()),
            stack=stack,
        )
        analysis = ArchitectureHypothesisEngine().infer(ir)
        if not any(item.status is not EvidenceStatus.INFERRED for item in analysis.hypotheses):
            framework = next((item for item in stack.frameworks if item.name in {"Django", "Flask", "FastAPI"}), None)
            if framework:
                analysis.hypotheses.append(ArchitectureHypothesis(
                    pattern="framework-guided application",
                    status=EvidenceStatus.INFERRED,
                    confidence=framework.confidence,
                    evidence_refs=sorted(framework.evidence_refs),
                    supporting_evidence=sorted(framework.evidence_refs),
                    explanation=f"Framework adapter signal detected for {framework.name}.",
                ))
        metrics = graph_metrics(graph)
        analysis.metrics = metrics | {key: value for key, value in analysis.metrics.items() if key.startswith("hypothesis_") or key.startswith("layered_")}
        analysis.smells = [{"type": "circular_dependency", "nodes": cycle} for cycle in metrics["strongly_connected_components"]]
        return analysis


__all__ = ["ArchitectureInferer", "ArchitectureHypothesisEngine"]
