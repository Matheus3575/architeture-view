from __future__ import annotations

from collections import defaultdict
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from architecture_recovery.ir import ArchitectureIR, Edge, EdgeType, EvidenceStatus, Node, NodeType


class SignificanceLevel(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNKNOWN = "unknown"


class ArchitecturalSignificance(BaseModel):
    model_config = ConfigDict(extra="forbid")

    subject: str
    significance: SignificanceLevel
    score: float = Field(default=0.0, ge=0.0, le=1.0)
    supporting_evidence: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    reasons: list[str] = Field(default_factory=list)
    contains_refs: list[str] = Field(default_factory=list)


class ProjectedEdge(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    source: str
    target: str
    kind: str
    status: EvidenceStatus = EvidenceStatus.INFERRED
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    evidence_refs: list[str] = Field(default_factory=list)
    raw_edge_ids: list[str] = Field(default_factory=list)
    support_count: int = Field(default=1, ge=1)
    supporting_observations: list[dict[str, Any]] = Field(default_factory=list)


class HighLevelArchitectureProjection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    detailed_node_count: int = Field(default=0, ge=0)
    high_level_node_count: int = Field(default=0, ge=0)
    projected_node_ids: list[str] = Field(default_factory=list)
    projected_edges: list[ProjectedEdge] = Field(default_factory=list)
    significances: list[ArchitecturalSignificance] = Field(default_factory=list)
    low_significance_refs: list[str] = Field(default_factory=list)
    unknown_refs: list[str] = Field(default_factory=list)

    @property
    def reduction_ratio(self) -> float:
        if not self.detailed_node_count:
            return 0.0
        return round(1.0 - self.high_level_node_count / self.detailed_node_count, 6)


class ArchitecturalProjectionBuilder:
    """Build a traceable high-level view without changing ArchitectureIR."""

    _ANCHOR_TYPES = {
        NodeType.REPOSITORY,
        NodeType.APPLICATION,
        NodeType.COMPONENT,
        NodeType.API,
        NodeType.ENDPOINT,
        NodeType.DATABASE,
        NodeType.CACHE,
        NodeType.QUEUE,
        NodeType.MESSAGE_BROKER,
        NodeType.CONTAINER,
        NodeType.EXTERNAL_SERVICE,
        NodeType.EXTERNAL_DEPENDENCY,
        NodeType.INFRASTRUCTURE,
    }
    _EDGE_WEIGHTS = {
        EdgeType.ROUTES_TO: 1.0,
        EdgeType.DEPENDS_ON: 0.75,
        EdgeType.QUERIES: 1.0,
        EdgeType.PUBLISHES: 1.0,
        EdgeType.CONSUMES: 1.0,
        EdgeType.CONNECTS_TO: 0.75,
        EdgeType.DEPLOYS: 0.5,
    }
    _INFRASTRUCTURE_KINDS = {"DATABASE", "CACHE", "QUEUE", "MESSAGE_BROKER", "CONTAINER", "SERVICE"}

    def build(self, ir: ArchitectureIR) -> HighLevelArchitectureProjection:
        raw_nodes = {node.id: node for node in ir.raw_graph.nodes}
        arch_nodes = {node.id: node for node in ir.architectural_graph.nodes}
        raw_to_arch = self._raw_to_arch(ir)
        evidence_ids = {item.id for item in ir.evidence}
        scores: dict[str, float] = defaultdict(float)
        refs: dict[str, set[str]] = defaultdict(set)
        reasons: dict[str, list[str]] = defaultdict(list)
        contains: dict[str, list[str]] = defaultdict(list)

        for node in arch_nodes.values():
            contains[node.id] = sorted(set(node.metadata.get("raw_node_ids", [])))
            node_refs = set(node.evidence_refs)
            for raw_id in contains[node.id]:
                raw = raw_nodes.get(raw_id)
                if raw:
                    node_refs.update(raw.evidence_refs)
            refs[node.id].update(node_refs & evidence_ids)
            if node.type in self._ANCHOR_TYPES:
                scores[node.id] += {
                    NodeType.APPLICATION: 4.0,
                    NodeType.COMPONENT: 3.0,
                    NodeType.API: 3.0,
                    NodeType.ENDPOINT: 3.0,
                    NodeType.REPOSITORY: 1.0,
                }.get(node.type, 2.5)
                reasons[node.id].append(f"semantic node type: {node.type.value}")

        for resource in ir.infrastructure_resources:
            refs[resource.id].update(set(resource.evidence_refs) & evidence_ids)
            if resource.kind.upper() in self._INFRASTRUCTURE_KINDS:
                scores[resource.id] += 3.0
                reasons[resource.id].append(f"observed infrastructure: {resource.kind}")

        candidate_index: dict[str, list[str]] = defaultdict(list)
        for candidate in ir.component_candidates:
            candidate_refs = set(candidate.evidence_refs) & evidence_ids
            for member in candidate.node_ids:
                subject = self._resolve(member, arch_nodes, raw_to_arch)
                if subject:
                    candidate_index[subject].append(candidate.id)
                    scores[subject] += 2.0
                    refs[subject].update(candidate_refs)
                    reasons[subject].append("component detection evidence")
                    if candidate.roles:
                        scores[subject] += 1.0
                        reasons[subject].append("semantic component role")

        framework_subjects: set[str] = set()
        for fact in ir.framework_facts:
            fact_refs = set(fact.evidence_refs) & evidence_ids
            for value in (fact.subject, fact.target, fact.attributes.get("endpoint"), fact.attributes.get("module")):
                subject = self._resolve(value, arch_nodes, raw_to_arch)
                if not subject:
                    continue
                framework_subjects.add(subject)
                scores[subject] += 3.0
                refs[subject].update(fact_refs)
                reasons[subject].append(f"framework fact: {fact.kind}")
                if fact.kind in {"APPLICATION", "HTTP_ENDPOINT", "CONTROLLER_LIKE"}:
                    scores[subject] += 1.0
                    reasons[subject].append("entrypoint or boundary fact")

        for edge in ir.architectural_graph.edges:
            weight = self._EDGE_WEIGHTS.get(edge.type, 0.0)
            if not weight or not edge.evidence_refs:
                continue
            for subject in (edge.source, edge.target):
                if subject in arch_nodes:
                    scores[subject] += min(weight, 1.0)
                    refs[subject].update(set(edge.evidence_refs) & evidence_ids)
                    reasons[subject].append(f"evidence-backed architectural relation: {edge.type.value}")

        for relation in ir.infrastructure_relations:
            for subject in (relation.source, relation.target):
                resolved = self._resolve(subject, arch_nodes, raw_to_arch)
                if resolved:
                    scores[resolved] += 1.5
                    refs[resolved].update(set(relation.evidence_refs) & evidence_ids)
                    reasons[resolved].append("explicit infrastructure relation")

        hypothesis_refs = {
            ref
            for hypothesis in ir.architecture.hypotheses
            for ref in hypothesis.evidence_refs
        }
        for subject in list(scores):
            if refs[subject] & hypothesis_refs:
                scores[subject] += 0.5
                reasons[subject].append("participates in an architecture hypothesis")

        significances: list[ArchitecturalSignificance] = []
        for subject in sorted(set(arch_nodes) | set(resource.id for resource in ir.infrastructure_resources)):
            node = arch_nodes.get(subject)
            score = min(scores.get(subject, 0.0) / 10.0, 1.0)
            has_refs = bool(refs.get(subject))
            anchored = subject in framework_subjects or subject in candidate_index or (node and node.type in {
                NodeType.REPOSITORY, NodeType.APPLICATION, NodeType.API, NodeType.ENDPOINT,
                NodeType.DATABASE, NodeType.CACHE, NodeType.QUEUE, NodeType.MESSAGE_BROKER,
                NodeType.CONTAINER, NodeType.EXTERNAL_SERVICE, NodeType.EXTERNAL_DEPENDENCY, NodeType.INFRASTRUCTURE,
            }) or subject in {item.id for item in ir.infrastructure_resources}
            if anchored and has_refs and score >= 0.30:
                level = SignificanceLevel.HIGH
            elif anchored and has_refs and score >= 0.15:
                level = SignificanceLevel.MEDIUM
            elif score > 0.0 and has_refs:
                level = SignificanceLevel.LOW
            else:
                level = SignificanceLevel.UNKNOWN
            significances.append(ArchitecturalSignificance(
                subject=subject,
                significance=level,
                score=round(score, 6),
                supporting_evidence=sorted(refs.get(subject, set())),
                evidence_refs=sorted(refs.get(subject, set())),
                reasons=sorted(set(reasons.get(subject, []))),
                contains_refs=contains.get(subject, []),
            ))

        selected = {
            item.subject
            for item in significances
            if item.significance in {SignificanceLevel.HIGH, SignificanceLevel.MEDIUM}
        }
        repository_ids = {node.id for node in arch_nodes.values() if node.type == NodeType.REPOSITORY}
        selected.update(repository_ids)
        selected &= set(arch_nodes) | set(resource.id for resource in ir.infrastructure_resources)
        projected_edges = self._project_edges(ir, selected, arch_nodes, raw_to_arch)
        low_refs = sorted({ref for item in significances if item.significance == SignificanceLevel.LOW for ref in item.contains_refs or [item.subject]})
        unknown_refs = sorted({ref for item in significances if item.significance == SignificanceLevel.UNKNOWN for ref in item.contains_refs or [item.subject]})
        return HighLevelArchitectureProjection(
            detailed_node_count=len(arch_nodes) + len(ir.infrastructure_resources),
            high_level_node_count=len(selected),
            projected_node_ids=sorted(selected),
            projected_edges=projected_edges,
            significances=significances,
            low_significance_refs=low_refs,
            unknown_refs=unknown_refs,
        )

    def _project_edges(self, ir: ArchitectureIR, selected: set[str], arch_nodes: dict[str, Node], raw_to_arch: dict[str, str]) -> list[ProjectedEdge]:
        grouped: dict[tuple[str, str, str], dict[str, Any]] = {}
        for edge in ir.architectural_graph.edges:
            source = self._selected_owner(edge.source, selected, arch_nodes, raw_to_arch)
            target = self._selected_owner(edge.target, selected, arch_nodes, raw_to_arch)
            if not source or not target or source == target:
                continue
            key = (source, target, edge.type.value)
            item = grouped.setdefault(key, {"refs": set(), "raw": set(), "edges": [], "confidence": 1.0, "status": edge.status})
            item["refs"].update(edge.evidence_refs)
            item["raw"].update(edge.raw_edge_ids or ([edge.id] if edge.id else []))
            item["edges"].append(edge)
            item["confidence"] = min(item["confidence"], edge.confidence)
            if edge.status == EvidenceStatus.UNCERTAIN:
                item["status"] = edge.status
        for relation in ir.infrastructure_relations:
            source = self._selected_owner(relation.source, selected, arch_nodes, raw_to_arch)
            target = self._selected_owner(relation.target, selected, arch_nodes, raw_to_arch)
            if not source or not target or source == target:
                continue
            key = (source, target, relation.type)
            item = grouped.setdefault(key, {"refs": set(), "raw": set(), "edges": [], "confidence": 1.0, "status": relation.status})
            item["refs"].update(relation.evidence_refs)
            item["raw"].add(relation.id)
            item["confidence"] = min(item["confidence"], relation.confidence)
            if relation.status == EvidenceStatus.UNCERTAIN:
                item["status"] = relation.status
        result: list[ProjectedEdge] = []
        for (source, target, kind), item in sorted(grouped.items()):
            result.append(ProjectedEdge(
                id=f"projection-edge:{source}:{target}:{kind}",
                source=source,
                target=target,
                kind=kind,
                status=item["status"],
                confidence=round(item["confidence"], 6),
                evidence_refs=sorted(item["refs"]),
                raw_edge_ids=sorted(item["raw"]),
                support_count=len(item["edges"]) or len(item["raw"]),
                supporting_observations=[{"edge_id": edge.id, "source": edge.source, "target": edge.target, "kind": edge.type.value} for edge in sorted(item["edges"], key=lambda value: value.id or "")],
            ))
        return result

    @staticmethod
    def _raw_to_arch(ir: ArchitectureIR) -> dict[str, str]:
        mapping: dict[str, str] = {}
        for node in ir.architectural_graph.nodes:
            for raw_id in node.metadata.get("raw_node_ids", []):
                mapping[raw_id] = node.id
        return mapping

    @staticmethod
    def _resolve(value: str | None, arch_nodes: dict[str, Node], raw_to_arch: dict[str, str]) -> str | None:
        if not value:
            return None
        if value in arch_nodes:
            return value
        if value in raw_to_arch:
            return raw_to_arch[value]
        if value.startswith("module:") and value in raw_to_arch:
            return raw_to_arch[value]
        module_name = value.split(":", 1)[-1].split(".", 1)[0]
        for raw_id, arch_id in raw_to_arch.items():
            if raw_id.endswith(f":{module_name}"):
                return arch_id
        return None

    def _selected_owner(self, value: str, selected: set[str], arch_nodes: dict[str, Node], raw_to_arch: dict[str, str]) -> str | None:
        resolved = self._resolve(value, arch_nodes, raw_to_arch) or value
        if resolved in selected:
            return resolved
        node = arch_nodes.get(resolved)
        if not node:
            return None
        raw_ids = set(node.metadata.get("raw_node_ids", []))
        for candidate in sorted(selected):
            parent = arch_nodes.get(candidate)
            if parent and raw_ids & set(parent.metadata.get("raw_node_ids", [])):
                return candidate
        return None


__all__ = [
    "ArchitecturalSignificance",
    "ArchitecturalProjectionBuilder",
    "HighLevelArchitectureProjection",
    "ProjectedEdge",
    "SignificanceLevel",
]