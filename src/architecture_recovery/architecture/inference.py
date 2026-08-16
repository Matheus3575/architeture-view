from __future__ import annotations

from architecture_recovery.graph.analysis import graph_metrics
from architecture_recovery.graph.builder import PropertyGraph
from architecture_recovery.ir import (
    ArchitectureAnalysis,
    ArchitectureHypothesis,
    EvidenceStatus,
    StackProfile,
)


class ArchitectureInferer:
    """Small, explainable rule set for the first architecture hypotheses."""

    def infer(self, graph: PropertyGraph, stack: StackProfile) -> ArchitectureAnalysis:
        metrics = graph_metrics(graph)
        hypotheses: list[ArchitectureHypothesis] = []
        layer_nodes = [node for node in graph.nodes.values() if node.layer]
        if layer_nodes:
            evidence = sorted({ref for node in layer_nodes for ref in node.evidence_refs})
            hypotheses.append(
                ArchitectureHypothesis(
                    pattern="layered",
                    status=EvidenceStatus.INFERRED,
                    confidence=min(0.95, 0.55 + len({node.layer for node in layer_nodes}) * 0.08),
                    evidence_refs=evidence,
                    explanation="Source nodes use recognizable controller/service/repository/domain layers.",
                )
            )
        if any(framework.name in {"Django", "Flask", "FastAPI"} for framework in stack.frameworks):
            framework = next(framework for framework in stack.frameworks if framework.name in {"Django", "Flask", "FastAPI"})
            hypotheses.append(
                ArchitectureHypothesis(
                    pattern="framework-guided application",
                    status=EvidenceStatus.INFERRED,
                    confidence=framework.confidence,
                    evidence_refs=framework.evidence_refs,
                    explanation=f"Framework adapter signal detected for {framework.name}.",
                )
            )
        if not hypotheses:
            hypotheses.append(
                ArchitectureHypothesis(
                    pattern="unknown",
                    status=EvidenceStatus.UNKNOWN,
                    confidence=0.0,
                    explanation="No architecture pattern had sufficient evidence.",
                )
            )
        return ArchitectureAnalysis(
            hypotheses=hypotheses,
            metrics=metrics,
            smells=[
                {"type": "circular_dependency", "nodes": cycle}
                for cycle in metrics["strongly_connected_components"]
            ],
        )
