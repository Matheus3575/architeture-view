from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from architecture_recovery.ir import ArchitectureAnalysis, ArchitectureHypothesis, ArchitectureIR, EdgeType, EvidenceStatus

_STATUS_FACTOR = {EvidenceStatus.OBSERVED: 1.0, EvidenceStatus.INFERRED: 0.7, EvidenceStatus.UNCERTAIN: 0.35, EvidenceStatus.UNKNOWN: 0.0}
_LAYER_ORDER = {"controllers": 0, "views": 0, "api": 0, "services": 1, "domain": 1, "repositories": 2, "infrastructure": 2, "models": 2}

@dataclass(frozen=True)
class EvidenceContribution:
    evidence_refs: tuple[str, ...]
    weight: float
    reason: str
    status: EvidenceStatus = EvidenceStatus.OBSERVED

class EvidenceScorer:
    """Small deterministic scorer: (support - contradiction) / (total + 1)."""
    @staticmethod
    def score(supporting: Iterable[EvidenceContribution], contradicting: Iterable[EvidenceContribution]) -> tuple[float, EvidenceStatus]:
        support_score = sum(item.weight * _STATUS_FACTOR[item.status] for item in supporting)
        contradiction_score = sum(item.weight * _STATUS_FACTOR[item.status] for item in contradicting)
        confidence = max(0.0, min(1.0, (support_score - contradiction_score) / (support_score + contradiction_score + 1.0)))
        if support_score <= 0.0:
            status = EvidenceStatus.UNKNOWN
        elif confidence >= 0.20 and support_score > contradiction_score:
            status = EvidenceStatus.INFERRED
        else:
            status = EvidenceStatus.UNCERTAIN
        return round(confidence, 6), status

class ArchitectureHypothesisEngine:
    """Evaluate hypotheses from an existing ArchitectureIR only."""
    def infer(self, ir: ArchitectureIR) -> ArchitectureAnalysis:
        supporting, contradicting = self._layered_signals(ir)
        confidence, status = EvidenceScorer.score(supporting, contradicting)
        support_refs = _refs(supporting)
        contradiction_refs = _refs(contradicting)
        refs = sorted(set(support_refs + contradiction_refs))
        if status is EvidenceStatus.UNKNOWN:
            explanation = "No evidence-bearing cross-layer relations were available for the layered hypothesis."
        else:
            explanation = f"Layered hypothesis uses {len(supporting)} supporting relation(s) and {len(contradicting)} contradicting relation(s)."
            if contradiction_refs:
                explanation += " Reverse cross-layer relations were preserved as contradictory evidence."
        return ArchitectureAnalysis(
            hypotheses=[ArchitectureHypothesis(pattern="layered", status=status, confidence=confidence, supporting_evidence=support_refs, contradicting_evidence=contradiction_refs, evidence_refs=refs, explanation=explanation)],
            metrics={"hypothesis_engine": "m6.1", "hypothesis_evidence_scoring": "(support - contradiction) / (support + contradiction + 1)", "layered_support_count": len(supporting), "layered_contradiction_count": len(contradicting)},
        )

    def _layered_signals(self, ir: ArchitectureIR) -> tuple[list[EvidenceContribution], list[EvidenceContribution]]:
        nodes = {node.id: node for node in ir.raw_graph.nodes}
        evidence = {item.id: item for item in ir.evidence}
        supporting, contradicting = [], []
        for edge in sorted(ir.raw_graph.edges, key=lambda item: (item.source, item.target, item.type.value, item.id or "")):
            source, target = nodes.get(edge.source), nodes.get(edge.target)
            if not source or not target or source.layer not in _LAYER_ORDER or target.layer not in _LAYER_ORDER or source.layer == target.layer:
                continue
            if edge.type not in {EdgeType.CALLS, EdgeType.IMPORTS, EdgeType.DEPENDS_ON}:
                continue
            refs = tuple(sorted(ref for ref in edge.evidence_refs if ref in evidence))
            if not refs:
                continue
            contribution = EvidenceContribution(refs, edge.confidence * max(evidence[ref].weight for ref in refs), f"{source.layer} -> {target.layer} via {edge.type.value}", edge.status)
            (supporting if _LAYER_ORDER[source.layer] < _LAYER_ORDER[target.layer] else contradicting).append(contribution)
        return supporting, contradicting

def _refs(contributions: Iterable[EvidenceContribution]) -> list[str]:
    return sorted({ref for item in contributions for ref in item.evidence_refs})

__all__ = ["ArchitectureHypothesisEngine", "EvidenceContribution", "EvidenceScorer"]